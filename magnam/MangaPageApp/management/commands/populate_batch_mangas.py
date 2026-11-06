from pathlib import Path

import pandas as pd
from PIL import Image

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from ProfilePageApp.models import Profile
from MangaPageApp.models import Manga, MangaTag
from MangaPageApp.serializers import CreateEditMangaSerializer

from utils.helper_functions import (
    load_dataframe,
    convert_labels_to_ids,
    parse_json_list,
    fake_request,
)


class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH / DELETE Mangas from CSV or Excel Use it with "
        "python manage.py populate_batch_mangas data.xlsx or python manage.py populate_batch_mangas data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        manga_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(manga_id)
        elif action == "PATCH":
            self.handle_patch(manga_id, row)
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, manga_id):
        if pd.isna(manga_id):
            raise ValueError("DELETE requires id")

        try:
            manga = Manga.objects.get(id=int(manga_id))
        except Manga.DoesNotExist:
            self.stderr.write(f"Manga {manga_id} not found")
            return

        # delete DB row
        manga.delete()
        self.stdout.write(f"Deleted Manga {manga_id}")

    def handle_create(self, row):
        owner = row.get("owner")
        if pd.isna(owner):
            raise ValueError("CREATE requires owner")

        try:
            owner = Profile.objects.get(id=int(owner))
        except Profile.DoesNotExist:
            raise ValueError(f"Profile {owner} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditMangaSerializer(
            data=data, context={"request": fake_request(owner), "owner": owner}
        )

        serializer.is_valid(raise_exception=True)

        manga = serializer.save(owner=owner)

        owner.mangas_following.add(manga)
        owner.mangas_owned.add(manga)

        self.stdout.write(f"Created Manga: {data.get('title')}")

    def handle_patch(self, manga_id, row):
        if pd.isna(manga_id):
            raise ValueError("PATCH requires id")

        try:
            manga = Manga.objects.get(id=int(manga_id))
        except Manga.DoesNotExist:
            raise ValueError(f"Manga {manga_id} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditMangaSerializer(
            instance=manga,
            data=data,
            partial=True,
            context={"request": fake_request(manga.owner)},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Updated Manga {manga_id}")

    def build_serializer_data(self, row):
        data = {}

        for field in ["title", "description"]:
            if field in row and not pd.isna(row[field]):
                data[field] = row[field]

        if "tags" in row:
            data["tags"] = row["tags"]

        if "collaborators" in row:
            data["collaborators"] = parse_json_list(row["collaborators"])

        image_name = row.get("image")

        if not pd.isna(image_name) and image_name:
            image = (self.dataset_root / str(image_name)).resolve()

            if not image.exists():
                raise ValueError(f"Image not found: {image}")

            with Image.open(image) as img:
                img.verify()

            data["image"] = File(image.open("rb"), name=image.name)

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

        df = convert_labels_to_ids(df, MangaTag)

        required_cols = {"action"}
        if not required_cols.issubset(df.columns):
            self.stderr.write("Missing required columns")
            return

        for idx, row in df.iterrows():
            try:
                self.process_row(row)
            except Exception as e:
                self.stderr.write(f"Row {idx}: {e}")

        self.stdout.write(self.style.SUCCESS("Process completed"))
