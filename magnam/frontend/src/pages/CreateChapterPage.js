import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

import FileUploadWrapper from "../componentWrappers/FileUploadWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import HasPermission from "../utils/HasPermission";
import pdfCheck from "../utils/pdfCheck";
import {
    setFetchAndSet,
    areArraysEqualAsSets,
    handleIdLabelItemSlotSelect,
} from "../utils/helper_functions";
import { validateText, validatePKRelation } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    CHAPTER_MIN_TITLE_LEN,
    CHAPTER_MAX_TITLE_LEN,
    CHAPTER_MIN_NO_LEN,
    CHAPTER_MAX_NO_LEN,
    CHAPTER_MIN_COLLABORATOR_COUNT,
    CHAPTER_MAX_COLLABORATOR_COUNT,
    CHAPTER_PDF_MAX_SIZE,
    CHAPTER_PDF_MAX_PAGE,
    ALLOWED_PDF_EXTENSIONS,
} from "../globals";

function CreateChapterPage({
    id = -1,
    title: prop_title = "",
    no: prop_no = "",
    collaborators: prop_collaborators = [],
    pdf: prop_pdf = null,
    price: prop_price = 0,
    edit = false,
    cancel_edit_func,
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");

    const { manga_id: manga_id_from_url } = useParams();
    const navigate = useNavigate();

    // in the editing page, we pass a cancel function. If it's not passed create page defaults for navigation to manga's page
    const handleCancel =
        cancel_edit_func || (() => navigate(`/manga/${manga_id_from_url}/`));

    const [chapter, set_chapter] = useState({
        id: id,
        title: prop_title,
        no: prop_no,
        collaborators: Array.isArray(prop_collaborators)
            ? prop_collaborators
            : [],
        pdf: prop_pdf,
        price: prop_price,
    });
    const [all_profiles_following, set_all_profiles_following] = useState([]);
    const [collaborators_error_message, set_collaborators_error_message] =
        useState("");

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");

    // fetch the profiles the current user follows
    useEffect(() => {
        setFetchAndSet(
            "/api/profile/profiles-following-symmetric/",
            set_all_profiles_following,
            set_collaborators_error_message,
            "follows",
        );
    }, []);

    async function check_file_requirements_and_set(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (
            await pdfCheck(
                file,
                CHAPTER_PDF_MAX_SIZE,
                CHAPTER_PDF_MAX_PAGE,
                set_error_message,
            )
        ) {
            set_chapter((prev) => ({ ...prev, pdf: file }));
        } else {
            e.target.value = null;
            set_chapter((prev) => ({ ...prev, pdf: null }));
        }
    }

    async function check_field_requirements() {
        const trimmed_title = chapter.title.trim();
        const trimmed_no = chapter.no.trim();
        set_chapter((prev) => ({
            ...prev,
            title: trimmed_title,
            no: trimmed_no,
        }));

        const isTitleValid = validateText({
            value: trimmed_title,
            fieldName: "Title",
            minLen: CHAPTER_MIN_TITLE_LEN,
            maxLen: CHAPTER_MAX_TITLE_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isNoValid = validateText({
            value: trimmed_no,
            fieldName: "No",
            minLen: CHAPTER_MIN_NO_LEN,
            maxLen: CHAPTER_MAX_NO_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isCollaboratorsValid = validatePKRelation({
            value: chapter.collaborators,
            fieldName: "Collaborators",
            minCount: CHAPTER_MIN_COLLABORATOR_COUNT,
            maxCount: CHAPTER_MAX_COLLABORATOR_COUNT,
            error_handler: set_error_message,
        });

        if (chapter.price < 0) {
            set_error_message("Price must be at least 0");
            return false;
        }

        if (chapter.pdf === null) {
            set_error_message("pdf is required");
            return false;
        }

        return isTitleValid && isNoValid && isCollaboratorsValid;
    }

    async function create_form_data(creating = false) {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();

        // append only if we are creating a new chapter, or edited (changed) a field
        if (creating || prop_title !== chapter.title) {
            form_data.append("title", chapter.title);
        }

        if (creating || prop_no !== chapter.no) {
            form_data.append("no", chapter.no);
        }

        if (creating || typeof chapter.pdf !== "string") {
            form_data.append("pdf", chapter.pdf);
        }

        if (creating || prop_price !== chapter.price) {
            form_data.append("price", chapter.price);
        }

        if (
            creating ||
            !areArraysEqualAsSets(prop_collaborators, chapter.collaborators)
        ) {
            chapter.collaborators.forEach((collaborator_id) =>
                form_data.append("collaborators", collaborator_id),
            );
        }

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data(true);
        if (!form_data) return;

        try {
            const create_chapter_response = await apiFetch(
                `/api/manga/create-chapter/${manga_id_from_url}/`,
                { method: "POST", body: form_data },
            );
            const [
                create_chapter_success_data,
                create_chapter_error_message,
                create_chapter_ok,
            ] = await handleFetch("create_chapter", create_chapter_response);

            if (create_chapter_ok) {
                navigate(`/manga/${manga_id_from_url}/`);
            } else {
                set_error_message(create_chapter_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during chapter creation.",
            );
        }
    }

    async function handle_edit() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            const edit_chapter_response = await apiFetch(
                `/api/manga/edit-chapter/${chapter.id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_chapter_success_data,
                edit_chapter_error_message,
                edit_chapter_ok,
            ] = await handleFetch("edit_chapter", edit_chapter_response);

            if (edit_chapter_ok) {
                edit_callback();
            } else {
                set_error_message(edit_chapter_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during chapter editing.",
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
                const delete_chapter_response = await apiFetch(
                    `/api/manga/delete-chapter/${chapter.id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_chapter_success_data,
                    delete_chapter_error_message,
                    delete_chapter_ok,
                ] = await handleFetch(
                    "delete_chapter",
                    delete_chapter_response,
                );
                if (delete_chapter_ok) {
                    edit_callback();
                } else {
                    set_error_message(delete_chapter_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during chapter deletion.",
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
                    value={chapter.title}
                    onChange={(e) =>
                        set_chapter((prev) => ({
                            ...prev,
                            title: e.target.value,
                        }))
                    }
                    maxLength={CHAPTER_MAX_TITLE_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="no"
                    label="No"
                    multiline={false}
                    required
                    rows={2}
                    value={chapter.no}
                    onChange={(e) =>
                        set_chapter((prev) => ({ ...prev, no: e.target.value }))
                    }
                    maxLength={CHAPTER_MAX_NO_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="price"
                    label="Price"
                    multiline={false}
                    required
                    rows={1}
                    value={chapter.price}
                    onChange={(e) =>
                        set_chapter((prev) => ({
                            ...prev,
                            price: parseInt(e.target.value.replace(",", "."))
                                ? parseInt(e.target.value.replace(",", "."))
                                : 0,
                        }))
                    }
                    maxLength={10}
                    fullWidth={true}
                />

                {collaborators_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={collaborators_error_message}
                        on_close={() => {
                            set_collaborators_error_message("");
                        }}
                        error_title="Chapter Collaborator Error"
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
                            selected_choices={chapter.collaborators}
                            handle_choice_select={(collaborator_id) => {
                                handleIdLabelItemSlotSelect(
                                    collaborator_id,
                                    set_chapter,
                                    "collaborators",
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
                        edit_text="Edit Chapter"
                        delete_text="Delete Chapter"
                        create_text="Publish Chapter"
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }

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
                        {edit ? "Edit Chapter" : "Create Chapter"}
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
                        {/* File column */}
                        <div
                            style={{
                                flex: "0 0 70%",
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                justifyContent: "center",
                                gap: theme.spacing.md,
                                border: `3px dashed ${theme.colors.border.subtle}`,
                                borderRadius: theme.radius.md,
                                backgroundColor:
                                    theme.colors.background.app_darker,
                            }}
                        >
                            <p style={{ ...theme.styles.descriptionText }}>
                                Max {CHAPTER_PDF_MAX_SIZE / (1024 * 1024)}MB
                            </p>

                            <FileUploadWrapper
                                label="Upload PDF"
                                onChange={check_file_requirements_and_set}
                                accept={ALLOWED_PDF_EXTENSIONS.map(
                                    (ext) => `.${ext}`,
                                ).join(",")}
                                selectedFiles={chapter.pdf ? [chapter.pdf] : []}
                                at_create_chapter_page
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
                            confirmation_message="Chapter will be deleted completely"
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
                            error_title="Create Chapter Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreateChapterPage;
