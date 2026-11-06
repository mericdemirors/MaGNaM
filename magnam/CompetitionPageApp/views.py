from .models import *
from rest_framework import generics, status
from .serializers import *
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.db.transaction import atomic

from MangaPageApp.models import Chapter
from PortfolioPageApp.models import Portfolio

from utils.permission import PermissionCheck, has_permission
from utils.helper_functions import get_qs_containing_all_tags, apply_registered_filters
from .globals import *
import logging

tx_logger = logging.getLogger("in_app_transactions")


class CompetitionTagView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    queryset = CompetitionTag.objects.all()
    serializer_class = ReturnCompetitionTagSerializer


class CompetitionView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = Competition.objects.all()
    serializer_class = ReturnCompetitionSerializer


class CreateCompetitionView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    serializer_class = CreateEditCompetitionSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        competition = serializer.save()

        return Response(
            {"data": {"id": competition.id}}, status=status.HTTP_201_CREATED
        )


class GetCompetitionView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnCompetitionSerializer

    def get(self, request, competition_id, format=None):
        competition = get_object_or_404(
            Competition.objects.annotate(
                num_of_chapter_submits=Count("chapter_submits", distinct=True),
                num_of_portfolio_submits=Count("portfolio_submits", distinct=True),
            ),
            id=competition_id,
        )

        data = self.serializer_class(competition, context={"request": request}).data

        data["num_of_chapter_submits"] = competition.num_of_chapter_submits
        data["num_of_portfolio_submits"] = competition.num_of_portfolio_submits

        # defaults when user is not authenticated
        data["user_submitted_item"] = ""
        data["profile_balance"] = -1

        if has_permission(request.user, "logged_in"):
            user_profile = request.user.profile

            # this should return a list with only single item
            user_owned_submitted_chapters = Chapter.objects.filter(
                owner=user_profile,
                id__in=competition.chapter_submits.all().values_list("id", flat=True),
            ).values_list("id", flat=True)
            if user_owned_submitted_chapters:
                data["user_submitted_item"] = (
                    f"chapter_{user_owned_submitted_chapters[0]}"
                )
            else:
                # this should return a list with only single item
                user_owned_submitted_portfolios = Portfolio.objects.filter(
                    owner=user_profile,
                    id__in=competition.portfolio_submits.all().values_list(
                        "id", flat=True
                    ),
                ).values_list("id", flat=True)
                if user_owned_submitted_portfolios:
                    data["user_submitted_item"] = (
                        f"portfolio_{user_owned_submitted_portfolios[0]}"
                    )

            data["profile_balance"] = user_profile.wallet

        return Response({"data": data}, status=status.HTTP_200_OK)


class EditCompetitionView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    serializer_class = CreateEditCompetitionSerializer

    def patch(self, request, competition_id, format=None):
        competition = get_object_or_404(Competition, id=competition_id)

        serializer = self.serializer_class(
            instance=competition, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        competition = serializer.save()

        return Response(status=status.HTTP_200_OK)


class DeleteCompetitionView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"

    def delete(self, request, competition_id, format=None):
        competition = get_object_or_404(Competition, id=competition_id)
        competition.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompetitionGalleryPagination(PageNumberPagination):
    page_size = COMPETITION_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = COMPETITION_MAX_PAGE_SIZE


class CompetitionGalleryView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnCompetitionGallerySerializer
    pagination_class = CompetitionGalleryPagination

    def get_queryset(self):
        queryset = Competition.objects.annotate(
            num_of_chapter_submits=Count("chapter_submits", distinct=True),
            num_of_portfolio_submits=Count("portfolio_submits", distinct=True),
        )

        # COMPETITION TYPE TAGS
        queryset = get_qs_containing_all_tags(
            queryset, self.request.query_params.get("tags", "")
        )

        registered_filters = [
            {
                "min_prefix": "num_of_portfolio_submits_min",
                "max_prefix": "num_of_portfolio_submits_max",
                "min_filter_kwarg": "num_of_portfolio_submits__gte",
                "max_filter_kwarg": "num_of_portfolio_submits__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "num_of_chapter_submits_min",
                "max_prefix": "num_of_chapter_submits_max",
                "min_filter_kwarg": "num_of_chapter_submits__gte",
                "max_filter_kwarg": "num_of_chapter_submits__lte",
                "filter_type": "int",
            },
            {
                "min_prefix": "price_min",
                "max_prefix": "price_max",
                "min_filter_kwarg": "price__gte",
                "max_filter_kwarg": "price__lte",
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
                "min_prefix": "end_date_min",
                "max_prefix": "end_date_max",
                "min_filter_kwarg": "end_date__gte",
                "max_filter_kwarg": "end_date__lte",
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
            "price": "-price",
            "-price": "price",
            "num_of_portfolio_submits": "-num_of_portfolio_submits",
            "-num_of_portfolio_submits": "num_of_portfolio_submits",
            "num_of_chapter_submits": "-num_of_chapter_submits",
            "-num_of_chapter_submits": "num_of_chapter_submits",
            "start_date": "-start_date",
            "-start_date": "start_date",
            "end_date": "-end_date",
            "-end_date": "end_date",
        }

        ordering_fields = []
        # since guests can query sorts, we need to filter these two to handle guests' not having follow lists
        for item in sort_param.split(","):
            item = item.strip()
            if item in mapping:
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
                headers={"X-Empty-Gallery": "No competition found"},
            )

        return super().list(request, *args, **kwargs)


class SubmitCompetitionItemView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    chapter_serializer = ReturnCompetitionChapterSerializer
    portfolio_serializer = ReturnCompetitionPortfolioSerializer

    def post(self, request, competition_id, item_string, format=None):
        user_profile = request.user.profile

        competition = get_object_or_404(Competition, id=competition_id)

        if timezone.now().date() > competition.end_date:
            return Response(
                {
                    "error": {
                        "submission": "Submission period has ended for this competition"
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now().date() < competition.start_date:
            return Response(
                {"error": {"submission": "This competition has not started yet"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:  # item_string is something like "chapter_6" or "portfolio_1"
            item_type, item_id = item_string.split("_")
            item_id = int(item_id)
        except:
            return Response(
                {"error": {"submission": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_type == "chapter":
            Model = Chapter
            submitted_item_serializer = self.chapter_serializer
            submit_field = competition.chapter_submits
        elif item_type == "portfolio":
            Model = Portfolio
            submitted_item_serializer = self.portfolio_serializer
            submit_field = competition.portfolio_submits
        else:
            return Response(
                {"error": {"submission": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(Model, id=item_id)  # get the item to submit
        self.check_object_permissions(
            request, item
        )  # check if request sender is the owner

        # we need to remove previous submission if any
        # first check if user submitted a chapter previously
        item_to_remove = Chapter.objects.filter(
            id__in=competition.chapter_submits.values_list("id", flat=True),
            owner=user_profile,
        ).first()
        removed_item_serializer = self.chapter_serializer
        submit_field_to_remove = competition.chapter_submits
        win_field = competition.chapter_wins
        removed_item_type = "chapter" if item_to_remove else None

        # if not, check if user submitted a portfolio previously
        if item_to_remove is None:
            item_to_remove = Portfolio.objects.filter(
                id__in=competition.portfolio_submits.values_list("id", flat=True),
                owner=user_profile,
            ).first()
            if item_to_remove:
                removed_item_serializer = self.portfolio_serializer
                submit_field_to_remove = competition.portfolio_submits
                win_field = competition.portfolio_wins
                removed_item_type = "portfolio"

        # if no previous submission is found, pay full price else half
        if item_to_remove is None:
            price = competition.price
        elif item_to_remove == item:
            return Response(
                {"error": {"submission": f"{item_string} is already submitted"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            price = competition.price // 2

        if has_permission(request.user, "admin"):
            price = 0

        if user_profile.wallet < price:
            return Response(
                {"error": {"submission": "Not enough money"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        balance_before = user_profile.wallet
        removed_item_id = item_to_remove.id if item_to_remove else None

        with atomic():
            if item_to_remove:
                if item_to_remove in win_field.all():
                    win_field.remove(item_to_remove)
                submit_field_to_remove.remove(item_to_remove)

            submit_field.add(item)
            new_balance = user_profile.wallet = user_profile.wallet - price
            user_profile.save()

        tx_logger.info(
            f"competition_submission user_id {user_profile.id} competition_id {competition.id} item_type {item_type} item_id {item.id} removed_item_type {removed_item_type} removed_item_id {removed_item_id} price {price} balance_before {balance_before} balance_after {new_balance} had_previous_submission {item_to_remove is not None}"
        )

        submitted_data = submitted_item_serializer(
            item, context={"request": request}
        ).data
        removed_data = (
            removed_item_serializer(item_to_remove, context={"request": request}).data
            if item_to_remove
            else False
        )

        return Response(
            {
                "data": {
                    "submitted": submitted_data,
                    "removed": removed_data,
                    "profile_balance": new_balance,
                }
            },
            status=status.HTTP_200_OK,
        )


class SubmitCompetitionWinnerView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    chapter_serializer = ReturnCompetitionChapterSerializer
    portfolio_serializer = ReturnCompetitionPortfolioSerializer

    def post(self, request, competition_id, item_string, format=None):
        competition = get_object_or_404(Competition, id=competition_id)

        try:  # item_string is something like "chapter_6" or "portfolio_1"
            item_type, item_id = item_string.split("_")
            item_id = int(item_id)
        except:
            return Response(
                {"error": {"winner": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_type == "chapter":
            Model = Chapter
            winner_item_serializer = self.chapter_serializer
            submit_field = competition.chapter_submits
            win_field = competition.chapter_wins
        elif item_type == "portfolio":
            Model = Portfolio
            winner_item_serializer = self.portfolio_serializer
            submit_field = competition.portfolio_submits
            win_field = competition.portfolio_wins
        else:
            return Response(
                {"error": {"winner": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(Model, id=item_id)

        if item not in submit_field.all():
            return Response(
                {"error": {"winner": f"Item not submitted: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        win_field.add(item)

        winner_data = winner_item_serializer(item, context={"request": request}).data

        return Response({"data": {"winner": winner_data}}, status=status.HTTP_200_OK)


class SubmitCompetitionLoserView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    chapter_serializer = ReturnCompetitionChapterSerializer
    portfolio_serializer = ReturnCompetitionPortfolioSerializer

    def post(self, request, competition_id, item_string, format=None):
        competition = get_object_or_404(Competition, id=competition_id)

        try:  # item_string is something like "chapter_6" or "portfolio_1"
            item_type, item_id = item_string.split("_")
            item_id = int(item_id)
        except:
            return Response(
                {"error": {"loser": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if item_type == "chapter":
            Model = Chapter
            loser_item_serializer = self.chapter_serializer
            win_field = competition.chapter_wins
        elif item_type == "portfolio":
            Model = Portfolio
            loser_item_serializer = self.portfolio_serializer
            win_field = competition.portfolio_wins
        else:
            return Response(
                {"error": {"loser": f"Invalid item format: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = get_object_or_404(Model, id=item_id)

        if item not in win_field.all():
            return Response(
                {"error": {"loser": f"Item not a winner: {item_string}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        win_field.remove(item)

        loser_data = loser_item_serializer(item, context={"request": request}).data

        return Response({"data": {"loser": loser_data}}, status=status.HTTP_200_OK)
