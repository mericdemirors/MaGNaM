"""
URL configuration for magnam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from magnam.health import ping_check
from . import views

urlpatterns = [
    path("magnamdefaultadminurlpath", admin.site.urls),  # admin panel
    path("", include("frontend.urls")),  # frontend
    # and other apps
    path("api/news/", include("NewsPageApp.urls", namespace="NewsPageApp")),
    path("api/profile/", include("ProfilePageApp.urls", namespace="ProfilePageApp")),
    path("api/manga/", include("MangaPageApp.urls", namespace="MangaPageApp")),
    path(
        "api/portfolio/", include("PortfolioPageApp.urls", namespace="PortfolioPageApp")
    ),
    path(
        "api/competition/",
        include("CompetitionPageApp.urls", namespace="CompetitionPageApp"),
    ),
    path(
        "api/kanban/", include("KanbanTaskPageApp.urls", namespace="KanbanTaskPageApp")
    ),
    path("ping/", ping_check, name="ping"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms_of_service, name="terms_of_service"),
]

# only at development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
