import React, { useEffect, useRef, useState } from "react";
import { useTheme } from "../context/ThemeContext";
import {
    FaYoutube,
    FaInstagram,
    FaPinterest,
    FaDiscord,
    FaTwitter,
    FaLink,
} from "react-icons/fa";
import MagnamIconPNG from "../../static/images/favicon.webp"; // your custom icon component
import { getPdfPageUrl } from "../utils/helper_functions";

import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.min.mjs";

// Ensure worker is set
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/legacy/build/pdf.worker.min.mjs",
    import.meta.url,
).toString();

export function HorizontalDivider() {
    const { theme } = useTheme();
    return (
        <div
            style={{
                height: theme.spacing.sm,
                width: "100%",
                backgroundColor: theme.colors.accent.primary,
                borderRadius: theme.radius.sm,
                flexShrink: 0,
            }}
        />
    );
}

export function VerticalDivider() {
    const { theme } = useTheme();
    return (
        <div
            style={{
                width: theme.spacing.sm,
                backgroundColor: theme.colors.accent.primary,
                borderRadius: theme.radius.sm,
                height: "100%",
                flexShrink: 0,
            }}
        />
    );
}

export function SectionLabel({ text }) {
    const { theme } = useTheme();
    return (
        <div
            style={{
                ...theme.styles.subtitleText,
                paddingBottom: theme.spacing.sm,
                textAlign: "center",
            }}
        >
            {text}
        </div>
    );
}

export function render_links({ links }) {
    const { theme } = useTheme();

    return (
        <div>
            {links && (
                <div style={{ paddingTop: theme.spacing.lg }}>
                    <ul
                        style={{
                            margin: 0,
                            paddingLeft: theme.spacing.lg,
                        }}
                    >
                        {links
                            .split(/\s+/)
                            .filter(Boolean)
                            .map((link, index) => (
                                <li
                                    key={index}
                                    style={{
                                        ...theme.styles.linkText,
                                        paddingBottom: theme.spacing.md,
                                        listStylePosition: "outside",
                                        overflowWrap: "anywhere",
                                    }}
                                >
                                    {parsed_link_injected_text(link, theme)}
                                </li>
                            ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export function parsed_link_injected_text(text, theme) {
    return (
        <div>
            {parse_text_into_text_and_link_dict(text).map((part, index) => {
                if (part.type === "text") {
                    return (
                        <span key={index} style={theme.styles.descriptionText}>
                            {part.content}
                        </span>
                    );
                }

                if (part.type === "link") {
                    return (
                        <a
                            key={index}
                            href={part.content}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                                ...theme.styles.linkText,
                                display: "inline-flex",
                                gap: theme.spacing.xs,
                            }}
                        >
                            <span
                                style={{
                                    display: "inline-flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    flexShrink: 0,
                                }}
                            >
                                {get_icon_for_url(part.content, theme)}
                            </span>
                            {part.content}
                        </a>
                    );
                }

                return null;
            })}
        </div>
    );
}

// Utility to split text into text + links
function parse_text_into_text_and_link_dict(text) {
    if (!text || typeof text !== "string") return [];

    // simple regex for URLs (http/https)
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = [];
    let lastIndex = 0;

    let match;
    while ((match = urlRegex.exec(text)) !== null) {
        // text before the link
        if (match.index > lastIndex) {
            parts.push({
                type: "text",
                content: text.slice(lastIndex, match.index),
            });
        }

        // the link itself
        parts.push({ type: "link", content: match[0] });

        lastIndex = match.index + match[0].length;
    }

    // remaining text after last link
    if (lastIndex < text.length) {
        parts.push({ type: "text", content: text.slice(lastIndex) });
    }

    return parts;
}

// Utility to detect domain and map to icon
export function get_icon_for_url(url, theme) {
    try {
        const icon_style = {
            paddingRight: theme.spacing.sm,
            fontSize: theme.typography.fontSize.xl,
        };
        const normalizedUrl = url.startsWith("http") ? url : `https://${url}`;
        const domain = new URL(normalizedUrl).hostname.toLowerCase();

        if (domain.includes("magnam.com")) {
            return (
                <img
                    src={MagnamIconPNG}
                    alt="https://magnam.com"
                    style={{
                        width: theme.spacing.lg,
                        height: theme.spacing.lg,
                        paddingRight: theme.spacing.sm,
                    }}
                />
            );
        }
        if (domain.includes("youtube.com") || domain.includes("youtu.be"))
            return <FaYoutube style={{ ...icon_style }} />;
        if (domain.includes("instagram.com"))
            return <FaInstagram style={{ ...icon_style }} />;
        if (domain.includes("pinterest.com"))
            return <FaPinterest style={{ ...icon_style }} />;
        if (domain.includes("discord.com"))
            return <FaDiscord style={{ ...icon_style }} />;
        if (domain.includes("twitter.com") || domain.includes("x.com"))
            return <FaTwitter style={{ ...icon_style }} />;

        // fallback generic link icon
        return <FaLink style={{ ...icon_style }} />;
    } catch (e) {
        return null; // not a valid URL
    }
}

function interpolateColor(color1, color2, t) {
    // color1 and color2 are "#RRGGBB"
    const c1 = parseInt(color1.slice(1), 16);
    const c2 = parseInt(color2.slice(1), 16);

    const r = Math.round(
        ((c1 >> 16) & 0xff) * (1 - t) + ((c2 >> 16) & 0xff) * t,
    );
    const g = Math.round(((c1 >> 8) & 0xff) * (1 - t) + ((c2 >> 8) & 0xff) * t);
    const b = Math.round((c1 & 0xff) * (1 - t) + (c2 & 0xff) * t);

    return `rgb(${r},${g},${b})`;
}

function generateBinColors(bins) {
    const n = bins.length;
    const midIndex = Math.floor(n / 2);

    const colors = [];

    // interpolate left → middle (Red → Blue)
    for (let i = 0; i <= midIndex; i++) {
        const t = i / midIndex;
        colors.push(interpolateColor("#ff4545", "#4545ff", t));
    }

    // interpolate middle → right (Blue → Green)
    for (let i = midIndex + 1; i < n; i++) {
        const t = (i - midIndex) / (n - 1 - midIndex);
        colors.push(interpolateColor("#4545ff", "#45ff45", t));
    }

    return colors;
}

export function findBin(score) {
    if (score >= -100 && score < -90) return "[-100,-90)";
    if (score >= -90 && score < -80) return "[-90,-80)";
    if (score >= -80 && score < -70) return "[-80,-70)";
    if (score >= -70 && score < -60) return "[-70,-60)";
    if (score >= -60 && score < -50) return "[-60,-50)";
    if (score >= -50 && score < -40) return "[-50,-40)";
    if (score >= -40 && score < -30) return "[-40,-30)";
    if (score >= -30 && score < -20) return "[-30,-20)";
    if (score >= -20 && score < -10) return "[-20,-10)";
    if (score >= -10 && score <= 10) return "[-10,10]";
    if (score > 10 && score <= 20) return "(10,20]";
    if (score > 20 && score <= 30) return "(20,30]";
    if (score > 30 && score <= 40) return "(30,40]";
    if (score > 40 && score <= 50) return "(40,50]";
    if (score > 50 && score <= 60) return "(50,60]";
    if (score > 60 && score <= 70) return "(60,70]";
    if (score > 70 && score <= 80) return "(70,80]";
    if (score > 80 && score <= 90) return "(80,90]";
    if (score > 90 && score <= 100) return "(90,100]";
    return null;
}

import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { MANGA_MAX_RATING, MANGA_MIN_RATING } from "../globals";
export function MangaRatingHistogram({
    histogram,
    rating,
    userRating,
    totalRatings,
}) {
    const { theme } = useTheme();
    const BINS_ORDER = [
        "[-100,-90)",
        "[-90,-80)",
        "[-80,-70)",
        "[-70,-60)",
        "[-60,-50)",
        "[-50,-40)",
        "[-40,-30)",
        "[-30,-20)",
        "[-20,-10)",
        "[-10,10]",
        "(10,20]",
        "(20,30]",
        "(30,40]",
        "(40,50]",
        "(50,60]",
        "(60,70]",
        "(70,80]",
        "(80,90]",
        "(90,100]",
    ];

    const colors = generateBinColors(BINS_ORDER);

    // Helper to find which bin a specific numeric rating falls into
    const getBinIndex = (val) => {
        if (val === null || val === undefined) return -1;
        const index = Math.floor((val + 100) / 10);
        return Math.min(Math.max(index, 0), BINS_ORDER.length - 1);
    };

    const data = BINS_ORDER.map((bin) => histogram?.[bin] ?? 0);
    const maxVal = Math.max(...data, 1);
    const step = Math.pow(10, Math.floor(Math.log10(maxVal)));
    const yTicks = [];
    for (let i = 0; i <= maxVal; i += step) {
        yTicks.push(i);
    }

    return (
        <BarChart
            xAxis={[
                {
                    scaleType: "band",
                    data: BINS_ORDER,
                    id: "x-axis",
                    valueFormatter: (value) => {
                        const index = BINS_ORDER.indexOf(value);
                        if (index === 0) return `${MANGA_MIN_RATING}`;
                        if (index === BINS_ORDER.length - 1)
                            return `+${MANGA_MAX_RATING}`;
                        return "";
                    },
                },
            ]}
            yAxis={[
                {
                    min: 0,
                    max: maxVal,
                    tickInterval: yTicks,
                    valueFormatter: (value) => value.toString(),
                },
            ]}
            series={BINS_ORDER.map((bin, index) => ({
                data: data.map((_, i) => (i === index ? data[i] : 0)),
                color: colors[index],
                stack: "ratings",
            }))}
            // hardcoded because MUI dont except theme.dimensions values
            width={560}
            height={480}
            borderRadius={8}
            slotProps={{
                tooltip: { trigger: "none" },
                legend: { hidden: true },
            }}
            sx={{
                // Tick labels (text)
                "& .MuiChartsAxis-tickLabel": {
                    stroke: theme.colors.text.primary,
                },
            }}
        >
            {/* 2. Update ChartsText fill */}
            <ChartsText
                text={`${totalRatings} Rating${totalRatings > 1 ? "s" : ""}`}
                style={{
                    fontSize: 14,
                    fontWeight: "bold",
                    fill: theme.colors.text.primary, // Changed from default to theme
                }}
                x={60}
                y={10}
            />

            {/* 3. Update Reference Line Labels */}
            {totalRatings && (
                <ChartsReferenceLine
                    x={BINS_ORDER[getBinIndex(rating)]}
                    lineStyle={{
                        stroke: theme.colors.text.primary,
                        strokeDasharray: "2 2",
                    }}
                    label={`⭐ ${Number(rating).toFixed(2)}`}
                    labelStyle={{
                        fontSize: 12,
                        fill: theme.colors.text.primary, // Changed from 'black'
                        fontWeight: "bold",
                    }}
                    labelAlign="start"
                />
            )}

            {userRating && (
                <ChartsReferenceLine
                    x={BINS_ORDER[getBinIndex(userRating)]}
                    lineStyle={{
                        stroke: theme.colors.text.primary,
                        strokeWidth: 2,
                        opacity: 0.6,
                    }}
                    label={`You: ${userRating}`}
                    labelAlign="start"
                    spacing={{ x: 5, y: 20 }}
                    labelStyle={{
                        fontSize: 12,
                        fill: theme.colors.text.primary, // Changed from 'gray'
                    }}
                />
            )}
        </BarChart>
    );
}

export function UploadedChapterFilePreview({ file }) {
    const { theme } = useTheme();
    const canvasRef = useRef(null);
    const [previewUrl, setPreviewUrl] = useState(null);

    const isFile = file instanceof File;
    const isUrl = typeof file === "string";

    const isPdf =
        (isFile && file.type === "application/pdf") ||
        (isUrl && file.toLowerCase().endsWith(".pdf"));

    const isSafeUrl = (url) => {
        try {
            const parsed = new URL(url);
            return ["http:", "https:"].includes(parsed.protocol);
        } catch {
            return false;
        }
    };

    useEffect(() => {
        if (!file || !isPdf) return;

        let objectUrl = null;
        let cancelled = false;

        const setupPreview = async () => {
            try {
                let source;

                // set up the blob url
                if (isFile) {
                    objectUrl = URL.createObjectURL(file);
                    setPreviewUrl(objectUrl);
                    source = objectUrl;
                } else if (isUrl && isSafeUrl(file)) {
                    setPreviewUrl(file);
                    source = file;
                } else {
                    console.warn("Unsafe or invalid pdf URL blocked.");
                    return;
                }

                // render the pdf and get the first page
                const loadingTask = pdfjsLib.getDocument(source);
                const pdf = await loadingTask.promise;

                if (cancelled) return;

                const page = await pdf.getPage(1);
                const viewport = page.getViewport({ scale: 0.5 });

                const canvas = canvasRef.current;
                if (!canvas) return;

                const ctx = canvas.getContext("2d");
                canvas.width = viewport.width;
                canvas.height = viewport.height;

                await page.render({
                    canvasContext: ctx,
                    viewport,
                }).promise;
            } catch (err) {
                if (!cancelled) {
                    console.error("Pdf Preview Error:", err);
                }
            }
        };

        setupPreview();

        // cleanup the url after
        return () => {
            cancelled = true;

            if (isFile && objectUrl) {
                URL.revokeObjectURL(objectUrl);
            }
        };
    }, [file, isPdf]);

    if (!file || !isPdf) return null;

    const style = {
        maxWidth: theme.dimensions.xl,
        maxHeight: theme.dimensions.xl,
        borderRadius: theme.radius.sm,
        border: `1px solid ${theme.colors.border.subtle}`,
        marginTop: theme.spacing.xs,
    };

    return <canvas ref={canvasRef} style={style} />;
}

export function PdfSlideshow({ pagesBaseUrl, numImages, interval = 1500 }) {
    const [index, setIndex] = useState(0);

    useEffect(() => {
        if (!pagesBaseUrl || numImages === 0) return;

        const timer = setInterval(() => {
            setIndex((prev) => (prev + 1) % numImages);
        }, interval);

        return () => clearInterval(timer);
    }, [pagesBaseUrl, numImages, interval]);

    if (!pagesBaseUrl || numImages === 0) return null;

    const currentSrc = getPdfPageUrl(pagesBaseUrl, index);

    return (
        <div
            style={{
                width: "100%",
                height: "100%",
                position: "relative",
            }}
        >
            <img
                src={currentSrc}
                alt="pdf page"
                loading="lazy"
                style={{
                    position: "absolute",
                    maxWidth: "100%",
                    maxHeight: "100%",
                    width: "auto",
                    height: "auto",
                    objectFit: "contain",
                    top: "50%",
                    left: "50%",
                    transform: "translate(-50%, -50%)",
                    transition: "opacity 0.4s ease-in-out",
                }}
            />
        </div>
    );
}
