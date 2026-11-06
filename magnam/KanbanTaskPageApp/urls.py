from django.urls import path
from . import views
from .views import *

app_name = "KanbanTaskPageApp"

urlpatterns = [
    path("tag/", KanbanTagView.as_view(), name="kanban-tag"),
    path("vote/", KanbanVoteView.as_view(), name="kanban-vote"),
    path("task/", KanbanTaskView.as_view(), name="kanban-task"),
    path("create-task/", CreateKanbanTaskView.as_view(), name="create-kanban-task"),
    path(
        "delete-task/<int:kanban_task_id>/",
        DeleteKanbanTaskView.as_view(),
        name="delete-kanban-task",
    ),
    path(
        "vote-task/<int:kanban_task_id>/",
        ChangeKanbanVoteView.as_view(),
        name="change-kanban-vote",
    ),
    # this one has parameters at the end like /kanban-gallery/?tags=1&tags=5&tags=12&sort=...
    path("kanban-gallery/", KanbanTaskGalleryView.as_view(), name="kanban-gallery"),
]
