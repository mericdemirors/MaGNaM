import React, { useState, useEffect, useRef } from "react";
import { Masonry } from "@mui/lab";

import CardWrapper from "../componentWrappers/CardWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import RegisteredSlidersDisplayWrapper from "../componentWrappers/RegisteredSlidersDisplayWrapper";
import DateSliderWrapper from "../componentWrappers/DateSliderWrapper";
import ControlPanelWrapper from "../componentWrappers/ControlPanelWrapper";
import HasPermission from "../utils/HasPermission";
import LoadSpinnerWrapper from "../componentWrappers/LoadSpinnerWrapper";
import { useTheme } from "../context/ThemeContext";
import {
    setFetchAndSet,
    galleryFetchAndSet,
    handleIdLabelItemSelect,
    scrollDebounceHelper,
    handleSortIdLabelItemSelect,
    constructRequestUrl,
} from "../utils/helper_functions";
import {
    COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX,
    COMPETITION_HOMEPAGE_PRICE_MAX_RANGE,
    HOMEPAGE_MAX_DATE,
    HOMEPAGE_MIN_DATE,
    GALLERY_FETCH_TIMEOUT_DELAY,
} from "../globals";

function ShowCompetitionHomePage() {
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");
    const admin_permission = HasPermission("admin");

    const abortRef = useRef(null); // to abort the previously send requests
    const fetchTimeout = useRef(null); // for preventing rapid request sending in back to back filter changes
    const [competition_gallery, set_competition_gallery] = useState([]);
    const [all_tags, set_all_tags] = useState([]); // will store all tags
    const [selected_tags, set_selected_tags] = useState([]); // will contain currently selected tags
    const [next_page, set_next_page] = useState(null);
    const [loading, set_loading] = useState(true);
    const [loading_more, set_loading_more] = useState(false);

    const [num_of_portfolio_submits_range, set_num_of_portfolio_submits_range] =
        useState([0, COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX]);
    const [num_of_chapter_submits_range, set_num_of_chapter_submits_range] =
        useState([0, COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX]);
    const [price_range, set_price_range] = useState([
        0,
        COMPETITION_HOMEPAGE_PRICE_MAX_RANGE,
    ]);

    const min_date = new Date(HOMEPAGE_MIN_DATE).getTime();
    const max_date = new Date(HOMEPAGE_MAX_DATE).getTime();
    const [start_dates_range, set_start_dates_range] = useState([
        min_date,
        max_date,
    ]);
    const [end_dates_range, set_end_dates_range] = useState([
        min_date,
        max_date,
    ]);

    const [gallery_error_message, set_gallery_error_message] = useState("");
    const [tags_error_message, set_tags_error_message] = useState("");

    // Sorting tags
    const all_sorts = [
        { id: "start_date", label: "start (+)" },
        { id: "-start_date", label: "start (-)" },
        { id: "end_date", label: "end (+)" },
        { id: "-end_date", label: "end (-)" },
        { id: "price", label: "entry fee (+)" },
        { id: "-price", label: "entry fee (-)" },
        { id: "num_of_portfolio_submits", label: "portfolios (+)" },
        { id: "-num_of_portfolio_submits", label: "portfolios (-)" },
        { id: "num_of_chapter_submits", label: "chapters (+)" },
        { id: "-num_of_chapter_submits", label: "chapters (-)" },
    ];
    const [selected_sorts, set_selected_sorts] = useState(["end_date"]);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/competition/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    function construct_request_url() {
        const registered_ranges = [
            {
                range: num_of_portfolio_submits_range,
                min_limit: 0,
                max_limit: COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "num_of_portfolio_submits_min",
                max_prefix: "num_of_portfolio_submits_max",
            },
            {
                range: num_of_chapter_submits_range,
                min_limit: 0,
                max_limit: COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "num_of_chapter_submits_min",
                max_prefix: "num_of_chapter_submits_max",
            },
            {
                range: price_range,
                min_limit: 0,
                max_limit: COMPETITION_HOMEPAGE_PRICE_MAX_RANGE,
                min_prefix: "price_min",
                max_prefix: "price_max",
            },
            {
                range: start_dates_range,
                min_limit: min_date,
                max_limit: max_date,
                min_prefix: "start_date_min",
                max_prefix: "start_date_max",
            },
            {
                range: end_dates_range,
                min_limit: min_date,
                max_limit: max_date,
                min_prefix: "end_date_min",
                max_prefix: "end_date_max",
            },
        ];

        return constructRequestUrl(
            "/api/competition/competition-gallery/",
            selected_tags,
            selected_sorts,
            registered_ranges,
        );
    }

    // Fetch competitions
    function fetch_competitions() {
        // Cancel previous request
        if (abortRef.current) {
            abortRef.current.abort();
        }

        const controller = new AbortController();
        abortRef.current = controller;

        set_competition_gallery([]);
        set_next_page(null);

        galleryFetchAndSet(
            construct_request_url(),
            set_competition_gallery,
            set_gallery_error_message,
            set_loading,
            set_next_page,
            "competition_gallery",
            controller.signal,
        );
    }

    function fetch_competitions_with_delay() {
        // runs the fetch command after GALLERY_FETCH_TIMEOUT_DELAY ms of no activity
        clearTimeout(fetchTimeout.current);
        fetchTimeout.current = setTimeout(() => {
            fetch_competitions();
        }, GALLERY_FETCH_TIMEOUT_DELAY);
    }

    // Initial fetch
    useEffect(() => {
        fetch_competitions();
    }, []);

    // for unmount cleanup
    useEffect(() => {
        return () => {
            if (abortRef.current) {
                abortRef.current.abort();
            }
        };
    }, []);

    // Refetch competitions when tags change
    useEffect(() => {
        fetch_competitions();
    }, [selected_tags, selected_sorts]);

    // Load more competitions with current filters
    async function load_more_competitions() {
        if (!next_page || loading_more) return;

        galleryFetchAndSet(
            next_page,
            set_competition_gallery,
            set_gallery_error_message,
            set_loading_more,
            set_next_page,
            "competition_gallery",
        );
    }

    useEffect(() => {
        return scrollDebounceHelper(load_more_competitions);
    }, [next_page, loading_more]);

    function render_sliders() {
        const ocfn = () => {
            fetch_competitions_with_delay();
        };

        const registered_sliders = [
            {
                label: "Portfolio Submissions",
                SliderType: IntegerSliderWrapper,
                range: num_of_portfolio_submits_range,
                min: 0,
                max: COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 10,
                on_change_fn: (v) => set_num_of_portfolio_submits_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Chapter Submissions",
                SliderType: IntegerSliderWrapper,
                range: num_of_chapter_submits_range,
                min: 0,
                max: COMPETITION_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 10,
                on_change_fn: (v) => set_num_of_chapter_submits_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Price",
                SliderType: IntegerSliderWrapper,
                range: price_range,
                min: 0,
                max: COMPETITION_HOMEPAGE_PRICE_MAX_RANGE,
                step: 10,
                on_change_fn: (v) => set_price_range(v),
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
                label: "End Date",
                SliderType: DateSliderWrapper,
                range: end_dates_range,
                min: min_date,
                max: max_date,
                step: 24 * 60 * 60 * 1000,
                on_change_fn: (v) => set_end_dates_range(v),
                on_commit_fn: ocfn,
            },
        ];

        return (
            <RegisteredSlidersDisplayWrapper
                registered_sliders={registered_sliders}
            />
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

        if (!competition_gallery.length)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    Collecting competitions...
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
                    {competition_gallery.map((competition) => {
                        const meta_data = [
                            `🏷️ ${competition.tags.map((tag) => tag.label).join(", ")}`,
                            `🗓️ ${competition.start_date ?? 0} - ${competition.end_date ?? 0}`,
                        ];

                        return (
                            <div
                                key={competition.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                            >
                                <CardWrapper
                                    title={competition.title}
                                    to={`${competition.id}`}
                                    image={competition.image}
                                    meta_data={meta_data}
                                />
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
                            create_permission={admin_permission}
                            create_button_text="Create Competition"
                            create_button_to="/competition/create-competition/"
                            tags_error_message={tags_error_message}
                            set_tags_error_message={() =>
                                set_tags_error_message("")
                            }
                            tags_error_title="Competition Tag Error"
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
                        <h1
                            style={{
                                ...theme.styles.titleText,
                                margin: 0,
                                marginBottom: theme.spacing.md,
                            }}
                        >
                            Competitions
                        </h1>

                        {render_gallery()}
                    </div>
                </div>
            </div>
        );
    }

    return render_main();
}

export default ShowCompetitionHomePage;
