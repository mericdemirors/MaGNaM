import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useLocation } from "react-router";

import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import SuccessPopUpWrapper from "../componentWrappers/SuccessPopUpWrapper";
import HasPermission from "../utils/HasPermission";
import { apiFetch, handleFetch } from "../utils/csrf";
import MangaViewerWrapper from "../componentWrappers/MangaViewerWrapper";
import { useTheme } from "../context/ThemeContext";
import { getPdfPageUrl } from "../utils/helper_functions";
function ReadMangaPage() {
    const navigate = useNavigate();
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");

    const { manga_id: manga_id_from_url, chapter_id: chapter_id_from_url } =
        useParams();

    const [manga, set_manga] = useState({
        id: -1,
        folder_name: "",
        num_of_chapters: 0,
        chapters: [],
        bookmark: null,
    });

    const [current_chapter_index, set_current_chapter_index] = useState(-1);

    // load the bookmarked page in the initial laod if user comes from 'go to bookmark' button in ShowMangaPage
    const location = useLocation();
    const [initial_page_to_load_in, set_initial_page_to_load_in] = useState(
        location.state?.bookmark_page ?? -1,
    );

    const [error_message, set_error_message] = useState("");
    const [success_message, set_success_message] = useState("");

    const chapter_index_to_page_urls_dict = useRef({}); // chapter index to pages dict
    const [cacheVersion, setCacheVersion] = useState(0); // integer flag for cache updates
    const [isPrepending, setIsPrepending] = useState(false); // boolean flag for scroll anchoring
    const [viewerInstanceKey, setViewerInstanceKey] = useState(0);

    const reset_reader_state = useCallback(() => {
        // wipe chapter cache
        chapter_index_to_page_urls_dict.current = {};

        // reset cache version so items recompute empty
        setCacheVersion((v) => v + 1);

        // reset prepend state
        setIsPrepending(false);

        // force viewer to fully remount
        setViewerInstanceKey((v) => v + 1);

        // reset the loaded bookmark
        set_initial_page_to_load_in(-1);
        set_current_chapter_index(-1);
    }, []);

    const items = React.useMemo(() => {
        const cache = chapter_index_to_page_urls_dict.current;

        // sort the chapters in [..., old chapter, current chapter, new chapter, ...] order
        const sortedChapterIndices = Object.keys(cache)
            .map(Number)
            .sort((a, b) => b - a);

        const elements = [];

        sortedChapterIndices.forEach((chapterIndex) => {
            const chapter = manga.chapters[chapterIndex];
            // add chapter cover page
            elements.push(
                <div
                    key={`Chapter ${chapterIndex} Page 0 cover key`}
                    chapter_index={chapterIndex}
                    chapter_page={0}
                    style={{
                        width: "100%",
                        height: theme.dimensions.xxxs,
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
                        {chapter.no} - {chapter.title}
                    </div>
                    <div style={theme.styles.subtitleText}>
                        {chapter.num_of_images === 0
                            ? "Preparing the PDF (will be ready in 10-20 seconds)"
                            : `(${chapter.num_of_images} pages)`}
                    </div>
                </div>,
            );

            // add the pages for the current chapter in this iteration
            const chapterPages = cache[chapterIndex];
            const pageElements = chapterPages.map((img) => (
                <div
                    key={`Chapter ${img.chapterIndex} Page ${img.pageIndex} page key`}
                    chapter_index={img.chapterIndex}
                    chapter_page={img.pageIndex}
                >
                    <img
                        style={{
                            width: "100%",
                            display: "block",
                            minHeight: theme.dimensions.xs,
                        }}
                        alt={`Chapter ${img.chapterIndex} Page ${img.pageIndex}`}
                        loading="lazy"
                        src={img.src}
                    />
                </div>
            ));

            elements.push(...pageElements);
        });

        return elements;
    }, [cacheVersion, manga.chapters]);

    const get_manga_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_manga_response = await apiFetch(
                    `/api/manga/read-manga/${manga_id_from_url}/`,
                    options,
                );
                const [
                    get_manga_success_data,
                    get_manga_error_message,
                    get_manga_ok,
                ] = await handleFetch("get_manga", get_manga_response);

                if (get_manga_ok) {
                    set_manga({
                        id: get_manga_success_data.id,
                        folder_name: get_manga_success_data.folder_name,
                        num_of_chapters:
                            get_manga_success_data.chapters?.length ?? 0,
                        chapters: get_manga_success_data.chapters ?? [],
                        bookmark: get_manga_success_data.bookmark ?? null,
                    });
                    set_error_message("");
                } else {
                    set_error_message(get_manga_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during manga fetch.",
                );
            }
        },
        [manga_id_from_url],
    );

    // marking a chapter as read
    async function mark_chapter_as_read(chapter_index) {
        // 1. Look up the specific chapter object using the array index
        const target_chapter = manga.chapters[chapter_index];

        // 2. Safely exit if it doesn't exist or lacks an ID
        if (!target_chapter || !target_chapter.id) return;

        // 3. Extract the actual database ID
        const chapter_id = target_chapter.id;

        if (target_chapter.is_user_read) return;

        try {
            const read_response = await apiFetch(
                `/api/manga/read-chapter/${chapter_id}/`,
                { method: "POST" },
            );

            const [read_success_data, read_error_message, read_ok] =
                await handleFetch("read_chapter", read_response);

            if (read_ok) {
                set_manga((prev_manga) => ({
                    ...prev_manga,
                    chapters: prev_manga.chapters.map((ch) =>
                        ch.id === chapter_id
                            ? { ...ch, is_user_read: true }
                            : ch,
                    ),
                }));
            }
        } catch (err) {
            console.error(
                err.message || "Network error marking chapter as read.",
            );
        }
    }

    async function handle_bookmark_submit(chapter_index, page_index) {
        set_success_message("");
        if (!manga.id) return;

        const chapter = manga.chapters?.[chapter_index];

        if (!chapter) {
            set_error_message("Invalid chapter.");
            return;
        }

        if (
            manga.bookmark &&
            manga.bookmark.chapter_id === chapter.id &&
            manga.bookmark.page === page_index
        ) {
            set_success_message(
                `Chapter ${chapter.no}: "${chapter.title}" page ${page_index} bookmarked.`,
            );
            return;
        }

        try {
            const form_data = new FormData();
            form_data.append("page", page_index);

            const submit_bookmark_response = await apiFetch(
                `/api/manga/bookmark-manga/${manga.id}/${chapter.id}/`,
                {
                    method: "POST",
                    body: form_data,
                },
            );

            const [
                submit_bookmark_success_data,
                submit_bookmark_error_message,
                submit_bookmark_ok,
            ] = await handleFetch("submit_bookmark", submit_bookmark_response);

            if (submit_bookmark_ok) {
                set_error_message("");
                set_manga((prev_manga) => ({
                    ...prev_manga,
                    bookmark: {
                        chapter_id: chapter.id,
                        page: page_index,
                    },
                }));
                set_success_message(
                    `Chapter ${chapter.no}: "${chapter.title}" page ${page_index} bookmarked.`,
                );
            } else {
                set_error_message(submit_bookmark_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during bookmark creation.",
            );
        }
    }

    // Initial fetch of the manga when url changes
    useEffect(() => {
        const controller = new AbortController();
        get_manga_details(controller.signal);
        chapter_index_to_page_urls_dict.current = {};
        return () => controller.abort();
    }, [manga_id_from_url, get_manga_details]);

    // Initial set of the current_chapter_index when manga or chapter id in url changes
    useEffect(() => {
        const idx = manga.chapters.findIndex(
            (ch) => ch.id === Number(chapter_id_from_url),
        );
        update_UI_selected_chapter(idx);
    }, [chapter_id_from_url, manga]);

    // Function to populate the cache with page image urls from chapter metadata
    const create_chapter_page_list = useCallback(
        (chapter_index) => {
            if (
                chapter_index < 0 ||
                chapter_index >= manga.num_of_chapters ||
                chapter_index_to_page_urls_dict.current[chapter_index]
            ) {
                return 0; // Return 0 if nothing was added
            }

            const chapter = manga.chapters[chapter_index];

            if (!chapter.is_user_bought) return 0; // Return 0 if user doesn't own it

            // each item we want to display in the viewer has 3 fields:
            // chapterIndex used to detect switches between chapters
            // pageIndex is used to create unique key to each image item
            // src is the image url to display
            const pageList = Array.from(
                { length: chapter.num_of_images },
                (_, i) => ({
                    chapterIndex: chapter_index,
                    pageIndex: i + 1,
                    src: getPdfPageUrl(chapter.pages_base_url, i),
                }),
            );
            chapter_index_to_page_urls_dict.current[chapter_index] = pageList;
            setCacheVersion((v) => v + 1);
            return pageList.length;
        },
        [manga],
    );

    // automatic cache update
    useEffect(() => {
        // create the current chapter's entry
        create_chapter_page_list(current_chapter_index);

        // chatgpt said we dont actually need this because no ones going to explode the cache by reading millions of pages
        // so I guess it just causes additional trouble by adding another 'deletion from past indices' index shift
        // remove chapters where index distance > 3
        // const cache = chapter_index_to_page_urls_dict.current;
        // const cachedChapterIndices = Object.keys(cache);

        // cachedChapterIndices.forEach((key) => {
        //     const indexInCache = parseInt(key, 10);
        //     if (Math.abs(indexInCache - current_chapter_index) > 3) {
        //         delete cache[indexInCache];
        //     }
        // });
    }, [current_chapter_index, create_chapter_page_list]);

    // functions to create the prev/next chapter page lists
    const preload_prev_chapter = useCallback(() => {
        if (current_chapter_index === -1) return 0;
        setIsPrepending(true);
        return create_chapter_page_list(current_chapter_index + 1);
    }, [current_chapter_index, create_chapter_page_list]);

    const preload_next_chapter = useCallback(() => {
        if (current_chapter_index === -1) return 0;
        setIsPrepending(false);
        return create_chapter_page_list(current_chapter_index - 1);
    }, [current_chapter_index, create_chapter_page_list]);

    // function to update chapter selector button highlights
    function update_UI_selected_chapter(idx) {
        if (0 <= idx && idx < manga.num_of_chapters) {
            if (manga.chapters[idx].is_user_bought) {
                // set as current chapter
                set_current_chapter_index(idx);
            } else {
                // else switch to -1 so "current_chapter_index >= 0" check fails
                set_error_message("You haven't bought this chapter yet.");
                set_current_chapter_index(-1);
            }
        }
    }

    // function to display the viewer
    function render_manga_viewer() {
        if (
            !(
                current_chapter_index < manga.num_of_chapters &&
                current_chapter_index >= 0
            )
        ) {
            return null;
        }

        if (!manga.chapters[current_chapter_index].is_user_bought) {
            set_error_message("You haven't bought this chapter yet.");
            set_current_chapter_index(-1);
            return null;
        }

        return (
            <MangaViewerWrapper
                key={viewerInstanceKey}
                initial_page_to_load_in={initial_page_to_load_in}
                handle_bookmark_submit={handle_bookmark_submit}
                items={items}
                current_chapter_index={current_chapter_index}
                preload_prev={preload_prev_chapter}
                preload_next={preload_next_chapter}
                update_UI_selected_chapter={update_UI_selected_chapter}
                mark_chapter_as_read={mark_chapter_as_read}
                shift={isPrepending}
            />
        );
    }

    function render_chapter_selector() {
        return (
            <div
                style={{
                    display: "flex",
                    gap: theme.spacing.sm,
                    padding: theme.spacing.md,
                    justifyContent: "center",
                }}
            >
                {manga.chapters?.map((ch, idx) => {
                    const disabled = !ch.is_user_bought;

                    return (
                        <div key={ch.id}>
                            <ButtonWrapper
                                disabled={disabled}
                                onClick={() => {
                                    if (idx === current_chapter_index) return;
                                    reset_reader_state();
                                    update_UI_selected_chapter(idx);
                                    navigate(
                                        `/read-manga/${manga_id_from_url}/${ch.id}`,
                                        { replace: true },
                                    );
                                }}
                                text={`${ch.no}: ${ch.title}`}
                                visualVariant={
                                    idx === current_chapter_index
                                        ? "soft" // The current chapter
                                        : idx < current_chapter_index &&
                                            !ch.is_user_read
                                          ? "outline" // Upcoming and unread
                                          : "ghost" // Others (past chapters, or upcoming but already read)
                                }
                            />
                        </div>
                    );
                })}
            </div>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }
        return (
            <div
                style={{
                    minHeight: "100vh",
                    background: theme.colors.background.app,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

                {/* Back button + Chapter bar */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        background: theme.colors.background.surface,
                        paddingRight: theme.spacing.md,
                    }}
                >
                    {/* Back to Manga (right, secondary) */}
                    {logged_in_permission && (
                        <div
                            style={{
                                marginLeft: theme.spacing.md,
                                flexShrink: 0,
                            }}
                        >
                            <ButtonWrapper
                                to={`/manga/${manga_id_from_url}/`}
                                text="Back to Manga"
                                visualVariant="outline"
                            />
                        </div>
                    )}

                    {/* <ButtonWrapper
                        text="Previous Chapter"
                        onClick={() => {
                            update_UI_selected_chapter(current_chapter_index + 1);
                        }}
                        visualVariant="outline"
                    />
                    <ButtonWrapper
                        text="Next Chapter"
                        onClick={() => {
                            update_UI_selected_chapter(current_chapter_index - 1);
                        }}
                        visualVariant="outline"
                    /> */}

                    {/* Chapter selector (left / center) */}
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            justifyContent: "center",
                        }}
                    >
                        {render_chapter_selector()}
                    </div>
                </div>

                {/* render the chapter */}
                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        justifyContent: "center",
                        padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    }}
                >
                    {render_manga_viewer()}
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => {
                            set_error_message("");
                        }}
                        error_title="Manga Error"
                    />
                )}

                {success_message && (
                    <SuccessPopUpWrapper
                        success_message={success_message}
                        on_close={() => set_success_message("")}
                        success_title="Bookmarked"
                    />
                )}
            </div>
        );
    }

    return render_main();
}

export default ReadMangaPage;
