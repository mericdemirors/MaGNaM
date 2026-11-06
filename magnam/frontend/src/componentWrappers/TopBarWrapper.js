import React from "react";
import { useTheme } from "../context/ThemeContext";

/**
 * TopBarWrapper
 * --------------
 * Context-setting header for content spaces.
 * Calm, informational, non-interruptive.
 */
export default function TopBarWrapper({
    title = "",
    metadata = null,
    tags = [],
    right_side = null,
}) {
    const { theme } = useTheme();

    return (
        <div
            style={{
                width: "100%",
                paddingBottom: theme.spacing.lg,
                boxSizing: "border-box",
            }}
        >
            {/* Title + metadata */}
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.xs,
                    maxWidth: "100%", // Prevent overflow
                }}
            >
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "left",
                    }}
                >
                    {title}
                </div>

                {metadata && (
                    <div
                        style={{
                            ...theme.styles.metadataText,
                            maxWidth: "100%",
                        }}
                    >
                        {metadata}
                    </div>
                )}
            </div>

            {/* Tags + right-side content */}
            {(tags.length > 0 || right_side) && (
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: theme.spacing.md,
                        flexWrap: "wrap",
                        width: "100%", // Ensure it stays in parent column
                        boxSizing: "border-box",
                    }}
                >
                    {/* Tags */}
                    {tags.length > 0 && (
                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                gap: theme.spacing.sm,
                            }}
                        >
                            🏷️
                            {tags.map((tag, index) => (
                                <span
                                    key={index}
                                    style={{ ...theme.styles.tagText }}
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Right-side slot */}
                    {right_side && (
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: theme.spacing.sm,
                                flexWrap: "wrap",
                                flexShrink: 0, // Prevent shrinking into tags
                            }}
                        >
                            {right_side}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
