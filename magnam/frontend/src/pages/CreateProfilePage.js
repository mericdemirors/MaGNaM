import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import EditDeleteCreateButtonsWrapper from "../componentWrappers/EditDeleteCreateButtonsWrapper";
import ImageUploadFieldWrapper from "../componentWrappers/ImageUploadFieldWrapper";
import HasPermission from "../utils/HasPermission";
import { useAuth } from "../context/AuthContext";
import { handlePreviewUrl } from "../utils/helper_functions";
import { validateText } from "../utils/helper_validators";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    PROFILE_MIN_NAME_LEN,
    PROFILE_MAX_NAME_LEN,
    PROFILE_MIN_PASSWORD_LEN,
    PROFILE_MAX_PASSWORD_LEN,
    PROFILE_MIN_EMAIL_LEN,
    PROFILE_MAX_EMAIL_LEN,
    PROFILE_IMAGE_MIN_H,
    PROFILE_IMAGE_MIN_W,
    PROFILE_IMAGE_MAX_H,
    PROFILE_IMAGE_MAX_W,
    PROFILE_IMAGE_MAX_SIZE,
} from "../globals";

function CreateProfilePage({
    id = -1,
    profile_name: prop_profile_name = "",
    email: prop_email = "",
    image: prop_image = null,
    edit = false,
    cancel_edit_func = () => {},
    edit_callback = () => {},
}) {
    const { theme } = useTheme();
    const navigate = useNavigate();
    const { logout, refreshAuth } = useAuth();

    const logged_in_permission = HasPermission("logged_in", id);

    const [profile, set_profile] = useState({
        id: id,
        profile_name: prop_profile_name,
        email: prop_email,
        password: "",
        image: prop_image,
    });

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [error_message, set_error_message] = useState("");
    const [preview_url, set_preview_url] = useState(null);

    useEffect(() => {
        return handlePreviewUrl(profile.image, set_preview_url);
    }, [profile.image]);

    async function check_field_requirements() {
        const trimmed_profile_name = profile.profile_name.trim();
        const trimmed_email = profile.email.trim();
        const trimmed_password = profile.password.trim();

        set_profile((prev) => ({
            ...prev,
            profile_name: trimmed_profile_name,
            email: trimmed_email,
            password: trimmed_password,
        }));

        const isProfileNameValid = validateText({
            value: trimmed_profile_name,
            fieldName: "Profile_name",
            minLen: PROFILE_MIN_NAME_LEN,
            maxLen: PROFILE_MAX_NAME_LEN,
            required: true,
            error_handler: set_error_message,
        });

        const isEmailValid = validateText({
            value: trimmed_email,
            fieldName: "Email",
            minLen: PROFILE_MIN_EMAIL_LEN,
            maxLen: PROFILE_MAX_EMAIL_LEN,
            required: true,
            error_handler: set_error_message,
        });

        if (!trimmed_email.includes("@")) {
            set_error_message("Email must contain '@' character");
            return false;
        }

        // we dont use the regular text validation because we need to tell the user to leave it empty for no change
        if (
            trimmed_password &&
            (trimmed_password.length < PROFILE_MIN_PASSWORD_LEN ||
                trimmed_password.length > PROFILE_MAX_PASSWORD_LEN)
        ) {
            set_error_message(
                `Left the password field empty to continue using old password, new password must be at least ${PROFILE_MIN_PASSWORD_LEN} and at most ${PROFILE_MAX_PASSWORD_LEN} characters`,
            );
            return false;
        }

        if (profile.image === null) {
            set_error_message("Image is required");
            return false;
        }

        return isProfileNameValid && isEmailValid;
    }

    async function handle_edit() {
        if (!(await check_field_requirements())) return;

        const form_data = new FormData();

        // append only if it's edited
        if (prop_profile_name !== profile.profile_name) {
            form_data.append("profile_name", profile.profile_name);
        }

        if (prop_email !== profile.email) {
            form_data.append("email", profile.email);
        }

        if (profile.password) {
            form_data.append("password", profile.password);
        }

        if (typeof profile.image !== "string") {
            form_data.append("image", profile.image);
        }

        try {
            const edit_profile_response = await apiFetch(
                `/api/profile/edit-profile/${id}/`,
                { method: "PATCH", body: form_data },
            );
            const [
                edit_profile_success_data,
                edit_profile_error_message,
                edit_profile_ok,
            ] = await handleFetch("edit_profile", edit_profile_response);

            if (edit_profile_ok) {
                await refreshAuth();
                edit_callback();
            } else {
                set_error_message(edit_profile_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during profile editing.",
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
                const delete_profile_response = await apiFetch(
                    `/api/profile/delete-profile/${profile.id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_profile_success_data,
                    delete_profile_error_message,
                    delete_profile_ok,
                ] = await handleFetch(
                    "delete_profile",
                    delete_profile_response,
                );

                if (delete_profile_ok) {
                    if (delete_profile_success_data.logout_after_deletion) {
                        await logout();
                    }
                    navigate("/");
                } else {
                    set_error_message(delete_profile_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during profile deletinon.",
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
                    name="name"
                    label="Name"
                    required
                    value={profile.profile_name}
                    onChange={(e) =>
                        set_profile((prev) => ({
                            ...prev,
                            profile_name: e.target.value,
                        }))
                    }
                    maxLength={PROFILE_MAX_NAME_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="email"
                    label="Email"
                    required
                    value={profile.email}
                    onChange={(e) =>
                        set_profile((prev) => ({
                            ...prev,
                            email: e.target.value,
                        }))
                    }
                    maxLength={PROFILE_MAX_EMAIL_LEN}
                    fullWidth={true}
                />

                <TextInputWrapper
                    name="password"
                    label="Password"
                    required
                    value={profile.password}
                    onChange={(e) =>
                        set_profile((prev) => ({
                            ...prev,
                            password: e.target.value,
                        }))
                    }
                    maxLength={PROFILE_MAX_PASSWORD_LEN}
                    fullWidth={true}
                />
                <p style={theme.styles.metadataText}>
                    Left the password field empty to continue using old password
                </p>

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
                        on_cancel={cancel_edit_func}
                        edit_text="Edit Profile"
                        delete_text="Delete Profile"
                        at_profilepage={true}
                    />
                </div>
            </div>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }

        const has_image = Boolean(profile.image);

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
                        Edit Profile
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
                                image={profile.image}
                                preview_url={preview_url}
                                alt={profile.profile_name}
                                max_preview_width={`${PROFILE_IMAGE_MAX_H}px`}
                                min_height={PROFILE_IMAGE_MIN_H}
                                min_width={PROFILE_IMAGE_MIN_W}
                                max_height={PROFILE_IMAGE_MAX_H}
                                max_width={PROFILE_IMAGE_MAX_W}
                                max_file_size={PROFILE_IMAGE_MAX_SIZE}
                                set_error_fn={set_error_message}
                                set_state_fn={set_profile}
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
                            confirmation_message="Profile will be deleted completely (Your items' ownership will be passed to collaborators if any)"
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
                            error_title="Edit Profile Error"
                        />
                    )}
                </div>
            </div>
        );
    }

    return render_main();
}

export default CreateProfilePage;
