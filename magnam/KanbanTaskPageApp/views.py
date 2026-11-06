from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from .models import *
from rest_framework import generics, status
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from utils.permission import PermissionCheck
from utils.helper_functions import get_qs_containing_all_tags, apply_registered_filters

from .globals import *


class KanbanTagView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    queryset = KanbanTaskTag.objects.all()
    serializer_class = ReturnKanbanTaskTagSerializer


class KanbanVoteView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = KanbanTaskVote.objects.all()
    serializer_class = ReturnKanbanTaskVoteSerializer


class KanbanTaskView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "admin"
    queryset = KanbanTask.objects.all()
    serializer_class = ReturnKanbanTaskSerializer


class CreateKanbanTaskView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"
    serializer_class = CreateKanbanTaskSerializer
    return_serializer_class = ReturnKanbanTaskSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_task = serializer.save(creator=request.user.profile)

        data = self.return_serializer_class(
            created_task, context={"request": request}
        ).data

        return Response({"data": data}, status=status.HTTP_200_OK)


class KanbanTaskGalleryPagination(PageNumberPagination):
    page_size = KANBAN_PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = KANBAN_MAX_PAGE_SIZE


class KanbanTaskGalleryView(generics.ListAPIView):
    permission_classes = [PermissionCheck]
    permission_type = "guest"
    serializer_class = ReturnKanbanTaskGallerySerializer
    pagination_class = KanbanTaskGalleryPagination

    def get_queryset(self):
        queryset = KanbanTask.objects.annotate(
            num_of_upvotes=Count("votes", filter=Q(votes__vote=True), distinct=True),
            num_of_downvotes=Count("votes", filter=Q(votes__vote=False), distinct=True),
        )

        # TASK TYPE TAGS
        queryset = get_qs_containing_all_tags(
            queryset, self.request.query_params.get("tags", "")
        )

        # SLIDER FILTERS
        registered_filters = [
            {
                "min_prefix": "importance_min",
                "max_prefix": "importance_max",
                "min_filter_kwarg": "importance__gte",
                "max_filter_kwarg": "importance__lte",
                "filter_type": "int",
            }
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
            "num_of_upvotes": "-num_of_upvotes",
            "importance": "-importance",
            "-importance": "importance",
            "date": "-id",
            "-date": "id",
        }

        ordering_fields = []
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
                headers={"X-Empty-Gallery": "No task found"},
            )

        return super().list(request, *args, **kwargs)


class DeleteKanbanTaskView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def delete(self, request, kanban_task_id):
        task = get_object_or_404(KanbanTask, id=kanban_task_id)
        self.check_object_permissions(request, task)

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangeKanbanVoteView(APIView):
    permission_classes = [PermissionCheck]
    permission_type = "logged_in"

    def post(self, request, kanban_task_id):
        profile = request.user.profile
        task = get_object_or_404(KanbanTask, id=kanban_task_id)

        raw = request.data.get("vote")

        if type(raw) not in (int, str, bool):
            return Response(
                {"error": {"kanban_task_voting": "Invalid vote value"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(raw, bool):
            vote_value = raw
        elif raw in [1, "1", "true", "True"]:
            vote_value = True
        elif raw in [-1, "-1", "false", "False"]:
            vote_value = False
        else:
            return Response(
                {"error": {"kanban_task_voting": "Invalid vote value"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vote, created = KanbanTaskVote.objects.get_or_create(
            voter=profile, task=task, defaults={"vote": vote_value}
        )

        previous = None if created else (1 if vote.vote else -1)

        # Case: user is removing the same vote
        if not created and vote.vote == vote_value:
            vote.delete()
            new = None
        else:
            vote.vote = vote_value
            vote.save()
            new = 1 if vote_value else -1

        # Compute vote deltas
        up_delta = 0
        down_delta = 0

        if previous is None and new == 1:
            up_delta = 1
        elif previous is None and new == -1:
            down_delta = 1
        elif previous == 1 and new is None:
            up_delta = -1
        elif previous == -1 and new is None:
            down_delta = -1
        elif previous == 1 and new == -1:
            up_delta = -1
            down_delta = +1
        elif previous == -1 and new == 1:
            up_delta = +1
            down_delta = -1

        return Response(
            {
                "data": {
                    "new_vote": new,
                    "upvote_change": up_delta,
                    "downvote_change": down_delta,
                }
            },
            status=status.HTTP_200_OK,
        )
