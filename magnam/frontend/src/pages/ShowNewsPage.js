import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";

import CreateNewsPage from "./CreateNewsPage";
import HasPermission from "../utils/HasPermission";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    parsed_link_injected_text,
    render_links,
} from "../componentWrappers/helper_components";

function ShowNewsPage() {
    const { theme } = useTheme();
    const admin_permission = HasPermission("admin");
    const logged_in_permission = HasPermission("logged_in");

    const { news_id: news_id_from_url } = useParams();

    const [news, set_news] = useState({
        id: -1,
        title: "",
        description: "",
        image: null,
        links: "",
    });
    const [show_edit, set_show_edit_page] = useState(false);
    const [error_message, set_error_message] = useState("");

    const get_news_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_news_response = await apiFetch(
                    `/api/news/get-news/${news_id_from_url}/`,
                    options,
                );
                const [
                    get_news_success_data,
                    get_news_error_message,
                    get_news_ok,
                ] = await handleFetch("get_news", get_news_response);

                if (get_news_ok) {
                    // we have the data body only if request was successful
                    set_news({
                        id: get_news_success_data.id,
                        title: get_news_success_data.title ?? "",
                        description: get_news_success_data.description ?? "",
                        image: get_news_success_data.image ?? null,
                        links: Array.isArray(get_news_success_data.links)
                            ? get_news_success_data.links.join(" ")
                            : "",
                    });

                    set_show_edit_page(false);
                    set_error_message("");
                } else {
                    set_error_message(get_news_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during getting news.",
                );
            }
        },
        [news_id_from_url],
    );

    // call the get_news_details when news_id_in_url changes
    useEffect(() => {
        const controller = new AbortController();
        get_news_details(controller.signal);

        return () => controller.abort();
    }, [news_id_from_url, get_news_details]);

    function render_main() {
        if (admin_permission && show_edit) {
            return (
                <div>
                    <CreateNewsPage
                        id={news.id}
                        title={news.title}
                        description={news.description}
                        image={news.image}
                        links={news.links}
                        edit={true}
                        cancel_edit_func={() => set_show_edit_page(false)}
                        edit_callback={get_news_details}
                    />
                </div>
            );
        }

        return (
            <div>
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

                {/* Main news content */}
                <div style={{ padding: theme.spacing.lg }}>
                    {/* Title */}
                    <div
                        style={{
                            ...theme.styles.titleText,
                            textAlign: "left",
                            marginTop: theme.spacing.sm,
                            marginBottom: theme.spacing.sm,
                        }}
                    >
                        {news.title}
                    </div>

                    {/* Image + Description row */}
                    <div
                        style={{
                            display: "flex",
                            gap: theme.spacing.lg,
                            marginTop: theme.spacing.lg,
                            alignItems: "flex-start",
                        }}
                    >
                        {/* Image – 70% */}
                        {news.image && (
                            <div style={{ flex: "0 0 70%" }}>
                                <img
                                    src={news.image}
                                    alt={news.title}
                                    loading="lazy"
                                    style={{
                                        width: "100%",
                                        borderRadius: theme.radius.md,
                                    }}
                                />
                            </div>
                        )}

                        {/* Description – 30% */}
                        <div
                            style={{
                                flex: "0 0 30%",
                                padding: theme.spacing.lg,
                            }}
                        >
                            {/* Admin actions */}
                            {admin_permission && (
                                <div
                                    style={{
                                        flex: "0 0 30%",
                                        padding: theme.spacing.lg,
                                        display: "flex",
                                        justifyContent: "center", // Centers horizontally
                                        alignItems: "center", // Centers vertically
                                        gap: theme.spacing.sm, // Adds space between buttons
                                    }}
                                >
                                    <ButtonWrapper
                                        text="Edit News"
                                        onClick={() => set_show_edit_page(true)}
                                        visualVariant="outline"
                                    />
                                </div>
                            )}

                            {parsed_link_injected_text(news.description, theme)}
                        </div>
                    </div>

                    {/* Links (full width, below) */}
                    {render_links({ links: news.links })}
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="News Error"
                    />
                )}
            </div>
        );
    }

    return render_main();
}

export default ShowNewsPage;
