import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";

/**
 * ProfileDirectingWrapper
 * -----------------------
 * Clickable profile box/link, small and unobtrusive.
 */
export default function ProfileDirectingWrapper({
    profile_id,
    profile_name,
    profile_image,
    sx,
}) {
    const { theme } = useTheme();
    const [isHovered, setIsHovered] = useState(false);

    return (
        <Link
            to={`/profile/${profile_id}/`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            style={{
                display: "flex",
                alignItems: "center",
                gap: theme.spacing.sm,
                padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                transition: `${theme.transition.fast}, transform ${theme.transition.fast}`,
                borderRadius: theme.radius.md,
                border: `3px dashed ${theme.colors.accent.secondary}`,
                cursor: "pointer",
                transform: isHovered ? "translateY(-2px)" : "translateY(0)",
                boxShadow: isHovered ? theme.colors.shadow.hover : "none",
                ...sx,
            }}
        >
            {profile_image && (
                <img
                    src={profile_image}
                    alt={profile_name}
                    style={{
                        width: 32,
                        height: 32,
                        borderRadius: "50%",
                        objectFit: "cover",
                        boxShadow: theme.colors.shadow.card,
                        transition: theme.transition.normal,
                    }}
                />
            )}
            <span
                style={{
                    ...theme.styles.subtitleText,
                }}
            >
                {profile_name}{" "}
                <span style={{ color: theme.colors.text.secondary }}>
                    (@{profile_id})
                </span>
            </span>
        </Link>
    );
}
