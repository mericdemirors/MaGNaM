import pandas as pd
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from ProfilePageApp.models import Profile
from MangaPageApp.models import Manga, Chapter, BoughtChapter
from MangaPageApp.serializers import CreateEditChapterSerializer
from utils.helper_functions import load_dataframe, parse_json_list, fake_request
from utils.file_checks import *

class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH / DELETE Chapters from CSV or Excel Use it with "
        "python manage.py populate_batch_chapters data.xlsx or python manage.py populate_batch_chapters data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        chapter_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(chapter_id)
        elif action == "PATCH":
            self.handle_patch(chapter_id, row)
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, chapter_id):
        if pd.isna(chapter_id):
            raise ValueError("DELETE requires id")

        try:
            chapter = Chapter.objects.get(id=int(chapter_id))
        except Chapter.DoesNotExist:
            self.stderr.write(f"Chapter {chapter_id} not found")
            return

        # delete DB row
        chapter.delete()
        self.stdout.write(f"Deleted Chapter {chapter_id}")

    def handle_create(self, row):
        manga = row.get("manga")
        if pd.isna(manga):
            raise ValueError("CREATE requires manga")
        owner = row.get("owner")
        if pd.isna(owner):
            raise ValueError("CREATE requires owner")

        try:
            manga = Manga.objects.get(id=int(manga))
        except Manga.DoesNotExist:
            raise ValueError(f"Manga {manga} does not exist")

        try:
            owner = Profile.objects.get(id=int(owner))
        except Profile.DoesNotExist:
            raise ValueError(f"Profile {owner} does not exist")

        data = self.build_serializer_data(row)
        serializer = CreateEditChapterSerializer(
            data=data,
            context={"manga": manga, "owner": owner, "request": fake_request(owner)},
        )
        serializer.is_valid(raise_exception=True)

        chapter = serializer.save(manga=manga, owner=owner)

        BoughtChapter.objects.create(profile=owner, chapter=chapter, paid_price=0)
        owner.chapters_owned.add(chapter)

        # collaborators
        for collaborator in serializer.validated_data.get("collaborators", []):
            BoughtChapter.objects.create(
                profile=collaborator, chapter=chapter, paid_price=0
            )
            collaborator.chapters_collaborated.add(chapter)

        # manga owner must also own the chapter
        _ = BoughtChapter.objects.get_or_create(
            profile=manga.owner, chapter=chapter, defaults={"paid_price": 0}
        )

        self.stdout.write(f"Created Chapter {chapter.title}")

    def handle_patch(self, chapter_id, row):
        if pd.isna(chapter_id):
            raise ValueError("PATCH requires id")

        try:
            chapter = Chapter.objects.get(id=int(chapter_id))
        except Chapter.DoesNotExist:
            raise ValueError(f"Chapter {chapter_id} does not exist")

        owner = chapter.owner

        data = self.build_serializer_data(row)

        serializer = CreateEditChapterSerializer(
            instance=chapter,
            data=data,
            partial=True,
            context={
                "manga": chapter.manga,
                "owner": owner,
                "request": fake_request(owner),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Updated Chapter {chapter.id}")

    def build_serializer_data(self, row):
        data = {}

        for field in ["title", "no", "price"]:
            if pd.notna(row.get(field)):
                data[field] = row[field]

        if "collaborators" in row:
            data["collaborators"] = parse_json_list(row["collaborators"])

        if pd.notna(row.get("pdf")):
            pdf_name = row.get("pdf")

            if not pd.isna(pdf_name) and pdf_name:
                pdf = (self.dataset_root / str(pdf_name)).resolve()

            if not pdf.exists():
                raise ValueError(f"pdf not found: {pdf}")
            data["pdf"] = File(open(pdf, "rb"))

        return data

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file_path"]).resolve()

        if not file_path.exists():
            self.stderr.write("File not found")
            return

        # folder containing the population info excel file and population media
        self.dataset_root = file_path.parent

        df = load_dataframe(file_path)

        required_cols = {"action"}
        if not required_cols.issubset(df.columns):
            self.stderr.write("Missing required columns")
            return

        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    self.process_row(row)
            except Exception as e:
                self.stderr.write(f"Row {index}: {e}")

        self.stdout.write(self.style.SUCCESS("Process completed"))
