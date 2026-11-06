import React, { useState, useEffect } from "react";

import manga_card_image from "../assets/manga.webp";
import portfolio_card_image from "../assets/portfolios.webp";
import competition_card_image from "../assets/competitions.webp";

import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import CarouselWrapper from "../componentWrappers/CarouselWrapper";
import CardWrapper from "../componentWrappers/CardWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import HasPermission from "../utils/HasPermission";
import { setFetchAndSet } from "../utils/helper_functions";
import { useTheme } from "../context/ThemeContext";

function ShowHomePage() {
    const { theme } = useTheme();

    const admin_permission = HasPermission("admin");
    const logged_in_permission = HasPermission("logged_in");

    const [news_carousel, set_news_carousel] = useState([]);
    const [carousel_error, set_carousel_error] = useState("");

    // get the news on mounting
    useEffect(() => {
        setFetchAndSet(
            "/api/news/news-carousel/",
            set_news_carousel,
            set_carousel_error,
            "news_carousel",
        );
    }, []);

    function render_main() {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    minHeight: "100vh",
                    backgroundColor: theme.colors.background.app,
                }}
            >
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

                {/* NEWS SECTION */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: theme.spacing.sm,
                        paddingBlock: theme.spacing.md,
                        paddingInline: theme.spacing.md,
                    }}
                >
                    {/* The carousel now handles its own state internally */}
                    <CarouselWrapper
                        news_carousel={news_carousel}
                        carousel_error={carousel_error}
                    />
                </div>

                {admin_permission && (
                    <div style={{ display: "flex", justifyContent: "center" }}>
                        <ButtonWrapper text="Create News" to="/create-news/" />
                    </div>
                )}

                <div
                    style={{
                        display: "flex",
                        justifyContent: "center",
                        flexWrap: "wrap",
                        padding: theme.spacing.md,
                        gap: theme.spacing.lg,
                    }}
                >
                    <CardWrapper
                        title="Portfolios"
                        to="/portfolio/"
                        image={portfolio_card_image}
                        sizeVariant="home"
                    />
                    <CardWrapper
                        title="Manga"
                        to="/manga/"
                        image={manga_card_image}
                        sizeVariant="home"
                    />
                    <CardWrapper
                        title="Competitions"
                        to="/competition/"
                        image={competition_card_image}
                        sizeVariant="home"
                    />
                </div>
            </div>
        );
    }

    return render_main();
}

export default ShowHomePage;
