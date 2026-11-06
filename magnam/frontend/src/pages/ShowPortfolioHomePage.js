import React, { useState, useEffect, useRef } from "react";
import { Masonry } from "@mui/lab";

import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import CardWrapper from "../componentWrappers/CardWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import RegisteredSlidersDisplayWrapper from "../componentWrappers/RegisteredSlidersDisplayWrapper";
import DateSliderWrapper from "../componentWrappers/DateSliderWrapper";
import ControlPanelWrapper from "../componentWrappers/ControlPanelWrapper";
import { useTheme } from "../context/ThemeContext";
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
import {
    HOMEPAGE_MIN_DATE,
    MAX_WORK_COUNT_PER_PORTFOLIO,
    PORTFOLIO_HOMEPAGE_INTEGER_RANGE_MAX,
    GALLERY_FETCH_TIMEOUT_DELAY,
} from "../globals";

function ShowPortfolioHomePage() {
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");

    const abortRef = useRef(null); // to abort the previously send requests
    const fetchTimeout = useRef(null); // for preventing rapid request sending in back to back filter changes
    const [portfolio_gallery, set_portfolio_gallery] = useState([]);
    const [all_tags, set_all_tags] = useState([]); // will store all tags
    const [selected_tags, set_selected_tags] = useState([]); // will contain currently selected tags
    const [next_page, set_next_page] = useState(null);
    const [loading, set_loading] = useState(true);
    const [loading_more, set_loading_more] = useState(false);

    const [num_of_likes_range, set_num_of_likes_range] = useState([
        0,
        PORTFOLIO_HOMEPAGE_INTEGER_RANGE_MAX,
    ]);
    const [num_of_works_range, set_num_of_works_range] = useState([
        0,
        MAX_WORK_COUNT_PER_PORTFOLIO,
    ]);
    const min_date = new Date(HOMEPAGE_MIN_DATE).getTime(); // Minimum: Jan 1, 2026
    const today = new Date(); // Maximum: tomorrow
    const max_date = new Date(
        today.getUTCFullYear(),
        today.getUTCMonth(),
        today.getUTCDate() + 1,
    ).getTime();
    const [dates_range, set_dates_range] = useState([min_date, max_date]);

    const [gallery_error_message, set_gallery_error_message] = useState("");
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
              ]
            : []),
        { id: "num_of_likes", label: "likes (+)" },
        { id: "-num_of_likes", label: "likes (-)" },
        { id: "num_of_works", label: "works (+)" },
        { id: "-num_of_works", label: "works (-)" },
        { id: "date", label: "date (+)" },
        { id: "-date", label: "date (-)" },
    ];
    const [selected_sorts, set_selected_sorts] = useState(["date"]);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/portfolio/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    function construct_request_url() {
        const registered_ranges = [
            {
                range: num_of_likes_range,
                min_limit: 0,
                max_limit: PORTFOLIO_HOMEPAGE_INTEGER_RANGE_MAX,
                min_prefix: "num_of_likes_min",
                max_prefix: "num_of_likes_max",
            },
            {
                range: num_of_works_range,
                min_limit: 0,
                max_limit: MAX_WORK_COUNT_PER_PORTFOLIO,
                min_prefix: "num_of_works_min",
                max_prefix: "num_of_works_max",
            },
            {
                range: dates_range,
                min_limit: min_date,
                max_limit: max_date,
                min_prefix: "date_min",
                max_prefix: "date_max",
            },
        ];

        return constructRequestUrl(
            "/api/portfolio/portfolio-gallery/",
            selected_tags,
            selected_sorts,
            registered_ranges,
        );
    }

    // Fetch portfolios
    function fetch_portfolios() {
        // Cancel previous request
        if (abortRef.current) {
            abortRef.current.abort();
        }

        const controller = new AbortController();
        abortRef.current = controller;

        set_portfolio_gallery([]);
        set_next_page(null);

        galleryFetchAndSet(
            construct_request_url(),
            set_portfolio_gallery,
            set_gallery_error_message,
            set_loading,
            set_next_page,
            "portfolio_gallery",
            controller.signal,
        );
    }

    function fetch_portfolios_with_delay() {
        // runs the fetch command after GALLERY_FETCH_TIMEOUT_DELAY ms of no activity
        clearTimeout(fetchTimeout.current);
        fetchTimeout.current = setTimeout(() => {
            fetch_portfolios();
        }, GALLERY_FETCH_TIMEOUT_DELAY);
    }

    // Initial fetch
    useEffect(() => {
        fetch_portfolios();
    }, []);

    // for unmount cleanup
    useEffect(() => {
        return () => {
            if (abortRef.current) {
                abortRef.current.abort();
            }
        };
    }, []);

    // Refetch portfolios when tags change
    useEffect(() => {
        fetch_portfolios();
    }, [selected_tags, selected_sorts]);

    // Load more portfolios with current filters
    async function load_more_portfolios() {
        if (!next_page || loading_more) return;

        galleryFetchAndSet(
            next_page,
            set_portfolio_gallery,
            set_gallery_error_message,
            set_loading_more,
            set_next_page,
            "portfolio_gallery",
        );
    }

    useEffect(() => {
        return scrollDebounceHelper(load_more_portfolios);
    }, [next_page, loading_more]);

    // async function handle_like(portfolio_id) {
    //     try {
    //         const like_response = await apiFetch(
    //             `/api/portfolio/like-portfolio/${portfolio_id}/`,
    //             { method: "POST" },
    //         );
    //         const [like_success_data, like_error_message, like_ok] =
    //             await handleFetch("portfolio_like", like_response);

    //         if (like_ok) {
    //             // Update the portfolio in state
    //             set_portfolio_gallery((prev) =>
    //                 prev.map((p) =>
    //                     p.id === portfolio_id
    //                         ? {
    //                               ...p,
    //                               is_user_liked: like_success_data.liked,
    //                               num_of_likes:
    //                                   p.num_of_likes +
    //                                   (like_success_data.liked ? 1 : -1),
    //                           }
    //                         : p,
    //                 ),
    //             );
    //         } else {
    //             set_gallery_error_message(like_error_message);
    //         }
    //     } catch (err) {
    //         set_gallery_error_message(
    //             err.message || "Network error during portfolio liking.",
    //         );
    //     }
    // }

    function render_sliders() {
        const ocfn = () => {
            fetch_portfolios_with_delay();
        };
        const registered_sliders = [
            {
                label: "Number of Likes",
                SliderType: IntegerSliderWrapper,
                range: num_of_likes_range,
                min: 0,
                max: PORTFOLIO_HOMEPAGE_INTEGER_RANGE_MAX,
                step: 10,
                on_change_fn: (v) => set_num_of_likes_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Number of Works",
                SliderType: IntegerSliderWrapper,
                range: num_of_works_range,
                min: 0,
                max: MAX_WORK_COUNT_PER_PORTFOLIO,
                step: 5,
                on_change_fn: (v) => set_num_of_works_range(v),
                on_commit_fn: ocfn,
            },
            {
                label: "Creation Date",
                SliderType: DateSliderWrapper,
                range: dates_range,
                min: min_date,
                max: max_date,
                step: 24 * 60 * 60 * 1000,
                on_change_fn: (v) => set_dates_range(v),
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

        if (!portfolio_gallery.length)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    Collecting portfolios...
                </div>
            );

        return (
            <div
                style={{
                    width: "100%",
                    paddingRight: theme.spacing.md,
                }}
            >
                <Masonry columns={3} spacing={theme.spacing.lg}>
                    {portfolio_gallery.map((portfolio) => {
                        const isLiked = portfolio.is_user_liked;

                        const meta_data = [
                            `🏷️ ${portfolio.tags.map((tag) => tag.label).join(", ")}`,
                            `❤️ ${portfolio.num_of_likes ?? 0}`,
                            `📁 ${portfolio.num_of_works ?? 0}`,
                            `🗓️ ${portfolio.date ?? 0}`,
                        ];

                        return (
                            <div
                                key={portfolio.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                            >
                                <CardWrapper
                                    title={portfolio.title}
                                    to={`${portfolio.id}`}
                                    image={portfolio.image}
                                    meta_data={meta_data}
                                />

                                {/* Like Button
                                CHANGE THIS TO A SwitchWrapper in the future if needed
                                {logged_in_permission && (
                                    <div 
                                        style={{ 
                                            marginTop: theme.spacing.sm, 
                                            marginBottom: theme.spacing.sm,
                                            display: "flex", 
                                            justifyContent: "center"
                                        }}
                                    >
                                        <ButtonWrapper
                                            onClick={() => handle_like(portfolio.id)}
                                            text={isLiked ? "Unlike" : "Like"}
                                            visualVariant={isLiked ? "outline" : "soft"}
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
                            create_button_text="Create Portfolio"
                            create_button_to="/portfolio/create-portfolio/"
                            tags_error_message={tags_error_message}
                            set_tags_error_message={() =>
                                set_tags_error_message("")
                            }
                            tags_error_title="Portfolio Tag Error"
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
                            Portfolios
                        </h1>

                        {render_gallery()}
                    </div>
                </div>
            </div>
        );
    }

    return render_main();
}

export default ShowPortfolioHomePage;
