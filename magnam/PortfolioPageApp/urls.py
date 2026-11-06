from django.urls import path
from . import views
from .views import *

app_name = "PortfolioPageApp"

urlpatterns = [
    path("portfolio/", PortfolioView.as_view(), name="portfolio"),
    path("tag/", PortfolioTagView.as_view(), name="portfolio-tag"),
    path("like/", PortfolioLikeView.as_view(), name="portfolio-like"),
    path("comment/", PortfolioCommentView.as_view(), name="portfolio-comment"),
    path("create-portfolio/", CreatePortfolioView.as_view(), name="create-portfolio"),
    path(
        "get-portfolio/<int:portfolio_id>/",
        GetPortfolioView.as_view(),
        name="get-portfolio",
    ),
    path(
        "edit-portfolio/<int:portfolio_id>/",
        EditPortfolioView.as_view(),
        name="edit-portfolio",
    ),
    path(
        "delete-portfolio/<int:portfolio_id>/",
        DeletePortfolioView.as_view(),
        name="delete-portfolio",
    ),
    path(
        "like-portfolio/<int:portfolio_id>/",
        TogglePortfolioLikeView.as_view(),
        name="toggle-portfolio-like",
    ),
    path(
        "create-comment/<int:portfolio_id>/",
        CreatePortfolioCommentView.as_view(),
        name="create-portfolio-comment",
    ),
    path(
        "get-comments/<int:portfolio_id>/",
        GetPortfolioCommentsView.as_view(),
        name="get-portfolio-comments",
    ),
    # this one has parameters at the end like /portfolio-gallery/?tags=1&tags=5&tags=12&sort=...
    path(
        "portfolio-gallery/", PortfolioGalleryView.as_view(), name="portfolio-gallery"
    ),
    path("work/", WorkView.as_view(), name="work"),
    path(
        "create-work/<int:portfolio_id>/", CreateWorkView.as_view(), name="create-work"
    ),
    path("delete-work/<int:work_id>/", DeleteWorkView.as_view(), name="delete-work"),
]
