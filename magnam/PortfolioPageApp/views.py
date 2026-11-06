import mimetypes

mimetypes.add_type("image/webp", ".webp")  # because webp is not native
from django.db.models import Q, Count
from .models import *
from rest_framework import generics, status
from .serializers import *
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser

from django.urls import reverse
from urllib.parse import urlencode
from utils.permission import PermissionCheck, has_permission
from utils.helper_functions import (
    get_qs_containing_all_tags,
    apply_registered_filters,
    get_page_comments_with_cursor,
)

from .globals import *


class PortfolioTagView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    queryset = PortfolioTag.objects.all()
    serializer_class = ReturnPortfolioTagSerializer


class PortfolioLikeView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = PortfolioLike.objects.all()
    serializer_class = ReturnPortfolioLikeSerializer


class PortfolioCommentView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = PortfolioComment.objects.all()
    serializer_class = ReturnPortfolioCommentSerializer


class PortfolioView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Portfolio.objects.all()
    serializer_class = ReturnPortfolioSerializer


class CreatePortfolioView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateEditPortfolioSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        portfolio = serializer.save(owner=request.user.profile)

        return Response({"data": {"id": portfolio.id}}, status=status.HTTP_201_CREATED)


class GetPortfolioView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnPortfolioSerializer

    def get(self, request, portfolio_id, format=None):
        portfolio = get_object_or_404(
            Portfolio.objects.annotate(
                num_of_likes=Count("likes", distinct=True),
                num_of_comments=Count("comments", distinct=True),
            ),
            id=portfolio_id,
        )

        data = self.serializer_class(portfolio, context={"request": request}).data

        # Like info
        data["num_of_likes"] = portfolio.num_of_likes

        data["is_user_liked"] = (
            has_permission(request.user, "logged_in")
            and PortfolioLike.objects.filter(
                portfolio=portfolio, profile=request.user.profile
            ).exists()
        )

        # Comments info
        data["num_of_comments"] = portfolio.num_of_comments

        return Response({"data": data}, status=status.HTTP_200_OK)


class EditPortfolioView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateEditPortfolioSerializer

    def patch(self, request, portfolio_id, format=None):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        self.check_object_permissions(request, portfolio)

        serializer = self.serializer_class(
            instance=portfolio, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        portfolio = serializer.save()

        return Response(status=status.HTTP_200_OK)


class DeletePortfolioView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, portfolio_id, format=None):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        self.check_object_permissions(request, portfolio)

        portfolio.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PortfolioGalleryPagination(PageNumberPagination):
    page_size = PORTFOLIO_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = PORTFOLIO_MAX_PAGE_SIZE


class PortfolioGalleryView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnPortfolioGallerySerializer
    pagination_class = PortfolioGalleryPagination

    def get_queryset(self):
        queryset = Portfolio.objects.annotate(
            num_of_likes=Count("likes", distinct=True),
            num_of_works=Count("works", distinct=True),
        )

        # PORTFOLIO TYPE TAGS
        queryset = get_qs_containing_all_tags(
            queryset, self.request.query_params.get("tags", "")
        )

        # SLIDER FILTERS
        registered_filters = [
            {
                "min_prefix": "num_of_likes_min",
                "max_prefix": "num_of_likes_max",
                "min_filter_kwarg": "num_of_likes__gte",
                "max_filter_kwarg": "num_of_likes__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_works_min",
                "max_prefix": "num_of_works_max",
                "min_filter_kwarg": "num_of_works__gte",
                "max_filter_kwarg": "num_of_works__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "date_min",
                "max_prefix": "date_max",
                "min_filter_kwarg": "date__gte",
                "max_filter_kwarg": "date__lte",
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
            "num_of_likes": "-num_of_likes",
            "-num_of_likes": "num_of_likes",
            "num_of_works": "-num_of_works",
            "-num_of_works": "num_of_works",
            "date": "-id",
            "-date": "id",
            # we are handling the profiles_following and -profiles_following sorts differently
        }

        ordering_fields = []
        # since guests can query sorts, we need to filter these two to handle guests' not having follow lists
        if has_permission(self.request.user, "logged_in"):
            profiles_following = self.request.user.profile.profiles_following.all()
        else:
            profiles_following = None

        for item in sort_param.split(","):
            item = item.strip()

            if profiles_following and item == "profiles_following":
                queryset = queryset.filter(owner__in=profiles_following)
            elif profiles_following and item == "-profiles_following":
                queryset = queryset.exclude(owner__in=profiles_following)
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
                headers={"X-Empty-Gallery": "No portfolio found"},
            )

        response = super().list(request, *args, **kwargs)

        if has_permission(request.user, "logged_in"):
            liked_portfolio_ids = set(
                PortfolioLike.objects.filter(
                    profile=request.user.profile, portfolio__in=queryset
                ).values_list("portfolio_id", flat=True)
            )
        else:
            liked_portfolio_ids = set()

        for portfolio_item in response.data["results"]:
            portfolio_item["is_user_liked"] = (
                portfolio_item["id"] in liked_portfolio_ids
            )

        return response


class TogglePortfolioLikeView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, portfolio_id):
        profile = request.user.profile
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)

        like, created = PortfolioLike.objects.get_or_create(
            portfolio=portfolio, profile=profile
        )

        if created:
            return Response({"data": {"liked": True}}, status=status.HTTP_200_OK)
        else:
            like.delete()
            return Response({"data": {"liked": False}}, status=status.HTTP_200_OK)


class CreatePortfolioCommentView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreatePortfolioCommentSerializer
    return_serializer_class = ReturnPortfolioCommentSerializer

    def post(self, request, portfolio_id):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        profile = request.user.profile

        serializer = self.serializer_class(
            data=request.data, context={"portfolio": portfolio, "profile": profile}
        )

        serializer.is_valid(raise_exception=True)
        created_comment = serializer.save()

        return_serializer = self.return_serializer_class(created_comment)
        return Response({"data": return_serializer.data}, status=status.HTTP_200_OK)


class GetPortfolioCommentsView(generics.ListAPIView):
    serializer_class = ReturnPortfolioCommentSerializer
    permission_classes = [PermissionCheck]
    permission_type = "guest"

    PAGE_SIZE = PORTFOLIO_COMMENTS_PAGE_SIZE

    def get_queryset(self):
        portfolio_id = self.kwargs["portfolio_id"]
        cursor = self.request.query_params.get("cursor")

        get_object_or_404(Portfolio, id=portfolio_id)

        base_qs = PortfolioComment.objects.filter(portfolio_id=portfolio_id)

        return get_page_comments_with_cursor(base_qs, cursor, self.PAGE_SIZE)

    def list(self, request, *args, **kwargs):
        portfolio_id = self.kwargs["portfolio_id"]
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Determine next cursor
        comment_ids = queryset.values_list("id", flat=True)

        next_cursor = min(comment_ids) if comment_ids else None

        if next_cursor:
            base_url = reverse(
                "PortfolioPageApp:get-portfolio-comments",
                kwargs={"portfolio_id": portfolio_id},
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


# === Work === # === Work === # === Work === # === Work === #


class WorkView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Work.objects.all()
    serializer_class = ReturnWorkSerializer


class CreateWorkView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = CreateWorkSerializer
    return_serializer_class = ReturnWorkSerializer

    def post(self, request, portfolio_id):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        self.check_object_permissions(request, portfolio)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        existing_count = portfolio.works.count()
        incoming_count = len(serializer.validated_data["work_files"])

        if existing_count + incoming_count >= MAX_WORK_COUNT_PER_PORTFOLIO:
            raise serializers.ValidationError(
                {
                    "limit": (
                        f"A portfolio can contain at most {MAX_WORK_COUNT_PER_PORTFOLIO} works. \
                          It already has {existing_count} + {incoming_count} more being upladed."
                    )
                }
            )

        title = serializer.validated_data.get("title", "")
        files = serializer.validated_data["work_files"]

        # we need to do the file checks here because:
        # we still want to create the work for valid ones and skip fault ones
        successes = []
        errors = []

        for index, file in enumerate(files):
            try:
                mime_type, _ = mimetypes.guess_type(file.name)
                ext = file.name.lower()

                if mime_type == "application/pdf" or ext.endswith(".pdf"):
                    pdf_check(
                        file,
                        max_file_size=WORK_PDF_MAX_SIZE,
                        max_pages=WORK_PDF_MAX_PAGE,
                    )

                elif mime_type and mime_type.startswith("image/"):
                    image_check(
                        file,
                        min_height=WORK_IMAGE_MIN_H,
                        min_width=WORK_IMAGE_MIN_W,
                        max_height=WORK_IMAGE_MAX_H,
                        max_width=WORK_IMAGE_MAX_W,
                        max_file_size=WORK_IMAGE_MAX_SIZE,
                    )

                elif mime_type and mime_type.startswith("video/"):
                    video_check(
                        file,
                        max_duration=WORK_VIDEO_MAX_DURATION,
                        max_file_size=WORK_VIDEO_MAX_SIZE,
                        min_width=WORK_VIDEO_MIN_W,
                        min_height=WORK_VIDEO_MIN_H,
                        max_width=WORK_VIDEO_MAX_W,
                        max_height=WORK_VIDEO_MAX_H,
                    )

                elif mime_type and mime_type.startswith("audio/"):
                    audio_check(
                        file,
                        max_duration=WORK_AUDIO_MAX_DURATION,
                        max_file_size=WORK_AUDIO_MAX_SIZE,
                    )

                else:
                    raise serializers.ValidationError("Unsupported file type.")

                work = Work(portfolio=portfolio, title=title, work_file=file)

                work.save()
                successes.append(work)

            except Exception as e:
                errors.append({"index": index, "filename": file.name, "error": str(e)})

        # Serialize only successfully created works
        success_data = self.return_serializer_class(
            successes, many=True, context={"request": request}
        ).data
        return Response(
            {"data": {"works": success_data, "status": errors}},
            status=(
                status.HTTP_201_CREATED if successes else status.HTTP_400_BAD_REQUEST
            ),
        )


class DeleteWorkView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, work_id, format=None):
        work = get_object_or_404(Work, id=work_id)
        self.check_object_permissions(request, work.portfolio)

        work.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
