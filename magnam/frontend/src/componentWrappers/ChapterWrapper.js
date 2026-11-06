import React from "react";
import HasPermission from "../utils/HasPermission";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { useTheme } from "../context/ThemeContext";
import { download_chapter_pdf } from "../utils/helper_functions";

export default function ChapterWrapper({
    chapter,
    manga_title,
    logged_in_permission,
    logged_in_manga_owner_permission,
    on_edit = () => {},
    on_buy = () => {},
    on_read = () => {},
}) {
    const { theme } = useTheme();

    if (!chapter) return null;

    const {
        id,
        title,
        no,
        owner,
        collaborators = [],
        publish_date,
        price,
        pdf,
        is_user_bought,
        is_user_read,
    } = chapter;
    const chapter_edit_permission =
        HasPermission("logged_in", owner?.id) ||
        logged_in_manga_owner_permission;

    return (
        <div
            style={{
                background: is_user_read
                    ? theme.colors.background.app
                    : theme.colors.background.surface,
                borderRadius: theme.radius.md,
                padding: theme.spacing.lg,
                boxShadow: theme.colors.shadow.card,
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.md,
                transition: theme.transition.normal,
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                }}
            >
                <div>
                    <div
                        style={{
                            ...theme.styles.subtitleText,
                            paddingBottom: theme.spacing.sm,
                        }}
                    >
                        {title}
                    </div>

                    <div style={{ ...theme.styles.descriptionText }}>
                        Chapter: {no}
                    </div>
                </div>
            </div>
            {/* Metadata */}
            <div
                style={{
                    ...theme.styles.metadataText,
                    display: "flex",
                    gap: theme.spacing.sm,
                    flexWrap: "wrap",
                }}
            >
                <span>{publish_date}</span>
                {owner && <span>{owner.profile_name}</span>}
                {collaborators.length > 0 && (
                    <span>
                        {`+ (${collaborators.map((c) => c.profile_name).join(", ")})`}
                    </span>
                )}
            </div>
            {/* Actions */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginTop: theme.spacing.sm,
                }}
            >
                <div
                    style={{
                        display: "flex",
                        gap: theme.spacing.sm,
                        alignItems: "center",
                    }}
                >
                    {logged_in_permission ? (
                        is_user_bought ? (
                            <>
                                <ButtonWrapper
                                    text={is_user_read ? "Re-read" : "Read"}
                                    onClick={on_read}
                                    visualVariant={
                                        is_user_read ? "outline" : "soft"
                                    }
                                />
                                {pdf && (
                                    <ButtonWrapper
                                        text="Download"
                                        onClick={async () => {
                                            try {
                                                await download_chapter_pdf(
                                                    pdf,
                                                    manga_title,
                                                    no,
                                                    title,
                                                );
                                            } catch (err) {
                                                console.error(
                                                    "Download failed:",
                                                    err,
                                                );
                                            }
                                        }}
                                        visualVariant="outline"
                                    />
                                )}
                            </>
                        ) : (
                            <ButtonWrapper
                                text={`Buy: ${price}${theme.coin}`}
                                onClick={on_buy}
                                visualVariant="danger"
                            />
                        )
                    ) : (
                        <p style={theme.styles.metadataText}>
                            Log in to buy/read/download
                        </p>
                    )}
                </div>

                {chapter_edit_permission && (
                    <ButtonWrapper
                        text="Edit"
                        onClick={on_edit}
                        visualVariant="outline"
                    />
                )}
            </div>{" "}
        </div>
    );
}
