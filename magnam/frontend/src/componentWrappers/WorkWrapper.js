import React, { useEffect, useState, useRef } from "react";
import { useTheme } from "../context/ThemeContext";
import { PdfSlideshow } from "./helper_components";
import {
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_PDF_EXTENSIONS,
} from "../globals";
/**
 * MediaRenderer
 * -------------
 * Responsible ONLY for deciding how to render a file.
 */
export function MediaRenderer({
    id,
    fileUrl,
    title,
    on_read_pdf,
    pagesBaseUrl,
    numImages,
}) {
    const { theme } = useTheme();
    if (!fileUrl) return null;

    const file = fileUrl.toLowerCase();

    // Helper function to dynamically generate a regex matching our extensions
    // e.g., creates match for /\.(png|jpg|jpeg|webp|gif|svg)$/
    const matchesExtension = (extensionsArray) => {
        const pattern = `\\.(${extensionsArray.join("|")})$`;
        return new RegExp(pattern).test(file);
    };

    if (matchesExtension(ALLOWED_IMAGE_EXTENSIONS)) {
        return (
            <a
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                    display: "block",
                    width: "100%",
                    height: "100%",
                    cursor: "pointer",
                }}
            >
                <img
                    src={fileUrl}
                    alt={title || "work"}
                    loading="lazy"
                    style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        display: "block",
                    }}
                />
            </a>
        );
    }

    if (matchesExtension(ALLOWED_VIDEO_EXTENSIONS)) {
        return (
            <video
                src={fileUrl}
                controls
                style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                }}
            />
        );
    }

    if (matchesExtension(ALLOWED_AUDIO_EXTENSIONS)) {
        return <audio src={fileUrl} controls style={{ width: "100%" }} />;
    }

    if (matchesExtension(ALLOWED_PDF_EXTENSIONS)) {
        const isProcessing = !numImages || numImages === 0;

        return (
            <div
                onClick={() => !isProcessing && on_read_pdf(id)}
                title={title || "work"}
                style={{
                    width: "100%",
                    height: "100%",
                    cursor: isProcessing ? "default" : "pointer",
                    position: "relative",
                }}
            >
                {isProcessing ? (
                    <div
                        style={{
                            width: "100%",
                            height: "100%",
                            backgroundColor: theme.colors.background.app_darker,
                            display: "flex",
                            flexDirection: "column",
                            justifyContent: "center",
                            alignItems: "center",
                            gap: theme.spacing.sm,
                            padding: theme.spacing.md,
                        }}
                    >
                        <div style={theme.styles.titleText}>
                            Preparing the PDF...
                        </div>
                        <div style={theme.styles.subtitleText}>
                            will be ready in 10-20 seconds
                        </div>
                    </div>
                ) : (
                    <PdfSlideshow
                        pagesBaseUrl={pagesBaseUrl}
                        numImages={numImages}
                    />
                )}
            </div>
        );
    }

    return null;
}

/**
 * WorkWrapper
 * ----------------
 * Content-first, gallery-style display for a single work.
 */
export default function WorkWrapper({ work, on_read_pdf = () => {} }) {
    const { theme } = useTheme();
    if (!work) return null;
    const { id, title, file_url } = work;

    return (
        <div
            style={{
                background: theme.colors.background.app,
                borderRadius: theme.radius.lg,
                boxShadow: theme.colors.shadow.card,
                padding: theme.spacing.md,
                paddingBottom: theme.spacing.lg,
                transition: theme.transition.normal,

                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.sm,
            }}
        >
            {/* Media frame */}
            <div
                style={{
                    width: "100%",
                    aspectRatio: "4 / 3",
                    background: theme.colors.background.muted,
                    borderRadius: theme.radius.md,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                    position: "relative",
                }}
            >
                <MediaRenderer
                    id={id}
                    fileUrl={file_url}
                    title={title}
                    on_read_pdf={on_read_pdf}
                    pagesBaseUrl={work.pages_base_url}
                    numImages={work.num_of_images}
                />
            </div>

            {/* Title */}
            {title && (
                <div
                    style={{
                        ...theme.styles.subtitleText,
                        textAlign: "center",
                    }}
                >
                    {title}
                </div>
            )}
        </div>
    );
}
