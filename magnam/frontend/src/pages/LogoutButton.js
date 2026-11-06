import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch, handleFetch } from "../utils/csrf";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import { useAuth } from "../context/AuthContext";

function LogoutButton() {
    const [loading, set_loading] = useState(false);
    const [error_message, set_error_message] = useState("");

    const { logout } = useAuth();
    const navigate = useNavigate();

    const handle_logout = async () => {
        set_loading(true);
        set_error_message("");

        try {
            const logout_response = await apiFetch("/api/profile/logout/", {
                method: "POST",
            });
            const [logout_success_data, logout_error_message, logout_ok] =
                await handleFetch("logout", logout_response);

            if (logout_ok) {
                await logout();
                navigate("/");
            } else {
                set_error_message(logout_error_message);
            }
        } catch (err) {
            set_error_message(err.message || "Network error during logout.");
        } finally {
            set_loading(false);
        }
    };

    function render_main() {
        return (
            <div>
                <ButtonWrapper
                    text={loading ? "Logging out..." : "Logout"}
                    onClick={handle_logout}
                    disabled={loading}
                    visualVariant="ghost"
                />

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => {
                            set_error_message("");
                        }}
                        error_title="Logout Error"
                    />
                )}
            </div>
        );
    }

    return render_main();
}

export default LogoutButton;
