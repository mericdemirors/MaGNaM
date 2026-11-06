from django.core.management.base import BaseCommand
from CompetitionPageApp.models import CompetitionTag

PREDEFINED_TAGS = [
    # Status / Format
    "Waiting",
    "Ongoing",
    "Ended",
    "Free-entry",
    "Paid-entry",
    "Work",
    "Chapter",
    "Team-based",
    "Solo-entry",
    "Not-AI",
    # Scope / Requirement
    "Drawing",
    "Writing",
    "Design",
    "Short-story",
    "One-page",
    "Fan-art",
    "Audio",
    "Video",
    "Music",
    "Voice-acting",
    # Prize / Incentive
    "Money-prize",
    "Publication",
    "Feedback-guaranteed",
]


class Command(BaseCommand):
    help = "Populate the CompetitionTag table with default tags"

    def handle(self, *args, **kwargs):
        for label in PREDEFINED_TAGS:
            CompetitionTag.objects.get_or_create(label=label)
        self.stdout.write(
            self.style.SUCCESS(
                f"Competition tags populated successfully: {', '.join(PREDEFINED_TAGS)}"
            )
        )
