import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import ImageUploadFieldWrapper from "../componentWrappers/ImageUploadFieldWrapper";
import HasPermission from "../utils/HasPermission";
import { handlePreviewUrl } from "../utils/helper_functions";
import { validateText, validateLinks } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    NEWS_MIN_TITLE_LEN,
    NEWS_MAX_TITLE_LEN,
    NEWS_MIN_DESCRIPTION_LEN,
    NEWS_MAX_DESCRIPTION_LEN,
    NEWS_MIN_LINKS_LEN,
    NEWS_MAX_LINKS_LEN,
    NEWS_IMAGE_MIN_H,
    NEWS_IMAGE_MIN_W,
    NEWS_IMAGE_MAX_H,
    NEWS_IMAGE_MAX_W,
    NEWS_IMAGE_MAX_SIZE,
} from "../globals";

function CreateNewsPage({
    id = -1,
    title: prop_title = "",
    description: prop_description = "",
    image: prop_image = null,
    links: prop_links = "",
    edit = false,
    cancel_edit_func,
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();

    // in the editing page, we pass a cancel function. If it's not passed create page defaults for home navigation
    const handleCancel = cancel_edit_func || (() => navigate("/"));

    const admin_permission = HasPermission("admin");

    const [news, set_news] = useState({
        id: id,
        title: prop_title,
        description: prop_description,
        image: prop_image,
        links: prop_links,
    });
    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");
    const [preview_url, set_preview_url] = useState(null);

    // create url for image
    useEffect(() => {
        return handlePreviewUrl(news.image, set_preview_url);
    }, [news.image]);

    async function check_field_requirements() {
        const trimmed_title = news.title.trim();
        const trimmed_description = news.description.trim();
        const trimmed_links = news.links.trim();

        set_news((prev) => ({
            ...prev,
            title: trimmed_title,
            description: trimmed_description,
            links: trimmed_links,
        }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: NEWS_MIN_TITLE_LEN,
            maxLen: NEWS_MAX_TITLE_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isDescriptionValid = validateText({
            value: trimmed_description,
            fieldName: "Description",
            minLen: NEWS_MIN_DESCRIPTION_LEN,
            maxLen: NEWS_MAX_DESCRIPTION_LEN,
            error_handler: set_error_message,
        });

        const isLinksValid = validateLinks({
            value: trimmed_links,
            fieldName: "Links",
            minLen: NEWS_MIN_LINKS_LEN,
            maxLen: NEWS_MAX_LINKS_LEN,
            error_handler: set_error_message,
        });

        if (news.image === null) {
            set_error_message("Image is required");
            return false;
        }

        return isTitleValid && isDescriptionValid && isLinksValid;
    }

    async function create_form_data(creating = false) {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();

        // append only if we are creating a new news, or edited (changed) a field
        if (creating || prop_title !== news.title) {
            form_data.append("title", news.title);
        }

        if (creating || prop_description !== news.description) {
            form_data.append("description", news.description);
        }

        if (creating || prop_links !== news.links) {
            form_data.append(
                "links",
                JSON.stringify(news.links.split(/\s+/).filter(Boolean)),
            );
        }

        if (creating || typeof news.image !== "string") {
            form_data.append("image", news.image);
        }

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data(true);
        if (!form_data) return;

        try {
            const create_news_response = await apiFetch(
                "/api/news/create-news/",
                { method: "POST", body: form_data },
            );
            const [
                create_news_success_data,
                create_news_error_message,
                create_news_ok,
            ] = await handleFetch("create_news", create_news_response);

            if (create_news_ok) {
                navigate(`/news/${create_news_success_data.id}/`);
            } else {
                set_error_message(create_news_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during news creation.",
            );
        }
    }

    async function handle_edit() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            const edit_news_response = await apiFetch(
                `/api/news/edit-news/${news.id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_news_success_data,
                edit_news_error_message,
                edit_news_ok,
            ] = await handleFetch("edit_news", edit_news_response);

            if (edit_news_ok) {
                edit_callback();
                set_error_message("");
            } else {
                set_error_message(edit_news_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during news editing.",
            );
        }
    }

    async function handle_delete(is_confirmed = false) {
        // if we were waiting on the standby, now we need confirmation on the delete call
        if (!asking_for_confirmation) {
            set_asking_for_confirmation(true);
        }
        // if delete was called with not confirmation, abort and go back to standby
        else if (!is_confirmed) {
            set_asking_for_confirmation(false);
        } else if (
            is_confirmed
        ) // if confirmed, do the deletion and go back to standy
        {
            set_asking_for_confirmation(false);
            const delete_news_response = await apiFetch(
                `/api/news/delete-news/${news.id}/`,
                { method: "DELETE" },
            );
            const [
                delete_news_success_data,
                delete_news_error_message,
                delete_news_ok,
            ] = await handleFetch("delete_news", delete_news_response);
            if (delete_news_ok) {
                navigate("/");
            } else {
                set_error_message(delete_news_error_message);
            }
        }
    }

    function render_input_panel() {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.lg,
                    height: "100%",
                }}
            >
                <TextInputWrapper
                    name="title"
                    label="Title"
                    multiline
                    required
                    rows={3}
                    value={news.title}
                    onChange={(e) =>
                        set_news((prev) => ({ ...prev, title: e.target.value }))
                    }
                    maxLength={NEWS_MAX_TITLE_LEN}
                    fullWidth
                />

                <TextInputWrapper
                    name="description"
                    label="Description"
                    multiline
                    rows={10}
                    value={news.description}
                    onChange={(e) =>
                        set_news((prev) => ({
                            ...prev,
                            description: e.target.value,
                        }))
                    }
                    maxLength={NEWS_MAX_DESCRIPTION_LEN}
                    fullWidth
                />

                <TextInputWrapper
                    name="links"
                    label="Links"
                    multiline
                    rows={8}
                    value={news.links}
                    onChange={(e) =>
                        set_news((prev) => ({ ...prev, links: e.target.value }))
                    }
                    maxLength={NEWS_MAX_LINKS_LEN}
                    fullWidth
                />

                {/* Actions */}
                <div
                    style={{
                        marginTop: "auto",
                        display: "flex",
                        justifyContent: "center",
                    }}
                >
                    <EditDeleteCreateButtonsWrapper
                        edit={edit}
                        on_edit={handle_edit}
                        on_delete={() => set_asking_for_confirmation(true)}
                        on_cancel={handleCancel}
                        on_create={handle_create}
                        edit_text="Edit News"
                        delete_text="Delete News"
                        create_text="Publish News"
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!admin_permission) return null;

        const has_image = Boolean(news.image);

        return (
            <div>
                <NavigationBarWrapper logged_in_permission={admin_permission} />

                <div
                    style={{
                        paddingInline: theme.spacing.lg,
                    }}
                >
                    <div
                        style={{
                            ...theme.styles.titleText,
                            textAlign: "left",
                            marginTop: theme.spacing.lg,
                            marginBottom: theme.spacing.lg,
                        }}
                    >
                        {edit ? "Edit News" : "Create News"}
                    </div>

                    {/* Main content */}
                    <div
                        style={{
                            display: "flex",
                            gap: theme.spacing.xl,
                            marginLeft: 0,
                            marginRight: theme.spacing.lg,
                            marginTop: theme.spacing.lg,
                            marginBottom: theme.spacing.lg,
                            alignItems: "stretch",
                            minHeight: theme.dimensions.xxl,
                        }}
                    >
                        {/* Image column */}
                        <div
                            style={{
                                flex: "0 0 70%",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                border: `3px dashed ${theme.colors.border.subtle}`,
                                borderRadius: theme.radius.md,
                                backgroundColor:
                                    theme.colors.background.app_darker,
                            }}
                        >
                            <ImageUploadFieldWrapper
                                has_image={has_image}
                                image={news.image}
                                preview_url={preview_url}
                                alt={news.title}
                                min_height={NEWS_IMAGE_MIN_H}
                                min_width={NEWS_IMAGE_MIN_W}
                                max_height={NEWS_IMAGE_MAX_H}
                                max_width={NEWS_IMAGE_MAX_W}
                                max_file_size={NEWS_IMAGE_MAX_SIZE}
                                set_error_fn={set_error_message}
                                set_state_fn={set_news}
                            />
                        </div>

                        {/* Input column */}
                        <div
                            style={{
                                flex: "0 0 30%",
                                background: theme.colors.background.app_darker,
                                borderRadius: theme.radius.md,
                                padding: theme.spacing.lg,
                                marginRight: theme.spacing.lg,
                                display: "flex",
                                flexDirection: "column",
                            }}
                        >
                            {render_input_panel()}
                        </div>
                    </div>

                    {/* Confirmation popup */}
                    {asking_for_confirmation && (
                        <ConfirmationPopUpWrapper
                            confirmation_title="Confirm Delete"
                            confirmation_message="News will be deleted completely"
                            on_accept={() => handle_delete(true)}
                            on_reject={() => set_asking_for_confirmation(false)}
                        />
                    )}

                    {/* Error popup */}
                    {error_message && (
                        <ErrorPopUpWrapper
                            error_message={error_message}
                            on_close={() => set_error_message("")}
                            error_title="Create News Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreateNewsPage;
