from django.urls import path
from .views import *

app_name = "MangaPageApp"

urlpatterns = [
    path("manga/", MangaView.as_view(), name="manga"),
    path("tag/", MangaTagView.as_view(), name="manga-tag"),
    path("rating/", MangaRatingView.as_view(), name="manga-rating"),
    path("comment/", MangaCommentView.as_view(), name="manga-comment"),
    path("create-manga/", CreateMangaView.as_view(), name="create-manga"),
    path("get-manga/<int:manga_id>/", GetMangaView.as_view(), name="get-manga"),
    path(
        "search-manga/<str:search_text>/",
        GetTextSearchMangaView.as_view(),
        name="search-manga",
    ),
    path("read-manga/<int:manga_id>/", ReadMangaView.as_view(), name="read-manga"),
    path("edit-manga/<int:manga_id>/", EditMangaView.as_view(), name="edit-manga"),
    path(
        "delete-manga/<int:manga_id>/", DeleteMangaView.as_view(), name="delete-manga"
    ),
    path(
        "follow-manga/<int:manga_id>/",
        ToggleFollowMangaView.as_view(),
        name="toggle-follow-manga",
    ),
    path(
        "rate-manga/<int:manga_id>/",
        ChangeMangaScoreView.as_view(),
        name="change-manga-score",
    ),
    path(
        "create-comment/<int:manga_id>/",
        CreateMangaCommentView.as_view(),
        name="create-manga-comment",
    ),
    path(
        "get-comments/<int:manga_id>/",
        GetMangaCommentsView.as_view(),
        name="get-manga-comments",
    ),
    # this one has parameters at the end like /manga-gallery/?tags=1&tags=5&tags=12&sort=...
    path("manga-gallery/", MangaGalleryView.as_view(), name="manga-gallery"),
    path("chapter/", ChapterView.as_view(), name="chapter"),
    path(
        "create-chapter/<int:manga_id>/",
        CreateChapterView.as_view(),
        name="create-chapter",
    ),
    path(
        "edit-chapter/<int:chapter_id>/", EditChapterView.as_view(), name="edit-chapter"
    ),
    path(
        "delete-chapter/<int:chapter_id>/",
        DeleteChapterView.as_view(),
        name="delete-chapter",
    ),
    path("buy-chapter/<int:chapter_id>/", BuyChapterView.as_view(), name="buy-chapter"),
    path(
        "read-chapter/<int:chapter_id>/", MarkReadChapterView.as_view(), name="mark-read-chapter"
    ),
    path(
        "bookmark-manga/<int:manga_id>/<int:chapter_id>/",
        PutMangaBookmarkView.as_view(),
        name="put-manga-bookmark",
    ),
]
