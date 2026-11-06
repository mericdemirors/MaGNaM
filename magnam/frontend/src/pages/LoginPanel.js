import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, handleFetch } from "../utils/csrf";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

import {
    PROFILE_MAX_PASSWORD_LEN,
    PROFILE_MAX_EMAIL_LEN,
    PROFILE_MAX_NAME_LEN,
} from "../globals";

function LoginPanel() {
    const [identifier, set_identifier] = useState("");
    const [password, set_password] = useState("");
    const [loading, set_loading] = useState(false);
    const [error_message, set_error_message] = useState("");

    const { refreshAuth } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();

    const handle_login = async (e) => {
        e.preventDefault();
        set_loading(true);
        set_error_message("");

        try {
            const login_response = await apiFetch("/api/profile/login/", {
                method: "POST",
                body: JSON.stringify({ identifier, password }),
            });
            const [login_success_data, login_error_message, login_ok] =
                await handleFetch("login", login_response);

            if (login_ok) {
                await refreshAuth();
                navigate("/");
            } else {
                set_error_message(login_error_message);
            }
        } catch (err) {
            set_error_message(err.message || "Network error during login.");
        } finally {
            set_loading(false);
        }
    };

    function render_main() {
        return (
            <form onSubmit={handle_login}>
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
                        Login
                    </div>

                    <TextInputWrapper
                        name="identifier (email or name)"
                        label="Identifier (email or name)"
                        type="text"
                        value={identifier}
                        onChange={(e) => set_identifier(e.target.value)}
                        required
                        autoComplete="username"
                        maxLength={Math.max(
                            PROFILE_MAX_EMAIL_LEN,
                            PROFILE_MAX_NAME_LEN,
                        )}
                    />

                    <TextInputWrapper
                        name="password"
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(e) => set_password(e.target.value)}
                        required
                        autoComplete="current-password"
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
                            text={loading ? "Logging in..." : "Login"}
                        />
                    </div>

                    {error_message && (
                        <ErrorPopUpWrapper
                            error_message={error_message}
                            on_close={() => {
                                set_error_message("");
                            }}
                            error_title="Login Error"
                        />
                    )}
                </div>
            </form>
        );
    }

    return render_main();
}

export default LoginPanel;
