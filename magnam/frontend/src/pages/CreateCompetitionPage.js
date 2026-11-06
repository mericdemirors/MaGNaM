import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import DateSliderWrapper from "../componentWrappers/DateSliderWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import ImageUploadFieldWrapper from "../componentWrappers/ImageUploadFieldWrapper";
import { useTheme } from "../context/ThemeContext";
import HasPermission from "../utils/HasPermission";
import {
    setFetchAndSet,
    handlePreviewUrl,
    areArraysEqualAsSets,
    handleIdLabelItemSlotSelect,
    formatTimestampToDateString,
} from "../utils/helper_functions";
import {
    validateText,
    validateLinks,
    validatePKRelation,
} from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import {
    COMPETITION_MIN_TITLE_LEN,
    COMPETITION_MAX_TITLE_LEN,
    COMPETITION_MIN_DESCRIPTION_LEN,
    COMPETITION_MAX_DESCRIPTION_LEN,
    COMPETITION_MIN_LINKS_LEN,
    COMPETITION_MAX_LINKS_LEN,
    COMPETITION_IMAGE_MIN_H,
    COMPETITION_IMAGE_MIN_W,
    COMPETITION_IMAGE_MAX_H,
    COMPETITION_IMAGE_MAX_W,
    COMPETITION_IMAGE_MAX_SIZE,
    COMPETITION_MIN_TAG_COUNT,
    COMPETITION_MAX_TAG_COUNT,
} from "../globals";

function CreateCompetitionPage({
    id = -1,
    title: prop_title = "",
    description: prop_description = "",
    image: prop_image = null,
    links: prop_links = "",
    price: prop_price = 0,
    start_date: prop_start_date = null,
    end_date: prop_end_date = null,
    tags: prop_tags = [],
    edit = false,
    cancel_edit_func,
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();

    // in the editing page, we pass a cancel function. If it's not passed create page defaults for home navigation
    const handleCancel = cancel_edit_func || (() => navigate("/competition/"));

    const admin_permission = HasPermission("admin");

    const [competition, set_competition] = useState({
        id: id,
        title: prop_title,
        description: prop_description,
        image: prop_image,
        links: prop_links,
        price: prop_price,
        start_date: prop_start_date,
        end_date: prop_end_date,
        tags: Array.isArray(prop_tags) ? prop_tags : [],
    });

    const today = new Date();
    const min_date = new Date(
        today.getUTCFullYear(),
        today.getUTCMonth(),
        today.getUTCDate() + 1,
    ).getTime();
    const max_date = new Date(
        today.getUTCFullYear() + 1,
        today.getUTCMonth(),
        today.getUTCDate() + 1,
    ).getTime();

    const [all_tags, set_all_tags] = useState([]);

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");
    const [tags_error_message, set_tags_error_message] = useState("");
    const [preview_url, set_preview_url] = useState(null);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/competition/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    // create url for image
    useEffect(() => {
        return handlePreviewUrl(competition.image, set_preview_url);
    }, [competition.image]);

    async function check_field_requirements() {
        const trimmed_title = competition.title.trim();
        const trimmed_description = competition.description.trim();
        const trimmed_links = competition.links.trim();

        set_competition((prev) => ({
            ...prev,
            title: trimmed_title,
            description: trimmed_description,
            links: trimmed_links,
        }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: COMPETITION_MIN_TITLE_LEN,
            maxLen: COMPETITION_MAX_TITLE_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isDescriptionValid = validateText({
            value: trimmed_description,
            fieldName: "Description",
            minLen: COMPETITION_MIN_DESCRIPTION_LEN,
            maxLen: COMPETITION_MAX_DESCRIPTION_LEN,
            required: true,
            error_handler: set_error_message,
        });

        if (competition.image === null) {
            set_error_message("Image is required");
            return false;
        }

        const isLinksValid = validateLinks({
            value: trimmed_links,
            fieldName: "Links",
            minLen: COMPETITION_MIN_LINKS_LEN,
            maxLen: COMPETITION_MAX_LINKS_LEN,
            error_handler: set_error_message,
        });

        const isTagsValid = validatePKRelation({
            value: competition.tags,
            fieldName: "Tags",
            minCount: COMPETITION_MIN_TAG_COUNT,
            maxCount: COMPETITION_MAX_TAG_COUNT,
            required: true,
            error_handler: set_error_message,
        });

        return (
            isTitleValid && isDescriptionValid && isLinksValid && isTagsValid
        );
    }

    async function create_form_data(creating = false) {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();

        // append only if we are creating a new competition, or edited (changed) a field
        if (creating || prop_title !== competition.title) {
            form_data.append("title", competition.title);
        }

        if (creating || prop_description !== competition.description) {
            form_data.append("description", competition.description);
        }

        if (creating || typeof competition.image !== "string") {
            form_data.append("image", competition.image);
        }

        if (creating || prop_links !== competition.links) {
            form_data.append(
                "links",
                JSON.stringify(competition.links.split(/\s+/).filter(Boolean)),
            );
        }

        if (creating || prop_price !== competition.price) {
            form_data.append("price", competition.price);
        }

        if (creating || prop_start_date !== competition.start_date) {
            form_data.append(
                "start_date",
                formatTimestampToDateString(competition.start_date),
            );
        }

        if (creating || prop_end_date !== competition.end_date) {
            form_data.append(
                "end_date",
                formatTimestampToDateString(competition.end_date),
            );
        }

        if (creating || !areArraysEqualAsSets(prop_tags, competition.tags)) {
            competition.tags.forEach((tag_id) =>
                form_data.append("tags", tag_id),
            );
        }

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data(true);
        if (!form_data) return;

        try {
            const create_competition_response = await apiFetch(
                "/api/competition/create-competition/",
                { method: "POST", body: form_data },
            );
            const [
                create_competition_success_data,
                create_competition_error_message,
                create_competition_ok,
            ] = await handleFetch(
                "create_competition",
                create_competition_response,
            );

            if (create_competition_ok) {
                navigate(`/competition/${create_competition_success_data.id}/`);
            } else {
                set_error_message(create_competition_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during competition creating.",
            );
        }
    }

    async function handle_edit() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            const edit_competition_response = await apiFetch(
                `/api/competition/edit-competition/${competition.id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_competition_success_data,
                edit_competition_error_message,
                edit_competition_ok,
            ] = await handleFetch(
                "edit_competition",
                edit_competition_response,
            );

            if (edit_competition_ok) {
                edit_callback();
            } else {
                set_error_message(edit_competition_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during competition editing.",
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
                const delete_competition_response = await apiFetch(
                    `/api/competition/delete-competition/${competition.id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_competition_success_data,
                    delete_competition_error_message,
                    delete_competition_ok,
                ] = await handleFetch(
                    "delete_competition",
                    delete_competition_response,
                );
                if (delete_competition_ok) {
                    navigate("/competition/");
                } else {
                    set_error_message(delete_competition_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during competition deleting.",
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
                    value={competition.title}
                    onChange={(e) =>
                        set_competition((prev) => ({
                            ...prev,
                            title: e.target.value,
                        }))
                    }
                    maxLength={COMPETITION_MAX_TITLE_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="description"
                    label="Description"
                    multiline
                    required
                    rows={5}
                    value={competition.description}
                    onChange={(e) =>
                        set_competition((prev) => ({
                            ...prev,
                            description: e.target.value,
                        }))
                    }
                    maxLength={COMPETITION_MAX_DESCRIPTION_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="price"
                    label="Price"
                    multiline={false}
                    required
                    rows={1}
                    value={competition.price}
                    onChange={(e) =>
                        set_competition((prev) => ({
                            ...prev,
                            price: parseInt(e.target.value.replace(",", "."))
                                ? parseInt(e.target.value.replace(",", "."))
                                : 0,
                        }))
                    }
                    maxLength={10}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="links"
                    label="Links"
                    multiline
                    rows={5}
                    value={competition.links}
                    onChange={(e) =>
                        set_competition((prev) => ({
                            ...prev,
                            links: e.target.value,
                        }))
                    }
                    maxLength={COMPETITION_MAX_LINKS_LEN}
                    fullWidth={true}
                />

                <p
                    style={{
                        ...theme.styles.descriptionText,
                        textAlign: "center",
                    }}
                >
                    Start & End Dates:
                </p>
                <DateSliderWrapper
                    value={[competition.start_date, competition.end_date]}
                    min={min_date}
                    max={max_date}
                    step={24 * 60 * 60 * 1000}
                    onChange={(e, [newStart, newEnd]) => {
                        set_competition((prev) => ({
                            ...prev,
                            start_date: newStart,
                            end_date: newEnd,
                        }));
                    }}
                    onChangeCommitted={(e, newValue) => {}}
                />

                {tags_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={tags_error_message}
                        on_close={() => {
                            set_tags_error_message("");
                        }}
                        error_title="Competition Tag Error"
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
                            selected_choices={competition.tags}
                            handle_choice_select={(tag_id) => {
                                handleIdLabelItemSlotSelect(
                                    tag_id,
                                    set_competition,
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
                        edit_text="Edit Competition"
                        delete_text="Delete Competition"
                        create_text="Publish Competition"
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!admin_permission) {
            return null;
        }
        const has_image = Boolean(competition.image);

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
                        {edit ? "Edit Competition" : "Create Competition"}
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
                                image={competition.image}
                                preview_url={preview_url}
                                alt={competition.title}
                                min_height={COMPETITION_IMAGE_MIN_H}
                                min_width={COMPETITION_IMAGE_MIN_W}
                                max_height={COMPETITION_IMAGE_MAX_H}
                                max_width={COMPETITION_IMAGE_MAX_W}
                                max_file_size={COMPETITION_IMAGE_MAX_SIZE}
                                set_error_fn={set_error_message}
                                set_state_fn={set_competition}
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
                            confirmation_message="Competition will be deleted completely"
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
                            error_title="Create Competition Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreateCompetitionPage;
