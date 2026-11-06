import React from "react";
import {
    Dialog,
    DialogContent,
    DialogActions,
    IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { useTheme } from "../context/ThemeContext";

export default function ConfirmationPopUpWrapper({
    confirmation_title = "Confirm",
    confirmation_message = "",
    on_accept = () => {},
    on_reject = () => {},
}) {
    const { theme } = useTheme();

    return (
        <Dialog
            open={true}
            onClose={on_reject}
            PaperProps={{
                style: {
                    borderRadius: theme.radius.lg,
                    backgroundColor: theme.colors.background.app_confirmation,
                    boxShadow: theme.colors.shadow.card,
                    padding: theme.spacing.lg,
                    minWidth: theme.dimensions.md,
                },
            }}
        >
            {/* Title */}
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.sm,
                    paddingBottom: theme.spacing.md,
                    position: "relative",
                }}
            >
                {/* Accent bar */}
                <div
                    style={{
                        width: 4,
                        height: 28,
                        backgroundColor: theme.colors.accent.confirmation,
                        borderRadius: theme.radius.sm,
                    }}
                />

                <div style={theme.styles.titleText}>{confirmation_title}</div>

                {/* Close icon */}
                <IconButton
                    aria-label="close"
                    onClick={on_reject}
                    sx={{
                        position: "absolute",
                        right: 0,
                        top: 0,
                        color: theme.colors.text.secondary,
                        transition: theme.transition.fast,
                        "&:hover": {
                            backgroundColor:
                                theme.colors.background.app_confirmation_darker,
                        },
                    }}
                >
                    <CloseIcon />
                </IconButton>
            </div>

            {/* Content */}
            <DialogContent
                sx={{
                    padding: 0,
                    paddingBottom: theme.spacing.lg,
                }}
            >
                <div
                    style={{
                        ...theme.styles.descriptionText,
                        textAlign: "left",
                    }}
                >
                    {confirmation_message}
                </div>
            </DialogContent>

            {/* Actions */}
            <DialogActions
                sx={{
                    padding: 0,
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: theme.spacing.sm,
                }}
            >
                <ButtonWrapper
                    text="Cancel"
                    visualVariant="danger"
                    onClick={on_reject}
                />

                <ButtonWrapper
                    text="Confirm"
                    visualVariant="soft"
                    onClick={on_accept}
                />
            </DialogActions>
        </Dialog>
    );
}
