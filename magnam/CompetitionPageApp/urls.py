from django.urls import path
from .views import *

app_name = "CompetitionPageApp"

urlpatterns = [
    path("competition/", CompetitionView.as_view(), name="competition"),
    path("tag/", CompetitionTagView.as_view(), name="competition-tag"),
    path(
        "create-competition/",
        CreateCompetitionView.as_view(),
        name="create-competition",
    ),
    path(
        "get-competition/<int:competition_id>/",
        GetCompetitionView.as_view(),
        name="get-competition",
    ),
    path(
        "edit-competition/<int:competition_id>/",
        EditCompetitionView.as_view(),
        name="edit-competition",
    ),
    path(
        "delete-competition/<int:competition_id>/",
        DeleteCompetitionView.as_view(),
        name="delete-competition",
    ),
    path(
        "submit/<int:competition_id>/<str:item_string>/",
        SubmitCompetitionItemView.as_view(),
        name="submit-competition-item",
    ),
    path(
        "winner/<int:competition_id>/<str:item_string>/",
        SubmitCompetitionWinnerView.as_view(),
        name="submit-competition-winner",
    ),
    path(
        "loser/<int:competition_id>/<str:item_string>/",
        SubmitCompetitionLoserView.as_view(),
        name="submit-competition-loser",
    ),
    # this one has parameters at the end like /competition-gallery/?tags=1&tags=5&tags=12&sort=...
    path(
        "competition-gallery/",
        CompetitionGalleryView.as_view(),
        name="competition-gallery",
    ),
]
