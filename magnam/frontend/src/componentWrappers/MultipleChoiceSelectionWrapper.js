import React from "react";
import { Button } from "@mui/material";
import { useTheme } from "../context/ThemeContext";

/**
 * MultipleChoiceSelectionWrapper
 * ------------------------------
 * Left-to-right, wrapped, gallery-friendly choice buttons
 */
export default function MultipleChoiceSelectionWrapper({
    all_choices = [],
    selected_choices = [],
    handle_choice_select = () => {},
    sx = {},
}) {
    const { theme } = useTheme();

    return (
        <div
            style={{
                display: "flex",
                flexWrap: "wrap",
                gap: theme.spacing.sm,
                width: "100%",
                ...sx,
            }}
        >
            {all_choices.map((choice) => {
                const is_selected = selected_choices.includes(choice.id);

                return (
                    <Button
                        key={choice.id}
                        onClick={() => handle_choice_select(choice.id)}
                        disableElevation
                        sx={{
                            minWidth: 0,
                            padding: `${theme.spacing.xs} ${theme.spacing.md}`,
                            borderRadius: theme.radius.lg,

                            ...theme.styles.baseText,
                            textAlign: "center",
                            wordWrap: "break-word",
                            whiteSpace: "pre-wrap",
                            overflowWrap: "anywhere",
                            wordBreak: "break-word",

                            backgroundColor: is_selected
                                ? theme.colors.accent.primary
                                : theme.colors.background.muted,

                            color: is_selected
                                ? theme.colors.text.primary
                                : theme.colors.text.secondary,

                            border: `1px solid ${
                                is_selected
                                    ? theme.colors.accent.active
                                    : theme.colors.border.subtle
                            }`,

                            transition: theme.transition.fast,
                            textTransform: "none",

                            "&:hover": {
                                backgroundColor: is_selected
                                    ? theme.colors.accent.hover
                                    : theme.colors.background.surface,
                            },
                        }}
                    >
                        {choice.label}
                    </Button>
                );
            })}
        </div>
    );
}
