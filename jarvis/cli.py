"""CLI interface for JARVIS."""

import click
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from jarvis.db.database import Database
from jarvis.db.models import (
    TaskCreate,
    TaskUpdate,
    TaskStatus,
    NoteCreate,
    NoteUpdate,
    KnowledgeCreate,
)
from jarvis.skills.tasks import TaskService
from jarvis.skills.notes import NoteService
from jarvis.skills.knowledge import KnowledgeService
from jarvis.utils.logger import setup_logger, get_logger
from jarvis.utils.config import config

console = Console()
logger = get_logger("cli")


def get_db() -> Database:
    """Get database instance."""
    return Database(config.db_path)


def get_task_service() -> TaskService:
    """Get task service."""
    return TaskService(get_db())


def get_note_service() -> NoteService:
    """Get note service."""
    return NoteService(get_db())


def get_knowledge_service() -> KnowledgeService:
    """Get knowledge service."""
    return KnowledgeService(get_db())


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """JARVIS - Your Local AI Assistant"""
    pass


@cli.group()
def task():
    """Task management commands"""
    pass


@task.command("add")
@click.argument("title")
@click.option("--description", "-d", help="Task description")
@click.option("--energy", "-e", type=int, default=5, help="Energy level 1-10")
@click.option("--deadline", help="Deadline (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
@click.option("--priority", "-p", type=int, default=3, help="Priority 1-5")
@click.option("--tag", multiple=True, help="Add tags")
def task_add(
    title: str, description: str, energy: int, deadline: str, priority: int, tag: tuple
):
    """Add a new task"""
    deadline_dt = None
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace(" ", "T"))
        except ValueError:
            try:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            except ValueError:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")

    data = TaskCreate(
        title=title,
        description=description,
        energy_level=energy,
        deadline=deadline_dt,
        priority=priority,
        tags=list(tag),
    )

    service = get_task_service()
    task = service.create(data)

    console.print(f"[green]OK[/green] Task created: [bold]{task.title}[/bold]")
    console.print(f"  ID: {task.id}")
    if task.deadline:
        console.print(f"  Deadline: {task.deadline.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"  Energy: {task.energy_level}/10")
    console.print(f"  Priority: {task.priority}/5")


@task.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "completed", "cancelled"]),
    help="Filter by status",
)
@click.option("--source", help="Filter by source")
@click.option("--limit", type=int, default=20, help="Limit results")
def task_list(status: str, source: str, limit: int):
    """List tasks"""
    service = get_task_service()

    status_enum = TaskStatus(status) if status else None
    tasks = service.list(status=status_enum, source=source, limit=limit)

    if not tasks:
        console.print("[yellow]No tasks found[/yellow]")
        return

    table = Table(title=f"Tasks ({len(tasks)})")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title", style="bold")
    table.add_column("Status", width=10)
    table.add_column("Priority", justify="center", width=8)
    table.add_column("Energy", justify="center", width=6)
    table.add_column("Deadline", width=12)

    for t in tasks:
        status_color = {
            "pending": "yellow",
            "completed": "green",
            "cancelled": "red",
        }.get(t.status, "white")

        deadline_str = t.deadline.strftime("%Y-%m-%d %H:%M") if t.deadline else "-"

        table.add_row(
            t.id[:8],
            t.title[:40] + ("..." if len(t.title) > 40 else ""),
            f"[{status_color}]{t.status}[/{status_color}]",
            str(t.priority),
            str(t.energy_level),
            deadline_str,
        )

    console.print(table)


@task.command("view")
@click.argument("task_id")
def task_view(task_id: str):
    """View task details"""
    service = get_task_service()
    task = service.get(task_id)

    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        return

    status_color = {
        "pending": "yellow",
        "completed": "green",
        "cancelled": "red",
    }.get(task.status, "white")

    panel = Panel(
        f"[bold cyan]Title:[/bold cyan] {task.title}\n\n"
        f"[bold cyan]Status:[/bold cyan] [{status_color}]{task.status}[/{status_color}]\n"
        f"[bold cyan]Priority:[/bold cyan] {task.priority}/5\n"
        f"[bold cyan]Energy:[/bold cyan] {task.energy_level}/10\n"
        f"[bold cyan]Source:[/bold cyan] {task.source}\n"
        f"[bold cyan]Deadline:[/bold cyan] {task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else 'None'}\n"
        f"[bold cyan]Created:[/bold cyan] {task.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        + (
            f"[bold cyan]Completed:[/bold cyan] {task.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
            if task.completed_at
            else ""
        )
        + (
            f"\n[bold cyan]Description:[/bold cyan]\n{task.description}\n"
            if task.description
            else ""
        )
        + (
            f"\n[bold cyan]Tags:[/bold cyan] {', '.join(task.tags)}\n"
            if task.tags
            else ""
        ),
        title=f"Task: {task_id[:8]}",
        border_style="blue",
    )
    console.print(panel)


@task.command("done")
@click.argument("task_id")
def task_done(task_id: str):
    """Mark task as completed"""
    service = get_task_service()
    task = service.complete(task_id)

    if task:
        console.print(f"[green]OK[/green] Task completed: {task.title}")
    else:
        console.print(f"[red]Task not found: {task_id}[/red]")


@task.command("delete")
@click.argument("task_id")
@click.option("--force", is_flag=True, help="Skip confirmation")
def task_delete(task_id: str, force: bool):
    """Delete a task"""
    if not force:
        if (
            not console.input(f"Delete task {task_id[:8]}? [y/N] ")
            .lower()
            .startswith("y")
        ):
            console.print("Cancelled")
            return

    service = get_task_service()
    if service.delete(task_id):
        console.print(f"[green]OK[/green] Task deleted")
    else:
        console.print(f"[red]Task not found: {task_id}[/red]")


@cli.group()
def note():
    """Note management commands"""
    pass


@note.command("add")
@click.argument("title", required=False)
@click.option("--content", "-c", help="Note content")
@click.option("--tag", multiple=True, help="Add tags")
def note_add(title: str, content: str, tag: tuple):
    """Add a new note"""
    if not title and not content:
        console.print("[red]Either title or content is required[/red]")
        return

    data = NoteCreate(
        title=title,
        content=content or title or "",
        tags=list(tag),
    )

    service = get_note_service()
    note = service.create(data)

    console.print(
        f"[green]OK[/green] Note created: [bold]{note.title or note.id[:8]}[/bold]"
    )
    console.print(f"  ID: {note.id}")


@note.command("list")
@click.option("--tag", help="Filter by tag")
@click.option("--limit", type=int, default=20)
def note_list(tag: str, limit: int):
    """List notes"""
    service = get_note_service()
    notes = service.list(tag=tag, limit=limit)

    if not notes:
        console.print("[yellow]No notes found[/yellow]")
        return

    table = Table(title=f"Notes ({len(notes)})")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Title")
    table.add_column("Preview", style="dim")
    table.add_column("Tags")

    for n in notes:
        preview = n.content[:50] + ("..." if len(n.content) > 50 else "")
        table.add_row(
            n.id[:8],
            n.title or "-",
            preview,
            ", ".join(n.tags) if n.tags else "-",
        )

    console.print(table)


@note.command("search")
@click.argument("query")
def note_search(query: str):
    """Search notes"""
    service = get_note_service()
    notes = service.search(query)

    if not notes:
        console.print(f"[yellow]No notes found matching '{query}'[/yellow]")
        return

    console.print(f"[green]Found {len(notes)} notes:[/green]")
    for n in notes:
        console.print(f"\n[bold]{n.title or n.id[:8]}[/bold]")
        console.print(f"  {n.content[:100]}...")


@note.command("delete")
@click.argument("note_id")
@click.option("--force", is_flag=True)
def note_delete(note_id: str, force: bool):
    """Delete a note"""
    if not force:
        if (
            not console.input(f"Delete note {note_id[:8]}? [y/N] ")
            .lower()
            .startswith("y")
        ):
            console.print("Cancelled")
            return

    service = get_note_service()
    if service.delete(note_id):
        console.print("[green]OK[/green] Note deleted")
    else:
        console.print(f"[red]Note not found: {note_id}[/red]")


@cli.group()
def know():
    """Knowledge management commands"""
    pass


@know.command("add")
@click.argument("fact")
@click.option("--category", "-c", help="Category")
@click.option("--source", "-s", help="Source")
@click.option("--tag", multiple=True)
def know_add(fact: str, category: str, source: str, tag: tuple):
    """Add knowledge"""
    data = KnowledgeCreate(
        fact=fact,
        category=category,
        source=source,
        tags=list(tag),
    )

    service = get_knowledge_service()
    knowledge = service.create(data)

    console.print(f"[green]OK[/green] Knowledge added")
    console.print(f"  ID: {knowledge.id}")
    if knowledge.category:
        console.print(f"  Category: {knowledge.category}")


@know.command("list")
@click.option("--category", help="Filter by category")
@click.option("--limit", type=int, default=20)
def know_list(category: str, limit: int):
    """List knowledge"""
    service = get_knowledge_service()
    items = service.list(category=category, limit=limit)

    if not items:
        console.print("[yellow]No knowledge found[/yellow]")
        return

    table = Table(title=f"Knowledge ({len(items)})")
    table.add_column("ID", style="dim", width=8)
    table.add_column("Fact")
    table.add_column("Category", style="cyan")

    for k in items:
        table.add_row(
            k.id[:8],
            k.fact[:60] + ("..." if len(k.fact) > 60 else ""),
            k.category or "-",
        )

    console.print(table)


@know.command("search")
@click.argument("query")
def know_search(query: str):
    """Search knowledge"""
    service = get_knowledge_service()
    items = service.search(query)

    if not items:
        console.print(f"[yellow]No knowledge found for '{query}'[/yellow]")
        return

    console.print(f"[green]Found {len(items)} items:[/green]")
    for k in items:
        console.print(f"\n[cyan]{k.category or 'General'}:[/cyan] {k.fact}")


@cli.command()
def status():
    """Show JARVIS status"""
    service = get_task_service()

    pending = service.count(TaskStatus.PENDING)
    completed_today = len(
        [
            t
            for t in service.list(status=TaskStatus.COMPLETED, limit=100)
            if t.completed_at and t.completed_at.date() == datetime.utcnow().date()
        ]
    )
    due_today = len(service.get_due_today())

    console.print(
        Panel(
            f"[bold cyan]JARVIS v0.1.0[/bold cyan]\n\n"
            f"[green]Pending tasks:[/green] {pending}\n"
            f"[yellow]Due today:[/yellow] {due_today}\n"
            f"[green]Completed today:[/green] {completed_today}",
            title="Status",
            border_style="blue",
        )
    )


@cli.command()
@click.argument("text")
def ask(text: str):
    """Ask JARVIS anything (natural language)"""
    from jarvis.jarvis import Jarvis

    jarvis = Jarvis(str(config.db_path))
    response = jarvis.process(text)
    console.print(response)


@cli.command()
def shell():
    """Interactive shell mode"""
    from jarvis.jarvis import Jarvis

    jarvis = Jarvis(str(config.db_path))
    jarvis.initialize()

    console.print(
        Panel(
            "[bold cyan]JARVIS Interactive Shell[/bold cyan]\n\n"
            "Type natural language commands. Press Ctrl+C to exit.\n\n"
            "Examples:\n"
            "  add task Study Python\n"
            "  what tasks do I have?\n"
            "  remember that I like coffee\n"
            "  add note Meeting at 3pm\n"
            "  briefing\n"
            "  schedule",
            title="Welcome",
            border_style="blue",
        )
    )

    try:
        while True:
            try:
                user_input = console.input("\n[bold green]>[/bold green] ")
                if user_input.strip():
                    response = jarvis.process(user_input)
                    console.print(f"\n{response}")
            except KeyboardInterrupt:
                break
    except EOFError:
        pass

    console.print("\n[dim]Goodbye![/dim]")


@cli.command()
def briefing():
    """Get daily briefing"""
    from jarvis.skills.briefing import BriefingService

    service = BriefingService(get_db())
    briefing = service.generate()
    console.print(Panel(briefing, title="Daily Briefing", border_style="cyan"))


@cli.command()
def schedule():
    """Generate energy-aware schedule"""
    from jarvis.skills.tasks import TaskService
    from jarvis.skills.schedule import ScheduleEngine, Task as ScheduleTask
    from jarvis.db.models import TaskStatus

    task_service = TaskService(get_db())
    engine = ScheduleEngine(get_db())

    pending = task_service.list(status=TaskStatus.PENDING, limit=20)

    if not pending:
        console.print("[yellow]No pending tasks to schedule.[/yellow]")
        return

    schedule_tasks = [
        ScheduleTask(
            id=t.id,
            title=t.title,
            energy_level=t.energy_level,
            deadline=t.deadline,
            priority=t.priority,
            status=t.status,
        )
        for t in pending
    ]

    schedule = engine.generate_schedule(schedule_tasks, max_hours=5)

    console.print(engine.format_schedule(schedule))


def init():
    """Initialize database"""
    db = get_db()
    db.initialize()
    console.print("[green]OK[/green] Database initialized successfully")


@cli.group()
def university():
    """University integration commands"""
    pass


@university.command("setup")
@click.option("--moodle", required=True, help="Moodle URL")
def university_setup(moodle: str):
    """Setup university connection"""
    from jarvis.skills.university.sync import UniversitySync

    username = console.input("Username: ")
    password = console.input("Password: ", hide_input=True)

    sync = UniversitySync(get_db())
    try:
        sync.setup(moodle, username, password)
        console.print("[green]OK[/green] University connected successfully!")
    except Exception as e:
        console.print(f"[red]Failed to setup: {e}[/red]")


@university.command("sync")
def university_sync():
    """Sync university data"""
    from jarvis.skills.university.sync import UniversitySync

    sync = UniversitySync(get_db())

    if not sync.is_configured():
        console.print(
            "[yellow]University not configured. Run 'jarvis university setup --moodle <url>'[/yellow]"
        )
        return

    console.print("[yellow]Syncing with university...[/yellow]")
    result = sync.sync()

    if result.success:
        console.print(f"[green]OK[/green] Sync completed!")
        console.print(f"  Courses: {result.courses_updated}")
        console.print(f"  Items fetched: {result.items_fetched}")
        console.print(f"  Tasks created: {result.tasks_created}")
    else:
        console.print("[red]Sync failed:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")


@university.command("courses")
def university_courses():
    """List university courses"""
    from jarvis.skills.university.sync import UniversitySync

    sync = UniversitySync(get_db())
    courses = sync.get_courses()

    if not courses:
        console.print("[yellow]No courses found[/yellow]")
        return

    table = Table(title=f"Courses ({len(courses)})")
    table.add_column("Code", style="cyan")
    table.add_column("Name")

    for course in courses:
        table.add_row(course.get("code", "-"), course.get("name", "Unknown"))

    console.print(table)


@university.command("tasks")
@click.option("--type", help="Filter by type")
def university_tasks(type: str):
    """List university assignments"""
    from jarvis.skills.university.sync import UniversitySync
    from jarvis.skills.university.models import AssignmentType

    sync = UniversitySync(get_db())
    type_enum = AssignmentType(type) if type else None
    assignments = sync.get_assignments(assignment_type=type_enum)

    if not assignments:
        console.print("[yellow]No assignments found[/yellow]")
        return

    table = Table(title=f"Assignments ({len(assignments)})")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Due")

    for a in assignments:
        due = a.get("due_date", "-")
        table.add_row(a.get("title", "")[:40], a.get("type", "-"), due)

    console.print(table)


@university.command("status")
def university_status():
    """Show university connection status"""
    from jarvis.skills.university.sync import UniversitySync

    sync = UniversitySync(get_db())

    if not sync.is_configured():
        console.print("[yellow]University not configured[/yellow]")
        console.print("Run 'jarvis university setup --moodle <url>' to configure")
        return

    last_sync = sync.get_last_sync()
    console.print(f"[green]University connected[/green]")
    console.print(
        f"Last sync: {last_sync.strftime('%Y-%m-%d %H:%M') if last_sync else 'Never'}"
    )


@cli.command(name="voice")
@click.option("--test", is_flag=True, help="Test voice interface setup")
@click.option("--ptt", is_flag=True, help="Push-to-talk mode")
@click.option("--continuous", is_flag=True, help="Continuous listening mode")
def voice(test, ptt, continuous):
    """Voice interface commands"""
    from jarvis.voice.voice_cli import run_voice_interface
    from jarvis.jarvis import Jarvis

    mode = "continuous" if continuous else "wake"

    try:
        if not test:
            jarvis_brain = Jarvis(str(config.db_path))
            jarvis_brain.initialize()
        else:
            jarvis_brain = None
            
        run_voice_interface(mode=mode, test=test, push_to_talk=ptt, brain=jarvis_brain)
    except KeyboardInterrupt:
        console.print("\n[yellow]Voice interface stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Voice interface error: {e}")


@cli.group()
def profile():
    """User profile commands"""
    pass


@profile.command("list")
def profile_list():
    """Show user profile"""
    from jarvis.skills.profile import ProfileService

    service = ProfileService(get_db())
    p = service.get_profile()

    console.print(
        Panel(
            f"[bold]User Profile[/bold]\n\n"
            f"Name: {p.name or 'Not set'}\n"
            f"Work Style: {p.work_style}\n"
            f"Grad Deadline: {p.grad_deadline or 'Not set'}\n"
            f"Graduation: {p.graduation_date or 'Not set'}\n"
            f"Job Preference: {p.job_preference}\n"
            f"Accountability: {p.accountability_style}",
            title="Profile",
        )
    )


@profile.command("set")
@click.argument("key")
@click.argument("value")
def profile_set(key, value):
    """Set profile value"""
    from jarvis.skills.profile import ProfileService
    from datetime import date

    service = ProfileService(get_db())

    if key in ["grad_deadline", "graduation_date"]:
        value = date.fromisoformat(value)

    service.set_preference(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")


@cli.group()
def goal():
    """Goal management commands"""
    pass


@goal.command("list")
@click.option("--area", help="Filter by area")
def goal_list(area):
    """List all goals"""
    from jarvis.skills.goals import GoalService
    from jarvis.skills.profile import ProfileService

    goal_service = GoalService(get_db())
    profile_service = ProfileService(get_db())

    goals = goal_service.get_goals(area_id=area, parent_only=True)
    areas = {a.id: a.name for a in profile_service.get_life_areas()}

    if not goals:
        console.print("[yellow]No goals found[/yellow]")
        return

    table = Table(title=f"Goals ({len(goals)})")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Area", style="green")
    table.add_column("Progress", style="yellow")
    table.add_column("Deadline")

    for g in goals:
        area_name = areas.get(g.area_id, "-") if g.area_id else "-"
        deadline = g.target_date.strftime("%Y-%m-%d") if g.target_date else "-"
        table.add_row(g.id, g.title[:30], area_name, f"{g.progress}%", deadline)

    console.print(table)


@goal.command("add")
@click.argument("title")
@click.option("--area", help="Life area ID")
@click.option("--deadline", help="Target date (YYYY-MM-DD)")
@click.option(
    "--priority", default="medium", help="Priority: low, medium, high, critical"
)
def goal_add(title, area, deadline, priority):
    """Add a new goal"""
    from jarvis.skills.goals import GoalService
    from datetime import date

    service = GoalService(get_db())

    target = date.fromisoformat(deadline) if deadline else None

    goal_id = service.create_goal(
        title=title, area_id=area, target_date=target, priority=priority
    )

    console.print(f"[green]Created goal: {title} ({goal_id})[/green]")


@goal.command("progress")
@click.argument("goal_id")
@click.argument("progress", type=int)
def goal_progress(goal_id, progress):
    """Update goal progress"""
    from jarvis.skills.goals import GoalService

    service = GoalService(get_db())
    service.update_progress(goal_id, progress)

    console.print(f"[green]Updated {goal_id} to {progress}%[/green]")


@goal.command("view")
@click.argument("goal_id")
def goal_view(goal_id):
    """View goal details"""
    from jarvis.skills.goals import GoalService
    from jarvis.skills.profile import ProfileService

    goal_service = GoalService(get_db())
    profile_service = ProfileService(get_db())

    goal = goal_service.get_goal(goal_id)
    if not goal:
        console.print("[red]Goal not found[/red]")
        return

    milestones = goal_service.get_milestones(goal_id)
    areas = {a.id: a.name for a in profile_service.get_life_areas()}

    console.print(
        Panel(
            f"[bold]{goal.title}[/bold]\n\n"
            f"Area: {areas.get(goal.area_id, '-')}\n"
            f"Progress: {goal.progress}%\n"
            f"Priority: {goal.priority}\n"
            f"Status: {goal.status}\n"
            f"Deadline: {goal.target_date or '-'}\n"
            f"Description: {goal.description or '-'}",
            title=f"Goal: {goal_id}",
        )
    )

    if milestones:
        console.print("\n[bold]Milestones:[/bold]")
        for m in milestones:
            status = (
                "[green]Done[/green]" if m.completed else "[yellow]Pending[/yellow]"
            )
            console.print(f"  [{status}] {m.title} ({m.progress}%)")


@cli.group()
def habit():
    """Habit tracking commands"""
    pass


@habit.command("list")
def habit_list():
    """List all habits"""
    from jarvis.skills.habits import HabitService
    from jarvis.skills.profile import ProfileService
    from datetime import date

    habit_service = HabitService(get_db())
    profile_service = ProfileService(get_db())

    habits = habit_service.get_habits()
    areas = {a.id: a.name for a in profile_service.get_life_areas()}

    today = date.today()
    today_logs = {log.habit_id: log for log in habit_service.get_today_logs()}

    if not habits:
        console.print("[yellow]No habits found[/yellow]")
        return

    table = Table(title=f"Habits ({len(habits)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Area")
    table.add_column("Streak", style="yellow")
    table.add_column("Today")

    for h in habits:
        area_name = areas.get(h.linked_area_id, "-") if h.linked_area_id else "-"
        today_status = (
            "[green]Done[/green]" if h.id in today_logs else "[red]Pending[/red]"
        )
        table.add_row(
            h.id, h.name[:25], area_name, f"{h.current_streak}d", today_status
        )

    console.print(table)


@habit.command("add")
@click.argument("name")
@click.option("--frequency", default="daily", help="Frequency: daily, weekly")
@click.option("--time", default="evening", help="Time of day: morning, evening")
@click.option("--area", help="Life area ID")
@click.option("--duration", type=int, help="Duration in minutes")
def habit_add(name, frequency, time, area, duration):
    """Add a new habit"""
    from jarvis.skills.habits import HabitService

    service = HabitService(get_db())
    habit_id = service.create_habit(
        name=name,
        frequency=frequency,
        time_of_day=time,
        linked_area_id=area,
        duration_minutes=duration,
    )

    console.print(f"[green]Created habit: {name} ({habit_id})[/green]")


@habit.command("log")
@click.argument("habit_id")
@click.option("--pages", type=int, help="Pages completed (for Quran)")
@click.option("--duration", type=int, help="Duration in minutes")
def habit_log(habit_id, pages, duration):
    """Log habit completion"""
    from jarvis.skills.habits import HabitService

    service = HabitService(get_db())
    service.log_habit(habit_id, pages=pages, duration_minutes=duration)

    console.print(f"[green]Logged habit {habit_id}[/green]")


@habit.command("check")
@click.argument("habit_id")
def habit_check(habit_id):
    """Quick check for habit"""
    from jarvis.skills.habits import HabitService

    service = HabitService(get_db())
    service.check_habit(habit_id)

    console.print(f"[green]Marked habit {habit_id} as complete for today[/green]")


@habit.command("stats")
@click.argument("habit_id", required=False)
def habit_stats(habit_id):
    """Show habit statistics"""
    from jarvis.skills.habits import HabitService

    service = HabitService(get_db())

    if habit_id:
        stats = service.get_stats(habit_id)
        console.print(
            Panel(
                f"[bold]{stats['name']}[/bold]\n\n"
                f"Current Streak: {stats['current_streak']} days\n"
                f"Best Streak: {stats['best_streak']} days\n"
                f"Total Completions: {stats['total_completions']}\n"
                f"Total Pages: {stats.get('total_pages', 0)}\n"
                f"Last 30 Days: {stats['last_30_days_completion']}%",
                title="Habit Stats",
            )
        )
    else:
        all_stats = service.get_all_stats()
        console.print(
            f"\n[bold]Today:[/bold] {all_stats['today_completed']}/{all_stats['today_pending'] + all_stats['today_completed']} completed\n"
        )

        for h in all_stats["habits"]:
            console.print(
                f"  {h['name']}: {h['current_streak']}d streak ({h['last_30_days_completion']}%)"
            )


@cli.group()
def review():
    """Review commands"""
    pass


@review.command("daily")
@click.option("--mood", type=int, help="Mood 1-10")
@click.option("--energy", type=int, help="Energy 1-10")
@click.option("--productivity", type=int, help="Productivity 1-10")
@click.option("--notes", help="Notes")
def review_daily(mood, energy, productivity, notes):
    """Create daily review"""
    from jarvis.skills.reviews import ReviewService

    service = ReviewService(get_db())
    service.create_daily_review(
        mood=mood, energy_level=energy, productivity_score=productivity, notes=notes
    )

    console.print("[green]Daily review saved[/green]")


@review.command("weekly")
def review_weekly():
    """Show weekly summary"""
    from jarvis.skills.reviews import ReviewService

    service = ReviewService(get_db())
    summary = service.generate_weekly_summary()
    stats = service.get_this_week_stats()

    console.print(
        Panel(
            f"[bold]This Week's Summary[/bold]\n\n"
            f"Habits Completed: {stats['completed_habits']}/{stats['habits_expected']}\n"
            f"Completion Rate: {stats['completion_rate']}%\n"
            f"Days Reviewed: {summary['days_reviewed']}\n"
            f"Avg Productivity: {summary.get('avg_productivity') or '-'}/10",
            title="Weekly Review",
        )
    )


@cli.group()
def accountability():
    """Accountability commands"""
    pass


@accountability.command("today")
def accountability_today():
    """Show today's accountability"""
    from jarvis.skills.profile import ProfileService
    from jarvis.skills.goals import GoalService
    from jarvis.skills.habits import HabitService
    from jarvis.skills.reviews import ReviewService
    from jarvis.skills.accountability import AccountabilityEngine

    profile_service = ProfileService(get_db())
    goal_service = GoalService(get_db())
    habit_service = HabitService(get_db())
    review_service = ReviewService(get_db())

    engine = AccountabilityEngine(
        get_db(), profile_service, goal_service, habit_service, review_service
    )

    message = engine.get_today_preview()
    console.print(Panel(message, title="Today's Focus"))


@accountability.command("push")
def accountability_push():
    """Get motivational push"""
    from jarvis.skills.profile import ProfileService
    from jarvis.skills.goals import GoalService
    from jarvis.skills.habits import HabitService
    from jarvis.skills.reviews import ReviewService
    from jarvis.skills.accountability import AccountabilityEngine

    profile_service = ProfileService(get_db())
    goal_service = GoalService(get_db())
    habit_service = HabitService(get_db())
    review_service = ReviewService(get_db())

    engine = AccountabilityEngine(
        get_db(), profile_service, goal_service, habit_service, review_service
    )

    message = engine.get_motivation_message()
    console.print(f"[bold yellow]{message}[/bold yellow]")


@accountability.command("overdue")
def accountability_overdue():
    """Show overdue items"""
    from jarvis.skills.profile import ProfileService
    from jarvis.skills.goals import GoalService
    from jarvis.skills.habits import HabitService
    from jarvis.skills.reviews import ReviewService
    from jarvis.skills.accountability import AccountabilityEngine

    profile_service = ProfileService(get_db())
    goal_service = GoalService(get_db())
    habit_service = HabitService(get_db())
    review_service = ReviewService(get_db())

    engine = AccountabilityEngine(
        get_db(), profile_service, goal_service, habit_service, review_service
    )

    messages = engine.get_overdue_warning()

    if messages:
        for msg in messages:
            console.print(Panel(msg, style="red"))
    else:
        console.print("[green]No overdue items[/green]")


@accountability.command("countdown")
def accountability_countdown():
    """Show graduation countdown"""
    from jarvis.skills.profile import ProfileService
    from jarvis.skills.goals import GoalService
    from jarvis.skills.habits import HabitService
    from jarvis.skills.reviews import ReviewService
    from jarvis.skills.accountability import AccountabilityEngine

    profile_service = ProfileService(get_db())
    goal_service = GoalService(get_db())
    habit_service = HabitService(get_db())
    review_service = ReviewService(get_db())

    engine = AccountabilityEngine(
        get_db(), profile_service, goal_service, habit_service, review_service
    )

    message = engine.get_graduation_countdown()
    if message:
        console.print(Panel(message, title="Graduation Countdown", style="yellow"))
    else:
        console.print("[yellow]No graduation date set[/yellow]")


@cli.command("setup-life")
def setup_life():
    """Initial setup for life management"""
    from jarvis.skills.setup_life import run_initial_setup

    run_initial_setup()


@cli.command(name="dashboard")
def dashboard():
    """Start the JARVIS dashboard (web UI)"""
    import subprocess
    import sys
    import os
    from pathlib import Path

    dashboard_dir = Path(__file__).parent / "dashboard"
    start_script = dashboard_dir / "start.sh"
    start_script.chmod(0o755)

    console.print("[cyan]Starting JARVIS Dashboard...[/cyan]")
    console.print("")
    console.print("[yellow]Dashboard will open at:[/yellow] http://localhost:8080")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    console.print("")

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(dashboard_dir.parent.parent)
        subprocess.run(["bash", str(start_script)], cwd=str(dashboard_dir), env=env)
    except KeyboardInterrupt:
        console.print("\n[green]Dashboard stopped[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Dashboard error: {e}")


def main():
    """Entry point."""
    setup_logger(level=config.log_level, debug=config.debug)
    cli()


if __name__ == "__main__":
    main()
