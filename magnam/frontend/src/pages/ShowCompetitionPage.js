import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Masonry } from "@mui/lab";

import CreateCompetitionPage from "./CreateCompetitionPage";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import CardWrapper from "../componentWrappers/CardWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import TopBarWrapper from "../componentWrappers/TopBarWrapper";
import HasPermission from "../utils/HasPermission";
import { useTheme } from "../context/ThemeContext";
import { apiFetch, handleFetch } from "../utils/csrf";
import { parsed_link_injected_text } from "../componentWrappers/helper_components";
import {
    HorizontalDivider,
    SectionLabel,
    render_links,
} from "../componentWrappers/helper_components";

function ShowCompetitionPage() {
    const { competition_id: competition_id_from_url } = useParams();
    const { theme } = useTheme();

    const logged_in_permission = HasPermission("logged_in");
    const admin_permission = HasPermission("admin");

    const [competition, set_competition] = useState({
        id: -1,
        title: "",
        description: "",
        image: null,
        links: "",
        start_date: null,
        end_date: null,
        price: 0,
        tags: [],
        chapter_submits: [],
        portfolio_submits: [],
        chapter_wins: [],
        portfolio_wins: [],
        user_submitted_item: "",
        num_of_chapter_submits: 0,
        num_of_portfolio_submits: 0,
    });

    const [profile_balance, set_profile_balance] = useState(-1);

    const [
        user_owned_submitted_chapters_and_portfolios,
        set_user_owned_submitted_chapters_and_portfolios,
    ] = useState([]);
    const [owned_item_to_submit, set_owned_item_to_submit] = useState("");

    const [show_edit, set_show_edit_page] = useState(false);

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");

    const get_competition_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_competition_response = await apiFetch(
                    `/api/competition/get-competition/${competition_id_from_url}/`,
                    options,
                );
                const [
                    get_competition_success_data,
                    get_competition_error_message,
                    get_competition_ok,
                ] = await handleFetch(
                    "get_competition",
                    get_competition_response,
                );

                if (get_competition_ok) {
                    set_competition((prev) => ({
                        id: get_competition_success_data.id,
                        title: get_competition_success_data.title ?? "",
                        description:
                            get_competition_success_data.description ?? "",
                        image: get_competition_success_data.image ?? null,
                        links: Array.isArray(get_competition_success_data.links)
                            ? get_competition_success_data.links.join(" ")
                            : "",
                        start_date:
                            get_competition_success_data.start_date ?? null,
                        end_date: get_competition_success_data.end_date ?? null,
                        price: get_competition_success_data.price ?? 0,
                        tags: get_competition_success_data.tags ?? [],
                        chapter_submits:
                            get_competition_success_data.chapter_submits ?? [],
                        portfolio_submits:
                            get_competition_success_data.portfolio_submits ??
                            [],
                        chapter_wins:
                            get_competition_success_data.chapter_wins ?? [],
                        portfolio_wins:
                            get_competition_success_data.portfolio_wins ?? [],
                        user_submitted_item:
                            get_competition_success_data.user_submitted_item ??
                            "",
                        num_of_chapter_submits:
                            get_competition_success_data.num_of_chapter_submits ??
                            0,
                        num_of_portfolio_submits:
                            get_competition_success_data.num_of_portfolio_submits ??
                            0,
                    }));
                    set_profile_balance(
                        get_competition_success_data.profile_balance,
                    );
                    set_show_edit_page(false);
                    set_owned_item_to_submit(
                        get_competition_success_data.user_submitted_item,
                    );
                    set_error_message("");
                } else {
                    set_error_message(get_competition_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during competition fetch.",
                );
            }
        },
        [competition_id_from_url],
    );

    function is_active() {
        const now = new Date();
        const start = new Date(competition.start_date);
        const end = new Date(competition.end_date);
        end.setHours(23, 59, 59);

        if (now < start || now > end) return false;
        return true;
    }

    // fetch owned items
    async function get_owned_chapters_and_portfolios() {
        try {
            const c_and_p_response = await apiFetch(
                "/api/profile/owned-chapters-and-portfolios/",
                { method: "GET" },
            );
            const [c_and_p_data, c_and_p_errorMessage, c_and_p_ok] =
                await handleFetch(
                    "owned_chapters_and_portfolios",
                    c_and_p_response,
                );

            if (c_and_p_ok) {
                const chapters = c_and_p_data.chapters.map((ch) => ({
                    id: `chapter_${ch.id}`,
                    label: `chapter ${ch.title} from ${ch.manga} : ${ch.no}`,
                }));

                const portfolios = c_and_p_data.portfolios.map((pf) => ({
                    id: `portfolio_${pf.id}`,
                    label: `portfolio ${pf.title}`,
                }));

                set_user_owned_submitted_chapters_and_portfolios([
                    ...chapters,
                    ...portfolios,
                ]);
                set_error_message("");
            } else {
                set_error_message(c_and_p_errorMessage);
            }
        } catch (err) {
            set_error_message(
                err.message ||
                    `Network error during owned chapters and portfolios fetch.`,
            );
        }
    }

    // Initial fetch
    useEffect(() => {
        const controller = new AbortController();
        get_competition_details(controller.signal);
        get_owned_chapters_and_portfolios();

        return () => controller.abort();
    }, [competition_id_from_url, get_competition_details]);

    async function handle_submit(is_confirmed = false) {
        if (!is_active()) {
            return;
        }
        const submission_price = competition.user_submitted_item
            ? Math.floor(competition.price / 2)
            : competition.price;
        if (profile_balance < submission_price && !admin_permission) {
            set_error_message(
                `Submission price is ${submission_price}${theme.coin} but you have ${profile_balance}${theme.coin}`,
            );
            return;
        }

        if (!asking_for_confirmation) {
            set_asking_for_confirmation(true);
        } else if (!is_confirmed) {
            set_asking_for_confirmation(false);
        } else if (is_confirmed) {
            set_asking_for_confirmation(false);
            try {
                const submit_response = await apiFetch(
                    `/api/competition/submit/${competition_id_from_url}/${owned_item_to_submit}/`,
                    { method: "POST" },
                );
                const [submit_success_data, submit_error_message, submit_ok] =
                    await handleFetch("submit", submit_response);

                if (submit_ok) {
                    const { submitted, removed, new_balance } =
                        submit_success_data;

                    set_profile_balance(new_balance);

                    set_competition((prev) => {
                        let chapters = [...prev.chapter_submits];
                        let portfolios = [...prev.portfolio_submits];
                        let num_of_chapters = prev.num_of_chapter_submits;
                        let num_of_portfolios = prev.num_of_portfolio_submits;

                        if (removed) {
                            // did we remove some old submission
                            if ("manga_id" in removed) {
                                chapters = chapters.filter(
                                    (ch) => ch.id !== removed.id,
                                );
                                num_of_chapters = num_of_chapters - 1;
                            } else {
                                portfolios = portfolios.filter(
                                    (pf) => pf.id !== removed.id,
                                );
                                num_of_portfolios = num_of_portfolios - 1;
                            }
                        }

                        if (submitted) {
                            // submitted is always full in a success
                            if ("manga_id" in submitted) {
                                chapters.push(submitted);
                                num_of_chapters = num_of_chapters + 1;
                            } else {
                                portfolios.push(submitted);
                                num_of_portfolios = num_of_portfolios + 1;
                            }
                        }

                        return {
                            ...prev,
                            chapter_submits: chapters,
                            portfolio_submits: portfolios,
                            user_submitted_item: owned_item_to_submit,
                            num_of_chapter_submits: num_of_chapters,
                            num_of_portfolio_submits: num_of_portfolios,
                        };
                    });

                    set_error_message("");
                } else {
                    set_error_message(submit_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during competition submit.",
                );
            }
        }
    }

    async function handle_win(item_str) {
        try {
            const win_response = await apiFetch(
                `/api/competition/winner/${competition_id_from_url}/${item_str}/`,
                { method: "POST" },
            );
            const [win_success_data, win_error_message, win_ok] =
                await handleFetch("win", win_response);

            if (win_ok) {
                const { winner } = win_success_data;
                set_competition((prev) => {
                    let chapters = [...prev.chapter_wins];
                    let portfolios = [...prev.portfolio_wins];

                    if ("manga_id" in winner) {
                        chapters.push(winner);
                    } else {
                        portfolios.push(winner);
                    }

                    return {
                        ...prev,
                        chapter_wins: chapters,
                        portfolio_wins: portfolios,
                    };
                });

                set_error_message("");
            } else {
                set_error_message(win_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during competition win.",
            );
        }
    }

    async function handle_lose(item_str) {
        try {
            const lose_response = await apiFetch(
                `/api/competition/loser/${competition_id_from_url}/${item_str}/`,
                { method: "POST" },
            );
            const [lose_success_data, lose_error_message, lose_ok] =
                await handleFetch("lose", lose_response);

            if (lose_ok) {
                const { loser } = lose_success_data;
                set_competition((prev) => {
                    let chapters = [...prev.chapter_wins];
                    let portfolios = [...prev.portfolio_wins];

                    if ("manga_id" in loser) {
                        chapters = chapters.filter(
                            (chapter) => chapter.id !== loser.id,
                        );
                    } else {
                        portfolios = portfolios.filter(
                            (portfolio) => portfolio.id !== loser.id,
                        );
                    }

                    return {
                        ...prev,
                        chapter_wins: chapters,
                        portfolio_wins: portfolios,
                    };
                });

                set_error_message("");
            } else {
                set_error_message(lose_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during competition lose.",
            );
        }
    }

    function render_competition_section(itemType, isWinnerView) {
        const isChapter = itemType === "chapter";

        const listKey = isWinnerView
            ? `${itemType}_wins`
            : `${itemType}_submits`;

        const data = competition[listKey] || [];

        // Winner visibility guard
        if (isWinnerView && !(!is_active() || admin_permission)) return null;

        // Winner IDs (to prevent duplicate selection)
        const winIds = new Set(
            competition[`${itemType}_wins`]?.map((item) => item.id) || [],
        );

        const countLabel = !isWinnerView
            ? ` (${competition[`num_of_${itemType}_submits`]})`
            : "";

        const title = `${isWinnerView ? "Winner" : "Submitted"} ${
            isChapter ? "Chapters" : "Portfolios"
        }${countLabel}`;

        return (
            <div
                style={{
                    marginBottom: theme.spacing.xxl,
                    padding: theme.spacing.xl,
                    backgroundColor: theme.colors.background.app,
                    borderRadius: theme.radius.xl,
                }}
            >
                {/* Section Title */}
                <div
                    style={{
                        ...theme.styles.subtitleText,
                        textAlign: "center",
                        marginBottom: theme.spacing.sm,
                    }}
                >
                    {title}
                </div>

                <div
                    style={{
                        borderRadius: theme.radius.xl,
                        maxHeight: theme.dimensions.xxxl,
                        overflowY: "auto",
                    }}
                >
                    {/* Masonry Gallery */}
                    <Masonry columns={4} spacing={2}>
                        {data.map((item) => {
                            const isAlreadyWinner = winIds.has(item.id);

                            const showWinnerBtn =
                                admin_permission &&
                                !isWinnerView &&
                                !isAlreadyWinner;

                            const showLoserBtn =
                                admin_permission && isWinnerView;

                            return (
                                <div
                                    key={`${isWinnerView ? "win" : "sub"}_${itemType}_${item.id}`}
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        gap: theme.spacing.sm,
                                    }}
                                >
                                    {/* Content Card */}
                                    <div
                                        style={{
                                            transition: theme.transition.normal,
                                        }}
                                    >
                                        <CardWrapper
                                            title={item.title}
                                            image={
                                                isChapter
                                                    ? item.manga_image
                                                    : item.image
                                            }
                                            meta_data={
                                                isChapter
                                                    ? `(from ${item.manga_title} : ${item.no})`
                                                    : ""
                                            }
                                            to={
                                                isChapter
                                                    ? `/read-manga/${item.manga_id}/${item.id}/`
                                                    : `/portfolio/${item.id}/`
                                            }
                                        />
                                    </div>

                                    {/* Admin Controls (quiet, secondary) */}
                                    {(showWinnerBtn || showLoserBtn) && (
                                        <div
                                            style={{
                                                display: "flex",
                                                justifyContent: "center",
                                            }}
                                        >
                                            <ButtonWrapper
                                                text={
                                                    isWinnerView
                                                        ? "Select Loser"
                                                        : "Select Winner"
                                                }
                                                onClick={() =>
                                                    isWinnerView
                                                        ? handle_lose(
                                                              `${itemType}_${item.id}`,
                                                          )
                                                        : handle_win(
                                                              `${itemType}_${item.id}`,
                                                          )
                                                }
                                            />
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </Masonry>
                </div>
            </div>
        );
    }

    function render_right_column() {
        // if competition is closed
        // if user hasn't selected something or selection is on the current submit
        const is_button_disabled =
            !is_active() ||
            owned_item_to_submit === "" ||
            competition.user_submitted_item === owned_item_to_submit;
        const submission_price = competition.user_submitted_item
            ? Math.floor(competition.price / 2)
            : competition.price;
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.xl,
                    height: "100%",
                    overflowX: "hidden",
                }}
            >
                {/* Submission Panel */}
                <div
                    style={{
                        padding: theme.spacing.lg,
                        backgroundColor: theme.colors.background.surface,
                        borderRadius: theme.radius.lg,
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.lg,
                            maxWidth: theme.dimensions.md,
                            margin: "0 auto",
                        }}
                    >
                        <SectionLabel
                            text={`Submission ${
                                is_active()
                                    ? `(Fee: ${submission_price}${theme.coin})`
                                    : "(Competition is not open)"
                            }`}
                        />

                        <div
                            style={{
                                maxHeight: theme.dimensions.xl,
                                overflowY: "auto",
                            }}
                        >
                            <MultipleChoiceSelectionWrapper
                                all_choices={
                                    user_owned_submitted_chapters_and_portfolios
                                }
                                selected_choices={[owned_item_to_submit]}
                                handle_choice_select={(id) => {
                                    if (!is_active()) return;
                                    set_owned_item_to_submit((prev) =>
                                        prev === id ? "" : id,
                                    );
                                }}
                            />
                        </div>

                        <div
                            style={{
                                display: "flex",
                                justifyContent: "center",
                                marginTop: theme.spacing.sm,
                            }}
                        >
                            <ButtonWrapper
                                onClick={handle_submit}
                                disabled={is_button_disabled}
                                visualVariant={
                                    is_button_disabled ? "outline" : "soft"
                                }
                                text="Submit to Competition"
                            />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    function render_main() {
        if (admin_permission && show_edit) {
            const tag_ids = competition.tags.map((tag) => tag.id);
            return (
                <div>
                    <CreateCompetitionPage
                        id={competition.id}
                        title={competition.title}
                        description={competition.description}
                        image={competition.image}
                        links={competition.links}
                        price={competition.price}
                        start_date={Date.parse(competition.start_date)}
                        end_date={Date.parse(competition.end_date)}
                        tags={tag_ids}
                        edit={true}
                        cancel_edit_func={() => set_show_edit_page(false)}
                        edit_callback={get_competition_details}
                    />
                </div>
            );
        }

        return (
            <div>
                {/* Navigation Bar */}
                <div
                    style={{
                        position: "sticky",
                        top: 0,
                        zIndex: 1000,
                        width: "100%",
                        backgroundColor: theme.colors.background.app, // Ensure it has a solid background
                    }}
                >
                    <NavigationBarWrapper
                        logged_in_permission={logged_in_permission}
                        profile_balance={profile_balance}
                    />
                </div>

                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "2fr 1fr", // Left dominates
                        gap: theme.spacing.xl,
                        padding: theme.spacing.xl,
                    }}
                >
                    {/* ================= LEFT COLUMN ================= */}
                    <div
                        style={{
                            display: "flex",
                            gap: theme.spacing.lg,
                            alignItems: "flex-start",
                        }}
                    >
                        {/* Main Image */}
                        <div style={{ flex: 1.2, width: "60%" }}>
                            {competition.image && (
                                <img
                                    src={competition.image}
                                    alt={competition.title}
                                    loading="lazy"
                                    style={{
                                        width: "100%",
                                        borderRadius: theme.radius.lg,
                                        boxShadow: theme.colors.shadow.card,
                                        transition: theme.transition.normal,
                                    }}
                                />
                            )}
                        </div>

                        {/* Metadata, Profile & Description */}
                        <div style={{ flex: 1, width: "40%" }}>
                            <TopBarWrapper
                                title={competition.title}
                                metadata={
                                    <>
                                        <span style={theme.styles.subtitleText}>
                                            🗓️ {competition.start_date} -{" "}
                                            {competition.end_date},{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            {competition.price}
                                            {theme.coin},{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            {competition.num_of_chapter_submits}{" "}
                                            chapter
                                            {`${competition.num_of_chapter_submits > 1 ? "s" : ""}`}
                                            ,{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            {
                                                competition.num_of_portfolio_submits
                                            }{" "}
                                            portfolio
                                            {`${competition.num_of_portfolio_submits > 1 ? "s" : ""}`}{" "}
                                        </span>
                                    </>
                                }
                                tags={competition.tags.map((tag) => tag.label)}
                            />

                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: theme.spacing.sm,
                                }}
                            >
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: theme.spacing.lg,
                                        width: "fit-content",
                                        padding: theme.spacing.md,
                                    }}
                                >
                                    {admin_permission && (
                                        <ButtonWrapper
                                            onClick={() =>
                                                set_show_edit_page(true)
                                            }
                                            text="Edit Competition"
                                            visualVariant="outline"
                                        />
                                    )}
                                </div>
                            </div>

                            {/* Description Card */}
                            <div
                                style={{
                                    marginTop: theme.spacing.md,
                                    padding: theme.spacing.md,
                                    borderRadius: theme.radius.md,
                                    backgroundColor:
                                        theme.colors.background.app,
                                    boxShadow: theme.colors.shadow.card,
                                }}
                            >
                                {parsed_link_injected_text(
                                    competition.description,
                                    theme,
                                )}
                            </div>

                            <HorizontalDivider />

                            {/* Links (full width, below) */}
                            {render_links({ links: competition.links })}
                        </div>
                    </div>

                    {/* ================= RIGHT COLUMN ================= */}
                    <div
                        style={{
                            paddingLeft: theme.spacing.lg,
                        }}
                    >
                        {logged_in_permission && render_right_column()}
                    </div>

                    {/* ================= WORKS GALLERY ================= */}
                    <div
                        style={{
                            gridColumn: "1 / span 2",
                            padding: theme.spacing.xxl,
                            backgroundColor: theme.colors.background.app_darker,
                            marginTop: theme.spacing.lg,
                            borderRadius: theme.radius.xl,
                        }}
                    >
                        {render_competition_section("chapter", false)}
                        {render_competition_section("portfolio", false)}
                        {render_competition_section("chapter", true)}
                        {render_competition_section("portfolio", true)}
                    </div>
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="Competition Error"
                    />
                )}

                {asking_for_confirmation &&
                    (() => {
                        // 1. Find the name of the item the user IS selecting
                        const selectedItem =
                            user_owned_submitted_chapters_and_portfolios.find(
                                (item) => item.id === owned_item_to_submit,
                            );
                        const selectedTitle = selectedItem
                            ? selectedItem.label
                            : "Selected Item";

                        // 2. Find the name of the item being REPLACED (if any)
                        const existingItem =
                            user_owned_submitted_chapters_and_portfolios.find(
                                (item) =>
                                    item.id === competition.user_submitted_item,
                            );
                        const existingTitle = existingItem
                            ? existingItem.label
                            : "Previous Submission";

                        // 3. Determine Cost and Logic
                        const isOverwrite =
                            competition.user_submitted_item !== "";
                        const cost = isOverwrite
                            ? Math.floor(competition.price / 2)
                            : competition.price;

                        return (
                            <ConfirmationPopUpWrapper
                                confirmation_title="Confirm Submit"
                                confirmation_message={
                                    isOverwrite
                                        ? `Replacing "${existingTitle}" with "${selectedTitle}" for ${cost}${theme.coin}`
                                        : `Submitting "${selectedTitle}" for ${cost}${theme.coin}`
                                }
                                on_accept={() => {
                                    handle_submit(true);
                                }}
                                on_reject={() => {
                                    set_asking_for_confirmation(false);
                                }}
                            />
                        );
                    })()}
            </div>
        );
    }

    return render_main();
}

export default ShowCompetitionPage;
