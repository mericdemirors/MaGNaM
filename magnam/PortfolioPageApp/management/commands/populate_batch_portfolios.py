from pathlib import Path

import pandas as pd
from PIL import Image

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from ProfilePageApp.models import Profile
from PortfolioPageApp.models import Portfolio, PortfolioTag
from PortfolioPageApp.serializers import CreateEditPortfolioSerializer

from utils.helper_functions import load_dataframe, convert_labels_to_ids, fake_request


class Command(BaseCommand):
    help = (
        "Batch CREATE / PATCH / DELETE Portfolios from CSV or Excel Use it with "
        "python manage.py populate_batch_portfolios data.xlsx or python manage.py populate_batch_portfolios data.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def process_row(self, row):
        action = str(row.get("action", "")).upper()
        portfolio_id = row.get("id")

        if action == "DELETE":
            self.handle_delete(portfolio_id)
        elif action == "PATCH":
            self.handle_patch(portfolio_id, row)
        elif action == "CREATE":
            self.handle_create(row)
        else:
            raise ValueError(f"Invalid action: {action}")

    def handle_delete(self, portfolio_id):
        if pd.isna(portfolio_id):
            raise ValueError("DELETE requires id")

        try:
            portfolio = Portfolio.objects.get(id=int(portfolio_id))
        except Portfolio.DoesNotExist:
            self.stderr.write(f"Portfolio {portfolio_id} not found")
            return

        portfolio.delete()
        self.stdout.write(f"Deleted Portfolio {portfolio_id}")

    def handle_create(self, row):
        owner = row.get("owner")
        if pd.isna(owner):
            raise ValueError("CREATE requires owner")

        try:
            owner = Profile.objects.get(id=int(owner))
        except Profile.DoesNotExist:
            raise ValueError(f"Profile {owner} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditPortfolioSerializer(
            data=data, context={"request": fake_request(owner)}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=owner)

        self.stdout.write(f"Created Portfolio: {data.get('title')}")

    def handle_patch(self, portfolio_id, row):
        if pd.isna(portfolio_id):
            raise ValueError("PATCH requires id")

        try:
            instance = Portfolio.objects.get(id=int(portfolio_id))
        except Portfolio.DoesNotExist:
            raise ValueError(f"Portfolio {portfolio_id} does not exist")

        data = self.build_serializer_data(row)

        serializer = CreateEditPortfolioSerializer(
            instance,
            data=data,
            partial=True,
            context={"request": fake_request(instance.owner)},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.stdout.write(f"Updated Portfolio {portfolio_id}")

    def build_serializer_data(self, row):
        data = {}

        for field in ["title", "description"]:
            if field in row and not pd.isna(row[field]):
                data[field] = str(row[field])

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
        df = convert_labels_to_ids(df, PortfolioTag)
        df["description"] = df["description"].fillna("")

        required_cols = {"action"}
        if not required_cols.issubset(df.columns):
            self.stderr.write("Missing required columns")
            return

        for idx, row in df.iterrows():
            try:
                self.process_row(row)
            except Exception as e:
                self.stderr.write(f"Row {idx}: {e}")

        self.stdout.write(self.style.SUCCESS("Portfolio import completed"))
