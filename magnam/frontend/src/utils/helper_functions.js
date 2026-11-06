import React from "react";
import { apiFetch, handleFetch } from "../utils/csrf";

import { PDF_PAGE_IMAGE_NAME_FORMAT_LEN } from "../globals";
import { validateText } from "./helper_validators";

export async function setFetchAndSet(url, set_state, set_error_fn, label = "") {
    try {
        const response = await apiFetch(url, { method: "GET" });
        const [data, error_message, ok] = await handleFetch(label, response);

        if (response.status === 204) {
            const empty_search_message =
                response.headers.get("X-Empty-Search") || `No ${label} found.`;

            set_error_fn(empty_search_message);
            return;
        }

        if (ok) {
            set_state(data);
            set_error_fn("");
        } else {
            set_error_fn(error_message);
        }
    } catch (err) {
        set_error_fn(err.message || `Network error during ${label} fetch.`);
    }
}

export async function galleryFetchAndSet(
    url,
    set_gallery_fn,
    set_error_fn,
    set_loading_fn,
    set_next_page_fn,
    label = "gallery",
    signal,
) {
    try {
        set_loading_fn(true);
        const response = await apiFetch(url, { signal, method: "GET" });
        const [data, error_message, ok] = await handleFetch(label, response);

        if (response.status === 204) {
            const empty_gallery_message =
                response.headers.get("X-Empty-Gallery") || `No ${label} found.`;

            set_error_fn(empty_gallery_message);
            set_next_page_fn(null);
            return;
        }

        if (ok) {
            set_gallery_fn((prev) => {
                const new_items = data.results.filter(
                    (new_item) => !prev.some((item) => item.id === new_item.id),
                );
                return [...prev, ...new_items];
            });

            set_error_fn("");
            set_next_page_fn(data.next);
        } else {
            set_error_fn(error_message);
        }
    } catch (err) {
        if (err.name === "AbortError") return;
        set_error_fn(err.message || `Network error during ${label} fetch.`);
    } finally {
        set_loading_fn(false);
    }
}

export function handleIdLabelItemSelect(id, set_selected_fn) {
    set_selected_fn((prev) => {
        if (prev.includes(id)) {
            return prev.filter((i) => i !== id);
        } else {
            return [...prev, id];
        }
    });
}

export function scrollDebounceHelper(
    scroll_triggered_fn,
    offset = 100,
    delay = 200,
) {
    // in every scroll event:
    // 1- we first terminate the ongoing load_more_...() that started in past 200ms
    // 2- then start a new load_more_...() process
    // 3- steps 1->2->1->2->1... continues till user stops scrolling
    // 4- user stops scrolling and last load_more_...() function we set runs

    let timeout = null;

    const handle_scroll = () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (
                window.innerHeight + window.scrollY >=
                document.body.offsetHeight - offset
            ) {
                scroll_triggered_fn();
            }
        }, delay);
    };

    // Attach listener
    window.addEventListener("scroll", handle_scroll);

    // Return cleanup function for useEffect
    return () => {
        clearTimeout(timeout);
        window.removeEventListener("scroll", handle_scroll);
    };
}

export function commentScrollDebounceHelper(
    scrollRef,
    scroll_triggered_fn,
    offset = 50,
    delay = 200,
) {
    let timeout = null;

    const handle_scroll = () => {
        const el = scrollRef.current;
        if (!el) return;

        clearTimeout(timeout);
        timeout = setTimeout(() => {
            if (el.scrollTop + el.clientHeight >= el.scrollHeight - offset) {
                scroll_triggered_fn();
            }
        }, delay);
    };

    const el = scrollRef.current;
    if (!el) return () => {}; // nothing to cleanup if element not ready

    el.addEventListener("scroll", handle_scroll);

    // Return cleanup function for useEffect
    return () => {
        clearTimeout(timeout);
        el.removeEventListener("scroll", handle_scroll);
    };
}

export function handleSortIdLabelItemSelect(id, set_selected_fn) {
    set_selected_fn((prev) => {
        const base_id = id.startsWith("-") ? id.slice(1) : id;

        // Remove any item sort with same base_id (both reversed and non-reversed)
        const cleaned = prev.filter((item) => {
            const item_base = item.startsWith("-") ? item.slice(1) : item;
            return item_base !== base_id;
        });

        // Toggle logic
        if (prev.includes(id)) {
            // If it's already selected: remove it
            return cleaned;
        } else {
            // Add this sorting option
            return [...cleaned, id];
        }
    });
}

export function constructRequestUrl(
    baseUrl,
    selected_tags = [],
    selected_sorts = [],
    registered_ranges = [],
) {
    let url = baseUrl;

    // Handle tags
    if (selected_tags.length > 0) {
        const tags_url_param = selected_tags.join(",");
        url += url.includes("?")
            ? `&tags=${tags_url_param}`
            : `?tags=${tags_url_param}`;
    }

    // Handle sorts
    if (selected_sorts.length > 0) {
        const sort_param = selected_sorts.join(",");
        url += url.includes("?")
            ? `&sort=${sort_param}`
            : `?sort=${sort_param}`;
    }

    // Handle ranges
    const appendParam = (u, key, value) =>
        u + (u.includes("?") ? "&" : "?") + `${key}=${value}`;
    registered_ranges.forEach(
        ({ range, min_limit, max_limit, min_prefix, max_prefix }) => {
            if (range[0] !== min_limit)
                url = appendParam(url, min_prefix, range[0]);
            if (range[1] !== max_limit)
                url = appendParam(url, max_prefix, range[1]);
        },
    );

    return url;
}

export function buildCommentsTree(comments) {
    const map = {};
    const roots = [];

    // Prepare map with children arrays
    comments.forEach((comment) => {
        map[comment.id] = { ...comment, children: [] };
    });

    // Build parent-child relationships
    comments.forEach((comment) => {
        if (comment.parent_comment_id) {
            map[comment.parent_comment_id]?.children.push(map[comment.id]);
        } else {
            roots.push(map[comment.id]);
        }
    });

    // Recursively sort comments and their children by descending id
    const sortCommentTree = (arr) => {
        arr.sort((a, b) => b.id - a.id);
        arr.forEach((item) => sortCommentTree(item.children));
        return arr;
    };

    return sortCommentTree(roots);
}

export const getPaginatedComments = async (
    signal,
    request_url,
    set_item_state_fn,
    set_comments_next_page_fn,
    set_error_fn,
) => {
    const options = signal ? { signal, method: "GET" } : { method: "GET" };

    try {
        const response = await apiFetch(request_url, options);
        const [success_data, error_message, ok] = await handleFetch(
            "get_comments",
            response,
        );

        if (ok) {
            // Merge results into state without duplicates
            set_item_state_fn((prev) => {
                const new_items = success_data.results.filter(
                    (item) =>
                        !prev.comments.some(
                            (existing) => existing.id === item.id,
                        ),
                );

                return {
                    ...prev,
                    comments: [...prev.comments, ...new_items],
                };
            });

            set_comments_next_page_fn(success_data.next);
            set_error_fn("");
        } else {
            set_error_fn(error_message);
        }
    } catch (err) {
        set_error_fn(err.message || "Network error during fetch.");
    }
};

export async function handleCreateComment(
    submitted_text, // Renamed for clarity
    min_comment_len,
    max_comment_len,
    set_error_fn,
    request_url,
    set_item_state_fn,
) {
    let raw_input = submitted_text.trim();
    if (raw_input === "") return false;

    let parent_id_to_send = -1;
    let comment_text = raw_input;

    // if it contains a reply ID
    if (raw_input.startsWith("@")) {
        // reply ID starts from @ till the first space character
        const parts = raw_input.split(/\s+/);
        const reply_id_string = parts[0];

        // if reply contains other characters than digits, it's an invalid parent comment ID
        const idMatch = reply_id_string.match(/^@(\d+)$/);
        if (!idMatch) return false;

        parent_id_to_send = parseInt(idMatch[1], 10);

        // now check if rest of the reply comment text is empty or not
        comment_text = parts.slice(1).join(" ").trim();
        if (comment_text === "") return false;
    }

    const isCommentValid = validateText({
        value: comment_text,
        fieldName: "Comment",
        minLen: min_comment_len,
        maxLen: max_comment_len,
        required: true,
        error_handler: set_error_fn,
    });
    if (!isCommentValid) return false;

    try {
        const form_data = new FormData();
        form_data.append("comment", comment_text);
        form_data.append("parent_comment_id", parent_id_to_send);

        const response = await apiFetch(request_url, {
            method: "POST",
            body: form_data,
        });
        const [data, error_message, ok] = await handleFetch(
            "create_comment",
            response,
        );

        if (ok) {
            // Append new comment + update count using functional update
            set_item_state_fn((prev) => ({
                ...prev,
                comments: [...prev.comments, data],
                num_of_comments: prev.num_of_comments + 1,
            }));

            set_error_fn("");
            return true; // Success!
        } else {
            set_error_fn(error_message);
            return false;
        }
    } catch (err) {
        set_error_fn(err.message || "Network error during comment creation.");
        return false;
    }
}

export function handlePreviewUrl(image, set_preview_url_fn) {
    // If no image or image is a string URL → clear preview
    if (!image || typeof image === "string") {
        set_preview_url_fn(null);
        return () => {};
    }

    // Create temporary URL
    const url = URL.createObjectURL(image);
    set_preview_url_fn(url);

    return () => {
        // Return cleanup function
        URL.revokeObjectURL(url);
        set_preview_url_fn(null);
    };
}

export function handleIdLabelItemSlotSelect(id, set_item_state, key) {
    set_item_state((prev) => {
        const arr = prev[key] || [];
        const contains = arr.includes(id);
        const updated = contains ? arr.filter((i) => i !== id) : [...arr, id];

        return {
            ...prev,
            [key]: updated,
        };
    });
}

export function areArraysEqualAsSets(a, b) {
    if (!Array.isArray(a) || !Array.isArray(b)) return false;
    if (a.length !== b.length) return false;

    const setA = new Set(a);
    const setB = new Set(b);

    if (setA.size !== setB.size) return false;

    for (const item of setA) {
        if (!setB.has(item)) return false;
    }

    return true;
}

export function formatTimestampToDateString(timestamp) {
    if (typeof timestamp !== "number" || isNaN(timestamp)) {
        return "2027-01-01";
    }
    const date = new Date(timestamp);
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, "0"); // Months are 0-indexed
    const day = String(date.getUTCDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

export function darkenHex(hex, amount) {
    let col = hex.replace("#", "");

    if (col.length === 8) col = col.slice(0, 6);

    const num = parseInt(col, 16);

    let r = (num >> 16) - amount;
    let g = ((num >> 8) & 0x00ff) - amount;
    let b = (num & 0x0000ff) - amount;

    r = Math.max(0, r);
    g = Math.max(0, g);
    b = Math.max(0, b);

    return `rgb(${r}, ${g}, ${b})`;
}

export function getPdfPageUrl(pages_base_url, index) {
    // Formats index to PDF_PAGE_IMAGE_NAME_FORMAT_LEN left zero filled digits
    // (e.g., 0000, 0001, 0002).webp
    const page = String(index).padStart(PDF_PAGE_IMAGE_NAME_FORMAT_LEN, "0");
    return `${pages_base_url}${page}.webp`;
}

export function checkFileSize(file, max_file_size, error_handler) {
    if (max_file_size && file.size > max_file_size) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const maxMB = (max_file_size / (1024 * 1024)).toFixed(2);
        error_handler(
            `Error: ${file.name} file size (${sizeMB} MB) exceeds max allowed size (${maxMB} MB).`,
        );
        return false;
    }
    return true;
}

// CHAPTER DOWNLAD UTILS
// fixes the download name
export function sanitize_filename(str = "") {
    return str.replace(/[^a-z0-9]/gi, "_").toLowerCase();
}
// creates filename string for chapter pdf
export function generate_chapter_filename(mangaTitle, chapterNo, chapterTitle) {
    const safeMangaTitle = sanitize_filename(mangaTitle);
    const safeChapterTitle = sanitize_filename(chapterTitle);

    return `${safeMangaTitle}-chapter_${chapterNo}-${safeChapterTitle}.pdf`;
}
// creates pdf blob for donwload
export async function fetch_pdf_blob(pdfUrl) {
    const response = await fetch(pdfUrl);
    if (!response.ok) {
        throw new Error("Failed to fetch pdf");
    }
    return await response.blob();
}

export function trigger_download(blob, filename) {
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;

    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
}

export async function download_chapter_pdf(
    pdfUrl,
    mangaTitle,
    chapterNo,
    chapterTitle,
) {
    const blob = await fetch_pdf_blob(pdfUrl);

    const filename = generate_chapter_filename(
        mangaTitle,
        chapterNo,
        chapterTitle,
    );

    trigger_download(blob, filename);
}
