import React from "react";
import { Link } from "react-router-dom";
import Card from "@mui/material/Card";
import CardActionArea from "@mui/material/CardActionArea";
import CardMedia from "@mui/material/CardMedia";
import CardContent from "@mui/material/CardContent";
import { useTheme } from "../context/ThemeContext";

/**
 * Helper to parse "240px" into 240 and divide to 3
 */
const getMinHeight = (maxHeightStr) => {
    if (!maxHeightStr) return "auto";
    const numericValue = parseInt(maxHeightStr, 10);
    return `${numericValue / 3}px`;
};

/**
 * CardWrapper
 * -----------
 * Image-first, fixed-size, gallery-style card
 * with optional minimal metadata support.
 */
export default function CardWrapper({
    title,
    image,
    to,
    meta_data,
    sizeVariant = "default" | "home" | "profile",
}) {
    const { theme } = useTheme();

    let W, H_MAX;
    switch (sizeVariant) {
        case "home":
            W = theme.dimensions.xxs;
            H_MAX = theme.dimensions.sm;
            break;
        case "profile":
            W = theme.dimensions.xxxs;
            H_MAX = theme.dimensions.xxxs;
            break;
        case "default":
        default: // fallback for wrong variants
            W = theme.dimensions.xs;
            H_MAX = theme.dimensions.xl;
            break;
    }

    const H_MIN = getMinHeight(H_MAX);

    if (!Array.isArray(meta_data)) meta_data = [meta_data];
    meta_data = meta_data.filter(Boolean);

    return (
        <Card
            component={Link}
            to={to}
            sx={{
                width: W,
                minHeight: H_MIN,
                maxHeight: H_MAX,
                display: "flex",
                flexDirection: "column",
                backgroundColor: theme.colors.background.surface,
                borderRadius: theme.radius.lg,
                boxShadow: theme.colors.shadow.card,
                textDecoration: "none",
                overflow: "hidden",
                transition: theme.transition.normal,

                "&:hover": {
                    transform: "translateY(-2px)",
                    boxShadow: theme.colors.shadow.hover,
                },
            }}
        >
            <CardActionArea
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100%", // Fill the Card
                    alignItems: "stretch",
                    overflow: "hidden",
                }}
            >
                {/* Image part */}
                <CardMedia
                    component="img"
                    image={image}
                    alt={title}
                    sx={{
                        width: "100%",
                        flex: "1 1 auto",
                        minHeight: 0,
                        objectFit: "cover",
                    }}
                />

                {/* Bottom glossy overlay */}
                <CardContent
                    sx={{
                        width: "100%",
                        padding: theme.spacing.sm,
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "center",
                        gap: theme.spacing.xs,

                        backgroundColor: theme.colors.background.muted,
                        backdropFilter: "blur(8px)",
                        boxSizing: "border-box",

                        flexShrink: 0,
                    }}
                >
                    {/* Title */}
                    <div
                        style={{
                            ...theme.styles.subtitleText,
                            textAlign: "center",

                            padding: theme.spacing.sm,

                            textShadow: theme.styles.textShadow,

                            ...(sizeVariant === "profile" && {
                                display: "-webkit-box",
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: "vertical",
                                overflow: "hidden",
                            }),
                        }}
                    >
                        {title}
                    </div>

                    {/* Metadata */}
                    {meta_data.length > 0 && (
                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                gap: theme.spacing.sm,
                                alignItems: "center",
                            }}
                        >
                            {meta_data.map((item, index) => (
                                <span
                                    key={index}
                                    style={{ ...theme.styles.metadataText }}
                                >
                                    {item}
                                </span>
                            ))}
                        </div>
                    )}
                </CardContent>
            </CardActionArea>
        </Card>
    );
}
