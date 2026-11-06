import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, handleFetch } from "../utils/csrf";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { validateText } from "../utils/helper_validators";

import {
    PROFILE_MIN_PASSWORD_LEN,
    PROFILE_MAX_PASSWORD_LEN,
    PROFILE_MIN_EMAIL_LEN,
    PROFILE_MAX_EMAIL_LEN,
} from "../globals";

function RegisterPanel() {
    const [email, set_email] = useState("");
    const [password, set_password] = useState("");
    const [loading, set_loading] = useState(false);
    const [error_message, set_error_message] = useState("");

    const { refreshAuth } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();

    async function check_field_requirements() {
        const trimmed_email = email.trim();
        const trimmed_password = password.trim();

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

        const isPasswordValid = validateText({
            value: trimmed_password,
            fieldName: "Password",
            minLen: PROFILE_MIN_PASSWORD_LEN,
            maxLen: PROFILE_MAX_PASSWORD_LEN,
            required: true,
            error_handler: set_error_message,
        });

        return isEmailValid && isPasswordValid;
    }

    const handle_register = async (e) => {
        e.preventDefault();
        if (!(await check_field_requirements())) return;
        set_loading(true);
        set_error_message("");

        try {
            const register_response = await apiFetch("/api/profile/register/", {
                method: "POST",
                body: JSON.stringify({ email, password }),
            });
            const [register_success_data, register_error_message, register_ok] =
                await handleFetch("register", register_response);

            if (register_ok) {
                await refreshAuth();
                navigate("/");
            } else {
                set_error_message(register_error_message);
            }
        } catch (err) {
            set_error_message(err.message || "Network error during register.");
        } finally {
            set_loading(false);
        }
    };

    function render_main() {
        return (
            <form onSubmit={handle_register}>
                <div
                    style={{
                        padding: theme.spacing.lg,
                        display: "flex",
                        flexDirection: "column",
                        gap: theme.spacing.md,
                        minWidth: theme.spacing.xxs,
                        boxSizing: "border-box",
                    }}
                >
                    {/* Title */}
                    <div
                        style={{
                            ...theme.styles.titleText,
                            marginBottom: theme.spacing.sm,
                        }}
                    >
                        Register
                    </div>

                    {/* Email */}
                    <TextInputWrapper
                        name="email"
                        label="Email"
                        type="email"
                        value={email}
                        onChange={(e) => set_email(e.target.value)}
                        required
                        autoComplete="email"
                        maxLength={PROFILE_MAX_EMAIL_LEN}
                    />

                    {/* Password */}
                    <TextInputWrapper
                        name="password"
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(e) => set_password(e.target.value)}
                        required
                        autoComplete="new-password"
                        maxLength={PROFILE_MAX_PASSWORD_LEN}
                    />

                    {/* Centered button */}
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "center",
                            marginTop: theme.spacing.sm,
                        }}
                    >
                        <ButtonWrapper
                            type="submit"
                            disabled={loading}
                            text={loading ? "Registering..." : "Register"}
                        />
                    </div>

                    {error_message && (
                        <ErrorPopUpWrapper
                            error_message={error_message}
                            on_close={() => set_error_message("")}
                            error_title="Register Error"
                        />
                    )}
                </div>
            </form>
        );
    }

    return render_main();
}

export default RegisterPanel;
