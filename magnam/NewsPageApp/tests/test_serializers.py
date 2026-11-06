import json
from django.urls import reverse
from ..models import *
from .base_test import NewsBaseTestCase
from ..globals import *
from ..serializers import *
from utils.test_utils import send_missing_field, send_invalid_field
from django.core.files.uploadedfile import SimpleUploadedFile


# ReturnNewsSerializer
class TestReturnNewsSerializerFields(NewsBaseTestCase):
    def test_return_news_returned_fields(self):
        # create the object
        _, _, _, tag = self.create_random_valid_object()

        # serialize the object as it's being returned to the frontend
        serializer = ReturnNewsSerializer(tag)
        data = serializer.data

        # check if serialized return contains all the fields it needs to
        self.assertEqual(
            set(data.keys()), {"id", "title", "description", "image", "links"}
        )


# CreateEditNewsSerializer
class TestNewsCreateEditSerializerFields(NewsBaseTestCase):
    def test_createedit_news_returned_fields(self):
        _, _, _, vote = self.create_random_valid_object()

        serializer = CreateEditNewsSerializer(vote)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"title", "description", "image", "links"})


# CreateEditNewsSerializer
class TestNewsCreateEditSerializerProcessing(NewsBaseTestCase):
    def test_field_stripping_functionality(self):
        # get raw data to pass to serializer
        original_vals, _, _ = self.get_random_valid_data()

        # prepare the padded strings for serializer
        stripped_title = original_vals["title"]
        stripped_description = original_vals["description"]
        stripped_links = original_vals["links"]

        original_vals["title"] = f"   {stripped_title}   "
        original_vals["description"] = f" \n  {stripped_description}  \t "
        original_vals["links"] = [f"  {link}  " for link in stripped_links]

        serializer = CreateEditNewsSerializer(data=original_vals)

        # check if serializer is valid
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # check if serializer data stripped the paddings
        self.assertEqual(serializer.validated_data["title"], stripped_title)
        self.assertEqual(serializer.validated_data["description"], stripped_description)
        self.assertEqual(serializer.validated_data["links"], stripped_links)


# CreateEditNewsSerializer
class TestCreateEditNewsSerializerInvalidData(NewsBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(f"{self.namespace}:create-news")
        self.client.force_authenticate(user=self.admin)

    def test_create_news_missing_fields(self):
        send_missing_field(self, self.url, ["title"])
        send_missing_field(self, self.url, ["description"])
        send_missing_field(self, self.url, ["image"])
        send_missing_field(self, self.url, ["links"])

    def test_create_news_invalid_fields(self):
        # short title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=NEWS_MIN_TITLE_LEN - 1),
        )

        # long title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=NEWS_MAX_TITLE_LEN + 10),
        )

        # long description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_title_value(L=NEWS_MAX_DESCRIPTION_LEN + 10),
        )

        # small dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=NEWS_IMAGE_MIN_W - 10),
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=NEWS_IMAGE_MIN_H - 10),
        )

        # big dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=NEWS_IMAGE_MAX_W + 10),
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=NEWS_IMAGE_MAX_H + 10),
        )

        # change the file name extension
        invalid_ext_file = self.get_random_image_value()
        invalid_ext_file.name = invalid_ext_file.name.rsplit(".", 1)[0] + ".mp4"
        send_invalid_field(self, self.url, "image", invalid_ext_file)

        # changing the file content doesn't give 400 error
        # I think django fixes the content type by looking at the extension

        # corrupt the binary data to fail PIL verify()
        invalid_content_file = SimpleUploadedFile(
            name="corrupt_image.png",
            content=b"this is definitely not a png file header",
            content_type="image/png",
        )
        send_invalid_field(self, self.url, "image", invalid_content_file)

        # exceeding max file size
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(target_size_bytes=NEWS_IMAGE_MAX_SIZE * 2),
        )

        # long links
        send_invalid_field(
            self,
            self.url,
            "links",
            json.dumps(self.get_random_links_value(L=int(NEWS_MAX_LINKS_LEN**0.75))),
        )

        # insecure links
        send_invalid_field(
            self,
            self.url,
            "links",
            json.dumps(["http://insecure.com", "ftp://files.com"]),
        )
