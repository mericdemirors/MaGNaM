import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import SuccessPopUpWrapper from "../componentWrappers/SuccessPopUpWrapper";
import { apiFetch, handleFetch } from "../utils/csrf";

function VerifyProfilePage() {
    const navigate = useNavigate();
    const { token: token_from_url } = useParams();
    const [success_message, set_success_message] = useState("");
    const [error_message, set_error_message] = useState("");
    const [countdown, set_countdown] = useState(3);

    useEffect(() => {
        if (!token_from_url) {
            set_error_message("Verification token missing.");
            return;
        }

        const verify_profile = async () => {
            try {
                const verify_response = await apiFetch(
                    `/api/profile/verify/${token_from_url}/`,
                    { method: "POST" },
                );
                const [verify_success_data, verify_error_msg, verify_ok] =
                    await handleFetch("verify_profile", verify_response);

                if (verify_ok) {
                    set_success_message(verify_success_data);
                } else {
                    set_error_message(
                        verify_error_msg || "Verification failed.",
                    );
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during verification.",
                );
            }
        };

        verify_profile();
    }, [token_from_url]);

    useEffect(() => {
        let timer_interval = null;

        if (success_message) {
            timer_interval = setInterval(() => {
                set_countdown((prev_count) => {
                    if (prev_count <= 1) {
                        // Time is up, clear interval and navigate
                        clearInterval(timer_interval);
                        navigate("/");
                        return 0;
                    }
                    return prev_count - 1;
                });
            }, 1000);
        }

        // Cleanup: Clear interval if component unmounts or success_message changes
        return () => {
            if (timer_interval) clearInterval(timer_interval);
        };
    }, [success_message, navigate]);

    return (
        <>
            {error_message && (
                <ErrorPopUpWrapper
                    error_title="Verification Error"
                    error_message={error_message}
                    on_close={() => set_error_message("")}
                />
            )}

            {success_message && (
                <SuccessPopUpWrapper
                    success_title="Verification Success"
                    success_message={`${success_message}. Redirecting to homepage in ${countdown}...`}
                    on_close={() => navigate("/")}
                />
            )}
        </>
    );
}

export default VerifyProfilePage;
