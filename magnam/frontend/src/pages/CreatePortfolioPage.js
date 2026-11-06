import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import ImageUploadFieldWrapper from "../componentWrappers/ImageUploadFieldWrapper";
import { useTheme } from "../context/ThemeContext";
import HasPermission from "../utils/HasPermission";
import {
    setFetchAndSet,
    handlePreviewUrl,
    areArraysEqualAsSets,
    handleIdLabelItemSlotSelect,
} from "../utils/helper_functions";
import { validateText, validatePKRelation } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import {
    PORTFOLIO_MIN_TITLE_LEN,
    PORTFOLIO_MAX_TITLE_LEN,
    PORTFOLIO_MIN_DESCRIPTION_LEN,
    PORTFOLIO_MAX_DESCRIPTION_LEN,
    PORTFOLIO_IMAGE_MIN_H,
    PORTFOLIO_IMAGE_MIN_W,
    PORTFOLIO_IMAGE_MAX_H,
    PORTFOLIO_IMAGE_MAX_W,
    PORTFOLIO_IMAGE_MAX_SIZE,
    PORTFOLIO_MIN_TAG_COUNT,
    PORTFOLIO_MAX_TAG_COUNT,
} from "../globals";

function CreatePortfolioPage({
    id = -1,
    title: prop_title = "",
    description: prop_description = "",
    image: prop_image = null,
    tags: prop_tags = [],
    edit = false,
    cancel_edit_func,
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();

    // in the editing page, we pass a cancel function. If it's not passed create page defaults for home navigation
    const handleCancel = cancel_edit_func || (() => navigate("/portfolio/"));

    const logged_in_permission = HasPermission("logged_in");

    const [portfolio, set_portfolio] = useState({
        id: id,
        title: prop_title,
        description: prop_description,
        image: prop_image,
        tags: Array.isArray(prop_tags) ? prop_tags : [],
    });

    const [all_tags, set_all_tags] = useState([]);

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");
    const [tags_error_message, set_tags_error_message] = useState("");
    const [preview_url, set_preview_url] = useState(null);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/portfolio/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    // create url for image
    useEffect(() => {
        return handlePreviewUrl(portfolio.image, set_preview_url);
    }, [portfolio.image]);

    async function check_field_requirements() {
        const trimmed_title = portfolio.title.trim();
        const trimmed_description = portfolio.description.trim();

        set_portfolio((prev) => ({
            ...prev,
            title: trimmed_title,
            description: trimmed_description,
        }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: PORTFOLIO_MIN_TITLE_LEN,
            maxLen: PORTFOLIO_MAX_TITLE_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isDescriptionValid = validateText({
            value: trimmed_description,
            fieldName: "Description",
            minLen: PORTFOLIO_MIN_DESCRIPTION_LEN,
            maxLen: PORTFOLIO_MAX_DESCRIPTION_LEN,
            required: true,
            error_handler: set_error_message,
        });

        if (portfolio.image === null) {
            set_error_message("Image is required");
            return false;
        }

        const isTagsValid = validatePKRelation({
            value: portfolio.tags,
            fieldName: "Tags",
            minCount: PORTFOLIO_MIN_TAG_COUNT,
            maxCount: PORTFOLIO_MAX_TAG_COUNT,
            error_handler: set_error_message,
        });

        return isTitleValid && isDescriptionValid && isTagsValid;
    }

    async function create_form_data(creating = false) {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();

        // append only if we are creating a new portfolio, or edited (changed) a field
        if (creating || prop_title !== portfolio.title) {
            form_data.append("title", portfolio.title);
        }

        if (creating || prop_description !== portfolio.description) {
            form_data.append("description", portfolio.description);
        }

        if (creating || typeof portfolio.image !== "string") {
            form_data.append("image", portfolio.image);
        }

        if (creating || !areArraysEqualAsSets(prop_tags, portfolio.tags)) {
            portfolio.tags.forEach((tag_id) =>
                form_data.append("tags", tag_id),
            );
        }

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data(true);
        if (!form_data) return;

        try {
            const create_portfolio_response = await apiFetch(
                "/api/portfolio/create-portfolio/",
                { method: "POST", body: form_data },
            );
            const [
                create_portfolio_success_data,
                create_portfolio_error_message,
                create_portfolio_ok,
            ] = await handleFetch(
                "create_portfolio",
                create_portfolio_response,
            );

            if (create_portfolio_ok) {
                navigate(`/portfolio/${create_portfolio_success_data.id}/`);
            } else {
                set_error_message(create_portfolio_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during portfolio creating.",
            );
        }
    }

    async function handle_edit() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            const edit_portfolio_response = await apiFetch(
                `/api/portfolio/edit-portfolio/${portfolio.id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_portfolio_success_data,
                edit_portfolio_error_message,
                edit_portfolio_ok,
            ] = await handleFetch("edit_portfolio", edit_portfolio_response);

            if (edit_portfolio_ok) {
                edit_callback();
            } else {
                set_error_message(edit_portfolio_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during portfolio editing.",
            );
        }
    }

    async function handle_delete(is_confirmed = false) {
        if (!asking_for_confirmation) {
            set_asking_for_confirmation(true);
        } else if (!is_confirmed) {
            set_asking_for_confirmation(false);
        } else if (is_confirmed) {
            set_asking_for_confirmation(false);
            try {
                const delete_portfolio_response = await apiFetch(
                    `/api/portfolio/delete-portfolio/${portfolio.id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_portfolio_success_data,
                    delete_portfolio_error_message,
                    delete_portfolio_ok,
                ] = await handleFetch(
                    "delete_portfolio",
                    delete_portfolio_response,
                );

                if (delete_portfolio_ok) {
                    navigate("/portfolio/");
                } else {
                    set_error_message(delete_portfolio_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during portfolio deleting.",
                );
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
                    value={portfolio.title}
                    onChange={(e) =>
                        set_portfolio((prev) => ({
                            ...prev,
                            title: e.target.value,
                        }))
                    }
                    maxLength={PORTFOLIO_MAX_TITLE_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="description"
                    label="Description"
                    multiline
                    required
                    rows={5}
                    value={portfolio.description}
                    onChange={(e) =>
                        set_portfolio((prev) => ({
                            ...prev,
                            description: e.target.value,
                        }))
                    }
                    maxLength={PORTFOLIO_MAX_DESCRIPTION_LEN}
                    fullWidth={true}
                />

                {tags_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={tags_error_message}
                        on_close={() => {
                            set_tags_error_message("");
                        }}
                        error_title="Portfolio Tag Error"
                    />
                ) : (
                    <>
                        <p
                            style={{
                                ...theme.styles.descriptionText,
                                textAlign: "center",
                            }}
                        >
                            Tags
                        </p>
                        <MultipleChoiceSelectionWrapper
                            all_choices={all_tags}
                            selected_choices={portfolio.tags}
                            handle_choice_select={(tag_id) => {
                                handleIdLabelItemSlotSelect(
                                    tag_id,
                                    set_portfolio,
                                    "tags",
                                );
                            }}
                        />
                    </>
                )}

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
                        on_delete={handle_delete}
                        on_cancel={handleCancel}
                        on_create={handle_create}
                        edit_text="Edit Portfolio"
                        delete_text="Delete Portfolio"
                        create_text="Publish Portfolio"
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }
        const has_image = Boolean(portfolio.image);

        return (
            <div>
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

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
                        {edit ? "Edit Portfolio" : "Create Portfolio"}
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
                                image={portfolio.image}
                                preview_url={preview_url}
                                alt={portfolio.title}
                                min_height={PORTFOLIO_IMAGE_MIN_H}
                                min_width={PORTFOLIO_IMAGE_MIN_W}
                                max_height={PORTFOLIO_IMAGE_MAX_H}
                                max_width={PORTFOLIO_IMAGE_MAX_W}
                                max_file_size={PORTFOLIO_IMAGE_MAX_SIZE}
                                set_error_fn={set_error_message}
                                set_state_fn={set_portfolio}
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
                            confirmation_message="Portfolio will be deleted completely"
                            on_accept={() => {
                                handle_delete(true);
                            }}
                            on_reject={() => {
                                set_asking_for_confirmation(false);
                            }}
                        />
                    )}

                    {/* Error popup */}
                    {error_message && (
                        <ErrorPopUpWrapper
                            error_message={error_message}
                            on_close={() => {
                                set_error_message("");
                            }}
                            error_title="Create Portfolio Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreatePortfolioPage;
