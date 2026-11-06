import json
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from ..models import *
from .base_test import *
from ..globals import *
from ..serializers import *
from utils.test_utils import send_missing_field, send_invalid_field


# ReturnCompetitionChapterSerializer
class TestReturnCompetitionChapterSerializerFields(CompetitionBaseTestCase):
    def test_competition_chapter_returned_fields(self):
        chapter = self.get_random_chapter_submits_value(count=1)[0]

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnCompetitionChapterSerializer(
            chapter, context={"request": request}
        )

        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {"id", "title", "no", "manga_id", "manga_title", "manga_image"},
        )


# ReturnCompetitionPortfolioSerializer
class TestReturnCompetitionPortfolioSerializerFields(CompetitionBaseTestCase):
    def test_competition_portfolio_returned_fields(self):
        portfolio = self.get_random_portfolio_submits_value(count=1)[0]

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnCompetitionPortfolioSerializer(
            portfolio, context={"request": request}
        )

        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "title", "image"})


# ReturnCompetitionTagSerializer
class TestReturnCompetitionTagSerializerFields(CompetitionTagBaseTestCase):
    def test_tag_returned_fields(self):
        _, _, _, tag = self.create_random_valid_object()

        serializer = ReturnCompetitionTagSerializer(tag)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "label"})


# ReturnCompetitionSerializer
class TestReturnCompetitionSerializerFields(CompetitionBaseTestCase):
    def test_competition_returned_fields(self):
        _, _, _, competition = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnCompetitionSerializer(
            competition, context={"request": request}
        )

        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "description",
                "image",
                "links",
                "start_date",
                "price",
                "end_date",
                "tags",
                "chapter_submits",
                "portfolio_submits",
                "chapter_wins",
                "portfolio_wins",
            },
        )


# CreateEditCompetitionSerializer
class TestCreateEditCompetitionSerializerFields(CompetitionBaseTestCase):
    def test_create_edit_competition_returned_fields(self):
        original_vals, _, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        serializer = CreateEditCompetitionSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(
            set(data.keys()),
            {
                "title",
                "description",
                "image",
                "links",
                "price",
                "start_date",
                "end_date",
                "tags",
            },
        )


# ReturnCompetitionGallerySerializer
class TestReturnCompetitionGallerySerializerFields(CompetitionBaseTestCase):
    def test_competition_gallery_returned_fields(self):
        _, _, _, competition = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnCompetitionGallerySerializer(
            competition, context={"request": request}
        )

        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "image",
                "tags",
                "title",
                "start_date",
                "end_date",
                "price",
                # "num_of_portfolio_submits",
                # "num_of_chapter_submits",
            },
        )


# CreateEditCompetitionSerializer
class TestCreateEditCompetitionSerializerProcessing(CompetitionBaseTestCase):
    def test_field_stripping_functionality(self):
        # get raw data to pass to serializer
        original_vals, _, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        # prepare the padded strings for serializer
        stripped_title = original_vals["title"]
        stripped_description = original_vals["description"]
        stripped_links = original_vals["links"]

        original_vals["title"] = f"   {stripped_title}   "
        original_vals["description"] = f" \n  {stripped_description}  \t "
        original_vals["links"] = [f"  {link}  " for link in stripped_links]

        serializer = CreateEditCompetitionSerializer(data=original_vals)

        # check if serializer is valid
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # check if serializer data stripped the paddings
        self.assertEqual(serializer.validated_data["title"], stripped_title)
        self.assertEqual(serializer.validated_data["description"], stripped_description)
        self.assertEqual(serializer.validated_data["links"], stripped_links)


# CreateEditCompetitionSerializer
class TestCreateEditCompetitionSerializerInvalidData(CompetitionBaseTestCase):
    def setUp(self):
        super().setUp()
        self.tags = self.get_random_tags_value()
        self.url = reverse(f"{self.namespace}:create-competition")
        self.client.force_authenticate(user=self.admin)

    def test_create_edit_competition_missing_fields(self):
        send_missing_field(
            self,
            self.url,
            ["title"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["description"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["image"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["links"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["price"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["start_date"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        send_missing_field(
            self,
            self.url,
            ["end_date"],
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # no tags is okay because we have 'allow_empty' in the serializer
        # send_missing_field(
        #     self, self.url, ["tags"], predefined_vals={**fast_creation_dict}
        # )

    def test_create_edit_competition_invalid_fields(self):
        # short title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=COMPETITION_MIN_TITLE_LEN - 1),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )    
        # long title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=COMPETITION_MAX_TITLE_LEN + 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # short description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=COMPETITION_MIN_DESCRIPTION_LEN - 1),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )    
        # long description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=COMPETITION_MAX_DESCRIPTION_LEN + 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # small dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=COMPETITION_IMAGE_MIN_W - 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=COMPETITION_IMAGE_MIN_H - 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )
        # big dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=COMPETITION_IMAGE_MAX_W + 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=COMPETITION_IMAGE_MAX_H + 10),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # change the file name extension
        invalid_ext_file = self.get_random_image_value()
        invalid_ext_file.name = invalid_ext_file.name.rsplit(".", 1)[0] + ".mp4"
        send_invalid_field(
            self,
            self.url,
            "image",
            invalid_ext_file,
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # changing the file content doesn't give 400 error
        # I think django fixes the content type
        # by looking at the extension

        # corrupt the binary data to fail PIL verify()
        invalid_content_file = SimpleUploadedFile(
            name="corrupt_image.png",
            content=b"this is definitely not a png file header",
            content_type="image/png",
        )

        send_invalid_field(
            self,
            self.url,
            "image",
            invalid_content_file,
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # exceeding max file size
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(target_size_bytes=COMPETITION_IMAGE_MAX_SIZE * 2),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # long links
        send_invalid_field(
            self,
            self.url,
            "links",
            json.dumps(self.get_random_links_value(L=int(COMPETITION_MAX_LINKS_LEN**0.75))),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # insecure links
        send_invalid_field(
            self,
            self.url,
            "links",
            json.dumps(["http://insecure.com", "ftp://files.com"]),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # negative price
        send_invalid_field(
            self,
            self.url,
            "price",
            -1,
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # floating point price
        send_invalid_field(
            self,
            self.url,
            "price",
            10.5,
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # end date in the past
        send_invalid_field(
            self,
            self.url,
            "end_date",
            timezone.now().date() - timezone.timedelta(days=1),
            predefined_vals={"tags": self.tags, **fast_creation_dict},
        )

        # end date before start date
        send_invalid_field(
            self,
            self.url,
            "end_date",
            timezone.now().date() + timezone.timedelta(days=5),
            predefined_vals={
                "start_date": timezone.now().date() + timezone.timedelta(days=10),
                "tags": self.tags,
                **fast_creation_dict,
            },
        )

        # more tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=COMPETITION_MAX_TAG_COUNT + 1),
            predefined_vals=fast_creation_dict,
        )