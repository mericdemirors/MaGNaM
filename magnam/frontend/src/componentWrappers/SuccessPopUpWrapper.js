import React from "react";
import { Dialog, DialogTitle, DialogContent, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTheme } from "../context/ThemeContext";

export default function SuccessPopUpWrapper({
    success_message = "",
    on_close = () => {},
    success_title = "Success",
}) {
    const { theme } = useTheme();

    return (
        <Dialog
            open={true}
            onClose={on_close}
            PaperProps={{
                style: {
                    borderRadius: theme.radius.lg,
                    backgroundColor: theme.colors.background.app_success,
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
                        backgroundColor: theme.colors.accent.success,
                        borderRadius: theme.radius.sm,
                    }}
                />

                <div style={theme.styles.titleText}>{success_title}</div>

                {/* Close icon */}
                <IconButton
                    aria-label="close"
                    onClick={on_close}
                    sx={{
                        position: "absolute",
                        right: 0,
                        top: 0,
                        color: theme.colors.text.secondary,
                        transition: theme.transition.fast,
                        "&:hover": {
                            backgroundColor:
                                theme.colors.background.app_success_darker,
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
                    {success_message}
                </div>
            </DialogContent>
        </Dialog>
    );
}
