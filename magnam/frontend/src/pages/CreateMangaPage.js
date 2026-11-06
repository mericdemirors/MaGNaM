import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import ImageUploadFieldWrapper from "../componentWrappers/ImageUploadFieldWrapper";
import HasPermission from "../utils/HasPermission";
import {
    setFetchAndSet,
    handlePreviewUrl,
    areArraysEqualAsSets,
    handleIdLabelItemSlotSelect,
} from "../utils/helper_functions";
import { validateText, validatePKRelation } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    MANGA_MIN_TITLE_LEN,
    MANGA_MAX_TITLE_LEN,
    MANGA_MIN_DESCRIPTION_LEN,
    MANGA_MAX_DESCRIPTION_LEN,
    MANGA_MIN_COLLABORATOR_COUNT,
    MANGA_MAX_COLLABORATOR_COUNT,
    MANGA_IMAGE_MIN_H,
    MANGA_IMAGE_MIN_W,
    MANGA_IMAGE_MAX_H,
    MANGA_IMAGE_MAX_W,
    MANGA_IMAGE_MAX_SIZE,
    MANGA_MIN_TAG_COUNT,
    MANGA_MAX_TAG_COUNT,
} from "../globals";

function CreateMangaPage({
    id = -1,
    title: prop_title = "",
    description: prop_description = "",
    image: prop_image = null,
    collaborators: prop_collaborators = [],
    tags: prop_tags = [],
    edit = false,
    cancel_edit_func,
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();

    // in the editing page, we pass a cancel function. If it's not passed create page defaults for home navigation
    const handleCancel = cancel_edit_func || (() => navigate("/manga/"));

    const logged_in_permission = HasPermission("logged_in");

    const [manga, set_manga] = useState({
        id: id,
        title: prop_title,
        description: prop_description,
        image: prop_image,
        collaborators: Array.isArray(prop_collaborators)
            ? prop_collaborators
            : [],
        tags: Array.isArray(prop_tags) ? prop_tags : [],
    });
    const [all_profiles_following, set_all_profiles_following] = useState([]);
    const [collaborators_error_message, set_collaborators_error_message] =
        useState("");

    const [all_tags, set_all_tags] = useState([]);

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");
    const [tags_error_message, set_tags_error_message] = useState("");

    const [preview_url, set_preview_url] = useState(null);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/manga/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    // fetch the profiles the current user follows
    useEffect(() => {
        setFetchAndSet(
            "/api/profile/profiles-following-symmetric/",
            set_all_profiles_following,
            set_collaborators_error_message,
            "follows",
        );
    }, []);

    // create url for image
    useEffect(() => {
        return handlePreviewUrl(manga.image, set_preview_url);
    }, [manga.image]);

    async function check_field_requirements() {
        const trimmed_title = manga.title.trim();
        const trimmed_description = manga.description.trim();

        set_manga((prev) => ({
            ...prev,
            title: trimmed_title,
            description: trimmed_description,
        }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: MANGA_MIN_TITLE_LEN,
            maxLen: MANGA_MAX_TITLE_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isDescriptionValid = validateText({
            value: trimmed_description,
            fieldName: "Description",
            minLen: MANGA_MIN_DESCRIPTION_LEN,
            maxLen: MANGA_MAX_DESCRIPTION_LEN,
            required: true,
            error_handler: set_error_message,
        });

        if (manga.image === null) {
            set_error_message("Image is required");
            return false;
        }

        const isCollaboratorsValid = validatePKRelation({
            value: manga.collaborators,
            fieldName: "Collaborators",
            minCount: MANGA_MIN_COLLABORATOR_COUNT,
            maxCount: MANGA_MAX_COLLABORATOR_COUNT,
            error_handler: set_error_message,
        });

        const isTagsValid = validatePKRelation({
            value: manga.tags,
            fieldName: "Tags",
            minCount: MANGA_MIN_TAG_COUNT,
            maxCount: MANGA_MAX_TAG_COUNT,
            required: true,
            error_handler: set_error_message,
        });

        // contains both or none of original and scan/translation tag
        if (
            (manga.tags.includes(1) && manga.tags.includes(2)) ||
            (!manga.tags.includes(1) && !manga.tags.includes(2))
        ) {
            set_error_message(
                "Please select either original, or scan/translation",
            );
            return false;
        }

        return (
            isTitleValid &&
            isDescriptionValid &&
            isCollaboratorsValid &&
            isTagsValid
        );
    }

    async function create_form_data(creating = false) {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();

        // append only if we are creating a new manga, or edited (changed) a field
        if (creating || prop_title !== manga.title) {
            form_data.append("title", manga.title);
        }

        if (creating || prop_description !== manga.description) {
            form_data.append("description", manga.description);
        }

        if (creating || typeof manga.image !== "string") {
            form_data.append("image", manga.image);
        }

        if (
            creating ||
            !areArraysEqualAsSets(prop_collaborators, manga.collaborators)
        ) {
            manga.collaborators.forEach((collaborator_id) =>
                form_data.append("collaborators", collaborator_id),
            );
        }

        if (creating || !areArraysEqualAsSets(prop_tags, manga.tags)) {
            manga.tags.forEach((tag_id) => form_data.append("tags", tag_id));
        }

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data(true);
        if (!form_data) return;

        try {
            const create_manga_response = await apiFetch(
                "/api/manga/create-manga/",
                { method: "POST", body: form_data },
            );
            const [
                create_manga_success_data,
                create_manga_error_message,
                create_manga_ok,
            ] = await handleFetch("create_manga", create_manga_response);

            if (create_manga_ok) {
                navigate(`/manga/${create_manga_success_data.id}/`);
            } else {
                set_error_message(create_manga_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during manga creating.",
            );
        }
    }

    async function handle_edit() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            const edit_manga_response = await apiFetch(
                `/api/manga/edit-manga/${manga.id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_manga_success_data,
                edit_manga_error_message,
                edit_manga_ok,
            ] = await handleFetch("edit_manga", edit_manga_response);

            if (edit_manga_ok) {
                edit_callback();
            } else {
                set_error_message(edit_manga_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during manga editing.",
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
                const delete_manga_response = await apiFetch(
                    `/api/manga/delete-manga/${manga.id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_manga_success_data,
                    delete_manga_error_message,
                    delete_manga_ok,
                ] = await handleFetch("delete_manga", delete_manga_response);

                if (delete_manga_ok) {
                    navigate("/manga/");
                } else {
                    set_error_message(delete_manga_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during manga deleting.",
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
                {collaborators_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={collaborators_error_message}
                        on_close={() => {
                            set_collaborators_error_message("");
                        }}
                        error_title="Manga Collaborator Error"
                    />
                ) : (
                    <>
                        <p
                            style={{
                                ...theme.styles.descriptionText,
                                textAlign: "center",
                            }}
                        >
                            Collaborators
                        </p>
                        <MultipleChoiceSelectionWrapper
                            all_choices={all_profiles_following.map((c) => ({
                                id: c.id,
                                label: c.profile_name,
                            }))}
                            selected_choices={manga.collaborators}
                            handle_choice_select={(collaborator_id) => {
                                handleIdLabelItemSlotSelect(
                                    collaborator_id,
                                    set_manga,
                                    "collaborators",
                                );
                            }}
                        />
                    </>
                )}

                <TextInputWrapper
                    name="title"
                    label="Title"
                    multiline
                    required
                    rows={3}
                    value={manga.title}
                    onChange={(e) =>
                        set_manga((prev) => ({
                            ...prev,
                            title: e.target.value,
                        }))
                    }
                    maxLength={MANGA_MAX_TITLE_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="description"
                    label="Description"
                    multiline
                    required
                    rows={5}
                    value={manga.description}
                    onChange={(e) =>
                        set_manga((prev) => ({
                            ...prev,
                            description: e.target.value,
                        }))
                    }
                    maxLength={MANGA_MAX_DESCRIPTION_LEN}
                    fullWidth={true}
                />

                {tags_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={tags_error_message}
                        on_close={() => {
                            set_tags_error_message("");
                        }}
                        error_title="Manga Tag Error"
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
                            selected_choices={manga.tags}
                            handle_choice_select={(tag_id) => {
                                handleIdLabelItemSlotSelect(
                                    tag_id,
                                    set_manga,
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
                        edit_text="Edit Manga"
                        delete_text="Delete Manga"
                        create_text="Publish Manga"
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }

        const has_image = Boolean(manga.image);

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
                        {edit ? "Edit Manga" : "Create Manga"}
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
                                image={manga.image}
                                preview_url={preview_url}
                                alt={manga.title}
                                min_height={MANGA_IMAGE_MIN_H}
                                min_width={MANGA_IMAGE_MIN_W}
                                max_height={MANGA_IMAGE_MAX_H}
                                max_width={MANGA_IMAGE_MAX_W}
                                max_file_size={MANGA_IMAGE_MAX_SIZE}
                                set_error_fn={set_error_message}
                                set_state_fn={set_manga}
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
                            confirmation_message="Manga will be deleted completely"
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
                            error_title="Create Manga Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreateMangaPage;
