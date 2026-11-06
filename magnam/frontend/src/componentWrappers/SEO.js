import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const SEO_DATA = {
    "/": {
        title: "MaGNaM — Türk Manga ve Anime Platformu",
        description:
            "Mangalarınızı ve fikirlerinizi yayınlayın, Türkiye'nin yerel manga ve anime platformunda hikayelerinizi paylaşın.",
    },

    "/manga/": {
        title: "Mangalar — MaGNaM",
        description:
            "MaGNaM'deki manga eserlerini keşfedin, yeni hikayeler okuyun ve favori içeriklerinizi takip edin.",
    },

    "/portfolio/": {
        title: "Portfolyolar — MaGNaM",
        description:
            "MaGNaM topluluğundaki sanatçıların ve içerik üreticilerinin portfolyolarını keşfedin.",
    },

    "/competition/": {
        title: "Yarışmalar — MaGNaM",
        description:
            "MaGNaM manga yarışmalarını keşfedin, yarışmalara katılın ve topluluğun eserlerini inceleyin.",
    },

    "/about/": {
        title: "MaGNaM Nedir?",
        description:
            "MaGNaM, anime ve manga içeriklerini bir araya getirmeyi ve içerik üreticilerinin eserlerini paylaşmasını amaçlayan bir platformdur.",
    },

    "/account/": {
        title: "Hesap — MaGNaM",
        description:
            "MaGNaM hesabınıza giriş yapın veya yeni bir hesap oluşturun.",
    },
};

const DEFAULT_SEO = {
    title: "MaGNaM",
    description:
        "MaGNaM, anime ve manga içeriklerini bir araya getiren içerik paylaşım platformudur.",
};

function setMetaTag(attribute, value, content) {
    let element = document.querySelector(`meta[${attribute}="${value}"]`);

    if (!element) {
        element = document.createElement("meta");
        element.setAttribute(attribute, value);
        document.head.appendChild(element);
    }

    element.setAttribute("content", content);
}

function setCanonical(url) {
    let element = document.querySelector('link[rel="canonical"]');

    if (!element) {
        element = document.createElement("link");
        element.setAttribute("rel", "canonical");
        document.head.appendChild(element);
    }

    element.setAttribute("href", url);
}

function SEO() {
    const location = useLocation();

    useEffect(() => {
        const path = location.pathname;
        const seo = SEO_DATA[path] || DEFAULT_SEO;
        const canonicalUrl = `https://studiomagnam.com${path}`;

        // Basic metadata
        document.title = seo.title;

        setMetaTag("name", "description", seo.description);

        // Open Graph
        setMetaTag("property", "og:title", seo.title);
        setMetaTag("property", "og:description", seo.description);
        setMetaTag("property", "og:url", canonicalUrl);

        // X / Twitter
        setMetaTag("name", "twitter:title", seo.title);
        setMetaTag("name", "twitter:description", seo.description);

        // Canonical
        setCanonical(canonicalUrl);
    }, [location.pathname]);

    return null;
}

export default SEO;
