import React, { useState, useEffect, useRef } from "react";
import { Masonry } from "@mui/lab";

import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import CardWrapper from "../componentWrappers/CardWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import RegisteredSlidersDisplayWrapper from "../componentWrappers/RegisteredSlidersDisplayWrapper";
import DateSliderWrapper from "../componentWrappers/DateSliderWrapper";
import ControlPanelWrapper from "../componentWrappers/ControlPanelWrapper";
import HasPermission from "../utils/HasPermission";
import LoadSpinnerWrapper from "../componentWrappers/LoadSpinnerWrapper";
import {
    setFetchAndSet,
    galleryFetchAndSet,
    handleIdLabelItemSelect,
    scrollDebounceHelper,
    handleSortIdLabelItemSelect,
    constructRequestUrl,
} from "../utils/helper_functions";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import { HorizontalDivider } from "../componentWrappers/helper_components";
import {
    HOMEPAGE_MIN_DATE,
    MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
    MAX_CHAPTER_COUNT_PER_MANGA,
    MANGA_MIN_COLLABORATOR_COUNT,
    MANGA_MAX_COLLABORATOR_COUNT,
    MANGA_MAX_RATING,
    MANGA_MIN_RATING,
    MANGA_MAX_TITLE_LEN,
    GALLERY_FETCH_TIMEOUT_DELAY,
} from "../globals";

function ShowMangaHomePage() {
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");

    const abortRef = useRef(null); // to abort the previously send requests
    const fetchTimeout = useRef(null); // for preventing rapid request sending in back to back filter changes
    const [manga_gallery, set_manga_gallery] = useState([]);
    const [all_tags, set_all_tags] = useState([]); // will store all tags
    const [selected_tags, set_selected_tags] = useState([]); // will contain currently selected tags
    const [next_page, set_next_page] = useState(null);
    const [loading, set_loading] = useState(true);
    const [loading_more, set_loading_more] = useState(false);

    const [ratings_range, set_ratings_range] = useState([
        MANGA_MIN_RATING,
        MANGA_MAX_RATING,
    ]);
    const [num_of_ratings_range, set_num_of_ratings_range] = useState([
        0,
        MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
    ]);
    const [num_of_chapters_range, set_num_of_chapters_range] = useState([
        0,
        MAX_CHAPTER_COUNT_PER_MANGA,
    ]);
    const [chapters_price_range, set_chapters_price_range] = useState([
        0,
        MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
    ]);
    const [num_of_collaborators_range, set_num_of_collaborators_range] =
        useState([MANGA_MIN_COLLABORATOR_COUNT, MANGA_MAX_COLLABORATOR_COUNT]);
    const [num_of_followers_range, set_num_of_followers_range] = useState([
        0,
        MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
    ]);
    const min_date = new Date(HOMEPAGE_MIN_DATE).getTime(); // Minimum: Jan 1, 2026
    const today = new Date(); // Maximum: tomorrow
    const max_date = new Date(
        today.getUTCFullYear(),
        today.getUTCMonth(),
        today.getUTCDate() + 1,
    ).getTime();
    const [start_dates_range, set_start_dates_range] = useState([
        min_date,
        max_date,
    ]);
    const [last_update_dates_range, set_last_update_dates_range] = useState([
        min_date,
        max_date,
    ]);

    const [searched_mangas, set_searched_mangas] = useState([]);
    const [search_text, set_search_text] = useState("");

    const [gallery_error_message, set_gallery_error_message] = useState("");
    const [text_search_error_message, set_text_search_error_message] =
        useState("");
    const [tags_error_message, set_tags_error_message] = useState("");

    // Sorting tags
    const all_sorts = [
        ...(logged_in_permission // include following lists if user is logged in
            ? [
                  { id: "profiles_following", label: "profiles following" },
                  {
                      id: "-profiles_following",
                      label: "profiles not following",
                  },
                  { id: "mangas_following", label: "mangas following" },
                  { id: "-mangas_following", label: "mangas not following" },
              ]
            : []),
        { id: "rating", label: "rating (+)" },
        { id: "-rating", label: "rating (-)" },
        { id: "num_of_chapters", label: "chapters (+)" },
        { id: "-num_of_chapters", label: "chapters (-)" },
        { id: "num_of_followers", label: "followers (+)" },
        { id: "-num_of_followers", label: "followers (-)" },
        { id: "num_of_ratings", label: "number of ratings (+)" },
        { id: "-num_of_ratings", label: "number of ratings (-)" },
        { id: "num_of_collaborators", label: "collaborators (+)" },
        { id: "-num_of_collaborators", label: "collaborators (-)" },
        { id: "start_date", label: "date (+)" },
        { id: "-start_date", label: "date (-)" },
        { id: "last_update_date", label: "update date (+)" },
        { id: "-last_update_date", label: "update date (-)" },
        { id: "chapters_price", label: "total price of chapters (+)" },
        { id: "-chapters_price", label: "total price of chapters (-)" },
    ];

    const [selected_sorts, set_selected_sorts] = useState(["last_update_date"]);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/manga/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    function construct_request_url() {
        const registered_ranges = [
            {
                range: ratings_range,
                min_limit: MANGA_MIN_RATING,
                max_limit: MANGA_MAX_RATING,
                min_prefix: "rating_min",
                max_prefix: "rating_max",
            },
            {
                range: num_of_ratings_range,
                min_limit: 0,
                max_limit: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "num_of_ratings_min",
                max_prefix: "num_of_ratings_max",
            },
            {
                range: num_of_chapters_range,
                min_limit: 0,
                max_limit: MAX_CHAPTER_COUNT_PER_MANGA,
                min_prefix: "num_of_chapters_min",
                max_prefix: "num_of_chapters_max",
            },
            {
                range: chapters_price_range,
                min_limit: 0,
                max_limit: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "chapters_price_min",
                max_prefix: "chapters_price_max",
            },
            {
                range: num_of_collaborators_range,
                min_limit: MANGA_MIN_COLLABORATOR_COUNT,
                max_limit: MANGA_MAX_COLLABORATOR_COUNT,
                min_prefix: "num_of_collaborators_min",
                max_prefix: "num_of_collaborators_max",
            },
            {
                range: num_of_followers_range,
                min_limit: 0,
                max_limit: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "num_of_followers_min",
                max_prefix: "num_of_followers_max",
            },
            {
                range: start_dates_range,
                min_limit: min_date,
                max_limit: max_date,
                min_prefix: "start_date_min",
                max_prefix: "start_date_max",
            },
            {
                range: last_update_dates_range,
                min_limit: min_date,
                max_limit: max_date,
                min_prefix: "last_update_date_min",
                max_prefix: "last_update_date_max",
            },
        ];

        return constructRequestUrl(
            "/api/manga/manga-gallery/",
            selected_tags,
            selected_sorts,
            registered_ranges,
        );
    }

    // Fetch mangas
    function fetch_mangas() {
        // Cancel previous request
        if (abortRef.current) {
            abortRef.current.abort();
        }

        const controller = new AbortController();
        abortRef.current = controller;

        set_manga_gallery([]);
        set_next_page(null);

        galleryFetchAndSet(
            construct_request_url(),
            set_manga_gallery,
            set_gallery_error_message,
            set_loading,
            set_next_page,
            "manga_gallery",
            controller.signal,
        );
    }

    function fetch_mangas_with_delay() {
        // runs the fetch command after GALLERY_FETCH_TIMEOUT_DELAY ms of no activity
        clearTimeout(fetchTimeout.current);
        fetchTimeout.current = setTimeout(() => {
            fetch_mangas();
        }, GALLERY_FETCH_TIMEOUT_DELAY);
    }

    // Initial fetch
    useEffect(() => {
        fetch_mangas();
    }, []);

    // for unmount cleanup
    useEffect(() => {
        return () => {
            if (abortRef.current) {
                abortRef.current.abort();
            }
        };
    }, []);

    // Refetch mangas when tags change
    useEffect(() => {
        fetch_mangas();
    }, [selected_tags, selected_sorts]);

    // Load more mangas with current filters
    async function load_more_mangas() {
        if (!next_page || loading_more) return;

        galleryFetchAndSet(
            next_page,
            set_manga_gallery,
            set_gallery_error_message,
            set_loading_more,
            set_next_page,
            "manga_gallery",
        );
    }

    useEffect(() => {
        return scrollDebounceHelper(load_more_mangas);
    }, [next_page, loading_more]);

    // async function handle_follow(manga_id) {
    //     try {
    //         const follow_response = await apiFetch(
    //             `/api/manga/follow-manga/${manga_id}/`,
    //             { method: "POST" },
    //         );
    //         const [follow_success_data, follow_error_message, follow_ok] =
    //             await handleFetch("manga_gallery", follow_response);

    //         if (follow_ok) {
    //             // Update the manga in state
    //             set_manga_gallery((prev) =>
    //                 prev.map((p) =>
    //                     p.id === manga_id
    //                         ? {
    //                               ...p,
    //                               is_user_following:
    //                                   follow_success_data.followed ??
    //                                   !p.is_user_following,
    //                               num_of_followers:
    //                                   p.num_of_followers +
    //                                   (follow_success_data.followed ? 1 : -1),
    //                           }
    //                         : p,
    //                 ),
    //             );
    //         } else {
    //             set_gallery_error_message(follow_error_message);
    //         }
    //     } catch (err) {
    //         set_gallery_error_message(
    //             err.message || "Network error during manga following.",
    //         );
    //     }
    // }

    async function handle_text_search() {
        if (!search_text.trim()) {
            set_searched_mangas([]);
            set_text_search_error_message("");
            return;
        }

        const search_url = `/api/manga/search-manga/${encodeURIComponent(search_text.trim())}/`;
        await setFetchAndSet(
            search_url,
            set_searched_mangas,
            set_text_search_error_message,
            "text_search",
        );
    }

    function render_sliders() {
        const ocfn = () => {
            fetch_mangas_with_delay();
        };
        const registered_sliders = [
            {
                label: "Rating",
                SliderType: IntegerSliderWrapper,
                range: ratings_range,
                min: MANGA_MIN_RATING,
                max: MANGA_MAX_RATING,
                step: 1,
                on_change_fn: (v) => set_ratings_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Number of Ratings",
                SliderType: IntegerSliderWrapper,
                range: num_of_ratings_range,
                min: 0,
                max: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 10,
                on_change_fn: (v) => set_num_of_ratings_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Number of Chapters",
                SliderType: IntegerSliderWrapper,
                range: num_of_chapters_range,
                min: 0,
                max: MAX_CHAPTER_COUNT_PER_MANGA,
                step: 10,
                on_change_fn: (v) => set_num_of_chapters_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Total Price of Chapters",
                SliderType: IntegerSliderWrapper,
                range: chapters_price_range,
                min: 0,
                max: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 100,
                on_change_fn: (v) => set_chapters_price_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Number of Collaborators",
                SliderType: IntegerSliderWrapper,
                range: num_of_collaborators_range,
                min: MANGA_MIN_COLLABORATOR_COUNT,
                max: MANGA_MAX_COLLABORATOR_COUNT,
                step: 1,
                on_change_fn: (v) => set_num_of_collaborators_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Number of Followers",
                SliderType: IntegerSliderWrapper,
                range: num_of_followers_range,
                min: 0,
                max: MANGA_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 10,
                on_change_fn: (v) => set_num_of_followers_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Start Date",
                SliderType: DateSliderWrapper,
                range: start_dates_range,
                min: min_date,
                max: max_date,
                step: 24 * 60 * 60 * 1000,
                on_change_fn: (v) => set_start_dates_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Last Update Date",
                SliderType: DateSliderWrapper,
                range: last_update_dates_range,
                min: min_date,
                max: max_date,
                step: 24 * 60 * 60 * 1000,
                on_change_fn: (v) => set_last_update_dates_range(v),
                on_commit_fn: ocfn,
            },
        ];

        return (
            <RegisteredSlidersDisplayWrapper
                registered_sliders={registered_sliders}
            />
        );
    }

    function render_text_search_inputs() {
        return (
            <div
                style={{
                    display: "flex",
                    alignItems: "flex-end",
                    gap: theme.spacing.sm,
                    padding: theme.spacing.sm,
                    flexDirection: "row", // Ensure side-by-side
                    alignItems: "stretch", // Forces children to fill vertical height
                }}
            >
                {/* Text input */}
                <div style={{ flex: 1 }}>
                    <TextInputWrapper
                        name="manga-search"
                        label="Search Manga by Title or ID"
                        value={search_text}
                        onChange={(e) => set_search_text(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault(); // Prevents adding a new line in the textarea
                                handle_text_search();
                            }
                        }}
                        maxLength={MANGA_MAX_TITLE_LEN}
                        fullWidth
                    />
                </div>

                <ButtonWrapper onClick={handle_text_search} text={"🔎"} />
            </div>
        );
    }

    function render_text_search() {
        if (text_search_error_message)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    {text_search_error_message}
                </div>
            );

        if (!searched_mangas.length) return null;

        return (
            <div
                style={{
                    width: "100%",
                    paddingInline: theme.spacing.md,
                }}
            >
                <Masonry columns={3} spacing={theme.spacing.lg}>
                    {searched_mangas.map((manga) => {
                        const meta_data = [
                            `🏷️ ${manga.tags.map((tag) => tag.label).join(", ")}`,
                            `⭐ ${manga.rating}`,
                            `📖 ${manga.num_of_chapters ?? 0} Chapters`,
                            `👤 ${manga.owner.profile_name}`,
                        ].filter(Boolean); // Removes the null entry if the user score isn't shown

                        return (
                            <div
                                key={manga.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                            >
                                <CardWrapper
                                    title={manga.title}
                                    to={`${manga.id}`}
                                    image={manga.image}
                                    meta_data={meta_data}
                                />
                            </div>
                        );
                    })}
                </Masonry>
            </div>
        );
    }

    function render_gallery() {
        if (loading) return <LoadSpinnerWrapper loading={true} />;

        if (gallery_error_message)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    {gallery_error_message}
                </div>
            );

        if (!manga_gallery.length)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    Collecting mangas...
                </div>
            );

        return (
            <div
                style={{
                    width: "100%",
                    paddingInline: theme.spacing.md,
                }}
            >
                <Masonry columns={3} spacing={theme.spacing.lg}>
                    {manga_gallery.map((manga) => {
                        const isFollowed = manga.is_user_following;

                        const meta_data = [
                            `🏷️ ${manga.tags.map((tag) => tag.label).join(", ")}`,
                            `${
                                manga.num_of_ratings === 0
                                    ? ""
                                    : `⭐ ${Number(manga.rating).toFixed(2) ?? 0} (${manga.num_of_ratings ?? 0})`
                            }`,
                            `📖 ${manga.num_of_chapters ?? 0} ${
                                manga.num_of_chapters > 0
                                    ? ` (${manga.total_price_of_all_chapters}${theme.coin})`
                                    : ""
                            }`,
                            `🗓️ ${manga.start_date ?? 0} / ${manga.last_update_date ?? 0}`,
                            `👥 ${manga.num_of_collaborators ?? 0}`,
                            `🔖 ${manga.num_of_followers ?? 0}`,
                        ].filter(Boolean); // Removes the null entry if the user score isn't shown

                        return (
                            <div
                                key={manga.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                            >
                                <CardWrapper
                                    title={manga.title}
                                    to={`${manga.id}`}
                                    image={manga.image}
                                    meta_data={meta_data}
                                />

                                {/* Follow Button
                                CHANGE THIS TO A SwitchWrapper in the future if needed
                                {logged_in_permission && (
                                    <div
                                        style={{
                                            marginTop: theme.spacing.sm,
                                            display: "flex",
                                            justifyContent: "center",
                                            width: "100%" 
                                        }}
                                    >
                                        <ButtonWrapper
                                            onClick={() => handle_follow(manga.id)}
                                            text={isFollowed ? "Unfollow" : "Follow"}
                                            visualVariant={isFollowed ? "outline" : "soft"}
                                        />
                                    </div>
                                )} */}
                            </div>
                        );
                    })}
                </Masonry>

                <LoadSpinnerWrapper loading={loading_more} />
            </div>
        );
    }

    function render_main() {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100vh",
                    backgroundColor: theme.colors.background.app,
                }}
            >
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

                {/* CONTENT AREA */}
                <div
                    style={{
                        display: "flex",
                        flex: 1,
                        gap: theme.spacing.xl,
                        padding: theme.spacing.lg,
                        overflow: "hidden",
                    }}
                >
                    {/* LEFT: CONTROLS */}
                    <div
                        style={{
                            width: "25%",
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.lg,
                            overflowY: "auto",
                            paddingRight: theme.spacing.md,
                        }}
                    >
                        <ControlPanelWrapper
                            create_permission={logged_in_permission}
                            create_button_text="Create Manga"
                            create_button_to="/manga/create-manga/"
                            tags_error_message={tags_error_message}
                            set_tags_error_message={() =>
                                set_tags_error_message("")
                            }
                            tags_error_title="Manga Tag Error"
                            all_tags={all_tags}
                            selected_tags={selected_tags}
                            on_tag_select={(id) =>
                                handleIdLabelItemSelect(id, set_selected_tags)
                            }
                            all_sorts={all_sorts}
                            selected_sorts={selected_sorts}
                            on_sort_select={(id) =>
                                handleSortIdLabelItemSelect(
                                    id,
                                    set_selected_sorts,
                                )
                            }
                            sliders={render_sliders()}
                        />
                    </div>

                    {/* RIGHT: GALLERY */}
                    <div
                        style={{
                            width: "75%",
                            flexGrow: 1,
                            overflowY: "auto",
                            overflowX: "hidden",
                        }}
                    >
                        {render_text_search_inputs()}
                        {render_text_search()}
                        <HorizontalDivider />
                        <div
                            style={{
                                marginTop: theme.spacing.md,
                            }}
                        >
                            <h1
                                style={{
                                    ...theme.styles.titleText,
                                    margin: 0,
                                    marginBottom: theme.spacing.md,
                                }}
                            >
                                Mangas
                            </h1>

                            {render_gallery()}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return render_main();
}

export default ShowMangaHomePage;
