"""Initial setup for JARVIS Life Management with your profile."""

from datetime import date
from jarvis.db.database import Database
from jarvis.skills.profile import ProfileService
from jarvis.skills.goals import GoalService
from jarvis.skills.habits import HabitService
from jarvis.skills.reviews import ReviewService
from jarvis.skills.accountability import AccountabilityEngine
from jarvis.utils.logger import get_logger

logger = get_logger("setup")


def run_initial_setup():
    print("=" * 60)
    print("JARVIS LIFE MANAGEMENT - INITIAL SETUP")
    print("=" * 60)
    print()

    db = Database()

    profile_service = ProfileService(db)
    goal_service = GoalService(db)
    habit_service = HabitService(db)
    review_service = ReviewService(db)

    print("[1/5] Setting up your profile...")
    profile_service.update_profile(
        name="Deep",
        work_style="evening",
        grad_deadline=date(2026, 6, 1),
        graduation_date=date(2026, 7, 1),
        job_preference="hybrid",
        preferred_language="english",
        accountability_style="strict_motivational",
        explicit_preferences={
            "work_days": ["sat", "sun", "mon"],
            "grad_session_hours": "3-5",
            "evening_block": "18:00-22:00",
            "peak_hours": ["18:00-22:00"],
            "third_language": None,
        },
    )
    print("  - Profile updated: Deep, evening worker, hybrid jobs")
    print("  - Grad deadline: June 1, 2026")
    print()

    print("[2/5] Creating life areas...")
    areas = profile_service.get_life_areas()
    for area in areas:
        print(f"  - {area.name}")
    print()

    print("[3/5] Setting up your goals...")

    career_id = "career"
    projects_id = "projects"
    learning_id = "learning"
    religion_id = "religion"
    health_id = "health"

    goals_created = []

    grad_project_id = goal_service.create_goal(
        title="Graduation Project",
        area_id=career_id,
        description="Complete and submit graduation project",
        target_date=date(2026, 6, 1),
        priority="critical",
    )
    goals_created.append(("Graduation Project", grad_project_id))

    goal_service.add_milestone(grad_project_id, "Proposal approved", order_index=0)
    goal_service.add_milestone(grad_project_id, "Chapter 1-3 complete", order_index=1)
    goal_service.add_milestone(grad_project_id, "Implementation done", order_index=2)
    goal_service.add_milestone(
        grad_project_id, "Final submission", target_date=date(2026, 6, 1), order_index=3
    )

    linkit_id = goal_service.create_goal(
        title="LINKIT MVP",
        area_id=projects_id,
        description="Ready for polish and better art",
        priority="high",
    )
    goals_created.append(("LINKIT MVP", linkit_id))

    goal_service.add_milestone(linkit_id, "Core gameplay polish", order_index=0)
    goal_service.add_milestone(linkit_id, "Better art assets", order_index=1)
    goal_service.add_milestone(linkit_id, "Testing and QA", order_index=2)
    goal_service.add_milestone(linkit_id, "Release-ready", order_index=3)

    legendary_id = goal_service.create_goal(
        title="Legendary Mansaf",
        area_id=projects_id,
        description="Second game project after LINKIT",
        priority="medium",
    )
    goals_created.append(("Legendary Mansaf", legendary_id))

    goal_service.add_milestone(legendary_id, "Lore and writing complete", order_index=0)
    goal_service.add_milestone(legendary_id, "Art style defined", order_index=1)
    goal_service.add_milestone(legendary_id, "Prototype", order_index=2)
    goal_service.add_milestone(legendary_id, "Alpha ready", order_index=3)

    afterfall_id = goal_service.create_goal(
        title="Afterfall",
        area_id=projects_id,
        description="Long-term AAA project",
        priority="low",
    )
    goals_created.append(("Afterfall", afterfall_id))

    goal_service.create_goal(
        title="UE5 Mastery",
        area_id=career_id,
        description="Become professional at Unreal Engine 5",
        target_date=date(2026, 7, 1),
        priority="high",
    )

    goal_service.create_goal(
        title="Job Search",
        area_id=career_id,
        description="Find a job to fund O4 Studio",
        target_date=date(2026, 8, 1),
        priority="high",
    )

    goal_service.create_goal(
        title="Portfolio",
        area_id=career_id,
        description="Build professional game dev portfolio",
        priority="high",
    )

    python_goal_id = goal_service.create_goal(
        title="Python Mastery",
        area_id=learning_id,
        description="Master Python for game dev and tools",
        priority="medium",
    )

    goal_service.create_goal(
        title="English Fluency",
        area_id=learning_id,
        description="Improve English for professional use",
        priority="medium",
    )

    goal_service.create_goal(
        title="Third Language",
        area_id=learning_id,
        description="Learn French or German for market value",
        priority="medium",
    )

    goal_service.create_goal(
        title="IT Breadth",
        area_id=learning_id,
        description="Learn cloud, security, networking basics",
        priority="low",
    )

    for goal_name, goal_id in goals_created:
        print(f"  - {goal_name} ({goal_id})")
    print()

    print("[4/5] Setting up your habits...")

    quran_id = habit_service.create_habit(
        name="Quran Recitation",
        description="Read and recite Quran daily",
        frequency="daily",
        time_of_day="morning",
        linked_goal_id=None,
        linked_area_id=religion_id,
        duration_minutes=30,
    )

    prayer_id = habit_service.create_habit(
        name="Prayer (5x Daily)",
        description="Pray all 5 daily prayers",
        frequency="daily",
        time_of_day="evening",
        linked_area_id=religion_id,
    )

    ue5_id = habit_service.create_habit(
        name="UE5 Practice",
        description="Practice Unreal Engine 5",
        frequency="daily",
        time_of_day="evening",
        linked_area_id=career_id,
        duration_minutes=90,
    )

    linkit_dev_id = habit_service.create_habit(
        name="LINKIT Development",
        description="Work on LINKIT game project",
        frequency="daily",
        time_of_day="evening",
        linked_goal_id=linkit_id,
        linked_area_id=projects_id,
        duration_minutes=120,
    )

    python_id = habit_service.create_habit(
        name="Python Practice",
        description="Practice Python programming",
        frequency="daily",
        time_of_day="evening",
        linked_goal_id=python_goal_id,
        linked_area_id=learning_id,
        duration_minutes=60,
    )

    english_id = habit_service.create_habit(
        name="English Study",
        description="Study and practice English",
        frequency="daily",
        time_of_day="evening",
        linked_area_id=learning_id,
        duration_minutes=30,
    )

    grad_id = habit_service.create_habit(
        name="Graduation Project Work",
        description="Work on grad project (Sat, Sun, Mon)",
        frequency="custom",
        time_of_day="morning",
        linked_goal_id=grad_project_id,
        linked_area_id=career_id,
        duration_minutes=240,
    )

    habits_created = [
        ("Quran Recitation", quran_id),
        ("Prayer (5x Daily)", prayer_id),
        ("UE5 Practice", ue5_id),
        ("LINKIT Development", linkit_dev_id),
        ("Python Practice", python_id),
        ("English Study", english_id),
        ("Grad Project Work", grad_id),
    ]

    for habit_name, habit_id in habits_created:
        print(f"  - {habit_name} ({habit_id})")
    print()

    print("[5/5] Summary...")
    print()
    print("=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    print()
    print("Your profile:")
    print("  - Name: Deep")
    print("  - Work style: Evening")
    print("  - Grad deadline: June 1, 2026")
    print("  - Grad project days: Sat, Sun, Mon (3-5hr sessions)")
    print()
    print("Goals created: 13")
    print("Habits created: 7")
    print()
    print("Your evening block: 18:00 - 22:00")
    print()
    print("Priority order for evenings:")
    print("  1. LINKIT Development (Tue, Wed, Thu)")
    print("  2. UE5 Practice")
    print("  3. Python Practice")
    print("  4. English Study")
    print()
    print("Next steps:")
    print("  1. Run 'jarvis accountability today' to see today's tasks")
    print("  2. Run 'jarvis habit log <id>' to mark habits complete")
    print("  3. Run 'jarvis goal list' to see all goals")
    print()

    logger.info("Initial setup completed successfully")


if __name__ == "__main__":
    run_initial_setup()
