from django.urls import path
from .views import index

urlpatterns = [
    path("", index),
    path("news/<int:news_id>/", index),
    path("create-news/", index),
    path("account/", index),
    path("profile/<int:profile_id>/", index),
    path("portfolio/", index),
    path("portfolio/<int:portfolio_id>/", index),
    path("portfolio/create-portfolio/", index),
    path("manga/", index),
    path("manga/<int:manga_id>/", index),
    path("read-manga/<int:manga_id>/", index),
    path("read-manga/<int:manga_id>/<int:chapter_id>/", index),
    path("manga/create-manga/", index),
    path("manga/create-chapter/<int:manga_id>/", index),
    path("competition/", index),
    path("competition/<int:competition_id>/", index),
    path("competition/create-competition/", index),
    path("about/", index),
    path("verify/<str:token>/", index),
    path("theme/", index),
]
