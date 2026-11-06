from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from utils.test_utils import *

from ..globals import *
from ..models import *
from MangaPageApp.tests.base_test import MangaBaseTestCase
from utils.helper_functions import send_verification_email
from django.conf import settings
from magnam.storage import file_storage

fast_creation_dict = {
    "mangas_following": [],
    "profiles_following": [],
    "profiles_blocked": [],
}


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class ProfileBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "ProfilePageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_email_value(self, L=20, seed=None):
        # we do -9 to match the given L parameter length
        return f"{get_dummy_text_string(L=L-9, seed=seed)}@test.com"

    def get_random_password_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_profile_name_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_profiles_following_value(self, count=1, seed=None):
        profiles_following = []

        for i in range(count):
            profiles_following.append(
                get_dummy_profile(seed=seed + i if seed is not None else None)
            )

        return profiles_following

    def get_random_profiles_blocked_value(self, count=1, seed=None):
        profiles_blocked = []

        for i in range(count):
            profiles_blocked.append(
                get_dummy_profile(seed=seed + i if seed is not None else None)
            )

        return profiles_blocked

    def get_random_mangas_following_value(self, count=1, seed=None):
        manga_tester = MangaBaseTestCase()

        mangas = []

        for i in range(count):
            _, _, _, manga = manga_tester.create_random_valid_object(
                seed=seed + i if seed is not None else None
            )

            mangas.append(manga)

        return mangas

    def get_random_image_value(
        self,
        W=PROFILE_IMAGE_MAX_W,
        H=PROFILE_IMAGE_MAX_H,
        target_size_bytes=PROFILE_IMAGE_MAX_SIZE / 10,
        ext="png",
        seed=None,
    ):
        return get_dummy_file(
            W=W, H=H, target_size_bytes=target_size_bytes, ext=ext, seed=seed
        )

    def get_random_wallet_value(self, seed=None):
        return random.Random(seed).randint(0, 100000)

    def get_random_verification_token_value(self, seed=None):
        return get_dummy_text_string(L=PROFILE_VERIFICATION_TOKEN_LEN, seed=seed)

    def get_random_is_verified_value(self, seed=None):
        return random.Random(seed).choice([True, False])

    def get_random_auth_provider_value(self, seed=None):
        return random.Random(seed).choice(["local", "google"])

    def get_random_non_verified_since_value(self):
        return timezone.now()

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        email = predefined_vals.get("email", self.get_random_email_value(seed=seed))
        password = predefined_vals.get(
            "password", self.get_random_password_value(seed=seed)
        )
        profile_name = predefined_vals.get(
            "profile_name", self.get_random_profile_name_value(seed=seed)
        )
        profiles_following = (
            predefined_vals["profiles_following"]
            if "profiles_following" in predefined_vals
            else self.get_random_profiles_following_value(seed=seed)
        )
        profiles_blocked = (
            predefined_vals["profiles_blocked"]
            if "profiles_blocked" in predefined_vals
            else self.get_random_profiles_blocked_value(seed=seed)
        )
        mangas_following = (
            predefined_vals["mangas_following"]
            if "mangas_following" in predefined_vals
            else self.get_random_mangas_following_value(seed=seed)
        )
        image = predefined_vals.get("image", self.get_random_image_value(seed=seed))
        wallet = predefined_vals.get("wallet", self.get_random_wallet_value(seed=seed))
        verification_token = predefined_vals.get(
            "verification_token", self.get_random_verification_token_value(seed=seed)
        )
        is_verified = predefined_vals.get(
            "is_verified", self.get_random_is_verified_value(seed=seed)
        )
        auth_provider = predefined_vals.get(
            "auth_provider", self.get_random_auth_provider_value(seed=seed)
        )
        non_verified_since = predefined_vals.get(
            "non_verified_since", self.get_random_non_verified_since_value()
        )

        if is_verified:  # verified profiles constraints
            verification_token = None
            non_verified_since = None
        else:  # non verified profiles constraints
            if verification_token is None:
                verification_token = self.get_random_verification_token_value(seed=seed)

            if non_verified_since is None:
                non_verified_since = self.get_random_non_verified_since_value()

            auth_provider = "local"

        original_vals = {
            "username": profile_name,
            "email": email,
            "password": password,
            "profile_name": profile_name,
            "profiles_following": [p.id for p in profiles_following],
            "profiles_blocked": [p.id for p in profiles_blocked],
            "mangas_following": [p.id for p in mangas_following],
            "image": image,
            "wallet": wallet,
            "verification_token": verification_token,
            "is_verified": is_verified,
            "non_verified_since": non_verified_since,
            "auth_provider": auth_provider,
        }

        vals_to_send_request = original_vals.copy()
        # we delete these because these are backend things
        # we only included these here to control the verification things later for controlled checks
        del vals_to_send_request["verification_token"]
        del vals_to_send_request["is_verified"]
        del vals_to_send_request["non_verified_since"]
        del vals_to_send_request["auth_provider"]

        vals_to_create_from = original_vals.copy()

        vals_to_create_from["profiles_following"] = profiles_following
        vals_to_create_from["profiles_blocked"] = profiles_blocked
        vals_to_create_from["mangas_following"] = mangas_following

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        profiles_following = vals_to_create_from.pop("profiles_following")
        profiles_blocked = vals_to_create_from.pop("profiles_blocked")
        mangas_following = vals_to_create_from.pop("mangas_following")

        user = User.objects.create_user(
            username=vals_to_create_from["username"],
            email=vals_to_create_from["email"],
            password=vals_to_create_from["password"],
        )
        send_verification_email(
            user_email=vals_to_create_from["email"],
            token=vals_to_create_from["verification_token"],
        )

        profile = Profile.objects.get(user=user)

        profile.profile_name = vals_to_create_from["profile_name"]
        profile.image = vals_to_create_from["image"]
        profile.wallet = vals_to_create_from["wallet"]
        profile.verification_token = vals_to_create_from["verification_token"]
        profile.is_verified = vals_to_create_from["is_verified"]
        profile.non_verified_since = vals_to_create_from["non_verified_since"]
        profile.auth_provider = vals_to_create_from["auth_provider"]
        profile.save()

        profile.profiles_following.set(profiles_following)
        profile.profiles_blocked.set(profiles_blocked)
        profile.mangas_following.set(mangas_following)

        vals_to_create_from["profiles_following"] = profiles_following
        vals_to_create_from["profiles_blocked"] = profiles_blocked
        vals_to_create_from["mangas_following"] = mangas_following

        return (original_vals, vals_to_send_request, vals_to_create_from, profile)

    def assert_database_image(self, profile: Profile):
        self.assertTrue(file_storage.exists(profile.image.name))
        self.assertTrue(
            profile.image.name.startswith(f"{settings.PROFILES_MEDIA_FOLDERNAME}/")
        )

    def assert_db_stored_values_match_expected_dict(
        self, profile: Profile, original_vals: dict
    ):
        # self.assertEqual(profile.user.username, original_vals["username"]) # we dont check this because registering generates random name
        self.assertEqual(profile.user.email, original_vals["email"])
        # self.assertEqual(profile.profile_name, original_vals["profile_name"]) # we dont check this because registering generates random name
        self.assertEqual(
            set([p.id for p in profile.profiles_following.all()]),
            set(original_vals["profiles_following"]),
        )
        self.assertEqual(
            set([p.id for p in profile.profiles_blocked.all()]),
            set(original_vals["profiles_blocked"]),
        )
        self.assertEqual(
            set([p.id for p in profile.mangas_following.all()]),
            set(original_vals["mangas_following"]),
        )
        self.assert_database_image(profile)
        # self.assertEqual(profile.wallet, original_vals["wallet"]) # we dont check this because registering hardsets wallet=0
        # self.assertEqual(
        #     profile.verification_token, original_vals["verification_token"] # we dont check this because registering generates random token
        # )
        # self.assertEqual(profile.is_verified, original_vals["is_verified"]) # we dont check this because registering sets this up
        # self.assertEqual(
        #     profile.non_verified_since, original_vals["non_verified_since"] # we dont check this because registering sets this up
        # )
        self.assertEqual(profile.auth_provider, original_vals["auth_provider"])

    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_profile: dict, profile: Profile
    ):
        self.assertEqual(retrieved_profile["id"], profile.id)
        self.assertEqual(retrieved_profile["profile_name"], profile.profile_name)
        self.assertEqual(
            set([p["id"] for p in retrieved_profile["profiles_following"]]),
            set([p.id for p in profile.profiles_following.all()]),
        )
        self.assertEqual(
            set([p["id"] for p in retrieved_profile["profiles_blocked"]]),
            set([p.id for p in profile.profiles_blocked.all()]),
        )
        self.assertEqual(
            set([m["id"] for m in retrieved_profile["mangas_following"]]),
            set([m.id for m in profile.mangas_following.all()]),
        )
        self.assertTrue(retrieved_profile["image"] != "")
        self.assertIn(str(profile.image), retrieved_profile["image"])
        self.assertEqual(retrieved_profile["wallet"], profile.wallet)
        self.assertEqual(retrieved_profile["open_date"], profile.open_date.isoformat())

    def assert_db_retrieved_dict_match_db_stored_values_for_non_owner_profile(
        self, retrieved_profile: dict, profile: Profile
    ):
        self.assertEqual(retrieved_profile["id"], profile.id)
        self.assertEqual(retrieved_profile["profile_name"], profile.profile_name)
        self.assertTrue(retrieved_profile["image"] != "")
        self.assertIn(str(profile.image), retrieved_profile["image"])
        self.assertEqual(retrieved_profile["open_date"], profile.open_date.isoformat())


@override_settings(DISABLE_EXTERNAL_CALLS_FOR_TESTING=True)
class ProfileMessageBaseTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        prepare_independent_test_space(self, "ProfilePageApp")

    def tearDown(self):
        clear_independent_test_space(self)

    def get_random_sender_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_receiver_value(self, seed=None):
        return get_dummy_profile(seed=seed)

    def get_random_message_value(self, L=10, seed=None):
        return get_dummy_text_string(L=L, seed=seed)

    def get_random_is_read_value(self, seed=None):
        return random.Random(seed).choice([True, False])

    def get_random_valid_data(self, seed=None, predefined_vals={}):
        sender = (
            predefined_vals["sender"]
            if "sender" in predefined_vals
            else self.get_random_sender_value(seed=seed)
        )
        receiver = (
            predefined_vals["receiver"]
            if "receiver" in predefined_vals
            else self.get_random_receiver_value(seed=seed)
        )
        message = predefined_vals.get(
            "message", self.get_random_message_value(seed=seed)
        )
        is_read = predefined_vals.get(
            "is_read", self.get_random_is_read_value(seed=seed)
        )
        original_vals = {
            "sender": sender.id,
            "receiver": receiver.id,
            "message": message,
            "is_read": is_read,
        }

        # message sending constraint
        sender.profiles_following.add(receiver)

        vals_to_send_request = original_vals.copy()
        vals_to_create_from = original_vals.copy()

        vals_to_create_from["sender"] = sender
        vals_to_create_from["receiver"] = receiver

        return original_vals, vals_to_send_request, vals_to_create_from

    def create_random_valid_object(self, seed=None, predefined_vals={}):
        original_vals, vals_to_send_request, vals_to_create_from = (
            self.get_random_valid_data(seed=seed, predefined_vals=predefined_vals)
        )

        profile_message = ProfileMessage.objects.create(**vals_to_create_from)

        return (
            original_vals,
            vals_to_send_request,
            vals_to_create_from,
            profile_message,
        )

    def assert_db_stored_values_match_expected_dict(
        self, profile_message: ProfileMessage, original_vals: dict
    ):
        self.assertEqual(profile_message.sender.id, original_vals["sender"])
        self.assertEqual(profile_message.receiver.id, original_vals["receiver"])
        self.assertEqual(profile_message.message, original_vals["message"])
        self.assertEqual(profile_message.is_read, original_vals["is_read"])
    def assert_db_retrieved_dict_match_db_stored_values(
        self, retrieved_profile_message: dict, profile_message: ProfileMessage
    ):
        self.assertEqual(retrieved_profile_message["id"], profile_message.id)
        self.assertEqual(retrieved_profile_message["sender"], profile_message.sender_id)
        self.assertEqual(
            retrieved_profile_message["receiver"], profile_message.receiver_id
        )
        self.assertEqual(retrieved_profile_message["message"], profile_message.message)
        self.assertEqual(retrieved_profile_message["is_read"], profile_message.is_read)
        self.assertEqual(
            retrieved_profile_message["timestamp"],
            timezone.localtime(profile_message.timestamp).isoformat(),
        )
