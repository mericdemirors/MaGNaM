import React from "react";
import { useTheme } from "../context/ThemeContext";
import { SectionLabel } from "./helper_components";

/**
 * RegisteredSlidersDisplayWrapper
 * --------------------------------
 * Vertical control column for registered sliders.
 * Owns internal spacing and padding.
 */
export default function RegisteredSlidersDisplayWrapper({
    registered_sliders = [],
    sx = {},
}) {
    const { theme } = useTheme();

    if (!registered_sliders.length) return null;

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.md,
                padding: theme.spacing.lg,
                ...sx,
            }}
        >
            {registered_sliders.map((item, index) => {
                const {
                    label,
                    SliderType,
                    range,
                    min,
                    max,
                    step,
                    on_change_fn,
                    on_commit_fn,
                } = item;

                return (
                    <div
                        key={index}
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: theme.spacing.sm, // spacing between label & slider
                            width: "100%", // ensure sliders fill parent
                        }}
                    >
                        <SectionLabel text={label} />

                        <SliderType
                            value={range}
                            min={min}
                            max={max}
                            step={step}
                            onChange={(e, newValue) => on_change_fn(newValue)}
                            onChangeCommitted={on_commit_fn}
                            sx={{ width: "100%" }} // slider fills container
                        />
                    </div>
                );
            })}
        </div>
    );
}
