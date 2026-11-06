from django.core.management.base import BaseCommand
from PortfolioPageApp.models import PortfolioTag

PREDEFINED_TAGS = [
    # Media Type / Format
    "Mixed",
    "Pdf",
    "Image",
    "Text",
    "Audio",
    "Video",
    "3D",
    "Comic",
    "Concept-art",
    "Asset-pack",
    "Not-AI",
    "Music",
    "Voice-acting",
    "Looking-for-partner",
    "Looking-for-employee",
    "Pose reference",
    "Photography",
    # Role / Skill
    "Story",
    "Drawing",
    "Background",
    "Animation",
    "Inking",
    "Coloring",
    "Editing",
    "Sfx",
    "Music",
    "World-building",
    "Script-writing",
    "Character-design",
    "Cosplay",
    "Handcraft",
    "Open-to-collab",
    "Commissions-open",
]


class Command(BaseCommand):
    help = "Populate the PortfolioTag table with default tags"

    def handle(self, *args, **kwargs):
        for label in PREDEFINED_TAGS:
            PortfolioTag.objects.get_or_create(label=label)
        self.stdout.write(
            self.style.SUCCESS(
                f"tags populated successfully: {', '.join(PREDEFINED_TAGS)}"
            )
        )
