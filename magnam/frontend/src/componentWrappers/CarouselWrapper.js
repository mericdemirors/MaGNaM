import React, { useState, useEffect } from "react";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { useTheme } from "../context/ThemeContext";

/**
 * CarouselWrapper — Gallery-style news carousel with glass title overlay
 *
 * @param {Array} news_carousel - list of news objects
 * @param {string|null} carousel_error - error message (if any)
 */
export default function CarouselWrapper({
    news_carousel = [],
    carousel_error = "",
}) {
    const [hoveredId, setHoveredId] = useState(null);
    const [current_index, set_current_index] = useState(0);
    const [user_interaction_key, set_user_interaction_key] = useState(0);

    const { theme } = useTheme();
    const ROTATION_TIME = 4000;
    const length = news_carousel.length;

    // Handle auto-rotation logic internally
    useEffect(() => {
        if (length <= 1) return;

        const interval = setInterval(() => {
            set_current_index((prev) => (prev + 1) % length);
        }, ROTATION_TIME);

        return () => clearInterval(interval);
    }, [length, user_interaction_key]);

    if (carousel_error)
        return (
            <div style={{ ...theme.styles.titleText }}>{carousel_error}</div>
        );

    if (!length)
        return <div style={{ ...theme.styles.titleText }}>Nothing new</div>;

    function previous_news() {
        set_current_index((prev) => (prev - 1 + length) % length);
        set_user_interaction_key((prev) => prev + 1);
    }

    function next_news() {
        set_current_index((prev) => (prev + 1) % length);
        set_user_interaction_key((prev) => prev + 1);
    }

    // Determine which items to display
    let displayItems = [];
    if (length > 1) {
        displayItems = [
            news_carousel[current_index],
            news_carousel[(current_index + 1) % length],
        ];
    } else {
        displayItems = [news_carousel[current_index]];
    }

    return (
        <div
            style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: theme.spacing.md,
                overflow: "hidden",
                padding: theme.spacing.md,
            }}
        >
            {/* Left navigation */}
            {length > 1 && (
                <ButtonWrapper
                    text="<"
                    onClick={previous_news}
                    visualVariant="outline"
                    sx={{ fontWeight: "bold" }}
                />
            )}

            {/* News Images */}
            <div
                style={{
                    display: "flex",
                    gap: theme.spacing.md,
                    justifyContent: "center",
                }}
            >
                {displayItems.map((item) => (
                    <a
                        key={item.id}
                        href={`/news/${item.id}/`}
                        onMouseEnter={() => setHoveredId(item.id)}
                        onMouseLeave={() => setHoveredId(null)}
                        style={{
                            display: "block",
                            width: theme.dimensions.xl,
                            height: theme.dimensions.sm,
                            position: "relative",
                            textDecoration: "none",
                            color: theme.colors.text.primary,
                            borderRadius: theme.radius.md,
                            overflow: "hidden",
                            flexShrink: 0,
                            transform:
                                hoveredId === item.id
                                    ? "translateY(-2px)"
                                    : "translateY(0)",
                            boxShadow:
                                hoveredId === item.id
                                    ? theme.colors.shadow.hover
                                    : theme.colors.shadow.card,
                            transition: theme.transition.normal,
                        }}
                    >
                        {item.image && (
                            <img
                                src={item.image}
                                alt={item.title}
                                style={{
                                    width: "100%",
                                    height: "100%",
                                    objectFit: "cover",
                                    display: "block",
                                }}
                            />
                        )}

                        {/* Glass overlay for title */}
                        <div
                            style={{
                                position: "absolute",
                                bottom: 0,
                                left: 0,
                                width: "100%",
                                height: "20%",
                                display: "flex",
                                padding: theme.spacing.md,
                                justifyContent: "center",
                                alignItems: "center",
                                backgroundColor: "rgba(255, 255, 255, 0.15)",
                                backdropFilter: "blur(4px)",
                                boxSizing: "border-box",
                            }}
                        >
                            <span
                                style={{
                                    ...theme.styles.titleText,
                                    display: "-webkit-box",
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: "vertical",
                                    overflow: "hidden",
                                    textShadow: theme.styles.textShadow,
                                }}
                            >
                                {item.title}
                            </span>
                        </div>
                    </a>
                ))}
            </div>

            {/* Right navigation */}
            {length > 1 && (
                <ButtonWrapper
                    text=">"
                    onClick={next_news}
                    visualVariant="outline"
                    sx={{ fontWeight: "bold" }}
                />
            )}
        </div>
    );
}
