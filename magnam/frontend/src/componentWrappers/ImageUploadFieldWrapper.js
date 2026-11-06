import React from "react";
import { useTheme } from "../context/ThemeContext";
import ImageUploadWrapper from "./ImageUploadWrapper";
import CurrentImageDisplayWrapper from "./CurrentImageDisplayWrapper";

export default function ImageUploadFieldWrapper({
    has_image = false,
    image = null,
    preview_url = "",
    alt = "",
    max_preview_width = null,

    min_height = 0,
    max_height = 0,
    min_width = 0,
    max_width = 0,
    max_file_size = 0,

    set_error_fn = () => {},
    set_state_fn = () => {},
}) {
    const { theme } = useTheme();

    return (
        <div
            style={{
                display: "flex", // 1. Enable Flexbox
                flexDirection: "column", // 2. Stack children vertically
                alignItems: "center", // 3. Center children horizontally
                justifyContent: "center", // 4. Center children vertically (if height allows)
                width: "100%", // 5. Take full width of parent to calculate center
                padding: theme.spacing.sm,
            }}
        >
            {has_image && (
                <div
                    style={{
                        paddingBottom: theme.spacing.lg,
                        width: "100%", // Allow display wrapper to handle its own max-width
                    }}
                >
                    <CurrentImageDisplayWrapper
                        image={image}
                        preview_url={preview_url}
                        alt={alt}
                        maxWidth={max_preview_width || theme.dimensions.xxl}
                    />
                </div>
            )}

            <div style={{ width: "fit-content" }}>
                <ImageUploadWrapper
                    min_height={min_height}
                    max_height={max_height}
                    min_width={min_width}
                    max_width={max_width}
                    max_file_size={max_file_size}
                    set_error_fn={set_error_fn}
                    set_state_fn={set_state_fn}
                />
            </div>
        </div>
    );
}
