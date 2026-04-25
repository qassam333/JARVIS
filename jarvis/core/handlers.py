"""Skill handlers for the decision engine."""

from jarvis.core.intent_parser import Intent
from jarvis.core.brain import Response, Context
from jarvis.db.models import (
    TaskCreate,
    TaskUpdate,
    NoteCreate,
    KnowledgeCreate,
    TaskStatus,
)
from jarvis.skills.tasks import TaskService
from jarvis.skills.notes import NoteService
from jarvis.skills.knowledge import KnowledgeService


def handle_add_task(intent: Intent, context: Context) -> Response:
    """Handle add task intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    title = intent.entities.get("title") or intent.entities.get("content", "")
    if not title:
        return Response(success=False, message="Please specify a task title")

    service = TaskService(context.db)

    task = service.create(
        TaskCreate(
            title=title,
            description=intent.entities.get("description"),
            energy_level=intent.entities.get("energy_level", 5),
            deadline=intent.entities.get("time"),
            priority=intent.entities.get("priority", 3),
        )
    )

    return Response(
        success=True,
        message=f"Task '{task.title}' created successfully",
        data=task,
    )


def handle_list_tasks(intent: Intent, context: Context) -> Response:
    """Handle list tasks intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    service = TaskService(context.db)
    tasks = service.list(status=TaskStatus.PENDING, limit=20)

    if not tasks:
        return Response(
            success=True,
            message="You have no pending tasks!",
        )

    task_list = "\n".join(
        [
            f"  {i+1}. {t.title} (Energy: {t.energy_level}, Priority: {t.priority})"
            for i, t in enumerate(tasks)
        ]
    )

    # Store task data for follow-up reference resolution
    task_data = [{"id": t.id, "title": t.title} for t in tasks]

    return Response(
        success=True,
        message=f"You have {len(tasks)} pending tasks:\n{task_list}",
        data=task_data,
    )


def handle_complete_task(intent: Intent, context: Context) -> Response:
    """Handle complete task intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    content = intent.entities.get("content", "")
    service = TaskService(context.db)

    tasks = service.list(status=TaskStatus.PENDING, limit=50)

    for task in tasks:
        if content.lower() in task.title.lower():
            completed = service.complete(task.id)
            return Response(
                success=True,
                message=f"Completed: {completed.title}",
            )

    return Response(
        success=False,
        message=f"Task '{content}' not found. Try listing your tasks first.",
    )


def handle_add_note(intent: Intent, context: Context) -> Response:
    """Handle add note intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    content = intent.entities.get("content", "")
    if not content:
        return Response(success=False, message="Please specify note content")

    service = NoteService(context.db)

    note = service.create(
        NoteCreate(
            content=content,
        )
    )

    return Response(
        success=True,
        message=f"Note saved: {note.id[:8]}...",
        data=note,
    )


def handle_search_notes(intent: Intent, context: Context) -> Response:
    """Handle search notes intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    query = intent.entities.get("content", "") or intent.entities.get("title", "")
    if not query:
        return Response(success=False, message="Please specify what to search")

    service = NoteService(context.db)
    notes = service.search(query)

    if not notes:
        return Response(success=True, message=f"No notes found for '{query}'")

    results = "\n".join(
        [f"  • {n.title or n.id[:8]}: {n.content[:50]}..." for n in notes[:5]]
    )

    return Response(
        success=True,
        message=f"Found {len(notes)} notes:\n{results}",
    )


def handle_add_knowledge(intent: Intent, context: Context) -> Response:
    """Handle add knowledge intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    fact = intent.entities.get("content", "") or intent.entities.get("fact", "")
    if not fact:
        return Response(success=False, message="Please specify what to remember")

    service = KnowledgeService(context.db)

    knowledge = service.create(KnowledgeCreate(fact=fact))

    return Response(
        success=True,
        message=f"Got it. I'll remember: {fact[:50]}...",
        data=knowledge,
    )


def handle_search_knowledge(intent: Intent, context: Context) -> Response:
    """Handle search knowledge intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    query = intent.entities.get("content", "")
    if not query:
        return Response(success=False, message="Please specify what to search")

    service = KnowledgeService(context.db)
    items = service.search(query)

    if not items:
        return Response(
            success=True, message=f"I don't have any knowledge about '{query}'"
        )

    results = "\n".join(
        [f"  • {k.category or 'General'}: {k.fact[:50]}..." for k in items[:5]]
    )

    return Response(
        success=True,
        message=f"What I know about '{query}':\n{results}",
    )


def handle_show_status(intent: Intent, context: Context) -> Response:
    """Handle show status intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.briefing import BriefingService

    briefing_service = BriefingService(context.db)
    message = briefing_service.quick_briefing()

    return Response(success=True, message=message)


def handle_briefing(intent: Intent, context: Context) -> Response:
    """Handle briefing intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.briefing import BriefingService

    briefing_service = BriefingService(context.db)
    message = briefing_service.generate(user_name=context.user_name)

    return Response(success=True, message=message)


def handle_schedule(intent: Intent, context: Context) -> Response:
    """Handle schedule intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.tasks import TaskService
    from jarvis.skills.schedule import ScheduleEngine, Task as ScheduleTask

    task_service = TaskService(context.db)
    engine = ScheduleEngine(context.db)

    pending = task_service.list(status=TaskStatus.PENDING, limit=20)

    if not pending:
        return Response(success=True, message="No pending tasks to schedule.")

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

    return Response(success=True, message=engine.format_schedule(schedule))


def handle_help(intent: Intent, context: Context) -> Response:
    """Handle help intent."""
    help_text = """
Here are some things you can ask me:

Tasks:
  • "add task [description]"
  • "remind me to [task]"
  • "what tasks do I have?"
  • "done [task name]"

Notes:
  • "add note [content]"
  • "search notes [query]"

Knowledge:
  • "remember that [fact]"
  • "what do I know about [topic]"

Schedule:
  • "briefing" - Get daily overview
  • "schedule" - Generate energy-aware schedule

University:
  • "sync university" - Sync with Moodle
  • "check assignments" - View university tasks

General:
  • "status"
  • "help"
"""
    return Response(success=True, message=help_text)


def handle_university_sync(intent: Intent, context: Context) -> Response:
    """Handle university sync intent."""
    if not context.db:
        return Response(success=False, message="Database not available")

    from jarvis.skills.university.sync import UniversitySync

    sync = UniversitySync(context.db)

    if not sync.is_configured():
        return Response(
            success=False,
            message="University not configured. Run 'jarvis university setup --moodle <url>' first.",
        )

    result = sync.sync()

    if result.success:
        return Response(
            success=True,
            message=f"University synced!\n"
            f"• {result.items_fetched} items fetched\n"
            f"• {result.tasks_created} tasks created",
        )
    else:
        return Response(
            success=False, message=f"Sync failed: {'; '.join(result.errors)}"
        )


def handle_unknown(intent: Intent, context: Context) -> Response:
    """Handle unknown intent."""
    return Response(
        success=False,
        message=f"I didn't understand that. Try 'help' for available commands.",
    )
