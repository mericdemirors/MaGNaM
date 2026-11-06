import React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import { SPINNERHEIGHT } from "../globals";
import { useTheme } from "../context/ThemeContext";

/**
 * LoadSpinnerWrapper
 * ------------------
 */
export default function LoadSpinnerWrapper({ loading = true, sx }) {
    const { theme } = useTheme();

    return (
        <div
            style={{
                ...theme.spinner_style,
                minHeight: loading ? theme.spacing.xxl : "0",
                transition: theme.transition.fast,
                ...sx,
            }}
        >
            {loading && (
                <CircularProgress
                    size={SPINNERHEIGHT}
                    sx={{
                        color: theme.colors.accent.primary,
                    }}
                />
            )}
        </div>
    );
}
