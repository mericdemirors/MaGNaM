import React from "react";
import { Slider } from "@mui/material";
import { useTheme } from "../context/ThemeContext";

/**
 * IntegerSliderWrapper
 * --------------------
 * Calm, gallery-aligned integer slider for filters & constraints.
 * Fully theme-driven. Minimal visual weight.
 */
export default function IntegerSliderWrapper({
    value,
    min,
    max,
    step,
    onChange,
    onChangeCommitted,
    is_rating_slider = false,
    showValue = "on",
    showLimits = true,
    showThumb = true,
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

    const marks = showLimits
        ? [
              { value: min, label: `${min}` },
              { value: max, label: `${max}` },
          ]
        : false;

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
                valueLabelDisplay={showValue}
                slotProps={{
                    input: { readOnly: !showThumb },
                }}
                sx={{
                    color: activeColor,

                    height: 4,
                    paddingY: theme.spacing.md,

                    pointerEvents: showThumb ? "auto" : "none",

                    "& .MuiSlider-rail": {
                        opacity: 1,
                        // Toggle gradient vs solid muted background
                        background: is_rating_slider
                            ? "linear-gradient(to right, #ff4545, #4545ff, #45ff45)"
                            : theme.colors.background.muted,
                        backgroundColor: is_rating_slider
                            ? "transparent"
                            : theme.colors.background.muted,
                    },

                    "& .MuiSlider-track": {
                        // Hide track if rating, show it if standard
                        background: is_rating_slider
                            ? "transparent"
                            : "currentColor",
                        border: "none",
                    },

                    "& .MuiSlider-thumb": {
                        display: showThumb ? "flex" : "none",
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
