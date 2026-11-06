import React from "react";
import { useTheme } from "../context/ThemeContext";

export default function CurrentImageDisplayWrapper({
    image,
    preview_url,
    alt = "Selected image",
    maxWidth = "480px",
    container_sx = {},
    image_sx = {},
}) {
    const { theme } = useTheme();

    if (!image) return null;
    if (typeof image !== "string" && !preview_url) return null;

    const imageUrl = typeof image === "string" ? image : preview_url;

    return (
        <div
            style={{
                width: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                padding: theme.spacing.lg,
                borderRadius: theme.radius.lg,
                ...container_sx,
            }}
        >
            <img
                src={imageUrl}
                alt={alt}
                style={{
                    width: "100%",
                    maxWidth,
                    objectFit: "contain",

                    borderRadius: theme.radius.md,
                    boxShadow: theme.colors.shadow.card,
                    transition: theme.transition.normal,

                    ...image_sx,
                }}
            />
        </div>
    );
}
