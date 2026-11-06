from django.urls import reverse
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

from ..models import *
from .base_test import *
from ..globals import *
from ..serializers import *

from utils.test_utils import send_missing_field, send_invalid_field
from MangaPageApp.tests.base_test import MangaBaseTestCase, ChapterBaseTestCase
from PortfolioPageApp.tests.base_test import PortfolioBaseTestCase


# ReturnMangaReferenceSerializer
class TestReturnMangaReferenceSerializerFields(ProfileBaseTestCase):
    def test_manga_reference_returned_fields(self):
        manga_tester = MangaBaseTestCase()
        _, _, _, manga = manga_tester.create_random_valid_object()

        serializer = ReturnMangaReferenceSerializer(manga)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "title", "image"})


# ReturnChapterReferenceSerializer
class TestReturnChapterReferenceSerializerFields(ProfileBaseTestCase):
    def test_chapter_reference_returned_fields(self):
        chapter_tester = ChapterBaseTestCase()
        _, _, _, chapter = chapter_tester.create_random_valid_object()

        serializer = ReturnChapterReferenceSerializer(chapter)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "title", "no", "manga", "manga_title"}
        )


# ReturnPortfolioReferenceSerializer
class TestReturnPortfolioReferenceSerializerFields(ProfileBaseTestCase):
    def test_portfolio_reference_returned_fields(self):
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, portfolio = portfolio_tester.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnPortfolioReferenceSerializer(
            portfolio, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "title", "image"})


# ReturnProfileReferenceSerializer
class TestReturnProfileReferenceSerializerFields(ProfileBaseTestCase):
    def test_profile_reference_returned_fields(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnProfileReferenceSerializer(
            profile, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "profile_name", "image"})


# ReturnFollowedProfileSerializer
class TestReturnFollowedProfileSerializerFields(ProfileBaseTestCase):
    def test_followed_profile_returned_fields(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        serializer = ReturnFollowedProfileSerializer(profile)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "profile_name"})


# ReturnMessagingProfileSerializer
class TestReturnMessagingProfileSerializerFields(ProfileBaseTestCase):
    def test_messaging_profile_returned_fields(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        serializer = ReturnMessagingProfileSerializer(profile)
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "profile_name",
                "image",
                # "unread_messages"
            },
        )


# ReturnUserSerializer
class TestReturnUserSerializerFields(ProfileBaseTestCase):
    def test_user_returned_fields(self):
        serializer = ReturnUserSerializer(self.user)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "username", "email"})


# ReturnProfileSerializer
class TestReturnProfileSerializerFields(ProfileBaseTestCase):
    def test_profile_returned_fields(self):
        _, _, _, profile = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnProfileSerializer(profile, context={"request": request})
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "user",
                "id",
                "profile_name",
                "image",
                "wallet",
                "open_date",
                "mangas_owned",
                "mangas_collaborated",
                "chapters_owned",
                "chapters_collaborated",
                "portfolios",
                "profiles_following",
                "profiles_blocked",
                "mangas_following",
            },
        )


# ReturnNonOwnerProfileSerializer
class TestReturnNonOwnerProfileSerializerFields(ProfileBaseTestCase):
    def test_non_owner_profile_returned_fields(self):
        _, _, _, profile = self.create_random_valid_object()

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = ReturnNonOwnerProfileSerializer(
            profile, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "profile_name",
                "image",
                "open_date",
                "mangas_owned",
                "mangas_collaborated",
                "chapters_owned",
                "chapters_collaborated",
                "portfolios",
            },
        )


# EditProfileSerializer
class TestEditProfileSerializerFields(ProfileBaseTestCase):
    def test_edit_profile_returned_fields(self):
        original_vals, _, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        serializer = EditProfileSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(
            set(data.keys()), {"profile_name", "email", "password", "image"}
        )


# ReturnProfileMessageSerializer
class TestReturnProfileMessageSerializerFields(ProfileMessageBaseTestCase):
    def test_profile_message_returned_fields(self):
        _, _, _, message = self.create_random_valid_object()

        serializer = ReturnProfileMessageSerializer(message)
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {"id", "sender", "receiver", "message", "timestamp", "is_read"},
        )


# CreateProfileMessageSerializer
class TestCreateProfileMessageSerializerFields(ProfileMessageBaseTestCase):
    def test_create_profile_message_returned_fields(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        serializer = CreateProfileMessageSerializer(
            data=original_vals,
            context={
                "sender": vals_to_create_from["sender"],
                "receiver": vals_to_create_from["receiver"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(set(data.keys()), {"message"})


# EditProfileSerializer
class TestEditProfileSerializerProcessing(ProfileBaseTestCase):
    def test_valid_edit_profile_field_processing(self):
        original_vals, _, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        stripped_profile_name = original_vals["profile_name"]
        stripped_email = original_vals["email"]
        stripped_password = original_vals["password"]

        original_vals["profile_name"] = f"   {stripped_profile_name}   "
        original_vals["email"] = f"\n  {stripped_email}   \t"
        original_vals["password"] = f"\t  {stripped_password}   "

        serializer = EditProfileSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        data = serializer.validated_data
        self.assertEqual(data["profile_name"], stripped_profile_name)
        self.assertEqual(data["email"], stripped_email)
        self.assertEqual(data["password"], stripped_password)


# EditProfileSerializer
class TestEditProfileSerializerInvalidData(ProfileBaseTestCase):
    def setUp(self):
        super().setUp()

        self.profile = self.user.profile
        self.url = reverse(
            f"{self.namespace}:edit-profile", kwargs={"profile_id": self.profile.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_edit_profile_invalid_fields(self):
        # short profile name
        send_invalid_field(
            self,
            self.url,
            "profile_name",
            self.get_random_profile_name_value(L=PROFILE_MIN_NAME_LEN - 1),
            predefined_vals=fast_creation_dict,
            call="patch",
        )
        # long profile_name
        send_invalid_field(
            self,
            self.url,
            "profile_name",
            self.get_random_profile_name_value(L=PROFILE_MAX_NAME_LEN + 10),
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # duplicate profile name
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        send_invalid_field(
            self,
            self.url,
            "profile_name",
            profile.profile_name,
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # short email
        send_invalid_field(
            self,
            self.url,
            "email",
            self.get_random_email_value(L=PROFILE_MIN_EMAIL_LEN - 1),
            predefined_vals=fast_creation_dict,
            call="patch",
        )
        # long email
        send_invalid_field(
            self,
            self.url,
            "email",
            self.get_random_email_value(L=PROFILE_MAX_EMAIL_LEN + 10),
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # invalid email with no @
        send_invalid_field(
            self,
            self.url,
            "email",
            "invalidemail.com",
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # duplicate mail name
        _, _, _, duplicate_user = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        send_invalid_field(
            self,
            self.url,
            "email",
            duplicate_user.user.email,
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # short password
        send_invalid_field(
            self,
            self.url,
            "password",
            self.get_random_password_value(L=PROFILE_MIN_PASSWORD_LEN - 1),
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # long password
        send_invalid_field(
            self,
            self.url,
            "password",
            self.get_random_password_value(L=PROFILE_MAX_PASSWORD_LEN + 10),
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # invalid image
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=PROFILE_IMAGE_MAX_W + 100),
            predefined_vals=fast_creation_dict,
            call="patch",
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=PROFILE_IMAGE_MAX_H + 100),
            predefined_vals=fast_creation_dict,
            call="patch",
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(W=PROFILE_IMAGE_MIN_W - 1),
            predefined_vals=fast_creation_dict,
            call="patch",
        )
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(H=PROFILE_IMAGE_MIN_H - 1),
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # wrong image extension
        invalid_ext_file = self.get_random_image_value()
        invalid_ext_file.name = invalid_ext_file.name.rsplit(".", 1)[0] + ".mp4"
        send_invalid_field(
            self,
            self.url,
            "image",
            invalid_ext_file,
            predefined_vals=fast_creation_dict,
            call="patch",
        )

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
            predefined_vals=fast_creation_dict,
            call="patch",
        )

        # exceeding max file size
        send_invalid_field(
            self,
            self.url,
            "image",
            self.get_random_image_value(target_size_bytes=PROFILE_IMAGE_MAX_SIZE * 2),
            predefined_vals=fast_creation_dict,
            call="patch",
        )


# CreateProfileMessageSerializer
class TestCreateProfileMessageSerializerProcessing(ProfileMessageBaseTestCase):
    def test_valid_create_profile_message_processing(self):
        original_vals, _, vals_to_create_from = self.get_random_valid_data()

        stripped_message = original_vals["message"]

        original_vals["message"] = f"\n\t   {stripped_message}   \t"

        serializer = CreateProfileMessageSerializer(
            data=original_vals,
            context={
                "sender": vals_to_create_from["sender"],
                "receiver": vals_to_create_from["receiver"],
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(data["message"], stripped_message)


# CreateProfileMessageSerializer
class TestCreateProfileMessageSerializerInvalidData(ProfileMessageBaseTestCase):
    def setUp(self):
        super().setUp()

        _, _, _, self.profile_message = self.create_random_valid_object()

        self.sender = self.profile_message.sender
        self.receiver = self.profile_message.receiver

        self.url = reverse(
            f"{self.namespace}:create-profile-message",
            kwargs={"profile_id": self.receiver.id},
        )

        self.client.force_authenticate(user=self.sender.user)

    def test_create_profile_message_missing_fields(self):
        send_missing_field(self, self.url, ["message"])

    def test_create_profile_message_invalid_fields(self):
        # short message
        send_invalid_field(
            self,
            self.url,
            "message",
            self.get_random_message_value(L=PROFILE_MESSAGE_MIN_LEN - 1),
        )

        # long message
        send_invalid_field(
            self,
            self.url,
            "message",
            self.get_random_message_value(L= PROFILE_MESSAGE_MAX_LEN + 10),
        )

    def test_create_profile_message_same_sender_receiver(self):
        serializer = CreateProfileMessageSerializer(
            data={"message": "hello"},
            context={"sender": self.sender, "receiver": self.sender},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("message", serializer.errors)

    def test_create_profile_message_not_following(self):
        self.sender.profiles_following.clear()

        serializer = CreateProfileMessageSerializer(
            data={"message": "hello"},
            context={"sender": self.sender, "receiver": self.receiver},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("message", serializer.errors)

    def test_create_profile_message_blocked_sender(self):
        self.sender.profiles_blocked.add(self.receiver)

        serializer = CreateProfileMessageSerializer(
            data={"message": "hello"},
            context={"sender": self.sender, "receiver": self.receiver},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("message", serializer.errors)

    def test_create_profile_message_blocked_by_receiver(self):
        self.receiver.profiles_blocked.add(self.sender)

        serializer = CreateProfileMessageSerializer(
            data={"message": "hello"},
            context={"sender": self.sender, "receiver": self.receiver},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("message", serializer.errors)
