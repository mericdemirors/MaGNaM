from django.utils import timezone

from django.db.models import Q, Avg, Count, Sum, Value, OuterRef, Subquery, FloatField
from django.db.models.functions import Coalesce
from .models import *
from rest_framework import generics, status
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.transaction import atomic

from django.urls import reverse
from urllib.parse import urlencode
from utils.permission import PermissionCheck, has_permission
from utils.helper_functions import (
    get_qs_containing_all_tags,
    apply_registered_filters,
    get_page_comments_with_cursor,
)

from .globals import *
import logging

tx_logger = logging.getLogger("in_app_transactions")


class MangaTagView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    queryset = MangaTag.objects.all()
    serializer_class = ReturnMangaTagSerializer


class MangaRatingView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = MangaRating.objects.all()
    serializer_class = ReturnMangaRatingSerializer


class MangaCommentView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = MangaComment.objects.all()
    serializer_class = ReturnMangaCommentSerializer


class MangaView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Manga.objects.all()
    serializer_class = ReturnMangaSerializer


class CreateMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateEditMangaSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request, "owner": request.user.profile},
        )
        serializer.is_valid(raise_exception=True)

        manga = serializer.save(owner=request.user.profile)

        request.user.profile.mangas_following.add(manga)
        request.user.profile.mangas_owned.add(manga)

        return Response({"data": {"id": manga.id}}, status=status.HTTP_201_CREATED)


def get_rating_histogram(manga):
    qs = MangaRating.objects.filter(manga=manga)

    histogram = {}

    for low, high, label in MANGA_RATING_BINS:
        if label == "[-10,10]":
            q = Q(score__gte=low, score__lte=high)
        elif label.startswith("["):
            q = Q(score__gte=low, score__lt=high)
        else:
            q = Q(score__gt=low, score__lte=high)

        histogram[label] = qs.filter(q).count()

    return histogram


class GetMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnMangaSerializer

    def get(self, request, manga_id, format=None):
        chapter_sum_subquery = (
            Chapter.objects.filter(manga=OuterRef("id"))
            .values("manga")
            .annotate(total=Sum("price"))
            .values("total")
        )

        manga = get_object_or_404(
            Manga.objects.annotate(
                rating=Avg("ratings__score"),
                num_of_ratings=Count("ratings", distinct=True),
                num_of_comments=Count("comments", distinct=True),
                num_of_followers=Count("followers__id", distinct=True),
                # Use Coalesce to handle cases with 0 chapters
                total_price_of_all_chapters=Coalesce(
                    Subquery(chapter_sum_subquery), Value(0)
                ),
            ),
            id=manga_id,
        )

        logged_in_permission = has_permission(request.user, "logged_in")

        data = self.serializer_class(manga, context={"request": request}).data

        # Rating info
        data["rating"] = round((manga.rating or 0), 3)
        data["num_of_ratings"] = manga.num_of_ratings
        data["rating_histogram"] = get_rating_histogram(manga)

        if logged_in_permission:
            user_rating = MangaRating.objects.filter(
                manga=manga, profile=request.user.profile
            ).values("score")
        else:
            user_rating = None
        data["is_user_rated"] = (
            logged_in_permission
            and user_rating.exists()
            and user_rating.first().get("score", False)
        )

        # Comments info
        data["num_of_comments"] = manga.num_of_comments

        # Chapters info
        data["total_price_of_all_chapters"] = manga.total_price_of_all_chapters

        # Follow info
        data["num_of_followers"] = manga.num_of_followers
        data["is_user_following"] = (
            logged_in_permission
            and manga.followers.filter(id=request.user.profile.id).exists()
        )

        data["profile_balance"] = (
            request.user.profile.wallet if logged_in_permission else -1
        )

        return Response({"data": data}, status=status.HTTP_200_OK)


class GetTextSearchMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnTextSearchMangaSerializer
    search_set_size = MANGA_SEARCH_SET_SIZE

    def get(self, request, search_text, format=None):
        if not search_text:
            return Response({"data": []}, status=status.HTTP_200_OK)

        ratings_avg = (
            MangaRating.objects.filter(manga=OuterRef("id"))
            .values("manga")
            .annotate(avg=Avg("score"))
            .values("avg")
        )

        base_queryset = Manga.objects.annotate(
            rating=Coalesce(
                Subquery(ratings_avg, output_field=FloatField()), Value(0.0)
            ),
            num_of_chapters=Count("chapters", distinct=True),
        )

        search_results_list = []
        found_ids = set()
        try:
            manga_id = int(search_text)
            if manga_id > 0:
                id_match_manga = base_queryset.filter(id=manga_id).first()
                if id_match_manga:
                    search_results_list.append(id_match_manga)
                    found_ids.add(id_match_manga.id)
        except ValueError:
            pass

        starts_with_results = list(
            base_queryset.filter(title__istartswith=search_text)
            .exclude(id__in=found_ids)
            .order_by("-rating")[: self.search_set_size]
        )

        search_results_list.extend(starts_with_results)
        found_ids.update(manga.id for manga in starts_with_results)

        contains_results = list(
            base_queryset.filter(title__icontains=search_text)
            .exclude(id__in=found_ids)
            .order_by("-rating")[: self.search_set_size]
        )

        search_results_list.extend(contains_results)

        if not search_results_list:
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                headers={"X-Empty-Search": "No manga found"},
            )

        serializer = self.serializer_class(
            search_results_list, many=True, context={"request": request}
        )

        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


class ReadMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = ReturnReadMangaSerializer

    def get(self, request, manga_id, format=None):
        manga = get_object_or_404(Manga, id=manga_id)

        data = self.serializer_class(manga, context={"request": request}).data

        return Response({"data": data}, status=status.HTTP_200_OK)


class EditMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateEditMangaSerializer

    def patch(self, request, manga_id, format=None):
        manga = get_object_or_404(Manga, id=manga_id)
        self.check_object_permissions(request, manga)

        serializer = self.serializer_class(
            instance=manga,
            data=request.data,
            partial=True,
            context={"owner": manga.owner},
        )
        serializer.is_valid(raise_exception=True)
        manga = serializer.save()

        return Response(status=status.HTTP_200_OK)


class DeleteMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, manga_id, format=None):
        manga = get_object_or_404(Manga, id=manga_id)
        self.check_object_permissions(request, manga)

        manga.image.delete(save=False)
        manga.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class MangaGalleryPagination(PageNumberPagination):
    page_size = MANGA_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = MANGA_MAX_PAGE_SIZE


class MangaGalleryView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnMangaGallerySerializer
    pagination_class = MangaGalleryPagination

    def get_queryset(self):
        # 1. Define Subqueries to isolate the calculations
        chapters_subquery = Chapter.objects.filter(manga=OuterRef("id")).values("manga")
        ratings_subquery = MangaRating.objects.filter(manga=OuterRef("id")).values(
            "manga"
        )

        queryset = Manga.objects.annotate(
            # Correct Sum using Subquery
            total_price_of_all_chapters=Coalesce(
                Subquery(
                    chapters_subquery.annotate(total=Sum("price")).values("total")
                ),
                Value(0),
            ),
            # Correct Average using Subquery
            rating=Coalesce(
                Subquery(
                    ratings_subquery.annotate(avg=Avg("score")).values("avg"),
                    output_field=FloatField(),
                ),
                Value(0.0),
            ),
            # Counts are fine with distinct=True
            num_of_ratings=Count("ratings", distinct=True),
            num_of_chapters=Count("chapters", distinct=True),
            num_of_collaborators=Count("collaborators", distinct=True),
            num_of_followers=Count("followers", distinct=True),
        )

        # MANGA TYPE TAGS
        queryset = get_qs_containing_all_tags(
            queryset, self.request.query_params.get("tags", "")
        )

        # SLIDER FILTERS
        registered_filters = [
            {
                "min_prefix": "rating_min",
                "max_prefix": "rating_max",
                "min_filter_kwarg": "rating__gte",
                "max_filter_kwarg": "rating__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_ratings_min",
                "max_prefix": "num_of_ratings_max",
                "min_filter_kwarg": "num_of_ratings__gte",
                "max_filter_kwarg": "num_of_ratings__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_chapters_min",
                "max_prefix": "num_of_chapters_max",
                "min_filter_kwarg": "num_of_chapters__gte",
                "max_filter_kwarg": "num_of_chapters__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "chapters_price_min",
                "max_prefix": "chapters_price_max",
                "min_filter_kwarg": "total_price_of_all_chapters__gte",
                "max_filter_kwarg": "total_price_of_all_chapters__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_collaborators_min",
                "max_prefix": "num_of_collaborators_max",
                "min_filter_kwarg": "num_of_collaborators__gte",
                "max_filter_kwarg": "num_of_collaborators__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_followers_min",
                "max_prefix": "num_of_followers_max",
                "min_filter_kwarg": "num_of_followers__gte",
                "max_filter_kwarg": "num_of_followers__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "start_date_min",
                "max_prefix": "start_date_max",
                "min_filter_kwarg": "start_date__gte",
                "max_filter_kwarg": "start_date__lte",
                "filter_type": "date",
            },
            {
                "min_prefix": "last_update_date_min",
                "max_prefix": "last_update_date_max",
                "min_filter_kwarg": "last_update_date__gte",
                "max_filter_kwarg": "last_update_date__lte",
                "filter_type": "date",
            },
        ]

        # apply all numeric & date filters in a single filter call
        queryset = apply_registered_filters(
            self.request.query_params, queryset, registered_filters
        )

        # SORTING SELECTIONS
        sort_param = self.request.query_params.get("sort", "")
        if sort_param == "":
            return queryset.order_by("?")

        mapping = {  # how to apply sortings on the table
            "rating": "-rating",
            "-rating": "rating",
            "num_of_ratings": "-num_of_ratings",
            "-num_of_ratings": "num_of_ratings",
            "num_of_chapters": "-num_of_chapters",
            "-num_of_chapters": "num_of_chapters",
            "chapters_price": "-total_price_of_all_chapters",
            "-chapters_price": "total_price_of_all_chapters",
            "num_of_collaborators": "-num_of_collaborators",
            "-num_of_collaborators": "num_of_collaborators",
            "num_of_followers": "-num_of_followers",
            "-num_of_followers": "num_of_followers",
            "start_date": "-id",
            "-start_date": "id",
            "last_update_date": "-last_update_date",
            "-last_update_date": "last_update_date",
            # we are handling the following and -following sorts differently
        }

        ordering_fields = []
        # since guests can query sorts, we need to filter these two to handle guests' not having follow lists
        if has_permission(self.request.user, "logged_in"):
            profiles_following = self.request.user.profile.profiles_following.all()
            mangas_following = self.request.user.profile.mangas_following.all()
        else:
            profiles_following = None
            mangas_following = None

        for item in sort_param.split(","):
            item = item.strip()

            if profiles_following and item == "profiles_following":
                queryset = queryset.filter(
                    Q(owner__in=profiles_following)
                    | Q(collaborators__in=profiles_following)
                )
            elif profiles_following and item == "-profiles_following":
                queryset = queryset.exclude(
                    Q(owner__in=profiles_following)
                    | Q(collaborators__in=profiles_following)
                )
            elif mangas_following and item == "mangas_following":
                queryset = queryset.filter(id__in=mangas_following)
            elif mangas_following and item == "-mangas_following":
                queryset = queryset.exclude(id__in=mangas_following)

            elif item in mapping:
                ordering_fields.append(mapping[item])

        if ordering_fields:
            queryset = queryset.order_by(*ordering_fields)
        else:
            queryset = queryset.order_by("?")

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                status=status.HTTP_204_NO_CONTENT,
                headers={"X-Empty-Gallery": "No manga found"},
            )

        response = super().list(request, *args, **kwargs)

        if has_permission(request.user, "logged_in"):
            rated_mangas = MangaRating.objects.filter(
                profile=request.user.profile, manga__in=queryset
            ).values("manga_id", "score")
            rated_manga_ids_to_scores = {
                m["manga_id"]: m["score"] for m in rated_mangas
            }
            following_ids = set(
                request.user.profile.mangas_following.filter(
                    id__in=queryset
                ).values_list("id", flat=True)
            )
        else:
            rated_manga_ids_to_scores = {}
            following_ids = set()

        for manga_item in response.data["results"]:
            manga_id = manga_item["id"]
            manga_item["user_score"] = rated_manga_ids_to_scores.get(manga_id, False)
            manga_item["is_user_following"] = manga_id in following_ids

        return response


class ToggleFollowMangaView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, manga_id, format=None):
        profile = request.user.profile

        target_manga = get_object_or_404(Manga, id=manga_id)

        if target_manga in profile.mangas_following.all():
            profile.mangas_following.remove(target_manga)
            return Response({"data": {"followed": False}}, status=status.HTTP_200_OK)
        else:
            profile.mangas_following.add(target_manga)
            return Response({"data": {"followed": True}}, status=status.HTTP_200_OK)


class ChangeMangaScoreView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, manga_id):
        profile = request.user.profile
        manga = get_object_or_404(Manga, id=manga_id)

        score = request.data.get("score")
        try:
            score = int(score)
            if not (MANGA_MIN_RATING <= score <= MANGA_MAX_RATING):
                return Response(
                    {
                        "error": {
                            "manga_rating": f"Score must be a number between {MANGA_MIN_RATING} and {MANGA_MAX_RATING}"
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (
            ValueError,
            AssertionError,
        ):  # catches both None and out of range score errors
            return Response(
                {
                    "error": {
                        "manga_rating": f"Score must be a number between {MANGA_MIN_RATING} and {MANGA_MAX_RATING}"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        rating, created = MangaRating.objects.get_or_create(
            manga=manga, profile=profile
        )
        rating.score = score
        rating.save()

        return Response({"data": {"score": rating.score}}, status=status.HTTP_200_OK)

    def delete(self, request, manga_id):
        profile = request.user.profile
        manga = get_object_or_404(Manga, id=manga_id)
        rating = get_object_or_404(MangaRating, manga=manga, profile=profile)
        rating.delete()

        return Response({"data": {"rated": False}}, status=status.HTTP_200_OK)


class CreateMangaCommentView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateMangaCommentSerializer
    return_serializer_class = ReturnMangaCommentSerializer

    def post(self, request, manga_id):
        manga = get_object_or_404(Manga, id=manga_id)
        profile = request.user.profile

        serializer = self.serializer_class(
            data=request.data, context={"manga": manga, "profile": profile}
        )

        serializer.is_valid(raise_exception=True)
        created_comment = serializer.save()

        return_serializer = self.return_serializer_class(created_comment)
        return Response({"data": return_serializer.data}, status=status.HTTP_200_OK)


class GetMangaCommentsView(generics.ListAPIView):
    serializer_class = ReturnMangaCommentSerializer
    permission_classes = [PermissionCheck]
    permission_type = "guest"

    PAGE_SIZE = MANGA_COMMENTS_PAGE_SIZE

    def get_queryset(self):
        manga_id = self.kwargs["manga_id"]
        cursor = self.request.query_params.get("cursor")

        get_object_or_404(Manga, id=manga_id)

        base_qs = MangaComment.objects.filter(manga_id=manga_id)

        return get_page_comments_with_cursor(base_qs, cursor, self.PAGE_SIZE)

    def list(self, request, *args, **kwargs):
        manga_id = self.kwargs["manga_id"]
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)

        # Determine next cursor
        parent_ids = queryset.values_list("id", flat=True)

        next_cursor = min(parent_ids) if parent_ids else None

        if next_cursor:
            base_url = reverse(
                "MangaPageApp:get-manga-comments", kwargs={"manga_id": manga_id}
            )

            # urlencode handles the query string safely: ?cursor=...
            query_string = urlencode({"cursor": next_cursor})

            next_url = f"{base_url}?{query_string}"
        else:
            next_url = None

        return Response(
            {"data": {"results": serializer.data, "next": next_url}},
            status=status.HTTP_200_OK,
        )


# === Chapter === # === Chapter === # === Chapter === # === Chapter === #


class ChapterView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Chapter.objects.all()
    serializer_class = ReturnChapterSerializer


class CreateChapterView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = CreateEditChapterSerializer

    def post(self, request, manga_id):
        manga = get_object_or_404(Manga, id=manga_id)
        self.check_object_permissions(
            request, [manga.owner] + list(manga.collaborators.all())
        )

        serializer = self.serializer_class(
            data=request.data, context={"manga": manga, "owner": request.user.profile}
        )
        serializer.is_valid(raise_exception=True)
        created_chapter = serializer.save()

        BoughtChapter.objects.create(
            profile=request.user.profile, chapter=created_chapter, paid_price=0
        )
        request.user.profile.chapters_owned.add(created_chapter)

        for collaborator in serializer.validated_data.get("collaborators", []):
            BoughtChapter.objects.create(
                profile=collaborator, chapter=created_chapter, paid_price=0
            )
            collaborator.chapters_collaborated.add(created_chapter)

        # if manga owner is not the creator or in the collaborators of the manga, he needs to have the chapter
        # we use get_or_create to not create the same BoughtChapter if manga owner was chapter owner or in collaborators
        _ = BoughtChapter.objects.get_or_create(
            profile=manga.owner, chapter=created_chapter, paid_price=0
        )

        return Response(status=status.HTTP_201_CREATED)


class EditChapterView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateEditChapterSerializer

    def patch(self, request, chapter_id, format=None):
        chapter = get_object_or_404(Chapter, id=chapter_id)
        self.check_object_permissions(request, [chapter.manga.owner, chapter.owner])

        serializer = self.serializer_class(
            instance=chapter,
            data=request.data,
            partial=True,
            context={"manga": chapter.manga, "owner": chapter.owner},
        )
        serializer.is_valid(raise_exception=True)
        chapter = serializer.save()

        return Response(status=status.HTTP_200_OK)


class DeleteChapterView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, chapter_id, format=None):
        chapter = get_object_or_404(Chapter, id=chapter_id)
        self.check_object_permissions(request, [chapter.manga.owner, chapter.owner])

        chapter.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class BuyChapterView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, chapter_id):
        profile = request.user.profile

        chapter = get_object_or_404(Chapter, id=chapter_id)
        chapter_owner_profile = get_object_or_404(Profile, id=chapter.owner.id)

        if profile.id == chapter_owner_profile.id:
            return Response(
                {"error": {"chapter_buy": "Can't buy owned chapter"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if BoughtChapter.objects.filter(profile=profile, chapter=chapter).exists():
            return Response(
                {"error": {"chapter_buy": "Chapter already bought"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        price = 0 if has_permission(request.user, "admin") else chapter.price

        if profile.wallet < price:
            return Response(
                {"error": {"chapter_buy": "Not enough money"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pdf = build_chapter_pdf_url(chapter, request)
        pages_base_url = build_chapter_pages_base_url(chapter, request)

        price_before_buyer = profile.wallet
        price_before_owner = chapter_owner_profile.wallet

        with atomic():
            new_balance = profile.wallet = profile.wallet - price
            profile.save()
            BoughtChapter.objects.create(
                profile=profile, chapter=chapter, paid_price=price
            )
            chapter_owner_profile.wallet = chapter_owner_profile.wallet + price
            chapter_owner_profile.save()

            new_owner_balance = chapter_owner_profile.wallet

        tx_logger.info(
            f"chapter_purchase buyer_id: {profile.id} buyer_before: {price_before_buyer} buyer_after: {new_balance} seller_id: {chapter_owner_profile.id} seller_before: {price_before_owner} seller_after: {new_owner_balance} chapter_id: {chapter.id} price: {price}"
        )

        return Response(
            {
                "data": {
                    "pdf": pdf,
                    "folder_name": chapter.folder_name,
                    "pages_base_url": pages_base_url,
                    "profile_balance": new_balance,
                }
            },
            status=status.HTTP_200_OK,
        )


class MarkReadChapterView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, chapter_id):
        profile = request.user.profile
        chapter = get_object_or_404(Chapter, id=chapter_id)

        # user has to own the chapter to read
        has_bought = BoughtChapter.objects.filter(
            profile=profile, chapter=chapter
        ).exists()

        if not has_bought:
            return Response(
                {
                    "error": {
                        "read_chapter": "You must buy this chapter before reading it."
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # get_or_create prevents errors if the frontend accidentally fires the request twice
        _, created = ReadChapter.objects.get_or_create(profile=profile, chapter=chapter)

        # Return 201 Created if it's new, or 200 OK if it already existed
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response({"data": {"is_read": True}}, status=response_status)


class PutMangaBookmarkView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, manga_id, chapter_id):
        profile = request.user.profile

        manga = get_object_or_404(Manga, id=manga_id)
        chapter = get_object_or_404(Chapter, id=chapter_id, manga=manga)

        # user has to own the chapter to read
        has_bought = BoughtChapter.objects.filter(
            profile=profile, chapter=chapter
        ).exists()

        if not has_bought:
            return Response(
                {
                    "error": {
                        "read_chapter": "You must buy this chapter before reading it."
                    }
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        page = request.data.get("page")

        try:
            page = int(page)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Invalid page number."}, status=status.HTTP_400_BAD_REQUEST
            )

        if page < 0:
            return Response(
                {"detail": "Page must be positive."}, status=status.HTTP_400_BAD_REQUEST
            )

        # we allow 'chapter.num_of_images' to be bookmarked because enabling cover pages adds +1 to page indices
        if page > chapter.num_of_images:
            return Response(
                {"detail": (f"Page must be smaller than " f"{chapter.num_of_images}.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        MangaBookmark.objects.update_or_create(
            manga=manga, profile=profile, defaults={"chapter": chapter, "page": page}
        )

        return Response({"success": True}, status=status.HTTP_200_OK)
