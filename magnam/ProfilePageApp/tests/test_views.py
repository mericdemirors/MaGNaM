from datetime import timedelta
from django.utils import timezone

from unittest.mock import patch, MagicMock
from django.urls import reverse
from ..models import *
from .base_test import *

from MangaPageApp.tests.base_test import ChapterBaseTestCase
from PortfolioPageApp.tests.base_test import PortfolioBaseTestCase
from ProfilePageApp.cron import delete_expired_unverified_profiles


# CsrfTokenView
class TestCsrfTokenView(ProfileBaseTestCase):
    def test_guest_can_get_csrf_token(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:csrf")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)

    def test_logged_in_user_can_get_csrf_token(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:csrf")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)


# RegisterView
class TestRegisterView(ProfileBaseTestCase):
    def test_user_can_register(self):
        self.client.logout()

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        url = reverse(f"{self.namespace}:register")
        response = self.client.post(
            url,
            {
                "email": vals_to_send_request["email"],
                "password": vals_to_send_request["password"],
            },
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email=original_vals["email"])
        self.assertTrue(hasattr(user, "profile"))

    def test_register_logs_user_in(self):
        self.client.logout()

        _, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals=fast_creation_dict
        )

        url = reverse(f"{self.namespace}:register")
        response = self.client.post(
            url,
            {
                "email": vals_to_send_request["email"],
                "password": vals_to_send_request["password"],
            },
        )

        self.assertEqual(response.status_code, 201)
        # session should be active after register
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_creates_profile_correctly(self):
        self.client.logout()

        original_vals, vals_to_send_request, _ = self.get_random_valid_data(
            predefined_vals={**fast_creation_dict, "auth_provider": "local"}
        )

        url = reverse(f"{self.namespace}:register")
        response = self.client.post(
            url,
            {
                "email": vals_to_send_request["email"],
                "password": vals_to_send_request["password"],
            },
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email=original_vals["email"])
        self.assertTrue(hasattr(user, "profile"))

        profile = user.profile
        self.assert_db_stored_values_match_expected_dict(profile, original_vals)

    def test_invalid_register_values(self):
        self.client.logout()

        self.url = reverse(f"{self.namespace}:register")

        def test_invalid_register_field(field, invalid_value):
            _, vals_to_send_request, _ = self.get_random_valid_data(
                predefined_vals=fast_creation_dict
            )
            vals_to_send_request[field] = invalid_value
            response = self.client.post(
                self.url, vals_to_send_request, format="multipart"
            )
            self.assertEqual(response.status_code, 400)

        # short password
        test_invalid_register_field(
            "password", self.get_random_password_value(L=PROFILE_MIN_PASSWORD_LEN - 1)
        )

        # long password
        test_invalid_register_field(
            "password", self.get_random_password_value(L=PROFILE_MAX_PASSWORD_LEN + 10)
        )

        # email with no @
        test_invalid_register_field("email", "mail_with_no_'at'_character")

        # short mail
        # we do it like this because mail min length is 1 and mail needs to have @
        # we cant create a mail that passes the test above and fails the min length
        test_invalid_register_field("email", "")

        # long password
        test_invalid_register_field(
            "email", self.get_random_email_value(L=PROFILE_MAX_EMAIL_LEN + 10)
        )

        # duplicate mail
        _, _, _, p = self.create_random_valid_object(predefined_vals=fast_creation_dict)
        test_invalid_register_field("email", p.user.email)


# LoginView
class TestLoginView(ProfileBaseTestCase):
    def test_user_can_login_with_email(self):
        self.client.logout()

        _, vals_to_send_request, _, p = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        url = reverse(f"{self.namespace}:login")
        response = self.client.post(
            url,
            {
                "identifier": vals_to_send_request["email"],
                "password": vals_to_send_request["password"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)

    def test_user_can_login_with_username(self):
        self.client.logout()

        _, vals_to_send_request, _, p = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        url = reverse(f"{self.namespace}:login")
        response = self.client.post(
            url,
            {
                "identifier": vals_to_send_request["profile_name"],
                "password": vals_to_send_request["password"],
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_login_with_wrong_data(self):
        self.client.logout()

        _, vals_to_send_request, _, p = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        url = reverse(f"{self.namespace}:login")

        # non existing mail
        response = self.client.post(
            url,
            {
                "identifier": self.get_random_email_value(),
                "password": vals_to_send_request["password"],
            },
        )
        self.assertEqual(response.status_code, 400)

        # non existing username
        response = self.client.post(
            url,
            {
                "identifier": self.get_random_profile_name_value(),
                "password": vals_to_send_request["password"],
            },
        )
        self.assertEqual(response.status_code, 400)

        # not matching password
        response = self.client.post(
            url,
            {
                "identifier": vals_to_send_request["profile_name"],
                "password": self.get_random_password_value(),
            },
        )
        self.assertEqual(response.status_code, 400)


# GoogleAuthView
@patch("ProfilePageApp.views.verify_google_id_token")
@patch("ProfilePageApp.views.send_verification_email")
@patch("ProfilePageApp.views.send_security_reset_email")
class TestGoogleAuthView(ProfileBaseTestCase):
    def get_url(self):
        return reverse(f"{self.namespace}:google-auth")

    def test_missing_id_token(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        response = self.client.post(self.get_url(), {}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Missing token")

    def test_invalid_google_payload(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        mock_verify_google_id_token.return_value = None

        response = self.client.post(
            self.get_url(), {"id_token": "invalid_token"}, format="json"
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "Invalid Google token")

    def test_google_account_without_email(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        mock_verify_google_id_token.return_value = {
            "email": None,
            "email_verified": True,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_token"}, format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Google account has no email")

    def test_google_register_with_verified_email(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        email = self.get_random_email_value()

        mock_verify_google_id_token.return_value = {
            "email": email,
            "email_verified": True,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=email)
        profile = user.profile

        # created checks
        self.assertEqual(profile.auth_provider, "google")

        # mark_verified checks
        self.assertTrue(profile.is_verified)
        self.assertIsNone(profile.verification_token)
        self.assertIsNone(profile.non_verified_since)

    def test_google_register_with_unverified_email(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        email = self.get_random_email_value()

        mock_verify_google_id_token.return_value = {
            "email": email,
            "email_verified": False,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )

        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=email)
        profile = user.profile

        # created checks
        self.assertEqual(
            profile.auth_provider, "local"
        )  # (email was not verified so auth provider stays as local)
        # mark_unverified checks
        self.assertFalse(profile.is_verified)
        self.assertIsNotNone(profile.verification_token)
        self.assertIsNotNone(profile.non_verified_since)

        # verification mail sent
        mock_send_verification_email.assert_called_once()
        args, kwargs = mock_send_verification_email.call_args
        self.assertEqual(args[0], email)
        self.assertEqual(args[1], profile.verification_token)

    def test_existing_user_switches_auth_provider_to_google(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={"auth_provider": "local"}
        )

        mock_verify_google_id_token.return_value = {
            "email": profile.user.email,
            "email_verified": False,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.auth_provider, "google")

    def test_imitation_protection_for_non_verified_profile(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        email = self.get_random_email_value()
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={
                "email": email,
                "is_verified": False,
                "auth_provider": "local",
            }
        )

        old_password_hash = profile.user.password
        mock_verify_google_id_token.return_value = {
            "email": email,
            "email_verified": False,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

        profile.user.refresh_from_db()
        # password changed
        self.assertNotEqual(profile.user.password, old_password_hash)
        # security email sent
        mock_send_security_reset_email.assert_called_once_with(email)

    def test_existing_user_mark_verified_when_google_email_verified(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        email = self.get_random_email_value()
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={"email": email, "is_verified": False}
        )

        mock_verify_google_id_token.return_value = {
            "email": email,
            "email_verified": True,
        }

        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()

        # mark_verified checks
        self.assertTrue(profile.is_verified)
        self.assertIsNone(profile.verification_token)
        self.assertIsNone(profile.non_verified_since)

    def test_google_login_logs_user_in(
        self,
        mock_send_security_reset_email,
        mock_send_verification_email,
        mock_verify_google_id_token,
    ):
        email = self.get_random_email_value()

        mock_verify_google_id_token.return_value = {
            "email": email,
            "email_verified": True,
        }
        response = self.client.post(
            self.get_url(), {"id_token": "valid_google_token"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)

        logged_user = User.objects.get(id=self.client.session["_auth_user_id"])
        self.assertEqual(logged_user.email, email)


# LogoutView
class TestLogoutView(ProfileBaseTestCase):
    def test_logged_in_user_can_logout(self):
        self.client.force_login(self.user)

        url = reverse(f"{self.namespace}:logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_guest_cannot_logout(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:logout")
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)


# MeView
class TestMeView(ProfileBaseTestCase):
    def test_me_returns_correct_profile(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"]["profile"], self.user.profile
        )
        self.assertEqual(
            response.data["data"]["is_verified"], self.user.profile.is_verified
        )

    def test_me_admin_flag(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_admin"])

        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_admin"])

    def test_me_unread_messages_count(self):
        self.client.force_authenticate(user=self.user)

        # create an unread message sent to self.user
        message_tester = ProfileMessageBaseTestCase()
        message_tester.create_random_valid_object(
            predefined_vals={"receiver": self.user.profile, "is_read": False}
        )

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["unread_messages"], 1)

    def test_me_unread_messages_excludes_blocked_senders(self):
        self.client.force_authenticate(user=self.user)

        blocked_profile = get_dummy_profile()

        message_tester = ProfileMessageBaseTestCase()
        message_tester.create_random_valid_object(
            predefined_vals={
                "sender": blocked_profile,
                "receiver": self.user.profile,
                "is_read": False,
            }
        )

        self.user.profile.profiles_blocked.add(blocked_profile)

        blocking_profile = get_dummy_profile()

        message_tester = ProfileMessageBaseTestCase()
        message_tester.create_random_valid_object(
            predefined_vals={
                "sender": blocking_profile,
                "receiver": self.user.profile,
                "is_read": False,
            }
        )

        blocking_profile.profiles_blocked.add(self.user.profile)

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["unread_messages"], 0)

    def test_guest_cannot_access_me(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# VerifyView
class TestVerifyView(ProfileBaseTestCase):
    def test_user_can_verify_with_correct_token(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={"is_verified": False, **fast_creation_dict}
        )

        self.client.force_authenticate(user=profile.user)

        url = reverse(
            f"{self.namespace}:verify", kwargs={"token": profile.verification_token}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertTrue(profile.is_verified)

        self.assertTrue(profile.is_verified)
        self.assertIsNone(profile.verification_token)
        self.assertIsNone(profile.non_verified_since)

    def test_already_verified_profile_returns_200(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={"is_verified": False, **fast_creation_dict}
        )

        self.client.force_authenticate(user=profile.user)

        # first verify
        url = reverse(
            f"{self.namespace}:verify", kwargs={"token": profile.verification_token}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        # then try to re-verify
        url = reverse(f"{self.namespace}:verify", kwargs={"token": "anytoken"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_token(self):
        profile = self.user.profile
        profile.mark_unverified()
        profile.save()

        self.client.force_authenticate(user=profile.user)

        url = reverse(f"{self.namespace}:verify", kwargs={"token": None})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        url = reverse(f"{self.namespace}:verify", kwargs={"token": " "})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        url = reverse(f"{self.namespace}:verify", kwargs={"token": "wrongtoken"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        profile.verification_token = None
        profile.save()
        url = reverse(f"{self.namespace}:verify", kwargs={"token": "wrongtoken"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_guest_cannot_verify(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:verify", kwargs={"token": "sometoken"})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)


# ResetVerificationView
class TestResetVerificationView(ProfileBaseTestCase):
    @patch("ProfilePageApp.views.send_verification_email")
    def test_user_can_reset_verification(self, mock_send_verification_email):
        self.client.force_authenticate(user=self.user)
        profile = self.user.profile

        url = reverse(f"{self.namespace}:reset-verification")
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()

        mock_send_verification_email.assert_called_once()
        self.assertFalse(profile.is_verified)
        self.assertIsNotNone(profile.verification_token)
        self.assertIsNotNone(profile.non_verified_since)
        self.assertEqual(profile.auth_provider, "local")

    @patch("ProfilePageApp.views.send_verification_email")
    def test_multiple_reset_verification(self, mock_send_verification_email):
        self.client.force_authenticate(user=self.user)
        profile = self.user.profile

        url = reverse(f"{self.namespace}:reset-verification")
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()

        mock_send_verification_email.assert_called_once()
        self.assertFalse(profile.is_verified)
        old_token = profile.verification_token
        self.assertIsNotNone(profile.verification_token)
        old_time = profile.non_verified_since
        self.assertIsNotNone(profile.non_verified_since)
        self.assertEqual(profile.auth_provider, "local")

        # user resetting it again should reset the token but not the date
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()

        self.assertEqual(mock_send_verification_email.call_count, 2)
        self.assertNotEqual(old_token, profile.verification_token)
        self.assertEqual(old_time, profile.non_verified_since)

    def test_guest_cannot_reset_verification(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:reset-verification")
        response = self.client.patch(url)

        self.assertEqual(response.status_code, 403)


# ProfileView
class TestRetrieveProfileView(ProfileBaseTestCase):
    def test_admin_can_retrieve_profiles(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, p1 = self.create_random_valid_object()
        _, _, _, p2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        # we need to do this because we create multiple other profiles during the testing
        # and we need to select the ones we need among them
        p1_result = [r for r in results if r["id"] == p1.id][0]
        p2_result = [r for r in results if r["id"] == p2.id][0]
        self.assert_db_retrieved_dict_match_db_stored_values(p1_result, p1)
        self.assert_db_retrieved_dict_match_db_stored_values(p2_result, p2)

    def test_logged_in_user_cannot_retrieve_profiles(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# GetSymmetricFollowedProfilesView
class TestGetSymmetricFollowedProfilesView(ProfileBaseTestCase):
    def test_returns_only_mutual_follows(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, profile_mutual = self.create_random_valid_object()
        _, _, _, profile_one_way1 = self.create_random_valid_object()
        _, _, _, profile_one_way2 = self.create_random_valid_object()

        self.user.profile.profiles_following.add(profile_mutual)
        profile_mutual.profiles_following.add(self.user.profile)

        self.user.profile.profiles_following.add(profile_one_way1)
        profile_one_way2.profiles_following.add(self.user.profile)

        url = reverse(f"{self.namespace}:profiles-following-symmetric")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        returned_ids = [p["id"] for p in response.data]
        self.assertIn(profile_mutual.id, returned_ids)
        self.assertNotIn(profile_one_way1.id, returned_ids)
        self.assertNotIn(profile_one_way2.id, returned_ids)

    def test_empty_result_when_no_mutual_follows(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:profiles-following-symmetric")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_guest_cannot_access_symmetric_follows(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:profiles-following-symmetric")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# GetMessagingProfilesView
class TestGetMessagingProfilesView(ProfileBaseTestCase):
    def test_returns_profiles_with_messages(self):
        self.client.force_authenticate(user=self.user)
        profile = self.user.profile

        _, _, _, sender_profile = self.create_random_valid_object()
        _, _, _, receiver_profile = self.create_random_valid_object()

        _, _, _, blocked_profile1 = self.create_random_valid_object()
        profile.profiles_blocked.add(blocked_profile1)
        _, _, _, blocked_profile2 = self.create_random_valid_object()
        blocked_profile2.profiles_blocked.add(profile)

        _, _, _, following_profile = self.create_random_valid_object()
        profile.profiles_following.add(following_profile)
        _, _, _, follower_profile = self.create_random_valid_object()
        follower_profile.profiles_following.add(profile)

        message_tester = ProfileMessageBaseTestCase()
        message_tester.create_random_valid_object(
            predefined_vals={"sender": profile, "receiver": receiver_profile}
        )
        message_tester = ProfileMessageBaseTestCase()
        message_tester.create_random_valid_object(
            predefined_vals={"sender": sender_profile, "receiver": profile}
        )

        url = reverse(f"{self.namespace}:profiles-messaging")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        returned_ids = [p["id"] for p in response.data]
        self.assertIn(receiver_profile.id, returned_ids)
        self.assertIn(sender_profile.id, returned_ids)
        self.assertNotIn(blocked_profile1.id, returned_ids)
        self.assertNotIn(blocked_profile2.id, returned_ids)
        self.assertIn(following_profile.id, returned_ids)
        self.assertNotIn(follower_profile.id, returned_ids)

    def test_guest_cannot_access_messaging_profiles(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:profiles-messaging")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# ProfileMessageView
class TestProfileMessageView(ProfileMessageBaseTestCase):
    def test_admin_can_retrieve_messages(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, m1 = self.create_random_valid_object()
        _, _, _, m2 = self.create_random_valid_object()

        url = reverse(f"{self.namespace}:profile-message")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        self.assertEqual(len(results), 2)
        self.assert_db_retrieved_dict_match_db_stored_values(results[1], m1)
        self.assert_db_retrieved_dict_match_db_stored_values(results[0], m2)

    def test_logged_in_user_cannot_retrieve_messages(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:profile-message")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# GetOwnedChaptersAndPortfoliosView
class TestGetOwnedChaptersAndPortfoliosView(ProfileBaseTestCase):
    def test_user_can_get_own_chapters_and_portfolios(self):
        self.client.force_authenticate(user=self.user)

        chapter_tester = ChapterBaseTestCase()
        portfolio_tester = PortfolioBaseTestCase()
        _, _, _, owned_chapter = chapter_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        _, _, _, collaborated_chapter = chapter_tester.create_random_valid_object(
            predefined_vals={"collaborators": [self.user.profile]}
        )
        _, _, _, other_chapter = chapter_tester.create_random_valid_object()
        _, _, _, owned_portfolio = portfolio_tester.create_random_valid_object(
            predefined_vals={"owner": self.user.profile}
        )
        _, _, _, other_portfolio = portfolio_tester.create_random_valid_object()

        url = reverse(f"{self.namespace}:owned-chapters-and-portfolios")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        returned_chapter_ids = [c["id"] for c in response.data["data"]["chapters"]]
        self.assertIn(owned_chapter.id, returned_chapter_ids)
        self.assertNotIn(collaborated_chapter.id, returned_chapter_ids)
        self.assertNotIn(other_chapter.id, returned_chapter_ids)

        returned_portfolio_ids = [c["id"] for c in response.data["data"]["portfolios"]]
        self.assertIn(owned_portfolio.id, returned_portfolio_ids)
        self.assertNotIn(other_portfolio.id, returned_portfolio_ids)

    def test_guest_cannot_access_owned_chapters_and_portfolios(self):
        self.client.logout()

        url = reverse(f"{self.namespace}:owned-chapters-and-portfolios")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# GetProfileView
class TestGetProfileView(ProfileBaseTestCase):
    def test_user_can_get_own_profile(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": self.user.profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values(
            response.data["data"], self.user.profile
        )

    def test_user_can_get_other_profile(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": other_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assert_db_retrieved_dict_match_db_stored_values_for_non_owner_profile(
            response.data["data"], other_profile
        )

    def test_response_includes_follow_and_block_flags(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, followed_profile = self.create_random_valid_object()
        _, _, _, blocked_profile = self.create_random_valid_object()
        self.user.profile.profiles_following.add(followed_profile)
        self.user.profile.profiles_blocked.add(blocked_profile)

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": followed_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["is_user_following"], True)
        self.assertEqual(response.data["data"]["is_user_blocked"], False)

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": blocked_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["is_user_following"], False)
        self.assertEqual(response.data["data"]["is_user_blocked"], True)

    def test_blocked_user_cannot_view_profile(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, blocker_profile = self.create_random_valid_object()
        # blocker_profile blocks self.user
        blocker_profile.profiles_blocked.add(self.user.profile)

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": blocker_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)

    def test_admin_can_view_profile_even_if_blocked(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, blocker_profile = self.create_random_valid_object()
        blocker_profile.profiles_blocked.add(self.admin.profile)

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": blocker_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_non_existing_profile_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:get-profile", kwargs={"profile_id": 0})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_access(self):
        self.client.logout()

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:get-profile", kwargs={"profile_id": other_profile.id}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# GetTextSearchProfileView
class TestGetTextSearchProfileView(ProfileBaseTestCase):
    def test_logged_in_user_can_search_profile(self):
        self.client.force_authenticate(user=self.user)
        _, _, _, profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:search-profile", kwargs={"search_text": str(profile.id)}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data

        # fields that are returned from the text search:
        # ("id", "profile_name", "image")
        retrieved_profile = results["data"][0]
        self.assertEqual(retrieved_profile["id"], profile.id)
        self.assertEqual(retrieved_profile["profile_name"], profile.profile_name)
        self.assertTrue(retrieved_profile["image"] != "")
        self.assertIn(str(profile.image), retrieved_profile["image"])

    def test_non_existing_profile_search(self):
        self.client.force_authenticate(user=self.user)
        # we use lots of zeros to guarantee that no profile matches with search because other profiles are created during testing
        url = reverse(
            f"{self.namespace}:search-profile",
            kwargs={"search_text": "00000000000000000000"},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 204)

    def test_search_profile_order(self):
        self.client.force_authenticate(user=self.user)
        _, _, _, profile1 = self.create_random_valid_object(
            predefined_vals={"profile_name": "567"}
        )  # first one because of ID match
        search_text = f"{profile1.id}"  # first look for ID match, then profile_name.starts_with then profile_name.contains
        _, _, _, profile2 = self.create_random_valid_object(
            predefined_vals={"profile_name": f"{profile1.id}234"}
        )  # second one because profile_name starts with 1
        _, _, _, profile3 = self.create_random_valid_object(
            predefined_vals={"profile_name": f"789{profile1.id}"}
        )  # third one because profile_name contains 1
        _, _, _, profile4 = self.create_random_valid_object(
            predefined_vals={"profile_name": "asd"}
        )  # shouldn't show up in the results

        url = reverse(
            f"{self.namespace}:search-profile", kwargs={"search_text": search_text}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        results = response.data
        ids = [m["id"] for m in results["data"]]
        self.assertIn(profile1.id, ids)
        self.assertIn(profile2.id, ids)
        self.assertIn(profile3.id, ids)
        self.assertNotIn(profile4.id, ids)

    def test_guest_cannot_search_profile(self):
        self.client.logout()
        _, _, _, profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:search-profile", kwargs={"search_text": str(profile.id)}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


# EditProfileView
class TestEditProfileView(ProfileBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = f"{self.namespace}:edit-profile"

    # we need a specialized version of this function because Profile edits sometime changes the profile.user too
    def update_and_assert_single_profile_field(
        self,
        profile,
        update_api_url,
        field_to_update,
        new_field_value,
        expected_response_code=200,
        field_assertion_function=None,
    ):
        response = self.client.patch(
            update_api_url, {field_to_update: new_field_value}, format="multipart"
        )

        self.assertEqual(response.status_code, expected_response_code)

        if field_assertion_function is not None:
            profile.refresh_from_db()
            profile.user.refresh_from_db()

            field_assertion_function(profile)

    def test_user_cannot_edit_another_profile(self):
        _, _, _, another_profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        self.client.force_authenticate(user=self.user)

        url = reverse(self.url, kwargs={"profile_id": another_profile.id})

        response = self.client.patch(
            url,
            {"profile_name": self.get_random_profile_name_value()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_all_profiles(self):
        _, _, _, target_profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )
        new_name = self.get_random_profile_name_value()

        self.client.force_authenticate(user=self.admin)

        url = reverse(self.url, kwargs={"profile_id": target_profile.id})
        response = self.client.patch(
            url, {"profile_name": new_name}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)

        target_profile.refresh_from_db()
        target_profile.user.refresh_from_db()

        self.assertEqual(target_profile.profile_name, new_name)
        self.assertEqual(target_profile.user.username, new_name)

    def test_owner_can_update_profile_name(self):
        profile = self.user.profile
        new_profile_name = self.get_random_profile_name_value()

        self.client.force_authenticate(user=profile.user)
        url = reverse(self.url, kwargs={"profile_id": profile.id})

        self.update_and_assert_single_profile_field(
            profile=profile,
            update_api_url=url,
            field_to_update="profile_name",
            new_field_value=new_profile_name,
            field_assertion_function=lambda updated_profile: (
                self.assertEqual(updated_profile.profile_name, new_profile_name),
                self.assertEqual(updated_profile.user.username, new_profile_name),
            ),
        )

    def test_owner_can_update_image(self):
        profile = self.user.profile
        old_image_path = profile.image.name
        new_image = self.get_random_image_value()

        self.client.force_authenticate(user=profile.user)
        url = reverse(self.url, kwargs={"profile_id": profile.id})

        self.update_and_assert_single_profile_field(
            profile=profile,
            update_api_url=url,
            field_to_update="image",
            new_field_value=new_image,
            field_assertion_function=lambda updated_profile: (
                self.assert_database_image(updated_profile),
                self.assertFalse(file_storage.exists(old_image_path)),
            ),
        )

    @patch("ProfilePageApp.views.send_verification_email")
    def test_owner_can_update_email_and_mark_unverified(
        self, mock_send_verification_email
    ):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals={
                "is_verified": True,
                "verification_token": None,
                "non_verified_since": None,
                "auth_provider": "google",
                **fast_creation_dict,
            }
        )
        new_email = self.get_random_email_value()

        self.client.force_authenticate(user=profile.user)
        url = reverse(self.url, kwargs={"profile_id": profile.id})

        response = self.client.patch(url, {"email": new_email}, format="multipart")
        self.assertEqual(response.status_code, 200)

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        # user email updated
        self.assertEqual(profile.user.email, new_email)

        # mark_unverified checks
        self.assertIsNotNone(profile.verification_token)
        self.assertFalse(profile.is_verified)
        self.assertIsNotNone(profile.non_verified_since)
        self.assertEqual(profile.auth_provider, "local")

        # send_verification_email called
        mock_send_verification_email.assert_called_once()
        _, kwargs = mock_send_verification_email.call_args
        self.assertEqual(kwargs["user_email"], new_email)
        self.assertEqual(kwargs["token"], profile.verification_token)

    def test_owner_can_update_password(self):
        profile = self.user.profile
        new_password = self.get_random_password_value()

        self.client.force_authenticate(user=profile.user)
        url = reverse(self.url, kwargs={"profile_id": profile.id})

        response = self.client.patch(
            url, {"password": new_password}, format="multipart"
        )
        self.assertEqual(response.status_code, 200)

        profile.user.refresh_from_db()
        self.assertTrue(profile.user.check_password(new_password))

    def test_guest_cannot_edit_profile(self):
        _, _, _, profile = self.create_random_valid_object(
            predefined_vals=fast_creation_dict
        )

        url = reverse(self.url, kwargs={"profile_id": profile.id})

        response = self.client.patch(
            url,
            {"profile_name": self.get_random_profile_name_value()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)

    def test_non_existing_profile_edit_returns_404(self):
        self.client.force_authenticate(user=self.admin)

        url = reverse(f"{self.namespace}:edit-profile", kwargs={"profile_id": 0})
        response = self.client.patch(url, {"profile_name": "test"})

        self.assertEqual(response.status_code, 404)


# DeleteProfileView
class TestDeleteProfileView(ProfileBaseTestCase):
    def test_owner_can_delete_own_profile(self):
        self.client.force_authenticate(user=self.user)

        profile_id = self.user.profile.id
        user_id = self.user.id

        url = reverse(
            f"{self.namespace}:delete-profile", kwargs={"profile_id": profile_id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["logout_after_deletion"])
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertFalse(Profile.objects.filter(id=profile_id).exists())

    def test_admin_can_delete_another_profile(self):
        self.client.force_authenticate(user=self.admin)

        _, _, _, target_profile = self.create_random_valid_object()
        target_user_id = target_profile.user.id
        target_profile_id = target_profile.id

        url = reverse(
            f"{self.namespace}:delete-profile", kwargs={"profile_id": target_profile_id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["logout_after_deletion"])
        self.assertFalse(User.objects.filter(id=target_user_id).exists())
        self.assertFalse(Profile.objects.filter(id=target_profile_id).exists())

    def test_non_owner_cannot_delete_profile(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:delete-profile", kwargs={"profile_id": other_profile.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Profile.objects.filter(id=other_profile.id).exists())

    def test_non_existing_profile_delete_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(f"{self.namespace}:delete-profile", kwargs={"profile_id": 0})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_delete_profile(self):
        self.client.logout()

        _, _, _, profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:delete-profile", kwargs={"profile_id": profile.id}
        )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)


# ToggleFollowProfileView
class TestToggleFollowProfileView(ProfileBaseTestCase):
    def test_user_can_follow_another_profile(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-follow-profile",
            kwargs={"profile_id": other_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(other_profile, self.user.profile.profiles_following.all())

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_profile, self.user.profile.profiles_following.all())

    def test_invalid_follows(self):
        self.client.force_authenticate(user=self.user)

        # cannot follow itself
        url = reverse(
            f"{self.namespace}:toggle-follow-profile",
            kwargs={"profile_id": self.user.profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_user_cannot_follow_blocked_profiles(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, blocker_profile = self.create_random_valid_object()
        blocker_profile.profiles_blocked.add(self.user.profile)

        _, _, _, blocked_profile = self.create_random_valid_object()
        self.user.profile.profiles_blocked.add(blocked_profile)

        url = reverse(
            f"{self.namespace}:toggle-follow-profile",
            kwargs={"profile_id": blocker_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        url = reverse(
            f"{self.namespace}:toggle-follow-profile",
            kwargs={"profile_id": blocked_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_non_existing_profile_follow_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:toggle-follow-profile", kwargs={"profile_id": 0}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_follow(self):
        self.client.logout()

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-follow-profile",
            kwargs={"profile_id": other_profile.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)


# ToggleBlockProfileView
class TestToggleBlockProfileView(ProfileBaseTestCase):
    def test_block_another_profile(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-block-profile",
            kwargs={"profile_id": other_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(other_profile, self.user.profile.profiles_blocked.all())

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_profile, self.user.profile.profiles_blocked.all())

    def test_blocking_removes_follow(self):
        self.client.force_authenticate(user=self.user)

        _, _, _, following_profile = self.create_random_valid_object()
        self.user.profile.profiles_following.add(following_profile)

        url = reverse(
            f"{self.namespace}:toggle-block-profile",
            kwargs={"profile_id": following_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(following_profile, self.user.profile.profiles_following.all())

        _, _, _, follower_profile = self.create_random_valid_object()
        follower_profile.profiles_following.add(self.user.profile)

        url = reverse(
            f"{self.namespace}:toggle-block-profile",
            kwargs={"profile_id": follower_profile.id},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        follower_profile.refresh_from_db()
        self.assertNotIn(self.user.profile, follower_profile.profiles_following.all())

    def test_user_cannot_block_self(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:toggle-block-profile",
            kwargs={"profile_id": self.user.profile.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

    def test_non_existing_profile_block_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:toggle-block-profile", kwargs={"profile_id": 0}
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_block(self):
        self.client.logout()

        _, _, _, other_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:toggle-block-profile",
            kwargs={"profile_id": other_profile.id},
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)


# CreateProfileMessageView
class TestCreateProfileMessageView(ProfileMessageBaseTestCase):
    def test_user_can_send_message(self):
        # is_read needs to be true to not fail the check since retrieving the message switches from False to True
        original_vals, vals_to_send, vals_to_create_from = self.get_random_valid_data(
            predefined_vals={"is_read": False}
        )

        self.client.force_authenticate(user=vals_to_create_from["sender"].user)

        url = reverse(
            f"{self.namespace}:create-profile-message",
            kwargs={"profile_id": vals_to_send["receiver"]},
        )
        response = self.client.post(url, vals_to_send)

        self.assertEqual(response.status_code, 200)
        message = ProfileMessage.objects.first()
        self.assert_db_stored_values_match_expected_dict(message, original_vals)

    def test_non_existing_receiver_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:create-profile-message", kwargs={"profile_id": 0}
        )
        response = self.client.post(url, {"message": "hello"})

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_send_message(self):
        self.client.logout()

        _, _, _, receiver_profile = self.create_random_valid_object()

        url = reverse(
            f"{self.namespace}:create-profile-message",
            kwargs={"profile_id": receiver_profile.id},
        )
        response = self.client.post(url, {"message": "hello"})

        self.assertEqual(response.status_code, 403)


# GetProfileMessageView
class TestGetProfileMessageView(ProfileMessageBaseTestCase):
    namespace = "ProfilePageApp"

    def create_message(self, sender, receiver, is_read=False, message="msg"):
        _, _, _, profile_message = self.create_random_valid_object(
            predefined_vals={
                "sender": sender,
                "receiver": receiver,
                "is_read": is_read,
                "message": message,
            }
        )

        return profile_message

    def test_only_fetched_incoming_messages_are_marked_as_read(self):
        sender = self.get_random_sender_value()
        receiver = self.get_random_receiver_value()

        sender.profiles_following.add(receiver)
        receiver.profiles_following.add(sender)

        # incoming unread -> should stay unread because out of reach
        incoming0 = self.create_message(
            sender=sender, receiver=receiver, is_read=False, message="incoming0"
        )

        # incoming unread -> should become read
        incoming1 = self.create_message(
            sender=sender, receiver=receiver, is_read=False, message="incoming1"
        )

        incoming2 = self.create_message(
            sender=sender, receiver=receiver, is_read=False, message="incoming2"
        )

        # outgoing unread -> should stay unread
        outgoing1 = self.create_message(
            sender=receiver, receiver=sender, is_read=False, message="outgoing1"
        )

        # already read incoming -> should remain read
        incoming_read = self.create_message(
            sender=sender, receiver=receiver, is_read=True, message="incoming_read"
        )

        self.client.force_authenticate(user=receiver.user)

        url = reverse(
            f"{self.namespace}:get-profile-messages", kwargs={"profile_id": sender.id}
        )

        response = self.client.get(url, {"page_size": 4})

        self.assertEqual(response.status_code, 200)

        incoming0.refresh_from_db()
        incoming1.refresh_from_db()
        incoming2.refresh_from_db()
        outgoing1.refresh_from_db()
        incoming_read.refresh_from_db()

        # incoming unread UNfetched -> should stay unread
        self.assertFalse(incoming0.is_read)

        # incoming unread fetched -> should become read
        self.assertTrue(incoming1.is_read)
        self.assertTrue(incoming2.is_read)

        # outgoing should not change
        self.assertFalse(outgoing1.is_read)

        # already read remains read
        self.assertTrue(incoming_read.is_read)

    def test_cursor_pagination(self):
        sender = self.get_random_sender_value()
        receiver = self.get_random_receiver_value()

        sender.profiles_following.add(receiver)
        receiver.profiles_following.add(sender)

        messages = []

        for i in range(6):
            msg = self.create_message(
                sender=sender if i % 2 == 0 else receiver,
                receiver=receiver if i % 2 == 0 else sender,
                is_read=False,
                message=f"message_{i}",
            )
            messages.append(msg)

        messages_sorted = sorted(messages, key=lambda x: x.id, reverse=True)

        self.client.force_authenticate(user=receiver.user)

        url = reverse(
            f"{self.namespace}:get-profile-messages", kwargs={"profile_id": sender.id}
        )

        # first cursor page
        response1 = self.client.get(url, {"page_size": 3})
        self.assertEqual(response1.status_code, 200)
        ids_page1 = [item["id"] for item in response1.data["results"]]
        expected_page1 = [m.id for m in messages_sorted[:3]]
        self.assertEqual(ids_page1, expected_page1)
        next_url = response1.data["next"]
        self.assertIsNotNone(next_url)

        # second cursor page
        response2 = self.client.get(next_url)
        self.assertEqual(response2.status_code, 200)
        ids_page2 = [item["id"] for item in response2.data["results"]]
        expected_page2 = [m.id for m in messages_sorted[3:6]]
        self.assertEqual(ids_page2, expected_page2)
        next_url = response2.data["next"]
        self.assertIsNone(next_url)

    def test_messages_are_ordered_by_descending_id(self):
        sender = self.get_random_sender_value()
        receiver = self.get_random_receiver_value()

        sender.profiles_following.add(receiver)
        receiver.profiles_following.add(sender)

        messages = []

        for i in range(5):
            msg = self.create_message(
                sender=sender, receiver=receiver, is_read=False, message=f"message_{i}"
            )
            messages.append(msg)

        expected_order = sorted([m.id for m in messages], reverse=True)
        self.client.force_authenticate(user=receiver.user)
        url = reverse(
            f"{self.namespace}:get-profile-messages", kwargs={"profile_id": sender.id}
        )

        response = self.client.get(url, {"page_size": 10})
        self.assertEqual(response.status_code, 200)

        returned_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(returned_ids, expected_order)

    def test_empty_message_queryset_returns_empty_results(self):
        sender = self.get_random_sender_value()
        receiver = self.get_random_receiver_value()

        self.client.force_authenticate(user=receiver.user)
        url = reverse(
            f"{self.namespace}:get-profile-messages", kwargs={"profile_id": sender.id}
        )
        response = self.client.get(url, {"page_size": 10})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertIsNone(response.data["next"])

    def test_logged_in_user_can_get_messages(self):
        _, _, _, profile_message = self.create_random_valid_object()
        self.client.force_authenticate(user=profile_message.receiver.user)
        url = reverse(
            f"{self.namespace}:get-profile-messages",
            kwargs={"profile_id": profile_message.sender.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_does_not_return_messages_from_other_conversations(self):
        self.client.force_authenticate(user=self.user)

        profile_a = self.get_random_receiver_value()
        profile_b = self.get_random_sender_value()

        profile_a.profiles_following.add(profile_b)
        profile_b.profiles_following.add(profile_a)

        _, _, _, msg_with_a = self.create_random_valid_object(
            predefined_vals={"sender": self.user.profile, "receiver": profile_a}
        )
        _, _, _, msg_between_others = self.create_random_valid_object(
            predefined_vals={"sender": profile_a, "receiver": profile_b}
        )

        url = reverse(
            f"{self.namespace}:get-profile-messages",
            kwargs={"profile_id": profile_a.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        returned_ids = [m["id"] for m in response.data["results"]]
        self.assertIn(msg_with_a.id, returned_ids)
        self.assertNotIn(msg_between_others.id, returned_ids)

    def test_guest_cannot_get_messages(self):
        _, _, _, profile_message = self.create_random_valid_object()

        self.client.logout()

        url = reverse(
            f"{self.namespace}:get-profile-messages",
            kwargs={"profile_id": profile_message.sender.id},
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_non_existing_profile_messages_returns_404(self):
        _, _, _, profile_message = self.create_random_valid_object()

        self.client.force_authenticate(user=profile_message.receiver.user)
        url = reverse(
            f"{self.namespace}:get-profile-messages", kwargs={"profile_id": 0}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ReadProfileMessageView
class TestReadProfileMessageView(ProfileMessageBaseTestCase):
    namespace = "ProfilePageApp"

    @patch("ProfilePageApp.views.async_to_sync")
    @patch("ProfilePageApp.views.get_channel_layer")
    def test_logged_in_user_can_mark_messages_as_read(
        self, mock_get_channel_layer, mock_async_to_sync
    ):
        _, _, _, profile_message = self.create_random_valid_object(
            predefined_vals={"is_read": False}
        )

        self.client.force_authenticate(user=profile_message.receiver.user)

        url = reverse(
            f"{self.namespace}:read-profile-messages",
            kwargs={
                "profile_id": profile_message.sender.id,
                "last_message_id": profile_message.id,
            },
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    @patch("ProfilePageApp.views.async_to_sync")
    @patch("ProfilePageApp.views.get_channel_layer")
    def test_only_unread_messages_before_or_equal_last_message_id_are_marked(
        self, mock_get_channel_layer, mock_async_to_sync
    ):
        sender = self.get_random_sender_value(seed=1)
        receiver = self.get_random_receiver_value(seed=2)

        sender.profiles_following.add(receiver)

        # should become read
        _, _, _, msg1 = self.create_random_valid_object(
            predefined_vals={
                "sender": sender,
                "receiver": receiver,
                "is_read": False,
                "message": "msg1",
            }
        )

        _, _, _, msg2 = self.create_random_valid_object(
            predefined_vals={
                "sender": sender,
                "receiver": receiver,
                "is_read": False,
                "message": "msg2",
            }
        )

        # should stay unread because id > last_message_id
        _, _, _, msg3 = self.create_random_valid_object(
            predefined_vals={
                "sender": sender,
                "receiver": receiver,
                "is_read": False,
                "message": "msg3",
            }
        )

        # should stay read because already read
        _, _, _, msg4 = self.create_random_valid_object(
            predefined_vals={
                "sender": sender,
                "receiver": receiver,
                "is_read": True,
                "message": "msg4",
            }
        )

        # should stay unread because its an ongoing message, not incoming
        _, _, _, msg5 = self.create_random_valid_object(
            predefined_vals={
                "sender": receiver,
                "receiver": sender,
                "is_read": False,
                "message": "msg5",
            }
        )

        self.client.force_authenticate(user=receiver.user)
        url = reverse(
            f"{self.namespace}:read-profile-messages",
            kwargs={"profile_id": sender.id, "last_message_id": msg2.id},
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        msg1.refresh_from_db()
        msg2.refresh_from_db()
        msg3.refresh_from_db()
        msg4.refresh_from_db()
        msg5.refresh_from_db()

        # <= last_message_id and unread => should become read
        self.assertTrue(msg1.is_read)
        self.assertTrue(msg2.is_read)

        # id > last_message_id => should remain unread
        self.assertFalse(msg3.is_read)

        # already read => should remain read
        self.assertTrue(msg4.is_read)

        # unread
        self.assertFalse(msg5.is_read)

    @patch("ProfilePageApp.views.async_to_sync")
    @patch("ProfilePageApp.views.get_channel_layer")
    def test_websocket_group_send_is_called(
        self, mock_get_channel_layer, mock_async_to_sync
    ):
        _, _, _, profile_message = self.create_random_valid_object(
            predefined_vals={"is_read": False}
        )

        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_group_send_callable = MagicMock()
        mock_async_to_sync.return_value = mock_group_send_callable

        self.client.force_authenticate(user=profile_message.receiver.user)

        url = reverse(
            f"{self.namespace}:read-profile-messages",
            kwargs={
                "profile_id": profile_message.sender.id,
                "last_message_id": profile_message.id,
            },
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        mock_async_to_sync.assert_called_once_with(mock_channel_layer.group_send)

        mock_group_send_callable.assert_called_once_with(
            f"profile_{profile_message.sender.id}",
            {
                "type": "read_message",
                "read_data": {
                    "id": profile_message.id,
                    "sender": profile_message.sender.id,
                    "receiver": profile_message.receiver.id,
                },
            },
        )

    def test_guest_cannot_mark_messages_as_read(self):
        _, _, _, profile_message = self.create_random_valid_object()
        self.client.logout()

        url = reverse(
            f"{self.namespace}:read-profile-messages",
            kwargs={
                "profile_id": profile_message.sender.id,
                "last_message_id": profile_message.id,
            },
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_non_existing_sender_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            f"{self.namespace}:read-profile-messages",
            kwargs={"profile_id": 0, "last_message_id": 1},
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# cron.delete_expired_unverified_profiles
class TestDeleteExpiredUnverifiedProfiles(ProfileBaseTestCase):
    @patch("ProfilePageApp.cron.send_cron_account_deletion_email")
    @patch("ProfilePageApp.cron.logger")
    def test_cron_deletes_only_old_unverified_profiles(
        self, mock_logger, mock_send_email
    ):

        cutoff_time = timezone.now() - timedelta(
            days=NON_VERIFIED_PROFILE_DELETION_COUNTDOWN_DAYS + 1
        )

        # OLD UNVERIFIED (should be deleted)
        _, _, _, old_unverified = self.create_random_valid_object(
            predefined_vals={
                "is_verified": False,
                "non_verified_since": cutoff_time,
                **fast_creation_dict,
            }
        )

        # Cache the expected email BEFORE deletion
        expected_deleted_email = old_unverified.user.email

        # OLD VERIFIED (should NOT be deleted)
        _, _, _, old_verified = self.create_random_valid_object(
            predefined_vals={"is_verified": True, **fast_creation_dict}
        )

        # NEW UNVERIFIED (should NOT be deleted)
        _, _, _, new_unverified = self.create_random_valid_object(
            predefined_vals={
                "is_verified": False,
                "non_verified_since": timezone.now(),
                **fast_creation_dict,
            }
        )

        # NEW VERIFIED (should NOT be deleted)
        _, _, _, new_verified = self.create_random_valid_object(
            predefined_vals={"is_verified": True, **fast_creation_dict}
        )

        # Run cron
        delete_expired_unverified_profiles()

        # Refresh / check existence
        self.assertFalse(Profile.objects.filter(id=old_unverified.id).exists())
        self.assertTrue(Profile.objects.filter(id=old_verified.id).exists())
        self.assertTrue(Profile.objects.filter(id=new_unverified.id).exists())
        self.assertTrue(Profile.objects.filter(id=new_verified.id).exists())

        # Check if logger was called
        mock_logger.info.assert_called()

        # Check if email was sent exactly once for the deleted user
        mock_send_email.assert_called_once_with(expected_deleted_email)
