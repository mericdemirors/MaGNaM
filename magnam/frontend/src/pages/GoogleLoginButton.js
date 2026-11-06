import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";

import { apiFetch } from "../utils/csrf";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import SuccessPopUpWrapper from "../componentWrappers/SuccessPopUpWrapper";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

function GoogleLoginButton() {
    const { refreshAuth } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();

    const [error_message, set_error_message] = useState("");
    const [success_message, set_success_message] = useState("");
    const [loading, set_loading] = useState(false);

    const handle_google_success = async (credentialResponse) => {
        set_error_message("");
        set_success_message("");
        set_loading(true);

        try {
            const id_token = credentialResponse?.credential;
            if (!id_token) {
                set_error_message("Missing Google credential");
                throw new Error("Missing Google credential");
            }

            const response = await apiFetch("/api/profile/google-auth/", {
                method: "POST",
                body: JSON.stringify({ id_token }),
            });

            if (!response.ok) {
                set_error_message("Google authentication failed");
                throw new Error("Google authentication failed");
            }

            await refreshAuth();
            set_success_message(
                "Login successful' you are being redirected to homepage",
            );
            navigate("/");
        } catch (err) {
            set_error_message(
                err.message || "Network error during Google login",
            );
        } finally {
            set_loading(false);
        }
    };

    function render_main() {
        return (
            <div
                style={{
                    padding: theme.spacing.lg,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: theme.spacing.sm,
                    minWidth: theme.spacing.xxs,
                    boxSizing: "border-box",
                }}
            >
                {/* Google Button */}
                <GoogleLogin
                    onSuccess={handle_google_success}
                    onError={() => {
                        set_error_message(
                            "Google login was cancelled or failed.",
                        );
                    }}
                    useOneTap={false}
                    disabled={loading}
                />

                {/* Error popup */}
                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="Google Login Error"
                    />
                )}

                {/* Success popup currently disabled because it only flashes for a second*/}
                {/* {success_message && (
                    <SuccessPopUpWrapper
                        success_message={success_message}
                        on_close={() => set_success_message("")}
                        success_title="Google Login Successful"
                    />
                )} */}
            </div>
        );
    }

    return render_main();
}

export default GoogleLoginButton;
