from django.urls import reverse
from rest_framework.test import APIRequestFactory
from ..models import *
from .base_test import *
from ..globals import *
from ..serializers import *
from utils.test_utils import send_missing_field, send_invalid_field
from unittest.mock import patch


# ReturnChapterMangaOwnerCollaboratorsReferenceSerializer
class TestReturnChapterMangaOwnerCollaboratorsReferenceSerializerFields(
    MangaBaseTestCase
):
    def test_owner_collaborator_reference_returned_fields(self):
        _, _, _, manga = self.create_random_valid_object()
        profile = manga.owner

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnChapterMangaOwnerCollaboratorsReferenceSerializer(
            profile, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "profile_name", "image"})


# ReturnChapterSerializer
class TestReturnChapterSerializerFields(ChapterBaseTestCase):
    def test_chapter_returned_fields(self):
        _, _, _, chapter = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnChapterSerializer(chapter, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "no",
                "manga",
                "owner",
                "collaborators",
                "publish_date",
                "price",
                "pdf",
                "folder_name",
                "num_of_images",
                "pages_base_url",
                "is_user_bought",
                "is_user_read",
            },
        )


# CreateEditChapterSerializer
class TestCreateEditChapterSerializerFields(ChapterBaseTestCase):
    def test_create_chapter_returned_fields(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()
        serializer = CreateEditChapterSerializer(
            data=original_vals,
            context={
                "manga": vals_to_create_from["manga"],
                "owner": vals_to_create_from["owner"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(
            set(data.keys()), {"title", "no", "collaborators", "price", "pdf"}
        )


# ReturnMangaTagSerializer
class TestReturnMangaTagSerializerFields(MangaTagBaseTestCase):
    def test_tag_returned_fields(self):
        _, _, _, tag = self.create_random_valid_object()

        serializer = ReturnMangaTagSerializer(tag)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "label"})


# ReturnMangaRatingSerializer
class TestReturnMangaRatingSerializerFields(MangaRatingBaseTestCase):
    def test_like_returned_fields(self):
        _, _, _, like = self.create_random_valid_object()

        serializer = ReturnMangaRatingSerializer(like)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "manga", "profile", "score"})


# ReturnMangaCommentSerializer
class TestReturnMangaCommentSerializerFields(MangaCommentBaseTestCase):
    def test_comment_returned_fields(self):
        _, _, _, comment = self.create_random_valid_object()

        serializer = ReturnMangaCommentSerializer(comment)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "profile_name", "comment", "parent_comment_id"}
        )


# ReturnMangaSerializer
class TestReturnMangaSerializerFields(MangaBaseTestCase):
    def test_manga_returned_fields(self):
        _, _, _, manga = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnMangaSerializer(manga, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "description",
                "image",
                "owner",
                "collaborators",
                "folder_name",
                "start_date",
                "last_update_date",
                "tags",
                "chapters",
                "bookmark",
            },
        )


# ReturnTextSearchMangaSerializer
class TestReturnTextSearchMangaSerializerFields(MangaBaseTestCase):
    def test_text_search_manga_returned_fields(self):
        _, _, _, manga = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnTextSearchMangaSerializer(
            manga, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "image",
                "owner",
                "tags",
                # "rating",
                # "num_of_chapters",
            },
        )


# ReturnReadMangaSerializer
class TestReturnReadMangaSerializerFields(MangaBaseTestCase):
    def test_read_manga_returned_fields(self):
        _, _, _, manga = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnReadMangaSerializer(manga, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "folder_name", "chapters", "bookmark"}
        )


# ReturnMangaGallerySerializer
class TestReturnMangaGallerySerializerFields(MangaBaseTestCase):
    def test_manga_gallery_returned_fields(self):
        _, _, _, manga = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnMangaGallerySerializer(manga, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "title",
                "image",
                "start_date",
                "last_update_date",
                "tags",
                # below are calculated in the view they are not serializer native
                # "rating",
                # "num_of_ratings",
                # "num_of_chapters",
                # "num_of_collaborators",
                # "num_of_followers",
                # "total_price_of_all_chapters",
            },
        )


# CreateEditMangaSerializer
class TestCreateEditMangaSerializerFields(MangaBaseTestCase):
    def test_create_edit_manga_returned_fields(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditMangaSerializer(
            data=original_vals,
            context={"request": request, "owner": vals_to_create_from["owner"]},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(
            set(data.keys()), {"title", "description", "image", "tags", "collaborators"}
        )


# CreateMangaCommentSerializer
class TestCreateMangaCommentSerializerFields(MangaCommentBaseTestCase):
    def test_create_comment_returned_fields(self):
        # get data for a comment with no parent
        original_vals, _, vals_to_create_from = self.get_random_valid_data(
            predefined_vals={"parent_comment": -1}
        )

        # serialize the data
        serializer = CreateMangaCommentSerializer(
            data=original_vals,
            context={
                "manga": vals_to_create_from["manga"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = serializer.validated_data

        # first comment wont have a parent because it's parentless
        self.assertEqual(set(data.keys()), {"comment", "parent_comment_id"})

        # save this comment as the first comment on that manga
        parent_comment = serializer.save()

        # then create a new comment that's replying to that comment
        new_original_vals, _, _ = self.get_random_valid_data(
            predefined_vals={"parent_comment": parent_comment}
        )

        reply_serializer = CreateMangaCommentSerializer(
            data=new_original_vals,
            context={
                "manga": vals_to_create_from["manga"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(reply_serializer.is_valid(), reply_serializer.errors)
        reply_data = reply_serializer.validated_data

        # serializer adds 'parent_comment' field in the validated data
        self.assertEqual(
            set(reply_data.keys()), {"comment", "parent_comment", "parent_comment_id"}
        )


# CreateEditChapterSerializer
class TestCreateEditChapterSerializerLimit(ChapterBaseTestCase):
    def test_chapter_limit_exceeded(self):
        NEW_LIMIT = 3
        with patch("MangaPageApp.serializers.MAX_CHAPTER_COUNT_PER_MANGA", NEW_LIMIT):
            # create a total of MAX_CHAPTER_COUNT_PER_MANGA mangas under the created manga
            manga_tester = MangaBaseTestCase()
            _, _, _, manga = manga_tester.create_random_valid_object()
            for _ in range(NEW_LIMIT):
                self.create_random_valid_object(predefined_vals={"manga": manga})

            # then try to serialize another data for a new chapter
            # it should fail the "if manga.chapters.count() >= MAX_CHAPTER_COUNT_PER_MANGA:" check
            original_vals, _, vals_to_create_from = self.get_random_valid_data(
                predefined_vals={"manga": manga}
            )

            factory = APIRequestFactory()
            request = factory.post("/")
            request.user = self.user

            serializer = CreateEditChapterSerializer(
                data=original_vals,
                context={
                    "request": request,
                    "manga": manga,
                    "owner": vals_to_create_from["owner"],
                },
            )

            self.assertFalse(serializer.is_valid())
            self.assertIn("limit", serializer.errors)

    def test_chapter_pdf_page_limit_exceeded_with_pdf_check(self):
        # try to serialize data for a new chapter with lots of pages
        # it should fail the pdf page count check in the pdf_check function
        original_vals, _, vals_to_create_from = self.get_random_valid_data(
            predefined_vals={
                "pdf": self.get_random_pdf_value(pages=CHAPTER_PDF_MAX_PAGE + 5)
            }
        )

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditChapterSerializer(
            data=original_vals,
            context={
                "request": request,
                "manga": vals_to_create_from["manga"],
                "owner": vals_to_create_from["owner"],
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("pdf", serializer.errors)

    def test_chapter_pdf_page_limit_exceeded_with_pdf_parse(self):
        # Use self.assertRaises to catch the expected RuntimeError
        with self.assertRaises(RuntimeError) as context:
            self.create_random_valid_object(
                predefined_vals={
                    "pdf": self.get_random_pdf_value(pages=CHAPTER_PDF_MAX_PAGE + 5)
                }
            )

        self.assertIn("dropped due to validation failure", str(context.exception))
        self.assertFalse(Chapter.objects.filter(id=1).exists())


# CreateEditMangaSerializer
class TestCreateEditMangaSerializerLimit(MangaBaseTestCase):
    def test_manga_limit_exceeded(self):
        NEW_LIMIT = 3
        with patch("MangaPageApp.serializers.MAX_MANGA_COUNT_PER_PROFILE", NEW_LIMIT):
            # create a total of MAX_MANGA_COUNT_PER_PROFILE mangas for the user
            profile = self.user.profile
            for _ in range(NEW_LIMIT):
                self.create_random_valid_object(predefined_vals={"owner": profile})

            # then try to serialize another data for a new manga
            # it should fail the "if profile.mangas.count() >= MAX_MANGA_COUNT_PER_PROFILE:" check
            original_vals, _, _ = self.get_random_valid_data(
                predefined_vals={"owner": profile}
            )

            factory = APIRequestFactory()
            request = factory.post("/")
            request.user = self.user

            serializer = CreateEditMangaSerializer(
                data=original_vals, context={"request": request, "owner": profile}
            )

            self.assertFalse(serializer.is_valid())
            self.assertIn("limit", serializer.errors)


# CreateEditMangaSerializer
class TestCreateEditMangaSerializerProcessing(MangaBaseTestCase):
    def test_valid_create_edit_manga_field_processing(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        stripped_title = original_vals["title"]
        stripped_description = original_vals["description"]

        original_vals["title"] = f"   {stripped_title}   "
        original_vals["description"] = f"\n  {stripped_description} \t"

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditMangaSerializer(
            data=original_vals,
            context={"request": request, "owner": vals_to_create_from["owner"]},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data
        self.assertEqual(data["title"], stripped_title)
        self.assertEqual(data["description"], stripped_description)


# CreateEditMangaSerializer
class TestCreateEditMangaSerializerInvalidData(MangaBaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.user.profile
        self.tags = self.get_random_tags_value()
        self.url = reverse(f"{self.namespace}:create-manga")
        self.client.force_authenticate(user=self.user)

    def test_create_edit_manga_missing_fields(self):
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
        send_missing_field(
            self, self.url, ["tags"], predefined_vals={"owner": self.profile}
        )
        # no collaborators is okay because we have 'allow_empty' in the serializer
        # send_missing_field(
        #     self, self.url, ["collaborators"], predefined_vals={"owner": self.profile}
        # )

    def test_create_edit_manga_invalid_fields(self):
        # short title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=MANGA_MIN_TITLE_LEN - 1),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # long title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=MANGA_MAX_TITLE_LEN + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # short description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=MANGA_MIN_DESCRIPTION_LEN - 1),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # long description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=MANGA_MAX_DESCRIPTION_LEN + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )

        # small dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=MANGA_IMAGE_MIN_W - 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=MANGA_IMAGE_MIN_H - 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        # big dimensions
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=MANGA_IMAGE_MAX_W + 10),
            predefined_vals={"owner": self.profile, "tags": self.tags},
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=MANGA_IMAGE_MAX_H + 10),
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
            self.get_random_image_value(target_size_bytes=MANGA_IMAGE_MAX_SIZE * 2),
        )

        # less tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=MANGA_MIN_TAG_COUNT - 1),
            predefined_vals={"creator": self.profile},
        )
        # more tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=MANGA_MAX_TAG_COUNT + 1),
            predefined_vals={"creator": self.profile},
        )

        # invalid tags (both original and translation tags are selected)
        send_invalid_field(
            self, self.url, "tags", [1, 2], predefined_vals={"owner": self.profile}
        )

        # more collaborator
        send_invalid_field(
            self,
            self.url,
            "collaborators",
            self.get_random_collaborators_value(count=MANGA_MAX_COLLABORATOR_COUNT + 1),
            predefined_vals={"creator": self.profile},
        )


# CreateMangaCommentSerializer
class TestCreateMangaCommentSerializerProcessing(MangaCommentBaseTestCase):
    def test_valid_create_manga_comment_processing(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        stripped_comment = original_vals["comment"]
        original_vals["comment"] = f"   {stripped_comment}   \n\t"

        serializer = CreateMangaCommentSerializer(
            data=original_vals,
            context={
                "manga": vals_to_create_from["manga"],
                "profile": vals_to_create_from["profile"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data
        self.assertEqual(data["comment"], stripped_comment)


# CreateMangaCommentSerializer
class TestCreateMangaCommentSerializerInvalidData(MangaCommentBaseTestCase):
    def setUp(self):
        super().setUp()
        manga_tester = MangaBaseTestCase()
        _, _, _, self.manga = manga_tester.create_random_valid_object()
        self.profile = self.user.profile
        self.url = reverse(
            f"{self.namespace}:create-manga-comment", kwargs={"manga_id": self.manga.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_create_manga_comment_missing_fields(self):
        # missing comment
        send_missing_field(self, self.url, ["comment"])
        send_missing_field(self, self.url, ["parent_comment_id"])

    def test_create_manga_comment_invalid_fields(self):
        # short comment
        send_invalid_field(
            self,
            self.url,
            "comment",
            self.get_random_comment_value(L=MANGA_MIN_COMMENT_LEN - 1),
            predefined_vals={
                "manga": self.manga,
                "profile": self.profile,
                "parent_comment": -1,
            },
        )

        # long comment
        send_invalid_field(
            self,
            self.url,
            "comment",
            self.get_random_comment_value(L=MANGA_MAX_COMMENT_LEN + 10),
            predefined_vals={
                "manga": self.manga,
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
            predefined_vals={"manga": self.manga, "profile": self.profile},
        )

        # existing parent comment but from another manga
        _, _, _, parent = self.create_random_valid_object()
        send_invalid_field(
            self,
            self.url,
            "parent_comment_id",
            parent.id,
            predefined_vals={"manga": self.manga, "profile": self.profile},
        )


# CreateEditChapterSerializer
class TestCreateEditChapterSerializerProcessing(ChapterBaseTestCase):
    def test_valid_create_edit_chapter_field_processing(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        original_vals, _, vals_to_create_from = self.get_random_valid_data(
            predefined_vals={"manga": manga, "owner": manga.owner}
        )

        stripped_title = original_vals["title"]
        stripped_no = original_vals["no"]
        integer_price = original_vals["price"]

        original_vals["title"] = f"   {stripped_title}   "
        original_vals["no"] = f"   {stripped_no}   "
        # price is casted to int
        original_vals["price"] = f"{integer_price}"
        # owner gets discarded from the collaborators

        factory = APIRequestFactory()
        request = factory.post("/")
        request.user = self.user

        serializer = CreateEditChapterSerializer(
            data=original_vals,
            context={
                "request": request,
                "manga": manga,
                "owner": vals_to_create_from["owner"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data
        self.assertEqual(data["title"], stripped_title)
        self.assertEqual(data["no"], stripped_no)
        self.assertEqual(data["price"], integer_price)


# CreateEditChapterSerializer
class TestCreateEditChapterSerializerInvalidData(ChapterBaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.user.profile
        manga_tester = MangaBaseTestCase()
        _, _, _, self.manga = manga_tester.create_random_valid_object(
            predefined_vals={"owner": self.profile}
        )
        self.url = reverse(
            f"{self.namespace}:create-chapter", kwargs={"manga_id": self.manga.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_create_edit_chapter_missing_fields(self):
        send_missing_field(
            self,
            self.url,
            ["title"],
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        send_missing_field(
            self,
            self.url,
            ["no"],
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        # no collaborators is okay because we have 'allow_empty' in the serializer
        # send_missing_field(
        #     self,
        #     self.url,
        #     ["collaborators"],
        #     predefined_vals={"manga": self.manga, "owner": self.profile},
        # )
        send_missing_field(
            self,
            self.url,
            ["price"],
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        send_missing_field(
            self,
            self.url,
            ["pdf"],
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

    def test_create_edit_chapter_invalid_fields(self):
        # short title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=CHAPTER_MIN_TITLE_LEN - 1),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        # long title
        send_invalid_field(
            self,
            self.url,
            "title",
            self.get_random_title_value(L=CHAPTER_MAX_TITLE_LEN + 10),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # short no
        send_invalid_field(
            self,
            self.url,
            "no",
            self.get_random_no_value(L=CHAPTER_MIN_NO_LEN - 1),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        # long no
        send_invalid_field(
            self,
            self.url,
            "no",
            self.get_random_no_value(L=CHAPTER_MAX_NO_LEN + 10),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # negative price
        send_invalid_field(
            self,
            self.url,
            "price",
            -1,
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # floating point price
        send_invalid_field(
            self,
            self.url,
            "price",
            10.5,
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # wrong file format
        send_invalid_field(
            self,
            self.url,
            "pdf",
            get_dummy_file(ext="png", target_size_bytes=CHAPTER_PDF_MAX_SIZE / 20),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # big pdf
        send_invalid_field(
            self,
            self.url,
            "pdf",
            self.get_random_pdf_value(target_size_bytes=CHAPTER_PDF_MAX_SIZE * 2),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )
        # long pdf
        send_invalid_field(
            self,
            self.url,
            "pdf",
            self.get_random_pdf_value(pages=CHAPTER_PDF_MAX_PAGE + 5),
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )

        # more collaborator
        send_invalid_field(
            self,
            self.url,
            "collaborators",
            self.get_random_collaborators_value(count=MANGA_MAX_COLLABORATOR_COUNT + 1),
            predefined_vals={"creator": self.profile},
        )

    def test_create_edit_chapter_duplicate_no(self):
        _, _, _, chapter = self.create_random_valid_object(
            predefined_vals={"manga": self.manga, "owner": self.profile}
        )

        # duplicate no
        send_invalid_field(
            self,
            self.url,
            "no",
            # intended use for the no is numbers but we allow strings too
            # so get_dummy_text_string is used for the test case for the 'long no' fail
            chapter.no,
            predefined_vals={"manga": self.manga, "owner": self.profile},
        )


# ReturnChapterSerializer
class TestReturnChapterSerializerReadStatus(ChapterBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.chapter = self.create_random_valid_object()
        self.manga = self.chapter.manga

        self.factory = APIRequestFactory()

    def test_is_user_read_false_for_unread_chapter(self):
        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnChapterSerializer(self.chapter, context={"request": request})

        self.assertFalse(serializer.data["is_user_read"])

    def test_is_user_read_true_for_read_chapter(self):
        ReadChapter.objects.create(profile=self.user.profile, chapter=self.chapter)

        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnChapterSerializer(self.chapter, context={"request": request})

        self.assertTrue(serializer.data["is_user_read"])


# ReturnMangaSerializer
# ReturnReadMangaSerializer
class TestMangaBookmarkSerializerFields(ChapterBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.chapter = self.create_random_valid_object()
        self.manga = self.chapter.manga

        self.factory = APIRequestFactory()

    def test_return_manga_serializer_without_bookmark(self):
        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnMangaSerializer(self.manga, context={"request": request})

        self.assertIsNone(serializer.data["bookmark"])

    def test_return_manga_serializer_with_bookmark(self):
        MangaBookmark.objects.create(
            manga=self.manga, profile=self.user.profile, chapter=self.chapter, page=0
        )

        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnMangaSerializer(self.manga, context={"request": request})

        self.assertEqual(
            serializer.data["bookmark"], {"chapter_id": self.chapter.id, "page": 0}
        )

    def test_return_read_manga_serializer_without_bookmark(self):
        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnReadMangaSerializer(self.manga, context={"request": request})

        self.assertIsNone(serializer.data["bookmark"])

    def test_return_read_manga_serializer_with_bookmark(self):
        MangaBookmark.objects.create(
            manga=self.manga, profile=self.user.profile, chapter=self.chapter, page=0
        )

        request = self.factory.get("/")
        request.user = self.user

        serializer = ReturnReadMangaSerializer(self.manga, context={"request": request})

        self.assertEqual(
            serializer.data["bookmark"], {"chapter_id": self.chapter.id, "page": 0}
        )
