from pathlib import PurePosixPath
import uuid

from .models import Profile
from rest_framework import generics, status
from .serializers import *
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.pagination import CursorPagination
from rest_framework.exceptions import PermissionDenied
from utils.permission import is_user_admin, PermissionCheck, is_user_admin
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# === For register/login/logout === #
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from google_auth.utils import verify_google_id_token
from utils.helper_functions import send_verification_email, send_security_reset_email
from .random_profile_name_util import generate_random_profile_name


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # This just sets the CSRF cookie on the client.
        return Response(status=status.HTTP_200_OK)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data["email"].strip()
        password = request.data["password"].strip()

        if not (PROFILE_MIN_PASSWORD_LEN <= len(password) <= PROFILE_MAX_PASSWORD_LEN):
            return Response(
                {
                    "error": {
                        "password": f"Password not valid, needs to be at least {PROFILE_MIN_PASSWORD_LEN} and at most {PROFILE_MAX_PASSWORD_LEN} characters"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "@" not in email or (
            not (PROFILE_MIN_EMAIL_LEN <= len(email) <= PROFILE_MAX_EMAIL_LEN)
        ):
            return Response(
                {
                    "error": {
                        "email": f"Email not valid, must contain @ and needs to be at least {PROFILE_MIN_EMAIL_LEN} and at most {PROFILE_MAX_EMAIL_LEN} characters"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": {"email": "Email already in use"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        while True:
            username = generate_random_profile_name()
            if not Profile.objects.filter(profile_name=username).exists():
                break

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        send_verification_email(user_email=email, token=user.profile.verification_token)
        login(request, user)
        return Response(status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data["identifier"].strip()
        password = request.data["password"].strip()

        try:  # Try to find by email first, then username
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                return Response(
                    {"error": {"login": "User doesn't exist"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        user = authenticate(request, username=user.username, password=password)

        if user is None:
            return Response(
                {"error": {"password": "Wrong (identified, password) combination"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        return Response({"data": "Logged in successfully"}, status=status.HTTP_200_OK)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response(
                {"error": "Missing token"}, status=status.HTTP_400_BAD_REQUEST
            )

        payload = verify_google_id_token(token)
        if not payload:
            return Response(
                {"error": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        email = payload.get("email")

        if not email:
            return Response(
                {"error": "Google account has no email"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_verified = payload.get("email_verified", False)
        user_exists = User.objects.filter(email=email).exists()
        # ---------------------
        # REGISTER
        # ---------------------
        if not user_exists:
            while True:
                username = generate_random_profile_name()
                if not Profile.objects.filter(profile_name=username).exists():
                    break

            password = uuid.uuid4().hex

            user = User.objects.create_user(
                username=username, email=email, password=password
            )

            profile = user.profile
            profile.auth_provider = "google"

            if email_verified:
                _ = profile.mark_verified()
            else:
                _, new_token = profile.mark_unverified()
                send_verification_email(user.email, new_token)

            profile.save()

        # ---------------------
        # LOGIN
        # ---------------------
        else:
            user = User.objects.get(email=email)
            profile = user.profile
            profile_update_fields = []

            if profile.auth_provider != "google":
                profile.auth_provider = "google"
                profile_update_fields = ["auth_provider"]

            # Imitation protection
            if not profile.is_verified:
                new_password = uuid.uuid4().hex
                user.set_password(new_password)
                user.save()
                send_security_reset_email(user.email)

            if email_verified:
                update_fields = profile.mark_verified()
                profile_update_fields = profile_update_fields + update_fields

            if profile_update_fields:
                profile.save(update_fields=profile_update_fields)

        login(request, user)
        return Response(status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnProfileSerializer

    def get(self, request):
        profile = request.user.profile
        profile_data = self.serializer_class(profile, context={"request": request}).data

        # All blocked profile IDs (both directions)
        blocked_ids = Profile.objects.filter(
            Q(id__in=profile.profiles_blocked.values_list("id", flat=True))
            | Q(id__in=profile.blocked_by.values_list("id", flat=True))
        ).values_list("id", flat=True)

        # Count unread messages excluding those from blocked IDs
        unread_messages_count = (
            ProfileMessage.objects.filter(receiver=profile, is_read=False)
            .exclude(sender_id__in=blocked_ids)
            .count()
        )

        return Response(
            {
                "data": {
                    "profile": profile_data,
                    "is_admin": is_user_admin(request.user),
                    "is_verified": profile.is_verified,
                    "unread_messages": unread_messages_count,
                }
            },
            status=status.HTTP_200_OK,
        )


class VerifyView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, token, format=None):
        if not token:
            return Response(
                {"error": {"token": "Verification token is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.profile

        if profile.is_verified:
            return Response(
                {"data": "Profile is already verified"}, status=status.HTTP_200_OK
            )

        if not profile.verification_token:
            return Response(
                {"error": {"token": "Profile has no verification token"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile.verification_token != token:
            return Response(
                {"error": {"token": "Invalid verification token"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = profile.mark_verified()
        profile.save(update_fields=update_fields)

        return Response(
            {"data": "Profile successfully verified"}, status=status.HTTP_200_OK
        )


class ResetVerificationView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def patch(self, request):
        profile = request.user.profile

        update_fields, new_token = profile.mark_unverified()
        profile.save(update_fields=update_fields)

        send_verification_email(user_email=profile.user.email, token=new_token)

        return Response(
            {"data": "New verification token mailed"}, status=status.HTTP_200_OK
        )


# === For register/login/logout === #


class ProfileView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Profile.objects.all()
    serializer_class = ReturnProfileSerializer


class GetSymmetricFollowedProfilesView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnFollowedProfileSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        # return the profiles we are following which also follows us back
        return profile.profiles_following.filter(profiles_following=profile)


class GetMessagingProfilesView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnMessagingProfileSerializer

    def get_queryset(self):
        source_profile = self.request.user.profile

        # blocked profile ids
        blocked_profiles = Profile.objects.filter(
            Q(id__in=source_profile.profiles_blocked.values_list("id", flat=True))
            | Q(id__in=source_profile.blocked_by.values_list("id", flat=True))
        )

        # profiles with messages
        messaging_profiles = (
            Profile.objects.filter(
                Q(messages_received__sender=source_profile)
                | Q(messages_sent__receiver=source_profile)
            )
            .exclude(id=source_profile.id)
            .exclude(id__in=blocked_profiles)
            .annotate(
                sent_messages=Count(
                    "messages_received",
                    filter=Q(messages_received__sender=source_profile),
                    distinct=True,
                ),
                unread_messages=Count(
                    "messages_sent",
                    filter=Q(
                        messages_sent__receiver=source_profile,
                        messages_sent__is_read=False,
                    ),
                    distinct=True,
                ),
            )
            .order_by("-sent_messages", "-id")
            .distinct()
        )

        # followings
        followed_profiles = source_profile.profiles_following.exclude(
            id__in=messaging_profiles.values_list("id", flat=True)
        ).exclude(id__in=blocked_profiles)

        return list(messaging_profiles) + list(followed_profiles)


class ProfileMessageView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = ProfileMessage.objects.all()
    serializer_class = ReturnProfileMessageSerializer


class GetOwnedChaptersAndPortfoliosView(generics.GenericAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    chapter_serializer_class = ReturnChapterReferenceSerializer
    portfolio_serializer_class = ReturnPortfolioReferenceSerializer

    def get(self, request, *args, **kwargs):
        profile = request.user.profile

        chapters = profile.chapters_owned.all()
        portfolios = profile.portfolios.all()

        serialized_chapters = self.chapter_serializer_class(
            chapters, many=True, context={"request": request}
        ).data
        serialized_portfolios = self.portfolio_serializer_class(
            portfolios, many=True, context={"request": request}
        ).data

        return Response(
            {
                "data": {
                    "chapters": serialized_chapters,
                    "portfolios": serialized_portfolios,
                }
            },
            status=status.HTTP_200_OK,
        )


class GetProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = (
        "logged_in"  # logged in users should be able to query every other user
    )

    def choose_returning_serializer(self, request, profile):
        try:  # if request if from owner of the profile, return the full fields
            self.check_object_permissions(request, profile)
            return ReturnProfileSerializer
        except (
            PermissionDenied
        ):  # if request is from non-owner profile, return only some of the fields
            return ReturnNonOwnerProfileSerializer

    def get(self, request, profile_id, format=None):
        profile = request.user.profile
        target_profile = get_object_or_404(Profile, id=profile_id)

        # cant view the profile if requested not admin and blocked
        if profile in target_profile.profiles_blocked.all() and not is_user_admin(
            request.user
        ):
            return Response(
                {"error": {"blocked": "You are blocked by the user."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer_class = self.choose_returning_serializer(request, target_profile)
        data = serializer_class(target_profile, context={"request": request}).data

        data["is_user_following"] = target_profile in profile.profiles_following.all()
        data["is_user_blocked"] = target_profile in profile.profiles_blocked.all()

        return Response({"data": data}, status=status.HTTP_200_OK)


class GetTextSearchProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnProfileReferenceSerializer
    search_set_size = PROFILE_SEARCH_SET_SIZE

    def get(self, request, search_text, format=None):
        if not search_text:
            return Response({"data": []}, status=status.HTTP_200_OK)

        base_queryset = Profile.objects.all()

        search_results_list = []
        found_ids = set()
        try:
            profile_id = int(search_text)
            if profile_id > 0:
                id_match_profile = base_queryset.filter(id=profile_id).first()
                if id_match_profile:
                    search_results_list.append(id_match_profile)
                    found_ids.add(id_match_profile.id)
        except ValueError:
            pass

        starts_with_results = list(
            base_queryset.filter(profile_name__istartswith=search_text)
            .exclude(id__in=found_ids)
            .order_by("id")[: self.search_set_size]
        )

        search_results_list.extend(starts_with_results)
        found_ids.update(profile.id for profile in starts_with_results)

        contains_results = list(
            base_queryset.filter(profile_name__icontains=search_text)
            .exclude(id__in=found_ids)
            .order_by("id")[: self.search_set_size]
        )

        search_results_list.extend(contains_results)

        if not search_results_list:
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                headers={"X-Empty-Search": "No profile found"},
            )

        serializer = self.serializer_class(
            search_results_list, many=True, context={"request": request}
        )

        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


class EditProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = EditProfileSerializer

    def patch(self, request, profile_id, format=None):
        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        profile = get_object_or_404(Profile, id=profile_id)
        self.check_object_permissions(request, profile)

        valid_data = serializer.validated_data
        user = profile.user
        profile_update_fields = []
        user_update_fields = []

        new_name = valid_data.get("profile_name")
        if new_name:
            profile.profile_name = new_name
            profile_update_fields.append("profile_name")
            user.username = new_name
            user_update_fields.append("username")

        new_image = valid_data.get("image")
        if new_image:
            new_image.name = f"{uuid.uuid4().hex}{PurePosixPath(new_image.name).suffix}"
            profile.image.delete(save=False)
            profile.image = new_image
            profile_update_fields.append("image")

        new_email = valid_data.get("email")
        if new_email:
            user.email = new_email
            user_update_fields.append("email")

            update_fields, new_token = profile.mark_unverified()
            profile_update_fields = profile_update_fields + update_fields
            send_verification_email(user_email=new_email, token=new_token)

        new_password = valid_data.get("password")
        if new_password:
            user.set_password(new_password)
            user_update_fields.append("password")

        if profile_update_fields:
            profile.save(update_fields=profile_update_fields)
        if user_update_fields:
            user.save(update_fields=user_update_fields)
            if new_password:
                update_session_auth_hash(request, user)

        return Response(status=status.HTTP_200_OK)


class DeleteProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, profile_id, format=None):
        profile = get_object_or_404(Profile, id=profile_id)
        self.check_object_permissions(request, profile)

        # logout only if user is deleting it's own profile (no logout if admin deleting a profile)
        logout_after_deletion = request.user.profile == profile

        profile.user.delete()  # deleting user cascade deletes the profile

        return Response(
            {"data": {"logout_after_deletion": logout_after_deletion}},
            status=status.HTTP_200_OK,
        )


class ToggleFollowProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, profile_id, format=None):
        profile = request.user.profile
        target_profile = get_object_or_404(Profile, id=profile_id)

        if profile == target_profile:
            return Response(
                {"error": {"follow": "You cannot follow yourself."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile in target_profile.profiles_blocked.all():
            return Response(
                {"error": {"follow": "You cannot follow someone blocked you"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_profile in profile.profiles_blocked.all():
            return Response(
                {"error": {"follow": "You cannot follow someone you blocked."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_profile in profile.profiles_following.all():
            profile.profiles_following.remove(target_profile)
        else:
            profile.profiles_following.add(target_profile)

        return Response(status=status.HTTP_200_OK)


class ToggleBlockProfileView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, profile_id, format=None):
        profile = request.user.profile
        target_profile = get_object_or_404(Profile, id=profile_id)

        if profile == target_profile:
            return Response(
                {"error": {"block": "You cannot block yourself."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_blocked = target_profile in profile.profiles_blocked.all()
        target_followed = target_profile in profile.profiles_following.all()
        target_following = profile in target_profile.profiles_following.all()

        if target_blocked:  # if target was blocked
            profile.profiles_blocked.remove(target_profile)  # remove the block
        else:  # if it's not blocked yet
            if target_followed:  # if it was followed
                profile.profiles_following.remove(
                    target_profile
                )  # remove the outgoing follow
            if target_following:  # if target was following the source
                target_profile.profiles_following.remove(
                    profile
                )  # remove the incoming follow
            profile.profiles_blocked.add(target_profile)  # block it

        return Response(status=status.HTTP_200_OK)


class CreateProfileMessageView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateProfileMessageSerializer
    return_serializer_class = ReturnProfileMessageSerializer

    def post(self, request, profile_id):
        sender = request.user.profile
        receiver = get_object_or_404(Profile, id=profile_id)

        serializer = self.serializer_class(
            data=request.data, context={"sender": sender, "receiver": receiver}
        )

        serializer.is_valid(raise_exception=True)
        created_message = serializer.save()

        return_serializer = self.return_serializer_class(created_message)
        return Response({"data": return_serializer.data}, status=status.HTTP_200_OK)


class ProfileMessageCursorPagination(CursorPagination):
    page_size = PROFILE_MESSAGE_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = PROFILE_MESSAGE_MAX_PAGE_SIZE
    ordering = "-id"


class GetProfileMessageView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnProfileMessageSerializer
    pagination_class = ProfileMessageCursorPagination

    def get_queryset(self):
        user_profile = self.request.user.profile
        other_profile = self.get_other_profile()

        return ProfileMessage.objects.filter(
            Q(sender=user_profile, receiver=other_profile)
            | Q(sender=other_profile, receiver=user_profile)
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is None:
            page = queryset

        other_profile = self.get_other_profile()

        # Mark unread incoming messages as read
        ids_to_mark = [
            m.id for m in page if m.sender == other_profile and not m.is_read
        ]

        if ids_to_mark:
            ProfileMessage.objects.filter(id__in=ids_to_mark).update(is_read=True)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_other_profile(self):
        if not hasattr(self, "_other_profile"):
            self._other_profile = get_object_or_404(
                Profile, id=self.kwargs.get("profile_id")
            )
        return self._other_profile


class ReadProfileMessageView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, profile_id, last_message_id):
        sender = get_object_or_404(Profile, id=profile_id)
        receiver = request.user.profile

        unread_qs = ProfileMessage.objects.filter(
            sender=sender, receiver=receiver, is_read=False, id__lte=last_message_id
        )

        unread_qs.update(is_read=True)

        # Notify sender via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"profile_{profile_id}",
            {
                "type": "read_message",
                "read_data": {
                    "id": last_message_id,
                    "sender": sender.id,
                    "receiver": receiver.id,
                },
            },
        )

        return Response(status=status.HTTP_200_OK)
