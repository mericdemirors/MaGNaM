from pathlib import Path

import pandas as pd
from PIL import Image

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from NewsPageApp.models import News
from NewsPageApp.serializers import CreateEditNewsSerializer

from utils.helper_functions import load_dataframe, parse_json_list


class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH / DELETE News from CSV or Excel Use it with "
        "python manage.py populate_batch_news data.xlsx or python manage.py populate_batch_news data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        news_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(news_id)
        elif action == "PATCH":
            self.handle_patch(news_id, row)
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, news_id):
        if pd.isna(news_id):
            raise ValueError("DELETE requires id")

        try:
            news = News.objects.get(id=int(news_id))
        except News.DoesNotExist:
            self.stderr.write(f"News {news_id} not found")
            return

        news.delete()
        self.stdout.write(f"Deleted News {news_id}")

    def handle_create(self, row):
        data = self.build_serializer_data(row)

        serializer = CreateEditNewsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Created News: {data.get('title')}")

    def handle_patch(self, news_id, row):
        if pd.isna(news_id):
            raise ValueError("PATCH requires id")

        try:
            instance = News.objects.get(id=int(news_id))
        except News.DoesNotExist:
            raise ValueError(f"News {news_id} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditNewsSerializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Updated News {int(news_id)}")

    def build_serializer_data(self, row):
        data = {}

        for field in ["title", "description"]:
            if field in row and not pd.isna(row[field]):
                data[field] = row[field]

        if "links" in row:
            data["links"] = parse_json_list(row["links"])

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

        # in case excel cells are registered as NaN, we set them to empty string
        # we dont let these fields to be NULL but empty string is okay
        df["description"] = df["description"].fillna("")
        df["links"] = df["links"].fillna("")

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
