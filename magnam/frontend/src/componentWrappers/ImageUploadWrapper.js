import React from "react";
import { useTheme } from "../context/ThemeContext";
import imageCheck from "../utils/imageCheck";
import FileUploadWrapper from "../componentWrappers/FileUploadWrapper";
import { ALLOWED_IMAGE_EXTENSIONS } from "../globals";

/**
 * ImageUploadWrapper
 * ------------------
 * Calm, validated image upload with clear constraints.
 */
export default function ImageUploadWrapper({
    min_height,
    max_height,
    min_width,
    max_width,
    max_file_size,
    set_error_fn,
    set_state_fn,
    disabled = false,
}) {
    const { theme } = useTheme();

    const handle_file_change = async (e) => {
        const file = e.target.files[0];

        if (
            await imageCheck(
                file,
                min_height,
                max_height,
                min_width,
                max_width,
                max_file_size,
                set_error_fn,
            )
        ) {
            set_state_fn((prev) => ({ ...prev, image: file }));
        } else {
            e.target.value = null;
            set_state_fn((prev) => ({ ...prev, image: null }));
        }
    };

    return (
        <div
            style={{
                padding: theme.spacing.sm,
            }}
        >
            {/* Constraints */}
            <div
                style={{
                    ...theme.styles.descriptionText,
                    fontSize: theme.typography.fontSize.sm,
                    paddingBottom: theme.spacing.sm,
                    textAlign: "center", // Add this to center the "Max file size" text
                }}
            >
                {max_file_size && (
                    <div>
                        Max file size:{" "}
                        {Math.round(max_file_size / (1024 * 1024))} MB
                    </div>
                )}

                {(min_width || max_width) && (
                    <div>
                        Width:&nbsp;
                        {min_width ? `≥ ${min_width}px` : ""}
                        {min_width && max_width ? " & " : ""}
                        {max_width ? `≤ ${max_width}px` : ""}
                    </div>
                )}

                {(min_height || max_height) && (
                    <div>
                        Height:&nbsp;
                        {min_height ? `≥ ${min_height}px` : ""}
                        {min_height && max_height ? " & " : ""}
                        {max_height ? `≤ ${max_height}px` : ""}
                    </div>
                )}
            </div>

            <FileUploadWrapper
                label="Upload Image"
                onChange={handle_file_change}
                accept={ALLOWED_IMAGE_EXTENSIONS.map((ext) => `.${ext}`).join(
                    ",",
                )}
                disabled={disabled}
            />
        </div>
    );
}
