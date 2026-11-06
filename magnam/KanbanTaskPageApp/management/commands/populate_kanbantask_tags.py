from django.core.management.base import BaseCommand
from KanbanTaskPageApp.models import KanbanTaskTag

PREDEFINED_TAGS = [
    # Request Type & Scope
    "Easy/one-line-fix",
    "Bug",  # Core bug or issue report
    "Feature",  # New functional requirement
    "Refactor",  # Code quality improvement, no functional change
    "Performance",  # Optimization task
    "Security",  # Vulnerability or security enhancement
    "UI/UX",  # Interface or user experience adjustment
    "Documentation",  # Need to update docs/help files
    "Deletion",  # Request to remove a feature (like 'delete feature')
    # Source
    "User-suggestion",
    "Internal-task",
]


class Command(BaseCommand):
    help = "Populate the KanbanTaskTag table with default tags"

    def handle(self, *args, **kwargs):
        for label in PREDEFINED_TAGS:
            KanbanTaskTag.objects.get_or_create(label=label)
        self.stdout.write(
            self.style.SUCCESS(
                f"Kanban tags populated successfully: {', '.join(PREDEFINED_TAGS)}"
            )
        )
