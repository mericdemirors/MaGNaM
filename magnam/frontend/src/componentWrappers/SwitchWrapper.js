import React from "react";
import Switch from "@mui/material/Switch";
import { useTheme } from "../context/ThemeContext";

/**
 * SwitchWrapper
 * --------------
 * Calm, gallery-friendly switch abstraction.
 * Used for binary states with subtle emphasis.
 */
export default function SwitchWrapper({
    text,
    checked,
    onEnable,
    onDisable,
    disabled = false,

    /**
     * visualVariant:
     * - "soft"   → default accent
     * - "danger" → destructive intent
     */
    visualVariant = "soft",

    sx,
}) {
    const { theme } = useTheme();

    const handleChange = (event) => {
        const isChecked = event.target.checked;

        if (isChecked) {
            onEnable?.();
        } else {
            onDisable?.();
        }
    };

    const variantStyles = {
        soft: {
            // Base (unchecked / disabled track)
            "& .MuiSwitch-track": {
                backgroundColor: theme.colors.background.muted,
                opacity: 1,
            },

            "& .MuiSwitch-thumb": {
                backgroundColor: theme.colors.accent.muted_second,
            },

            // Checked state
            "& .MuiSwitch-switchBase.Mui-checked": {
                color: theme.colors.accent.active,
            },

            "& .MuiSwitch-switchBase.Mui-checked .MuiSwitch-thumb": {
                backgroundColor: theme.colors.accent.active,
            },

            "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                backgroundColor: theme.colors.accent.hover,
                opacity: 1,
            },
        },

        danger: {
            "& .MuiSwitch-track": {
                backgroundColor: theme.colors.background.muted,
                opacity: 1,
            },

            "& .MuiSwitch-thumb": {
                backgroundColor: theme.colors.accent.muted_second,
            },

            "& .MuiSwitch-switchBase.Mui-checked": {
                color: theme.colors.accent.error_hover,
            },

            "& .MuiSwitch-switchBase.Mui-checked .MuiSwitch-thumb": {
                backgroundColor: theme.colors.accent.error_hover,
            },

            "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                backgroundColor: theme.colors.accent.error,
                opacity: 1,
            },
        },
    };

    let selectedVariant = variantStyles[visualVariant] || variantStyles.soft;

    if (disabled) {
        selectedVariant = {
            ...selectedVariant,
            "& .MuiSwitch-thumb": {
                backgroundColor: theme.colors.background.muted,
            },
            "& .MuiSwitch-switchBase.Mui-checked .MuiSwitch-thumb": {
                backgroundColor: theme.colors.background.muted,
            },
        };
    }

    return (
        <div
            style={{
                display: "flex",
                alignItems: "center",
                gap: theme.spacing.sm,
            }}
        >
            <p style={{ ...theme.styles.metadataText, margin: 0 }}>{text}</p>
            <Switch
                checked={checked}
                onChange={handleChange}
                disabled={disabled}
                sx={{
                    transition: theme.transition.normal,
                    ...selectedVariant,
                    ...sx,
                }}
            />
        </div>
    );
}
