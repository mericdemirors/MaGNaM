import React, { useState } from "react";
import { useTheme } from "../context/ThemeContext";
import TextInputWrapper from "./TextInputWrapper";
import ButtonWrapper from "./ButtonWrapper";
import LoadSpinnerWrapper from "./LoadSpinnerWrapper";
import { darkenHex } from "../utils/helper_functions";
/**
 * CommentPanelWrapper — Reusable Comments UI Component
 */
export default function CommentPanelWrapper({
    num_of_comments,
    max_comment_len,
    handle_new_comment,
    scroll_ref,
    tree_comments,
    loading,
    logged_in_permission,
}) {
    const { theme } = useTheme();

    const [local_comment, set_local_comment] = useState("");
    const [is_posting_comment, set_is_posting_comment] = useState(false);
    const runAsync = async () => {
        if (!handle_new_comment || local_comment.trim() === "") return;

        try {
            set_is_posting_comment(true);
            const isSuccess = await handle_new_comment(local_comment);
            if (isSuccess) {
                set_local_comment("");
            }
        } finally {
            set_is_posting_comment(false);
        }
    };

    const CommentNode = (comment, indent_level) => {
        const depth = Math.min(indent_level, 4);
        const backgroundColor = darkenHex(
            theme.colors.background.app,
            depth * 3,
        );

        return (
            <div
                key={comment.id}
                style={{
                    paddingLeft:
                        indent_level < 4 ? `${indent_level * 0.75}rem` : "none",
                    paddingTop: theme.spacing.sm,
                    background: backgroundColor,
                    border: `2px solid ${theme.colors.border.subtle}`,
                    borderRadius: theme.radius.md,
                    gap: theme.spacing.xs,
                }}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: theme.spacing.sm,
                    }}
                >
                    {/* Reply button (permission-gated) */}
                    {logged_in_permission && (
                        <ButtonWrapper
                            text="Reply"
                            onClick={() => set_local_comment(`@${comment.id} `)}
                            visualVariant="outline"
                        />
                    )}

                    {/* Comment line (always visible, wraps fully) */}
                    <div
                        style={{
                            ...theme.styles.descriptionText,
                            overflowWrap: "anywhere",
                            wordBreak: "break-word",
                            flex: 1,
                        }}
                    >
                        {/* Author prefix (permission-gated) */}
                        {logged_in_permission && (
                            <span>
                                {`[${comment.id}] - ${comment.profile_name}: `}
                            </span>
                        )}

                        {/* Comment text (unconditional) */}
                        <span style={{ color: theme.colors.text.primary }}>
                            {comment.comment}
                        </span>
                    </div>
                </div>

                {/* Recursive children — unchanged */}
                {comment.children?.map((child) =>
                    CommentNode(child, indent_level + 1),
                )}
            </div>
        );
    };

    return (
        <div
            style={{
                paddingTop: theme.spacing.sm,
                background: theme.colors.background.surface,
                borderRadius: theme.radius.lg,
            }}
        >
            {/* Header */}
            <div
                style={{
                    ...theme.styles.titleText,
                    paddingBottom: theme.spacing.sm,
                }}
            >
                💬 ({num_of_comments})
            </div>

            {/* Write new comment — SAME permission logic */}
            {logged_in_permission && (
                <div
                    style={{
                        display: "flex",
                        alignItems: "flex-end",
                        gap: theme.spacing.sm,
                        padding: theme.spacing.sm,
                        flexDirection: "row", // Ensure side-by-side
                        alignItems: "stretch", // Forces children to fill vertical height
                    }}
                >
                    {/* Text input */}
                    <div style={{ flex: 1 }}>
                        <TextInputWrapper
                            name="new-comment"
                            label="Write a comment..."
                            value={local_comment}
                            onChange={(e) => set_local_comment(e.target.value)}
                            onKeyDown={(e) => {
                                if (
                                    e.key === "Enter" &&
                                    !e.shiftKey &&
                                    !is_posting_comment
                                ) {
                                    e.preventDefault(); // Prevents adding a new line in the textarea
                                    runAsync();
                                }
                            }}
                            multiline
                            rows={3}
                            maxLength={max_comment_len}
                            fullWidth
                        />
                    </div>

                    {/* Post button */}
                    <ButtonWrapper
                        text={is_posting_comment ? "Posting..." : "Post"}
                        onClick={runAsync}
                        disabled={
                            local_comment.trim() === "" || is_posting_comment
                        }
                        sx={{ height: "auto" }}
                    />
                </div>
            )}

            {/* Threaded comments */}
            <div
                ref={scroll_ref}
                style={{
                    maxHeight: theme.dimensions.lg,
                    overflowY: "auto",
                    padding: theme.spacing.sm,
                    borderRadius: theme.radius.lg,
                }}
            >
                {num_of_comments === 0 ? (
                    <div
                        style={{
                            ...theme.styles.metadataText,
                            textAlign: "center",
                            padding: theme.spacing.sm,
                        }}
                    >
                        No comments yet.
                    </div>
                ) : (
                    tree_comments.map((comment) => CommentNode(comment, 0))
                )}

                <LoadSpinnerWrapper loading={loading} />
            </div>
        </div>
    );
}
