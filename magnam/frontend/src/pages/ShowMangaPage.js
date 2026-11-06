import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import JSZip from "jszip";
import { saveAs } from "file-saver";

import CreateMangaPage from "./CreateMangaPage";
import CreateChapterPage from "./CreateChapterPage";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import SwitchWrapper from "../componentWrappers/SwitchWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import ProfileDirectingWrapper from "../componentWrappers/ProfileDirectingWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import TopBarWrapper from "../componentWrappers/TopBarWrapper";
import HasPermission from "../utils/HasPermission";
import CommentPanelWrapper from "../componentWrappers/CommentPanelWrapper";
import ChapterWrapper from "../componentWrappers/ChapterWrapper";
import {
    commentScrollDebounceHelper,
    buildCommentsTree,
    handleCreateComment,
    getPaginatedComments,
    fetch_pdf_blob,
    generate_chapter_filename,
    sanitize_filename,
} from "../utils/helper_functions";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    SectionLabel,
    findBin,
    MangaRatingHistogram,
} from "../componentWrappers/helper_components";
import {
    MANGA_MAX_RATING,
    MANGA_MIN_RATING,
    MANGA_MIN_COMMENT_LEN,
    MANGA_MAX_COMMENT_LEN,
} from "../globals";

function ShowMangaPage() {
    const { theme } = useTheme();
    const admin_permission = HasPermission("admin");
    const logged_in_permission = HasPermission("logged_in");
    // we don't have the "owner" of the manga yet, so we can't do id_check, we'll do it in the render_main

    const navigate = useNavigate();

    const { manga_id: manga_id_from_url } = useParams();

    const [manga, set_manga] = useState({
        id: -1,
        title: "",
        description: "",
        image: null,
        owner: null,
        collaborators: [],
        start_date: null,
        last_update_date: null,
        folder_name: "",
        tags: [],
        rating: 0,
        num_of_ratings: 0,
        comments: [],
        num_of_comments: 0,
        num_of_chapters: 0,
        total_price_of_all_chapters: 0,
        num_of_followers: 0,
        is_user_rated: false,
        is_user_following: false,
        chapters: [],
        rating_histogram: [],
        bookmark: null,
    });

    const [original_chapter_order, set_original_chapter_order] = useState([]);
    const all_sorts = [
        { id: 0, label: "reverse reading order" },
        { id: 1, label: "reading order" },
        { id: 2, label: "newest publish date first" },
        { id: 3, label: "oldest publish date first" },
    ];
    const [current_sort, set_current_sort] = useState(0);

    const [profile_balance, set_profile_balance] = useState(-1);
    const [user_temporary_score, set_user_temporary_score] = useState(0);

    const comment_panel_scroll_ref = useRef(null);
    const [comments_next_page, comments_set_next_page] = useState(null);
    const [loading_more_comments, set_loading_more_comments] = useState(false);
    const [tree_comments, set_tree_comments] = useState([]);
    const [show_edit, set_show_edit_page] = useState(false);
    const [show_chapter_edit, set_show_chapter_edit_page] = useState(false);

    // 0: we are not asking for confirmation
    // any other value: asking for confirmation to buy that chapter
    const [asking_for_confirmation, set_asking_for_confirmation] = useState(0);
    const [error_message, set_error_message] = useState("");
    const [comments_error_message, set_comments_error_message] = useState("");

    const get_manga_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_manga_response = await apiFetch(
                    `/api/manga/get-manga/${manga_id_from_url}/`,
                    options,
                );
                const [
                    get_manga_success_data,
                    get_manga_error_message,
                    get_manga_ok,
                ] = await handleFetch("get_manga", get_manga_response);

                if (get_manga_ok) {
                    set_manga((prev) => ({
                        ...prev,
                        id: get_manga_success_data.id,
                        title: get_manga_success_data.title ?? "",
                        description: get_manga_success_data.description ?? "",
                        image: get_manga_success_data.image ?? null,
                        owner: get_manga_success_data.owner ?? null, // This is an object like this: owner: {'id': 6, 'profile_name': user6, 'image': 'image_url'}
                        collaborators:
                            get_manga_success_data.collaborators ?? [],
                        start_date: get_manga_success_data.start_date ?? null,
                        last_update_date:
                            get_manga_success_data.last_update_date ?? null,
                        folder_name: get_manga_success_data.folder_name ?? "",
                        tags: get_manga_success_data.tags ?? [],
                        rating: get_manga_success_data.rating ?? 0,
                        num_of_ratings:
                            get_manga_success_data.num_of_ratings ?? 0,
                        num_of_followers:
                            get_manga_success_data.num_of_followers ?? 0,
                        num_of_comments:
                            get_manga_success_data.num_of_comments ?? 0,
                        num_of_chapters:
                            get_manga_success_data.chapters?.length ?? 0,
                        total_price_of_all_chapters:
                            get_manga_success_data.total_price_of_all_chapters ??
                            0,
                        is_user_rated:
                            get_manga_success_data.is_user_rated ?? false,
                        is_user_following:
                            get_manga_success_data.is_user_following ?? false,
                        chapters: get_manga_success_data.chapters ?? [],
                        rating_histogram:
                            get_manga_success_data.rating_histogram ?? [],
                        bookmark: get_manga_success_data.bookmark ?? null,
                    }));

                    set_original_chapter_order(
                        get_manga_success_data.chapters ?? [],
                    );

                    set_profile_balance(get_manga_success_data.profile_balance);
                    set_user_temporary_score(
                        get_manga_success_data.is_user_rated
                            ? get_manga_success_data.is_user_rated
                            : 0,
                    );

                    // this call to get the comments is the first call
                    // to load more comments we do separate calls without re-fetching the porfolio stats
                    comments_set_next_page(null);
                    get_manga_comments(
                        signal,
                        `/api/manga/get-comments/${manga_id_from_url}/`,
                    );

                    set_show_edit_page(false);
                    set_show_chapter_edit_page(false);
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

    const get_manga_comments = useCallback(
        async (signal, request_url) => {
            getPaginatedComments(
                signal,
                request_url,
                set_manga,
                comments_set_next_page,
                set_comments_error_message,
            );
        },
        [manga_id_from_url],
    );

    // Initial fetch
    useEffect(() => {
        const controller = new AbortController();
        get_manga_details(controller.signal);

        return () => controller.abort();
    }, [manga_id_from_url, get_manga_details]);

    // Load more comments
    async function load_more_comments() {
        if (!comments_next_page || loading_more_comments) return;

        set_loading_more_comments(true);

        try {
            const controller = new AbortController();
            await get_manga_comments(controller.signal, comments_next_page);
        } finally {
            set_loading_more_comments(false);
        }
    }

    useEffect(() => {
        if (!manga.comments) return;
        set_tree_comments(buildCommentsTree(manga.comments));
    }, [manga.comments]);

    useEffect(() => {
        return commentScrollDebounceHelper(
            comment_panel_scroll_ref,
            load_more_comments,
        );
    }, [comments_next_page, loading_more_comments]);

    useEffect(() => {
        handle_chapter_sort(current_sort);
    }, [current_sort, original_chapter_order]);

    function handle_chapter_sort(sort_type) {
        set_current_sort(sort_type);

        if (!original_chapter_order) return;

        let new_list = [...original_chapter_order];

        if (sort_type === 0) {
            new_list = [...original_chapter_order];
        } else if (sort_type === 1) {
            new_list = [...original_chapter_order].reverse();
        } else if (sort_type === 2) {
            new_list.sort((a, b) => new Date(b.id) - new Date(a.id));
        } else if (sort_type === 3) {
            new_list.sort((a, b) => new Date(a.id) - new Date(b.id));
        }

        set_manga((prev) => ({ ...prev, chapters: new_list }));
    }

    async function handle_follow() {
        if (!manga.id) return;

        try {
            const follow_response = await apiFetch(
                `/api/manga/follow-manga/${manga.id}/`,
                { method: "POST" },
            );
            const [follow_success_data, follow_error_message, follow_ok] =
                await handleFetch("follow", follow_response);

            if (follow_ok) {
                set_manga((prev) => ({
                    ...prev,
                    is_user_following: follow_success_data.followed,
                    num_of_followers: follow_success_data.followed
                        ? prev.num_of_followers + 1
                        : prev.num_of_followers - 1,
                }));
                set_error_message("");
            } else {
                set_error_message(follow_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during manga following.",
            );
        }
    }

    async function handle_score_submit() {
        if (!manga.id) return;

        try {
            if (
                user_temporary_score < MANGA_MIN_RATING ||
                user_temporary_score > MANGA_MAX_RATING
            ) {
                set_error_message(
                    `Error: score must be between ${MANGA_MIN_RATING} and ${MANGA_MAX_RATING}`,
                );
                return;
            }

            const form_data = new FormData();
            form_data.append("score", user_temporary_score);
            const submit_score_response = await apiFetch(
                `/api/manga/rate-manga/${manga.id}/`,
                { method: "POST", body: form_data },
            );
            const [
                submit_score_success_data,
                submit_score_error_message,
                submit_score_ok,
            ] = await handleFetch("submit_score", submit_score_response);

            if (submit_score_ok) {
                const was_num_of_ratings = manga.num_of_ratings;
                const was_sum = manga.rating * was_num_of_ratings;
                const was_user_rated = manga.is_user_rated; // previous score if any
                const now_user_rated = submit_score_success_data.score;

                set_manga((prev) => {
                    const newHistogram = { ...prev.rating_histogram };

                    // Remove old score from histogram if overwriting
                    // since manga.is_user_rated being 0 is a valid rating we want the if check to result in true
                    if (was_user_rated !== false) {
                        const oldBin = findBin(was_user_rated);
                        if (oldBin)
                            newHistogram[oldBin] =
                                (newHistogram[oldBin] || 1) - 1;
                    }

                    // Add new score to histogram
                    const newBin = findBin(now_user_rated);
                    if (newBin)
                        newHistogram[newBin] = (newHistogram[newBin] || 0) + 1;

                    // Update rating & counts
                    // since manga.is_user_rated being 0 is a valid rating we want the if check to result in true
                    let newRating =
                        was_user_rated !== false
                            ? (was_sum - was_user_rated + now_user_rated) /
                              was_num_of_ratings
                            : (was_sum + now_user_rated) /
                              (was_num_of_ratings + 1);

                    return {
                        ...prev,
                        rating: newRating,
                        // since manga.is_user_rated being 0 is a valid rating we want the if check to result in true
                        num_of_ratings:
                            was_user_rated !== false
                                ? was_num_of_ratings
                                : was_num_of_ratings + 1,
                        is_user_rated: now_user_rated,
                        rating_histogram: newHistogram,
                    };
                });

                set_user_temporary_score(now_user_rated);
                set_error_message("");
            } else {
                set_error_message(submit_score_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during manga scoring.",
            );
        }
    }

    async function handle_score_delete() {
        if (!manga.id) return;

        try {
            const delete_score_response = await apiFetch(
                `/api/manga/rate-manga/${manga.id}/`,
                { method: "DELETE" },
            );
            const [
                delete_score_success_data,
                delete_score_error_message,
                delete_score_ok,
            ] = await handleFetch("delete_score", delete_score_response);

            if (delete_score_ok) {
                const was_num_of_ratings = manga.num_of_ratings;
                const was_sum = manga.rating * was_num_of_ratings;
                const was_user_rated = manga.is_user_rated;

                set_manga((prev) => {
                    const newHistogram = { ...prev.rating_histogram };
                    const oldBin = findBin(was_user_rated);
                    if (oldBin)
                        newHistogram[oldBin] = (newHistogram[oldBin] || 1) - 1;

                    return {
                        ...prev,
                        rating:
                            was_num_of_ratings !== 1
                                ? (was_sum - was_user_rated) /
                                  (was_num_of_ratings - 1)
                                : 0,
                        num_of_ratings: was_num_of_ratings - 1,
                        is_user_rated: false,
                        rating_histogram: newHistogram,
                    };
                });

                set_user_temporary_score(0);
                set_error_message("");
            } else {
                set_error_message(delete_score_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during manga score deletion.",
            );
        }
    }

    async function handle_new_comment(submitted_text) {
        return await handleCreateComment(
            submitted_text,
            MANGA_MIN_COMMENT_LEN,
            MANGA_MAX_COMMENT_LEN,
            set_comments_error_message,
            `/api/manga/create-comment/${manga.id}/`,
            set_manga,
        );
    }

    async function handle_chapter_buy(chapter_id, is_confirmed = false) {
        const chapter_to_buy = manga.chapters.find(
            (chapter) => chapter.id === chapter_id,
        );
        if (
            !chapter_to_buy ||
            (chapter_to_buy.price > profile_balance && !admin_permission)
        ) {
            set_error_message(
                chapter_to_buy ? "Not enough money" : "Chapter not found",
            );
            return;
        }

        if (!asking_for_confirmation) {
            set_asking_for_confirmation(chapter_id);
        } else if (!is_confirmed) {
            set_asking_for_confirmation(0);
        } else if (is_confirmed) {
            set_asking_for_confirmation(0);

            try {
                const buy_chapter_response = await apiFetch(
                    `/api/manga/buy-chapter/${chapter_id}/`,
                    { method: "POST" },
                );
                const [
                    buy_chapter_success_data,
                    buy_chapter_error_message,
                    buy_chapter_ok,
                ] = await handleFetch("buy_chapter", buy_chapter_response);

                if (buy_chapter_ok) {
                    set_profile_balance(buy_chapter_success_data.new_balance);

                    // update the bought chapter
                    set_manga((prev) => ({
                        ...prev,
                        chapters: prev.chapters.map((chapter) =>
                            chapter.id === chapter_id
                                ? {
                                      ...chapter,
                                      is_user_bought: true,
                                      pdf: buy_chapter_success_data.pdf,
                                      folder_name:
                                          buy_chapter_success_data.folder_name,
                                      pages_base_url:
                                          buy_chapter_success_data.pages_base_url,
                                  }
                                : chapter,
                        ),
                    }));
                    set_error_message("");
                } else {
                    set_error_message(buy_chapter_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during chapter buying.",
                );
            }
        }
    }

    async function handle_download_all_chapters() {
        try {
            const zip = new JSZip();

            const boughtChapters = manga.chapters.filter(
                (c) => c.is_user_bought && c.pdf,
            );

            if (boughtChapters.length === 0) {
                set_error_message("No bought chapters to download");
                return;
            }

            await Promise.all(
                boughtChapters.map(async (chapter) => {
                    const blob = await fetch_pdf_blob(chapter.pdf);

                    const filename = generate_chapter_filename(
                        manga.title,
                        chapter.no,
                        chapter.title,
                    );

                    zip.file(filename, blob);
                }),
            );

            const zipBlob = await zip.generateAsync({ type: "blob" });
            const zipName = `${sanitize_filename(manga.title)}-chapters.zip`;

            saveAs(zipBlob, zipName);
        } catch (err) {
            set_error_message("Failed to download all chapters");
        }
    }

    function render_rating_panel() {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    width: "100%",
                }}
            >
                <div
                    style={{
                        backgroundColor: theme.colors.background.app,
                        borderRadius: theme.radius.md,
                        padding: theme.spacing.sm,
                    }}
                >
                    {/* Plot */}
                    <MangaRatingHistogram
                        histogram={manga.rating_histogram}
                        rating={manga.rating}
                        userRating={manga.is_user_rated}
                        totalRatings={manga.num_of_ratings}
                    />
                </div>

                {/* Slider + actions */}
                {logged_in_permission && (
                    <div
                        style={{
                            width: "100%",
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                        }}
                    >
                        <IntegerSliderWrapper
                            value={user_temporary_score}
                            min={MANGA_MIN_RATING}
                            max={MANGA_MAX_RATING}
                            step={1}
                            onChange={(e, newValue) =>
                                set_user_temporary_score(newValue)
                            }
                            onChangeCommitted={() => {}}
                            is_rating_slider={true}
                        />

                        <div
                            style={{
                                display: "flex",
                                gap: theme.spacing.md,
                            }}
                        >
                            {logged_in_permission && (
                                <SwitchWrapper
                                    text={"Follow"}
                                    checked={manga.is_user_following}
                                    onEnable={handle_follow}
                                    onDisable={handle_follow}
                                />
                            )}
                            <ButtonWrapper
                                text="Submit Rate"
                                onClick={handle_score_submit}
                                disabled={
                                    user_temporary_score === manga.is_user_rated
                                }
                            />
                            <ButtonWrapper
                                text="Delete Rate"
                                onClick={handle_score_delete}
                                disabled={manga.is_user_rated === false}
                                visualVariant="danger"
                            />
                        </div>
                    </div>
                )}
            </div>
        );
    }

    function render_right_column(logged_in_owner_permission) {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.xl,
                    overflowX: "hidden",
                    height: "100%",
                }}
            >
                {/* Rating Panel */}
                <div
                    style={{
                        padding: theme.spacing.xl,
                        backgroundColor: theme.colors.background.surface,
                        borderRadius: theme.radius.lg,
                        boxShadow: theme.colors.shadow.card,
                    }}
                >
                    {render_rating_panel()}
                </div>

                {/* Comments */}
                <div
                    style={{
                        flexGrow: logged_in_owner_permission ? 0 : 1, // Grow only if not owner
                        overflowY: "auto",
                    }}
                >
                    {comments_error_message === "" ? (
                        <CommentPanelWrapper
                            num_of_comments={manga.num_of_comments}
                            max_comment_len={MANGA_MAX_COMMENT_LEN}
                            handle_new_comment={handle_new_comment}
                            scroll_ref={comment_panel_scroll_ref}
                            tree_comments={tree_comments}
                            loading={loading_more_comments}
                            logged_in_permission={logged_in_permission}
                        />
                    ) : (
                        <p>{comments_error_message}</p>
                    )}
                </div>
            </div>
        );
    }

    function render_main() {
        const logged_in_owner_permission = HasPermission(
            "logged_in",
            manga.owner?.id,
        );
        const logged_in_collaborator_permission =
            HasPermission(
                "logged_in",
                manga.collaborators.map((c) => c.id),
            ) || logged_in_owner_permission;

        if (logged_in_owner_permission && show_edit) {
            const tag_ids = manga.tags.map((tag) => tag.id);
            const collaborator_ids = manga.collaborators.map(
                (collaborator) => collaborator.id,
            );
            return (
                <div>
                    <CreateMangaPage
                        id={manga.id}
                        title={manga.title}
                        description={manga.description}
                        image={manga.image}
                        collaborators={collaborator_ids}
                        tags={tag_ids}
                        edit={true}
                        cancel_edit_func={() => set_show_edit_page(false)}
                        edit_callback={get_manga_details}
                    />
                </div>
            );
        }
        // show_chapter_edit is false when nothing is being edited, otherwise an index at manga.chapters
        // so show_chapter_edit being 0 is a valid index we want to run render_chapter_edit if show_chapter_edit==0
        if (logged_in_collaborator_permission && show_chapter_edit !== false) {
            const chapter_to_edit = manga.chapters[show_chapter_edit];
            const collaborator_ids = chapter_to_edit.collaborators.map(
                (collaborator) => collaborator.id,
            );
            return (
                <div>
                    <CreateChapterPage
                        id={chapter_to_edit.id}
                        title={chapter_to_edit.title}
                        no={chapter_to_edit.no}
                        collaborators={collaborator_ids}
                        pdf={chapter_to_edit.pdf}
                        price={chapter_to_edit.price}
                        edit={true}
                        cancel_edit_func={() =>
                            set_show_chapter_edit_page(false)
                        }
                        edit_callback={get_manga_details}
                    />
                </div>
            );
        }

        return (
            <div>
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                    profile_balance={profile_balance}
                />

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
                            {manga.image && (
                                <img
                                    src={manga.image}
                                    alt={manga.title}
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
                                title={manga.title}
                                metadata={
                                    <>
                                        <span style={theme.styles.subtitleText}>
                                            🗓️ {manga.start_date} /{" "}
                                            {manga.last_update_date},{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            🔖 {manga.num_of_followers}
                                        </span>
                                    </>
                                }
                                tags={manga.tags.map((tag) => tag.label)}
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
                                        boxShadow: theme.colors.shadow.card,
                                    }}
                                >
                                    👤
                                    <ProfileDirectingWrapper
                                        profile_id={manga.owner?.id}
                                        profile_name={manga.owner?.profile_name}
                                        profile_image={manga.owner?.image}
                                    />
                                    {manga.collaborators.length > 0 && <>👥</>}
                                    {manga.collaborators.map(
                                        (collaborator, index) => (
                                            <ProfileDirectingWrapper
                                                key={index}
                                                profile_id={collaborator.id}
                                                profile_name={
                                                    collaborator.profile_name
                                                }
                                                profile_image={
                                                    collaborator.image
                                                }
                                            />
                                        ),
                                    )}
                                </div>

                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: theme.spacing.lg,
                                        width: "fit-content",
                                        padding: theme.spacing.md,
                                    }}
                                >
                                    {logged_in_owner_permission && (
                                        <ButtonWrapper
                                            onClick={() =>
                                                set_show_edit_page(true)
                                            }
                                            text="Edit Manga"
                                            visualVariant="outline"
                                        />
                                    )}
                                </div>
                            </div>

                            {/* Description Card */}
                            <div
                                style={{
                                    ...theme.styles.descriptionText,
                                    marginTop: theme.spacing.md,
                                    padding: theme.spacing.md,
                                    borderRadius: theme.radius.md,
                                    backgroundColor:
                                        theme.colors.background.app,
                                    boxShadow: theme.colors.shadow.card,
                                }}
                            >
                                {manga.description}
                            </div>
                        </div>
                    </div>

                    {/* ================= RIGHT COLUMN ================= */}
                    <div
                        style={{
                            paddingLeft: theme.spacing.lg,
                        }}
                    >
                        {render_right_column(logged_in_owner_permission)}
                    </div>

                    {/* ================= CHAPTERS LIST ================= */}
                    <div
                        style={{
                            gridColumn: "1 / span 2",
                            padding: theme.spacing.xxl,
                            backgroundColor: theme.colors.background.app_darker,
                            marginTop: theme.spacing.lg,
                        }}
                    >
                        <div
                            style={{
                                gridColumn: "1 / span 2",
                                padding: theme.spacing.lg,
                                backgroundColor:
                                    theme.colors.background.app_darker,
                            }}
                        >
                            <div
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "1fr auto 1fr",
                                    alignItems: "center",
                                    marginBottom: theme.spacing.md,
                                    gap: theme.spacing.md,
                                }}
                            >
                                {/* 1. LEFT SLOT (Bookmark) */}
                                <div style={{ justifySelf: "start" }}>
                                    {logged_in_permission &&
                                        manga.bookmark &&
                                        (() => {
                                            const chapter =
                                                manga.chapters?.find(
                                                    (ch) =>
                                                        ch.id ===
                                                        manga.bookmark
                                                            .chapter_id,
                                                );
                                            if (!chapter) return null;
                                            return (
                                                <ButtonWrapper
                                                    text={`Continue ${chapter.no}: ${chapter.title} [${manga.bookmark.page}]`}
                                                    onClick={() =>
                                                        navigate(
                                                            `/read-manga/${manga.id}/${manga.bookmark.chapter_id}/`,
                                                            {
                                                                state: {
                                                                    bookmark_page:
                                                                        manga
                                                                            .bookmark
                                                                            .page,
                                                                },
                                                            },
                                                        )
                                                    }
                                                />
                                            );
                                        })()}
                                </div>

                                {/* 2. MIDDLE SLOT (Sort Selections) */}
                                <div style={{ justifySelf: "center" }}>
                                    {manga.num_of_chapters === 0 ? (
                                        <SectionLabel text="No chapter available" />
                                    ) : (
                                        <>
                                            <SectionLabel
                                                text={
                                                    `Sort Chapters (${manga.num_of_chapters} ` +
                                                    `chapter${manga.num_of_chapters !== 1 ? "s" : ""} ` +
                                                    `costing ${manga.total_price_of_all_chapters}${theme.coin})`
                                                }
                                            />

                                            <MultipleChoiceSelectionWrapper
                                                all_choices={all_sorts}
                                                selected_choices={[
                                                    current_sort,
                                                ]}
                                                handle_choice_select={
                                                    set_current_sort
                                                }
                                            />
                                        </>
                                    )}
                                </div>

                                {/* 3. RIGHT SLOT (Create Button) */}
                                <div style={{ justifySelf: "end" }}>
                                    {logged_in_collaborator_permission && (
                                        <ButtonWrapper
                                            to={`/manga/create-chapter/${manga.id}/`}
                                            text="Create Chapter"
                                        />
                                    )}
                                </div>
                            </div>

                            <div
                                style={{
                                    borderRadius: theme.radius.xl,
                                    maxHeight: theme.dimensions.xxxl,
                                    overflowY: "auto",
                                    padding: theme.spacing.lg,
                                    margin: theme.spacing.md,
                                }}
                            >
                                {manga.chapters.map((chapter, index) => (
                                    <div
                                        key={index}
                                        style={{
                                            padding: theme.spacing.sm,
                                        }}
                                    >
                                        <ChapterWrapper
                                            chapter={chapter}
                                            manga_title={manga.title}
                                            logged_in_permission={
                                                logged_in_permission
                                            }
                                            logged_in_manga_owner_permission={
                                                logged_in_owner_permission
                                            }
                                            on_edit={() => {
                                                set_show_chapter_edit_page(
                                                    index,
                                                );
                                            }} // this needs chapter index in the manga.chapters
                                            on_buy={() => {
                                                handle_chapter_buy(chapter.id);
                                            }} // this needs chapter.id to send a request to the api
                                            on_read={() => {
                                                navigate(
                                                    `/read-manga/${manga.id}/${chapter.id}/`,
                                                );
                                            }} // this needs chapter.id to send a request to the api
                                        />
                                    </div>
                                ))}
                                {manga.chapters.some(
                                    (c) => c.is_user_bought,
                                ) && (
                                    <div
                                        style={{ marginTop: theme.spacing.lg }}
                                    >
                                        <ButtonWrapper
                                            text="Download Chapters"
                                            onClick={
                                                handle_download_all_chapters
                                            }
                                            visualVariant="outline"
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="Manga Error"
                    />
                )}

                {asking_for_confirmation > 0 &&
                    (() => {
                        const selectedChapter = manga.chapters.find(
                            (chapter) => chapter.id === asking_for_confirmation,
                        );

                        return (
                            <ConfirmationPopUpWrapper
                                confirmation_title="Confirm Buy"
                                confirmation_message={
                                    selectedChapter
                                        ? `Chapter "${selectedChapter.title} (Chapter: ${selectedChapter.no})" will be bought for ${selectedChapter.price}${theme.coin}`
                                        : "This chapter will be bought"
                                }
                                on_accept={() => {
                                    handle_chapter_buy(
                                        asking_for_confirmation,
                                        true,
                                    );
                                }}
                                on_reject={() => {
                                    set_asking_for_confirmation(0);
                                }}
                            />
                        );
                    })()}
            </div>
        );
    }

    return render_main();
}

export default ShowMangaPage;
