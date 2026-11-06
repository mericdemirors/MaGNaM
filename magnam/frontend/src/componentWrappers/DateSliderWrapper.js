import React from "react";
import { Slider } from "@mui/material";
import { useTheme } from "../context/ThemeContext";

/**
 * DateSliderWrapper
 * --------------------
 * Calm, gallery-aligned date slider for filters & constraints.
 * Fully theme-driven. Minimal visual weight.
 */
export default function DateSliderWrapper({
    value,
    min,
    max,
    step,
    onChange,
    onChangeCommitted,
    sx,
}) {
    const { theme } = useTheme();

    const isAtFullRange =
        Array.isArray(value) &&
        value.length === 2 &&
        value[0] === min &&
        value[1] === max;
    const activeColor = isAtFullRange
        ? theme.colors.background.muted
        : theme.colors.accent.primary;

    const formatDate = (timestamp) =>
        new Date(timestamp).toISOString().split("T")[0];

    const marks = [
        { value: min, label: formatDate(min) },
        { value: max, label: formatDate(max) },
    ];

    return (
        <div
            style={{
                width: "100%",
                paddingLeft: theme.spacing.sm,
                paddingRight: theme.spacing.sm,
                ...sx,
            }}
        >
            <Slider
                value={value}
                min={min}
                max={max}
                step={step}
                marks={marks}
                onChange={onChange}
                onChangeCommitted={onChangeCommitted}
                valueLabelDisplay="on"
                valueLabelFormat={formatDate}
                sx={{
                    color: activeColor,

                    height: 4,
                    paddingY: theme.spacing.md,

                    "& .MuiSlider-rail": {
                        opacity: 1,
                        backgroundColor: theme.colors.background.muted,
                    },

                    "& .MuiSlider-track": {
                        border: "none",
                    },

                    "& .MuiSlider-thumb": {
                        width: 14,
                        height: 14,
                        backgroundColor: theme.colors.background.surface,
                        border: `2px solid ${activeColor}`,
                        boxShadow: theme.colors.shadow.card,
                        transition: theme.transition.fast,

                        "&:hover": {
                            boxShadow: theme.colors.shadow.hover,
                        },

                        "&.Mui-active": {
                            boxShadow: theme.colors.shadow.hover,
                        },
                    },

                    "& .MuiSlider-markLabel": {
                        fontFamily: theme.typography.fontFamily.primary,
                        fontSize: theme.typography.fontSize.xs,
                        color: theme.colors.text.muted,
                        paddingTop: theme.spacing.xs,

                        // Targeting the first mark (min)
                        '&[data-index="0"]': {
                            transform: "none", // Remove the -50% centering
                        },

                        // Targeting the last mark (max)
                        '&[data-index="1"]': {
                            transform: "translateX(-100%)", // Pull the label to the left
                        },
                    },

                    "& .MuiSlider-valueLabel": {
                        fontFamily: theme.typography.fontFamily.primary,
                        fontSize: theme.typography.fontSize.xs,
                        backgroundColor: theme.colors.background.surface,
                        color: theme.colors.text.primary,
                        borderRadius: theme.radius.sm,
                        boxShadow: theme.colors.shadow.card,
                    },
                }}
            />
        </div>
    );
}
