from django.urls import reverse
from rest_framework.test import APIRequestFactory
from ..models import *
from .base_test import *
from ..globals import *
from ..serializers import *
from utils.test_utils import send_missing_field, send_invalid_field
from unittest.mock import patch


# ReturnPortfolioOwnerReferenceSerializer
class TestReturnPortfolioOwnerReferenceSerializerFields(PortfolioBaseTestCase):
    def test_owner_reference_returned_fields(self):
        _, _, _, portfolio = self.create_random_valid_object()
        profile = portfolio.owner

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnPortfolioOwnerReferenceSerializer(
            profile, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "profile_name", "image"})


# ReturnWorkSerializer
class TestReturnWorkSerializerFields(WorkBaseTestCase):
    def test_work_returned_fields(self):
        _, _, _, work = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnWorkSerializer(work, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "portfolio",
                "id",
                "title",
                "file_url",
                "folder_name",
                "num_of_images",
                "pages_base_url",
                "is_pdf",
            },
        )


# CreateWorkSerializer
class TestCreateWorkSerializerFields(WorkBaseTestCase):
    def test_create_work_returned_fields(self):
        original_vals, _, _ = self.get_random_valid_data()
        # serializer expects a list of files so we assign the correct 'work_files' field as a listed version of the 'work_file' field
        original_vals["work_files"] = [original_vals["work_file"]]
        del original_vals[
            "work_file"
        ]  # check the bottom of the file for explanation for this deletion
        serializer = CreateWorkSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(set(data.keys()), {"title", "work_files"})


# ReturnPortfolioTagSerializer
class TestReturnPortfolioTagSerializerFields(PortfolioTagBaseTestCase):
    def test_tag_returned_fields(self):
        _, _, _, tag = self.create_random_valid_object()

        serializer = ReturnPortfolioTagSerializer(tag)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "label"})


# ReturnPortfolioLikeSerializer
class TestReturnPortfolioLikeSerializerFields(PortfolioLikeBaseTestCase):
    def test_like_returned_fields(self):
        _, _, _, like = self.create_random_valid_object()

        serializer = ReturnPortfolioLikeSerializer(like)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "portfolio", "profile"})


# ReturnPortfolioCommentSerializer
class TestReturnPortfolioCommentSerializerFields(PortfolioCommentBaseTestCase):
    def test_comment_returned_fields(self):
        _, _, _, comment = self.create_random_valid_object()

        serializer = ReturnPortfolioCommentSerializer(comment)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "profile_name", "comment", "parent_comment_id"}
        )


# ReturnPortfolioSerializer
class TestReturnPortfolioSerializerFields(PortfolioBaseTestCase):
    def test_portfolio_returned_fields(self):
        _, _, _, portfolio = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnPortfolioSerializer(portfolio, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "description",
                "image",
                "owner",
                "date",
                "folder_name",
                "tags",
                "works",
            },
        )


# ReturnPortfolioGallerySerializer
class TestReturnPortfolioGallerySerializerFields(PortfolioBaseTestCase):
    def test_portfolio_gallery_returned_fields(self):
        _, _, _, portfolio = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnPortfolioGallerySerializer(
            portfolio, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "image",
                "date",
                "tags",
                # below are calculated in the view they are not serializer native
                # "num_of_likes",
                # "num_of_works",
            },
        )


# CreateEditPortfolioSerializer
class TestCreateEditPortfolioSerializerFields(PortfolioBaseTestCase):
    def test_create_edit_portfolio_returned_fields(self):
        original_vals, _, _ = self.get_random_valid_data()

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditPortfolioSerializer(
            data=original_vals, context={"request": request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(set(data.keys()), {"title", "description", "image", "tags"})


# CreatePortfolioCommentSerializer
class TestCreatePortfolioCommentSerializerFields(PortfolioCommentBaseTestCase):
    def test_create_comment_returned_fields(self):
        # get data for a comment with no parent
        original_vals, _, vals_to_create_from = self.get_random_valid_data(
            predefined_vals={"parent_comment": -1}
        )

        # serialize the data
        serializer = CreatePortfolioCommentSerializer(
            data=original_vals,
            context={
                "portfolio": vals_to_create_from["portfolio"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = serializer.validated_data

        # first comment wont have a parent because it's parentless
        self.assertEqual(set(data.keys()), {"comment", "parent_comment_id"})

        # save this comment as the first comment on that portfolio
        parent_comment = serializer.save()

        # then create a new comment that's replying to that comment
        new_original_vals, _, _ = self.get_random_valid_data(
            predefined_vals={"parent_comment": parent_comment}
        )

        reply_serializer = CreatePortfolioCommentSerializer(
            data=new_original_vals,
            context={
                "portfolio": vals_to_create_from["portfolio"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(reply_serializer.is_valid(), reply_serializer.errors)
        reply_data = reply_serializer.validated_data

        # serializer adds 'parent_comment' field in the validated data
        self.assertEqual(
            set(reply_data.keys()), {"comment", "parent_comment", "parent_comment_id"}
        )


# CreateEditPortfolioSerializer
class TestCreateEditPortfolioSerializerLimit(PortfolioBaseTestCase):
    def test_portfolio_limit_exceeded(self):
        NEW_LIMIT = 3
        with patch(
            "PortfolioPageApp.serializers.MAX_PORTFOLIO_COUNT_PER_PROFILE", NEW_LIMIT
        ):
            # create a total of MAX_PORTFOLIO_COUNT_PER_PROFILE portfolios for the user
            profile = self.user.profile
            for _ in range(NEW_LIMIT):
                self.create_random_valid_object(predefined_vals={"owner": profile})

            # then try to serialize another data for a new portfolio
            # it should fail the "if profile.portfolios.count() >= MAX_PORTFOLIO_COUNT_PER_PROFILE:" check
            original_vals, _, _ = self.get_random_valid_data()

            factory = APIRequestFactory()
            request = factory.post("/")
            request.user = self.user

            serializer = CreateEditPortfolioSerializer(
                data=original_vals, context={"request": request}
            )

            self.assertFalse(serializer.is_valid())
            self.assertIn("limit", serializer.errors)


# CreateEditPortfolioSerializer
class TestCreateEditPortfolioSerializerProcessing(PortfolioBaseTestCase):
    def test_valid_create_edit_portfolio_field_processing(self):
        original_vals, _, _ = self.get_random_valid_data()

        stripped_title = original_vals["title"]
        stripped_description = original_vals["description"]

        original_vals["title"] = f"   {stripped_title}   "
        original_vals["description"] = f"\n  {stripped_description} \t"

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditPortfolioSerializer(
            data=original_vals, context={"request": request}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data
        self.assertEqual(data["title"], stripped_title)
        self.assertEqual(data["description"], stripped_description)


# CreateEditPortfolioSerializer
class TestCreateEditPortfolioSerializerInvalidData(PortfolioBaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.user.profile
        self.tags = self.get_random_tags_value()
        self.url = reverse(f"{self.namespace}:create-portfolio")
        self.client.force_authenticate(user=self.user)

    def test_create_edit_portfolio_missing_fields(self):
        send_missing_field(
            self,
            self.url,
            ["title"],
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_missing_field(
            self,
            self.url,
            ["description"],
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_missing_field(
            self,
            self.url,
            ["image"],
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # no tag is okay because we have 'allow_empty' in the serializer
        # send_missing_field(
        #     self, self.url, ["tags"], predefined_vals={"owner": self.profile}
        # )

    def test_create_edit_portfolio_invalid_fields(self):
        # short title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=PORTFOLIO_MIN_TITLE_LEN - 1),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # long title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=PORTFOLIO_MAX_TITLE_LEN + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # long description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=PORTFOLIO_MAX_DESCRIPTION_LEN + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # small dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=PORTFOLIO_IMAGE_MIN_W - 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=PORTFOLIO_IMAGE_MIN_H - 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # big dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=PORTFOLIO_IMAGE_MAX_W + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=PORTFOLIO_IMAGE_MAX_H + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # change the file name extension
        invalid_ext_file = self.get_random_image_value()
        invalid_ext_file.name = invalid_ext_file.name.rsplit(".", 1)[0] + ".mp4"
        send_invalid_field(
            self,
            self.url,
            "image",
            invalid_ext_file,
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # changing the file content doesn't give 400 error
        # I think its because by looking at the extension django fixes the content type

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
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # exceeding max file size
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(target_size_bytes=PORTFOLIO_IMAGE_MAX_SIZE * 2),
        )

        # more tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=PORTFOLIO_MAX_TAG_COUNT + 1),
            predefined_vals={"creator": self.profile},
        )


# CreatePortfolioCommentSerializer
class TestCreatePortfolioCommentSerializerProcessing(PortfolioCommentBaseTestCase):
    def test_valid_create_portfolio_comment_processing(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        stripped_comment = original_vals["comment"]
        original_vals["comment"] = f"   {stripped_comment}   \n\t"

        serializer = CreatePortfolioCommentSerializer(
            data=original_vals,
            context={
                "portfolio": vals_to_create_from["portfolio"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data
        self.assertEqual(data["comment"], stripped_comment)


# CreatePortfolioCommentSerializer
class TestCreatePortfolioCommentSerializerInvalidData(PortfolioCommentBaseTestCase):
    def setUp(self):
        super().setUp()
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, self.portfolio = portfolio_tester.create_random_valid_object()
        self.profile = self.user.profile
        self.url = reverse(
            f"{self.namespace}:create-portfolio-comment",
            kwargs={"portfolio_id": self.portfolio.id},
        )
        self.client.force_authenticate(user=self.user)

    def test_create_portfolio_comment_missing_fields(self):
        # missing comment
        send_missing_field(self, self.url, ["comment"])
        send_missing_field(self, self.url, ["parent_comment_id"])

    def test_create_portfolio_comment_invalid_fields(self):
        # short comment
        send_invalid_field(
            self,
            self.url,
            "comment",
            self.get_random_comment_value(L=PORTFOLIO_MIN_COMMENT_LEN - 1),
            predefined_vals={
                "portfolio": self.portfolio,
                "profile": self.profile,
                "parent_comment": -1,
            },
        )
        
        # long comment
        send_invalid_field(
            self,
            self.url,
            "comment",
            self.get_random_comment_value(L=PORTFOLIO_MAX_COMMENT_LEN + 10),
            predefined_vals={
                "portfolio": self.portfolio,
                "profile": self.profile,
                "parent_comment": -1,
            },
        )

        # non existing parent comment
        send_invalid_field(
            self,
            self.url,
            "parent_comment_id",
            0,
            predefined_vals={"portfolio": self.portfolio, "profile": self.profile},
        )

        # existing parent comment but from another portfolio
        _, _, _, parent = self.create_random_valid_object()
        send_invalid_field(
            self,
            self.url,
            "parent_comment_id",
            parent.id,
            predefined_vals={"portfolio": self.portfolio, "profile": self.profile},
        )


# CreateWorkSerializer
class TestCreateWorkSerializerProcessing(WorkBaseTestCase):
    def test_valid_work_title_processing(self):
        # padded title
        original_vals, _, _ = self.get_random_valid_data()
        original_vals["work_files"] = [original_vals["work_file"]]
        del original_vals[
            "work_file"
        ]  # check the bottom of the file for explanation for this deletion
        stripped_title = original_vals["title"]

        original_vals["title"] = f"   {stripped_title}   \n\t"

        serializer = CreateWorkSerializer(data=original_vals)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["title"], stripped_title)


# CreateWorkSerializer
class TestCreateWorkSerializerInvalidData(WorkBaseTestCase):
    def setUp(self):
        super().setUp()
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        self.url = reverse(
            f"{self.namespace}:create-work", kwargs={"portfolio_id": portfolio.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_create_work_missing_fields(self):
        # missing title
        _, vals_to_send_request, _ = self.get_random_valid_data()
        # we need to do this line explicity so we cant just call send_invalid_field()
        vals_to_send_request["work_files"] = [vals_to_send_request["work_file"]]
        del vals_to_send_request[
            "work_file"
        ]  # check the bottom of the file for explanation for this deletion
        for f in ["title"]:
            del vals_to_send_request[f]
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)
        for f in ["title"]:
            self.assertIn(f, response.data)

        # missing work_files should not work
        _, vals_to_send_request, _ = self.get_random_valid_data()
        # we need to do this line explicity so we cant just call send_invalid_field()
        vals_to_send_request["work_files"] = []
        del vals_to_send_request[
            "work_file"
        ]  # check the bottom of the file for explanation for this deletion
        for f in ["work_files"]:
            del vals_to_send_request[f]
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)
        for f in ["work_files"]:
            self.assertIn(f, response.data)

    def test_create_work_invalid_fields(self):
        # long title
        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={
                "title": self.get_random_title_value(L=WORK_MAX_TITLE_LEN + 10)
            }
        )
        # we need to do this line explicity so we cant just call send_invalid_field()
        vals_to_send_request["work_files"] = [vals_to_send_request["work_file"]]
        del vals_to_send_request[
            "work_file"
        ]  # check the bottom of the file for explanation for this deletion
        response = self.client.post(self.url, vals_to_send_request, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)


# "del vals_to_send_request["work_file"]" we need to delete this to prevent some django error
# If I understood correctly, django does something with some suffixes. "-id" gets the id "-s" makes it list or something
# and if I dont delete the 'work_file' field, I guess django creates the 'work_files' field from 'work_file' field or something like that
# it gives "{'work_files': {0: [ErrorDetail(string='The submitted file is empty.', code='empty')]}}" error
