import React from "react";
import HasPermission from "../utils/HasPermission";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { useTheme } from "../context/ThemeContext";
import { darkenHex } from "../utils/helper_functions";

const ERROR_PRIORITY_MAP = {
    0: "📍",
    1: "📍",
    2: "📌",
    3: "📌",
    4: "❗",
    5: "❗",
    6: "‼️",
    7: "‼️",
    8: "🚨",
    9: "🚨",
};

const getEmoji = (val) => ERROR_PRIORITY_MAP[val] ?? "❓";

export default function KanbanTaskWrapper({
    kanban_task,
    logged_in_permission,
    on_upvote = () => {},
    on_downvote = () => {},
    on_delete = () => {},
}) {
    const { theme } = useTheme();
    if (!kanban_task) return null;

    const {
        id,
        importance,
        tags = [],
        description,
        num_of_upvotes,
        num_of_downvotes,
        creator_id,
    } = kanban_task;

    const kanban_task_owner_permission = HasPermission("logged_in", creator_id);
    const depth = Math.min(importance, 4);
    const backgroundColor = darkenHex(
        theme.colors.background.app_error,
        depth * 10,
    );

    return (
        <div
            style={{
                background: backgroundColor,
                borderRadius: theme.radius.md,
                padding: theme.spacing.md,
                boxShadow: theme.colors.shadow.card,
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.sm,
                transition: theme.transition.normal,
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "baseline",
                    gap: theme.spacing.sm,
                }}
            >
                <span
                    style={{
                        ...theme.styles.subtitleText,
                        fontWeight: theme.typography.fontWeight.bold,
                    }}
                >
                    {getEmoji(importance)} {importance}
                </span>

                {tags.length > 0 && (
                    <span
                        style={{
                            ...theme.styles.descriptionText,
                            textAlign: "right",
                        }}
                    >
                        {tags.map((t) => t.label).join(", ")}
                    </span>
                )}
            </div>

            {/* Body */}
            <div
                style={{
                    ...theme.styles.descriptionText,
                    lineHeight: theme.typography.lineHeight.relaxed,
                    wordBreak: "break-word",
                    overflowWrap: "anywhere",
                }}
            >
                {description}
            </div>

            {/* Footer / Actions */}
            {(logged_in_permission || kanban_task_owner_permission) && (
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        paddingTop: theme.spacing.sm,
                    }}
                >
                    {logged_in_permission ? (
                        <div style={{ display: "flex", gap: theme.spacing.sm }}>
                            <ButtonWrapper
                                onClick={() => on_upvote(id)}
                                text={`▲ ${num_of_upvotes}`}
                                visualVariant="outline"
                            />
                            <ButtonWrapper
                                onClick={() => on_downvote(id)}
                                text={`▼ ${num_of_downvotes}`}
                                visualVariant="outline"
                            />
                        </div>
                    ) : (
                        <div />
                    )}

                    {kanban_task_owner_permission && (
                        <ButtonWrapper
                            onClick={() => on_delete(id)}
                            text="Delete"
                            visualVariant="danger"
                        />
                    )}
                </div>
            )}
        </div>
    );
}
