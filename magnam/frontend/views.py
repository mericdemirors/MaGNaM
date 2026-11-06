from django.conf import settings
from django.shortcuts import render

SEO_DATA = {
    "/": {
        "title": "MaGNaM — Türk Manga ve Anime Platformu",
        "description": (
            "Mangalarınızı ve fikirlerinizi yayınlayın, Türkiye'nin yerel "
            "manga ve anime platformunda hikayelerinizi paylaşın."
        ),
    },
    "/manga/": {
        "title": "Mangalar — MaGNaM",
        "description": (
            "MaGNaM'deki manga eserlerini keşfedin, yeni hikayeler okuyun "
            "ve favori içeriklerinizi takip edin."
        ),
    },
    "/portfolio/": {
        "title": "Portfolyolar — MaGNaM",
        "description": (
            "MaGNaM topluluğundaki sanatçıların ve içerik üreticilerinin "
            "portfolyolarını keşfedin."
        ),
    },
    "/competition/": {
        "title": "Yarışmalar — MaGNaM",
        "description": (
            "MaGNaM manga yarışmalarını keşfedin, yarışmalara katılın "
            "ve topluluğun eserlerini inceleyin."
        ),
    },
    "/about/": {
        "title": "MaGNaM Nedir?",
        "description": (
            "MaGNaM, anime ve manga içeriklerini bir araya getirmeyi ve "
            "içerik üreticilerinin eserlerini paylaşmasını amaçlayan bir platformdur."
        ),
    },
    "/account/": {
        "title": "Hesap — MaGNaM",
        "description": ("MaGNaM hesabınıza giriş yapın veya yeni bir hesap oluşturun."),
    },
}


def index(request, *args, **kwargs):
    seo = SEO_DATA.get(
        request.path,
        {
            "title": "MaGNaM",
            "description": (
                "MaGNaM, anime ve manga içeriklerini bir araya getiren "
                "içerik paylaşım platformudur."
            ),
        },
    )

    return render(
        request,
        "frontend/index.html",
        {
            "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
            "SEO_TITLE": seo["title"],
            "SEO_DESCRIPTION": seo["description"],
        },
    )
