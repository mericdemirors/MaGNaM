from django.core.management.base import BaseCommand
from MangaPageApp.models import MangaTag

PREDEFINED_TAGS = [
    # Status / Format
    "Original",
    "Scan/Translation",
    "Finished",
    "Ongoing",
    "Hiatus",
    "Light-Novel",
    "Manhwa",
    "Manhua",
    "Oneshot",
    "Webcomic",
    "Colored",
    "Black&White",
    "Not-AI",
    # Genre
    "Action",
    "Fantasy",
    "Romance",
    "Sci-fi",
    "Horror",
    "Thriller",
    "Comedy",
    "Slice-of-life",
    "Mystery",
    "Drama",
    "Historical",
    "Supernatural",
    "Mecha",
    "Sports",
    "Post-apocalyptic",
    "Isekai",
    "Yuri",
    "Yaoi",
    "Shonen",
    "Shojo",
    "Seinen",
    "Josei",
    "Adventure",
    "Martial-arts",
    "School-life",
    "Magic",
    "Psychological",
    "Tragedy",
    "Wholesome",
    "Educational",
    "Medical",
    "Memoir",
    "Military",
    "Music",
    "Mythology",
    "Pets",
    "Racing",
    "Reverse-Harem",
    "Harem",
    "Space",
    "Survival",
    "Time-Travel",
]


class Command(BaseCommand):
    help = "Populate the MangaTag table with default tags"

    def handle(self, *args, **kwargs):
        for label in PREDEFINED_TAGS:
            MangaTag.objects.get_or_create(label=label)
        self.stdout.write(
            self.style.SUCCESS(
                f"Manga tags populated successfully: {', '.join(PREDEFINED_TAGS)}"
            )
        )
