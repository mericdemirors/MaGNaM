import json
from pathlib import Path

import pandas as pd
from PIL import Image

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from CompetitionPageApp.models import Competition, CompetitionTag
from CompetitionPageApp.serializers import CreateEditCompetitionSerializer

from utils.helper_functions import (
    load_dataframe,
    convert_labels_to_ids,
    parse_json_list,
)


class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH / DELETE Competitions from CSV or Excel Use it with "
        "python manage.py populate_batch_competitions data.xlsx or python manage.py populate_batch_competitions data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        comp_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(comp_id)
        elif action == "PATCH":
            self.handle_patch(comp_id, row)
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, comp_id):
        if pd.isna(comp_id):
            raise ValueError("DELETE requires id")

        try:
            competition = Competition.objects.get(id=int(comp_id))
        except Competition.DoesNotExist:
            self.stderr.write(f"Competition {comp_id} not found")
            return

        # delete DB row
        competition.delete()
        self.stdout.write(f"Deleted Competition {comp_id}")

    def handle_create(self, row):
        data = self.build_serializer_data(row)

        serializer = CreateEditCompetitionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Created Competition: {data.get('title')}")

    def handle_patch(self, comp_id, row):
        if pd.isna(comp_id):
            raise ValueError("PATCH requires id")

        try:
            instance = Competition.objects.get(id=int(comp_id))
        except Competition.DoesNotExist:
            raise ValueError(f"Competition {comp_id} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditCompetitionSerializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Updated Competition {comp_id}")

    def build_serializer_data(self, row):
        data = {}

        for field in ["title", "description", "price", "start_date", "end_date"]:
            if field in row and not pd.isna(row[field]):
                data[field] = row[field]

        if "links" in row:
            data["links"] = parse_json_list(row["links"])

        if "tags" in row:
            data["tags"] = row["tags"]

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

        df = convert_labels_to_ids(df, CompetitionTag)
        df["start_date"] = pd.to_datetime(df["start_date"]).dt.date
        df["end_date"] = pd.to_datetime(df["end_date"]).dt.date
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
