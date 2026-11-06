import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { Masonry } from "@mui/lab";

import CreatePortfolioPage from "./CreatePortfolioPage";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import SwitchWrapper from "../componentWrappers/SwitchWrapper";
import FileUploadWrapper from "../componentWrappers/FileUploadWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ProfileDirectingWrapper from "../componentWrappers/ProfileDirectingWrapper";
import HasPermission from "../utils/HasPermission";
import CommentPanelWrapper from "../componentWrappers/CommentPanelWrapper";
import TopBarWrapper from "../componentWrappers/TopBarWrapper";
import WorkWrapper from "../componentWrappers/WorkWrapper";
import imageCheck from "../utils/imageCheck";
import pdfCheck from "../utils/pdfCheck";
import videoCheck from "../utils/videoCheck";
import audioCheck from "../utils/audioCheck";
import MangaViewerWrapper from "../componentWrappers/MangaViewerWrapper";
import {
    commentScrollDebounceHelper,
    buildCommentsTree,
    getPaginatedComments,
    handleCreateComment,
    getPdfPageUrl,
} from "../utils/helper_functions";
import { validateText } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    SectionLabel,
    parsed_link_injected_text,
} from "../componentWrappers/helper_components";
import {
    PORTFOLIO_MIN_COMMENT_LEN,
    PORTFOLIO_MAX_COMMENT_LEN,
    WORK_MIN_TITLE_LEN,
    WORK_MAX_TITLE_LEN,
    WORK_IMAGE_MAX_SIZE,
    WORK_IMAGE_MIN_H,
    WORK_IMAGE_MIN_W,
    WORK_IMAGE_MAX_H,
    WORK_IMAGE_MAX_W,
    WORK_PDF_MAX_SIZE,
    WORK_PDF_MAX_PAGE,
    WORK_VIDEO_MAX_SIZE,
    WORK_VIDEO_MIN_H,
    WORK_VIDEO_MIN_W,
    WORK_VIDEO_MAX_H,
    WORK_VIDEO_MAX_W,
    WORK_VIDEO_MAX_DURATION,
    WORK_AUDIO_MAX_SIZE,
    WORK_AUDIO_MAX_DURATION,
    WORK_VIDEO_MIN_DURATION,
    WORK_AUDIO_MIN_DURATION,
} from "../globals";

function ShowPortfolioPage() {
    const { theme } = useTheme();
    const { portfolio_id: portfolio_id_from_url } = useParams();

    const logged_in_permission = HasPermission("logged_in");
    // we don't have the "owner" of the portfolio yet, so we can't do id_check, we'll do it in the render_main

    const max_file_size_text =
        (WORK_IMAGE_MAX_SIZE !== 0
            ? `image max file size: ${WORK_IMAGE_MAX_SIZE / (1024 * 1024)} MB`
            : "") +
        (WORK_IMAGE_MIN_H !== 0
            ? `\nimage min height: ${WORK_IMAGE_MIN_H}px`
            : "") +
        (WORK_IMAGE_MAX_H !== 0
            ? `\nimage max height: ${WORK_IMAGE_MAX_H}px`
            : "") +
        (WORK_IMAGE_MIN_W !== 0
            ? `\nimage min width: ${WORK_IMAGE_MIN_W}px`
            : "") +
        (WORK_IMAGE_MAX_W !== 0
            ? `\nimage max width: ${WORK_IMAGE_MAX_W}px`
            : "") +
        (WORK_PDF_MAX_SIZE !== 0
            ? `\n\nPDF max file size: ${WORK_PDF_MAX_SIZE / (1024 * 1024)} MB`
            : "") +
        (WORK_VIDEO_MAX_SIZE !== 0
            ? `\n\nvideo max file size: ${WORK_VIDEO_MAX_SIZE / (1024 * 1024)} MB`
            : "") +
        (WORK_VIDEO_MIN_H !== 0
            ? `\nvideo min height: ${WORK_VIDEO_MIN_H}px`
            : "") +
        (WORK_VIDEO_MAX_H !== 0
            ? `\nvideo max height: ${WORK_VIDEO_MAX_H}px`
            : "") +
        (WORK_VIDEO_MIN_W !== 0
            ? `\nvideo min width: ${WORK_VIDEO_MIN_W}px`
            : "") +
        (WORK_VIDEO_MAX_W !== 0
            ? `\nvideo max width: ${WORK_VIDEO_MAX_W}px`
            : "") +
        (WORK_VIDEO_MIN_DURATION !== 0
            ? `\nvideo min duration: ${WORK_VIDEO_MIN_DURATION} sn`
            : "") +
        (WORK_VIDEO_MAX_DURATION !== 0
            ? `\nvideo max duration: ${WORK_VIDEO_MAX_DURATION} sn`
            : "") +
        (WORK_AUDIO_MAX_SIZE !== 0
            ? `\n\naudio max file size: ${WORK_AUDIO_MAX_SIZE / (1024 * 1024)} MB`
            : "") +
        (WORK_AUDIO_MIN_DURATION !== 0
            ? `\naudio min duration: ${WORK_AUDIO_MIN_DURATION} sn`
            : "") +
        (WORK_AUDIO_MAX_DURATION !== 0
            ? `\naudio max duration: ${WORK_AUDIO_MAX_DURATION} sn`
            : "");

    const [portfolio, set_portfolio] = useState({
        id: -1,
        title: "",
        description: "",
        image: null,
        date: null,
        folder_name: "",
        tags: [],
        comments: [],
        num_of_comments: 0,
        owner: null,
        is_user_liked: false,
        num_of_likes: 0,
        works: [],
    });
    const comment_panel_scroll_ref = useRef(null);
    const [comments_next_page, comments_set_next_page] = useState(null);
    const [loading_more_comments, set_loading_more_comments] = useState(false);
    const [tree_comments, set_tree_comments] = useState([]);
    const [show_edit, set_show_edit_page] = useState(false);

    // 0: we are not asking for confirmation
    // any other value: asking for confirmation to delete that work
    const [asking_for_confirmation, set_asking_for_confirmation] = useState(0);
    const [error_message, set_error_message] = useState("");
    const [comments_error_message, set_comments_error_message] = useState("");

    const [work, set_work] = useState({
        title: "",
        files: [],
        uploading: false,
    });

    // id of the selected work user wants to read the pdf of
    const [pdf_work_id_to_read, set_pdf_work_id_to_read] = useState(0);

    const items = React.useMemo(() => {
        if (pdf_work_id_to_read === 0) return [];

        const selectedWork = portfolio.works.find(
            (w) => w.id === pdf_work_id_to_read,
        );

        if (!selectedWork) return [];
        const imageUrls = create_work_image_urls(selectedWork);

        const pageElements = imageUrls.map((url, index) => (
            <div
                key={`Work-${pdf_work_id_to_read}-Page-${index}-div`}
                chapter_index={pdf_work_id_to_read} // this is not used for works but we declare it to not break the viewer logic
                chapter_page={index + 1}
            >
                <img
                    style={{
                        width: "100%",
                        display: "block",
                        minHeight: theme.dimensions.md,
                    }}
                    alt={`Work ${pdf_work_id_to_read} Page ${index}`}
                    loading="lazy"
                    src={url}
                />
            </div>
        ));
        return pageElements;
    }, [pdf_work_id_to_read, portfolio.works, theme]);

    const get_portfolio_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_portfolio_response = await apiFetch(
                    `/api/portfolio/get-portfolio/${portfolio_id_from_url}/`,
                    options,
                );
                const [
                    get_portfolio_success_data,
                    get_portfolio_error_message,
                    get_portfolio_ok,
                ] = await handleFetch("get_portfolio", get_portfolio_response);

                if (get_portfolio_ok) {
                    set_portfolio((prev) => ({
                        ...prev,
                        id: get_portfolio_success_data.id,
                        title: get_portfolio_success_data.title ?? "",
                        description:
                            get_portfolio_success_data.description ?? "",
                        image: get_portfolio_success_data.image ?? null,
                        date: get_portfolio_success_data.date ?? null,
                        folder_name:
                            get_portfolio_success_data.folder_name ?? "",
                        tags: get_portfolio_success_data.tags ?? [],
                        num_of_comments:
                            get_portfolio_success_data.num_of_comments ?? 0,
                        owner: get_portfolio_success_data.owner ?? null, // This is an object like this: owner: {'id': 6, 'profile_name': user6, 'image': 'image_url'}
                        is_user_liked:
                            get_portfolio_success_data.is_user_liked ?? false,
                        num_of_likes:
                            get_portfolio_success_data.num_of_likes ?? 0,
                        works: get_portfolio_success_data.works ?? [],
                    }));

                    // this call to get the comments is the first call
                    // to load more comments we do separate calls without re-fetching the porfolio stats
                    comments_set_next_page(null);
                    get_portfolio_comments(
                        signal,
                        `/api/portfolio/get-comments/${portfolio_id_from_url}/`,
                    );

                    set_show_edit_page(false);
                    set_error_message("");
                } else {
                    set_error_message(get_portfolio_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during portfolio fetch.",
                );
            }
        },
        [portfolio_id_from_url],
    );

    // function to create work's image url list
    function create_work_image_urls(work) {
        const urls = []; // Initialize the list

        for (let i = 0; i < work.num_of_images; i++) {
            const url = getPdfPageUrl(work.pages_base_url, i);
            urls.push(url);
        }

        return urls; // Return the final array
    }

    const get_portfolio_comments = useCallback(
        async (signal, request_url) => {
            getPaginatedComments(
                signal,
                request_url,
                set_portfolio,
                comments_set_next_page,
                set_comments_error_message,
            );
        },
        [portfolio_id_from_url],
    );

    // Initial fetch
    useEffect(() => {
        const controller = new AbortController();
        get_portfolio_details(controller.signal);

        return () => controller.abort();
    }, [portfolio_id_from_url, get_portfolio_details]);

    // Load more comments
    async function load_more_comments() {
        if (!comments_next_page || loading_more_comments) return;

        set_loading_more_comments(true);

        try {
            const controller = new AbortController();
            await get_portfolio_comments(controller.signal, comments_next_page);
        } finally {
            set_loading_more_comments(false);
        }
    }

    useEffect(() => {
        if (!portfolio.comments) return;
        set_tree_comments(buildCommentsTree(portfolio.comments));
    }, [portfolio.comments]);

    useEffect(() => {
        return commentScrollDebounceHelper(
            comment_panel_scroll_ref,
            load_more_comments,
        );
    }, [comments_next_page, loading_more_comments]);

    async function handle_like() {
        if (!portfolio.id) return;

        try {
            const like_response = await apiFetch(
                `/api/portfolio/like-portfolio/${portfolio.id}/`,
                { method: "POST" },
            );
            const [like_success_data, like_error_message, like_ok] =
                await handleFetch("like", like_response);

            if (like_ok) {
                set_portfolio((prev) => ({
                    ...prev,
                    is_user_liked: like_success_data.liked,
                    num_of_likes: like_success_data.liked
                        ? prev.num_of_likes + 1
                        : prev.num_of_likes - 1,
                }));
                set_error_message("");
            } else {
                set_error_message(like_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during portfolio liking.",
            );
        }
    }

    async function handle_new_comment(submitted_text) {
        return await handleCreateComment(
            submitted_text,
            PORTFOLIO_MIN_COMMENT_LEN,
            PORTFOLIO_MAX_COMMENT_LEN,
            set_comments_error_message,
            `/api/portfolio/create-comment/${portfolio.id}/`,
            set_portfolio,
        );
    }

    async function check_multiple_file_requirements_and_set(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        let valid_files = [];
        let error_messages = [];

        const file_error_handler = (err_msg) => {
            error_messages.push(err_msg);
        };

        for (const file of files) {
            const mime_type = file.type;
            const ext = file.name.toLowerCase();

            let is_valid = false;

            if (mime_type.startsWith("image/")) {
                // Image check
                is_valid = await imageCheck(
                    file,
                    WORK_IMAGE_MIN_H,
                    WORK_IMAGE_MAX_H,
                    WORK_IMAGE_MIN_W,
                    WORK_IMAGE_MAX_W,
                    WORK_IMAGE_MAX_SIZE,
                    file_error_handler,
                );
            } else if (
                mime_type === "application/pdf" ||
                ext.endsWith(".pdf")
            ) {
                // pdf check
                is_valid = await pdfCheck(
                    file,
                    WORK_PDF_MAX_SIZE,
                    WORK_PDF_MAX_PAGE,
                    file_error_handler,
                );
            } else if (mime_type.startsWith("video/")) {
                // Video check
                is_valid = await videoCheck(
                    file,
                    WORK_VIDEO_MIN_H,
                    WORK_VIDEO_MAX_H,
                    WORK_VIDEO_MIN_W,
                    WORK_VIDEO_MAX_W,
                    WORK_VIDEO_MIN_DURATION,
                    WORK_VIDEO_MAX_DURATION,
                    WORK_VIDEO_MAX_SIZE,
                    file_error_handler,
                );
            } else if (mime_type.startsWith("audio/")) {
                // Audio check
                is_valid = await audioCheck(
                    file,
                    WORK_AUDIO_MIN_DURATION,
                    WORK_AUDIO_MAX_DURATION,
                    WORK_AUDIO_MAX_SIZE,
                    file_error_handler,
                );
            } else {
                file_error_handler(`${file.name}: Unsupported file type.`);
            }
            if (is_valid) {
                valid_files.push(file);
            }
        }

        if (valid_files.length > 0) {
            set_work((prev) => ({
                ...prev,
                files: [...(prev.files || []), ...valid_files],
            }));
        }

        if (error_messages.length > 0) {
            set_error_message(error_messages.join(", "));
        }
    }

    async function check_field_requirements() {
        const trimmed_title = work.title.trim();
        set_work((prev) => ({ ...prev, title: trimmed_title }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: WORK_MIN_TITLE_LEN,
            maxLen: WORK_MAX_TITLE_LEN,
            error_handler: set_error_message,
        });

        if (work.files.length === 0) {
            set_error_message("At least one work file is required");
            return false;
        }

        return isTitleValid;
    }

    async function handle_work_create() {
        if (!work.files.length || work.uploading || !portfolio.id) return;

        if (!(await check_field_requirements())) return null;

        set_work((prev) => ({ ...prev, uploading: true }));

        try {
            const form_data = new FormData();
            form_data.append("title", work.title);
            work.files.forEach((file, index) => {
                form_data.append("work_files", file, `${index}__${file.name}`);
            });

            const create_work_response = await apiFetch(
                `/api/portfolio/create-work/${portfolio.id}/`,
                { method: "POST", body: form_data },
            );
            const [
                create_work_success_data,
                create_work_error_message,
                create_work_ok,
            ] = await handleFetch("create_work", create_work_response);

            if (create_work_ok) {
                const { works, status } = create_work_success_data;

                // add successfull works
                set_portfolio((prev) => ({
                    ...prev,
                    works: [...works, ...prev.works],
                }));

                // if main request was successfull but there are some errors for some of the files
                if (status.length > 0) {
                    const failed_indices = status.map((s) => s.index);
                    const failed_files = status.map((s) => s.filename);
                    const failed_errors = status.map((s) => s.error);

                    set_error_message(
                        `Failed to upload: ${failed_files.join(", ")}.` +
                            `${failed_errors.join(", ")}` +
                            `${create_work_error_message || ""}`,
                    );

                    // keep the failed files in the upload cache
                    set_work((prev) => ({
                        ...prev,
                        files: prev.files.filter((_, i) =>
                            failed_indices.includes(i),
                        ),
                    }));
                } else {
                    set_error_message("");
                    set_work((prev) => ({ ...prev, title: "", files: [] }));
                }
            } else {
                set_error_message(create_work_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during work creation.",
            );
        } finally {
            set_work((prev) => ({ ...prev, uploading: false }));
        }
    }

    async function handle_work_delete(work_id, is_confirmed = false) {
        if (!asking_for_confirmation) {
            set_asking_for_confirmation(work_id);
        } else if (!is_confirmed) {
            set_asking_for_confirmation(0);
        } else if (is_confirmed) {
            set_asking_for_confirmation(0);

            try {
                const delete_work_response = await apiFetch(
                    `/api/portfolio/delete-work/${work_id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_work_success_data,
                    delete_work_error_message,
                    delete_work_ok,
                ] = await handleFetch("delete_work", delete_work_response);

                if (delete_work_ok) {
                    set_portfolio((prev) => ({
                        ...prev,
                        works: prev.works.filter((work) => work.id !== work_id),
                    }));
                    set_error_message("");
                } else {
                    set_error_message(delete_work_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during work deletion.",
                );
            }
        }
    }

    function render_owner_creation_zone() {
        return (
            <div>
                {/* Flex container to hold Left and Right columns */}
                <div
                    style={{
                        display: "flex",
                        gap: theme.spacing.xl,
                        alignItems: "flex-start",
                    }}
                >
                    {/* LEFT SIDE: File info */}
                    <div
                        style={{
                            flex: 1,
                            backgroundColor: theme.colors.background.app,
                            padding: theme.spacing.sm,
                        }}
                    >
                        <pre
                            style={{
                                ...theme.styles.descriptionText,
                                fontSize: theme.typography.fontSize.sm,
                            }}
                        >
                            {max_file_size_text}
                        </pre>
                    </div>

                    {/* RIGHT SIDE: Form inputs & action */}
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                            alignItems: "center",
                        }}
                    >
                        <TextInputWrapper
                            name="title"
                            label="Work Title"
                            multiline
                            rows={3}
                            value={work.title}
                            onChange={(e) =>
                                set_work((prev) => ({
                                    ...prev,
                                    title: e.target.value,
                                }))
                            }
                            maxLength={WORK_MAX_TITLE_LEN}
                        />

                        <FileUploadWrapper
                            label="Select Files"
                            onChange={check_multiple_file_requirements_and_set}
                            multiple
                            selectedFiles={work.files}
                        />

                        <ButtonWrapper
                            // Dynamically update the text based on file count
                            text={
                                work.uploading
                                    ? "Uploading..."
                                    : `Upload Work (${work.files.length} ${work.files.length === 1 ? "file" : "files"})`
                            }
                            disabled={work.files.length === 0 || work.uploading}
                            onClick={handle_work_create}
                        />
                    </div>
                </div>
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
                {/* Comments */}
                <div
                    style={{
                        flexGrow: logged_in_owner_permission ? 0 : 1, // Grow only if not owner
                        overflowY: "auto",
                    }}
                >
                    {comments_error_message === "" ? (
                        <CommentPanelWrapper
                            num_of_comments={portfolio.num_of_comments}
                            max_comment_len={PORTFOLIO_MAX_COMMENT_LEN}
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

                {/* Owner Creation Panel */}
                {logged_in_owner_permission && (
                    <div
                        style={{
                            padding: theme.spacing.xl,
                            backgroundColor: theme.colors.background.surface,
                            borderRadius: theme.radius.lg,
                            boxShadow: theme.colors.shadow.card,
                        }}
                    >
                        {render_owner_creation_zone()}
                    </div>
                )}
            </div>
        );
    }

    function render_main() {
        const logged_in_owner_permission = HasPermission(
            "logged_in",
            portfolio.owner?.id,
        );

        if (pdf_work_id_to_read > 0) {
            return (
                <div>
                    {/* Navigation Bar */}
                    <div
                        style={{
                            position: "sticky",
                            top: 0,
                            zIndex: 1000,
                            width: "100%",
                            backgroundColor: theme.colors.background.app,
                        }}
                    >
                        <NavigationBarWrapper
                            logged_in_permission={logged_in_permission}
                        />
                    </div>

                    {/* Consistent Back Button Bar */}
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            background: theme.colors.background.surface,
                            padding: `${theme.spacing.sm} ${theme.spacing.md}`, // Vertical padding to give it height
                        }}
                    >
                        <div
                            style={{
                                marginLeft: theme.spacing.md,
                                flexShrink: 0,
                            }}
                        >
                            <ButtonWrapper
                                text="Back to Portfolio"
                                onClick={() => set_pdf_work_id_to_read(0)}
                                visualVariant="outline"
                            />
                        </div>

                        {/* Empty flex spacer to maintain the layout structure of the other page */}
                        <div style={{ flex: 1 }} />
                    </div>

                    {/* Viewer Container with matching padding */}
                    <div
                        style={{
                            flex: 1,
                            display: "flex",
                            justifyContent: "center",
                            padding: theme.spacing.lg,
                        }}
                    >
                        <MangaViewerWrapper
                            items={items}
                            current_chapter_index={pdf_work_id_to_read}
                            isViewingPortfolioWork={true}
                        />
                    </div>
                </div>
            );
        }
        if (logged_in_owner_permission && show_edit) {
            const tag_ids = portfolio.tags.map((tag) => tag.id);
            return (
                <div>
                    <CreatePortfolioPage
                        id={portfolio.id}
                        title={portfolio.title}
                        description={portfolio.description}
                        image={portfolio.image}
                        tags={tag_ids}
                        edit={true}
                        cancel_edit_func={() => set_show_edit_page(false)}
                        edit_callback={get_portfolio_details}
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
                            {portfolio.image && (
                                <img
                                    src={portfolio.image}
                                    alt={portfolio.title}
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
                                title={portfolio.title}
                                metadata={
                                    <>
                                        <span style={theme.styles.subtitleText}>
                                            🗓️ {portfolio.date},{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            📁 {portfolio.works.length},{" "}
                                        </span>
                                        <span style={theme.styles.subtitleText}>
                                            ❤️ {portfolio.num_of_likes}
                                        </span>
                                    </>
                                }
                                tags={portfolio.tags.map((tag) => tag.label)}
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
                                    <ProfileDirectingWrapper
                                        profile_id={portfolio.owner?.id}
                                        profile_name={
                                            portfolio.owner?.profile_name
                                        }
                                        profile_image={portfolio.owner?.image}
                                    />
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
                                    {logged_in_permission && (
                                        <SwitchWrapper
                                            text={"Like"}
                                            checked={portfolio.is_user_liked}
                                            onEnable={handle_like}
                                            onDisable={handle_like}
                                            visualVariant="danger"
                                        />
                                    )}

                                    {logged_in_owner_permission && (
                                        <ButtonWrapper
                                            onClick={() =>
                                                set_show_edit_page(true)
                                            }
                                            text="Edit Portfolio"
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
                                    portfolio.description,
                                    theme,
                                )}
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

                    {/* ================= WORKS GALLERY ================= */}
                    <div
                        style={{
                            gridColumn: "1 / span 2",
                            padding: theme.spacing.xl,
                            backgroundColor: theme.colors.background.app_darker,
                            marginTop: theme.spacing.lg,
                            borderRadius: theme.radius.md,
                            maxHeight: theme.dimensions.xxxl,
                            overflowY: "auto",
                        }}
                    >
                        {portfolio.works.length === 0 ? (
                            <SectionLabel text="No work available" />
                        ) : (
                            <Masonry columns={3} spacing={2}>
                                {portfolio.works.map((work) => (
                                    <div
                                        key={work.id}
                                        style={{
                                            borderRadius: theme.radius.md,
                                            overflow: "hidden",
                                            boxShadow: theme.colors.shadow.card,
                                            transition: theme.transition.normal,
                                            display: "flex", // Added flex to the card
                                            flexDirection: "column", // Stack WorkWrapper and Button container
                                        }}
                                    >
                                        <WorkWrapper
                                            work={work}
                                            on_read_pdf={(work_id) =>
                                                set_pdf_work_id_to_read(work_id)
                                            }
                                        />
                                        {logged_in_owner_permission && (
                                            <div
                                                style={{
                                                    marginTop: theme.spacing.sm,
                                                    marginBottom:
                                                        theme.spacing.sm, // Added some bottom spacing
                                                    display: "flex",
                                                    justifyContent: "center", // This centers the button horizontally
                                                }}
                                            >
                                                <ButtonWrapper
                                                    text="Delete"
                                                    onClick={() =>
                                                        handle_work_delete(
                                                            work.id,
                                                        )
                                                    }
                                                    visualVariant="danger"
                                                />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </Masonry>
                        )}
                    </div>
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="Portfolio Error"
                    />
                )}

                {asking_for_confirmation > 0 &&
                    (() => {
                        const selectedWork = portfolio.works.find(
                            (work) => work.id === asking_for_confirmation,
                        );
                        const titleDisplay = selectedWork?.title
                            ? ` "${selectedWork.title}"`
                            : "";
                        return (
                            <ConfirmationPopUpWrapper
                                confirmation_title="Confirm Delete"
                                confirmation_message={
                                    selectedWork
                                        ? `Work${titleDisplay} will be deleted completely`
                                        : "This work will be deleted completely"
                                }
                                on_accept={() => {
                                    handle_work_delete(
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

export default ShowPortfolioPage;
