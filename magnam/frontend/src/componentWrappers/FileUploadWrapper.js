import React from "react";
import Button from "@mui/material/Button";
import { useTheme } from "../context/ThemeContext";
import { UploadedChapterFilePreview } from "../componentWrappers/helper_components";
import {
    ALLOWED_PDF_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
} from "../globals";
/**
 * FileUploadWrapper
 * -----------------
 * Calm, gallery-friendly file upload component.
 * Uploads are secondary actions and should not dominate the UI.
 */

const ALL_ALLOWED_EXTENSIONS = [
    ...ALLOWED_PDF_EXTENSIONS,
    ...ALLOWED_VIDEO_EXTENSIONS,
    ...ALLOWED_AUDIO_EXTENSIONS,
    ...ALLOWED_IMAGE_EXTENSIONS,
]
    .map((ext) => `.${ext}`)
    .join(",");

export default function FileUploadWrapper({
    label = "Upload File",
    onChange,
    multiple = false,
    accept = ALL_ALLOWED_EXTENSIONS,
    selectedFiles = [],
    disabled = false,
    at_create_chapter_page = false,
}) {
    const { theme } = useTheme();
    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                width: "100%",
            }}
        >
            <Button
                component="label"
                disabled={disabled}
                sx={{
                    fontFamily: theme.typography.fontFamily.primary,
                    fontSize: theme.typography.fontSize.sm,
                    fontWeight: theme.typography.fontWeight.medium,
                    textTransform: "none",
                    borderRadius: theme.radius.md,
                    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                    backgroundColor: theme.colors.accent.primary,
                    color: theme.colors.text.primary,
                    border: `1px solid ${theme.colors.border.subtle}`,
                    boxShadow: "none",
                    transition: theme.transition.normal,

                    "&:hover": {
                        backgroundColor: theme.colors.accent.hover,
                        boxShadow: theme.colors.shadow.hover,
                    },

                    "&:disabled": {
                        backgroundColor: theme.colors.background.muted,
                        color: theme.colors.text.muted,
                    },
                }}
            >
                {label}
                <input
                    type="file"
                    multiple={multiple}
                    accept={accept}
                    hidden
                    onChange={onChange}
                />
            </Button>

            {selectedFiles.length > 0 && (
                <ul
                    style={{
                        margin: 0,
                        width: "100%",
                        paddingTop: theme.spacing.sm,

                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",

                        listStyle: "none", // important for visual calm
                        paddingLeft: 0,
                    }}
                >
                    {selectedFiles.map((file, index) => (
                        <li
                            key={index}
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                width: "100%",
                            }}
                        >
                            {at_create_chapter_page && (
                                <UploadedChapterFilePreview file={file} />
                            )}

                            <span
                                style={{
                                    ...theme.styles.descriptionText,
                                    fontSize: theme.typography.fontSize.sm,
                                    marginTop: theme.spacing.xs,
                                    textAlign: "center",
                                    maxWidth: "90%",
                                    wordBreak: "break-word",
                                    overflowWrap: "anywhere",
                                }}
                            >
                                {file instanceof File
                                    ? file.name
                                    : file.split("/").pop()}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
