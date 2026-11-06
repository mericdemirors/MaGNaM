from django.urls import path
from .views import *

app_name = "NewsPageApp"

urlpatterns = [
    path("news/", NewsView.as_view(), name="news"),
    path("create-news/", CreateNewsView.as_view(), name="create-news"),
    path("get-news/<int:news_id>/", GetNewsView.as_view(), name="get-news"),
    path("edit-news/<int:news_id>/", EditNewsView.as_view(), name="edit-news"),
    path("delete-news/<int:news_id>/", DeleteNewsView.as_view(), name="delete-news"),
    path("news-carousel/", NewsCarouselView.as_view(), name="news-carousel"),
]
