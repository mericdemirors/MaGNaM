import React from "react";
import Button from "@mui/material/Button";
import { Link } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";

/**
 * ButtonWrapper
 * -------------
 * Calm, gallery-friendly button abstraction.
 * Buttons are secondary UI elements in this platform.
 */
export default function ButtonWrapper({
    text,
    to,
    onClick,
    disabled = false,
    /**
     * visualVariant:
     * - "soft"     → default, subtle filled
     * - "outline"  → bordered, minimal
     * - "ghost"    → text-only
     */
    visualVariant = "soft",
    type = "button", // defaults to being a button, we use "submit" for login and register panels
    sx,
}) {
    const { theme } = useTheme();

    const buttonProps = Boolean(to) ? { component: Link, to } : { onClick };

    // Variant styles mapped to your design system
    const variantStyles = {
        soft: {
            backgroundColor: theme.colors.accent.primary,
            color: theme.colors.text.primary,
            boxShadow: "none",
            "&:hover": {
                backgroundColor: theme.colors.accent.hover,
                boxShadow: theme.colors.shadow.hover,
            },
        },

        outline: {
            backgroundColor: "transparent",
            color: theme.colors.text.primary,
            border: `2px solid ${theme.colors.border.subtle}`,
            "&:hover": {
                backgroundColor: theme.colors.background.muted,
            },
        },

        ghost: {
            backgroundColor: "transparent",
            color: theme.colors.text.secondary,
            "&:hover": {
                color: theme.colors.text.primary,
                backgroundColor: theme.colors.background.muted,
            },
        },

        danger: {
            backgroundColor: theme.colors.accent.error,
            color: theme.colors.text.primary,
            boxShadow: "none",
            "&:hover": {
                backgroundColor: theme.colors.accent.error_hover,
                boxShadow: theme.colors.shadow.hover,
            },
        },
    };

    // fallback to soft when wrong visualVariant key is passed
    const selectedVariant = variantStyles[visualVariant] || variantStyles.soft;

    return (
        <Button
            type={type}
            {...buttonProps}
            disabled={disabled}
            sx={{
                fontFamily: theme.typography.fontFamily.primary,
                fontSize: theme.typography.fontSize.sm,
                fontWeight: theme.typography.fontWeight.medium,

                textTransform: "none",
                borderRadius: theme.radius.md,
                padding: theme.spacing.sm,

                transition: theme.transition.normal,

                ...selectedVariant,
                ...sx,
            }}
        >
            {text}
        </Button>
    );
}
