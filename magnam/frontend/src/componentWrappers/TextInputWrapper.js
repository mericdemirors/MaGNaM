import React from "react";
import TextField from "@mui/material/TextField";
import { useTheme } from "../context/ThemeContext";

/**
 * TextInputWrapper
 * ----------------
 * Calm, gallery-friendly text input abstraction.
 * Inputs are supportive UI elements, never dominant.
 */
export default function TextInputWrapper({
    name,
    label,
    type = "text",
    value,
    onChange,
    onKeyDown = () => {},

    required = false,
    autoComplete,
    maxLength,

    multiline = false,
    rows,

    disabled = false,
    defaultValue,

    fullWidth = false,

    sx,
}) {
    const { theme } = useTheme();

    return (
        <TextField
            name={name}
            label={label}
            type={type}
            value={value}
            onChange={onChange}
            onKeyDown={onKeyDown}
            required={required}
            disabled={disabled}
            autoComplete={autoComplete}
            multiline={multiline}
            rows={rows}
            defaultValue={defaultValue}
            fullWidth={fullWidth}
            variant="outlined"
            slotProps={maxLength ? { htmlInput: { maxLength } } : undefined}
            sx={{
                /* Label — metadata-level, calm */
                "& .MuiInputLabel-root": {
                    color: theme.colors.text.primary,
                    fontFamily: theme.typography.fontFamily.primary,
                },

                "& .MuiInputLabel-root.Mui-focused": {
                    color: theme.colors.accent.primary,
                },

                /* Input container */
                "& .MuiOutlinedInput-root": {
                    color: theme.colors.text.primary,
                    fontFamily: theme.typography.fontFamily.primary,

                    backgroundColor: theme.colors.background.surface,
                    borderRadius: theme.radius.md,
                    transition: theme.transition.normal,

                    /* Padding rhythm */
                    paddingY: multiline ? theme.spacing.sm : theme.spacing.xs,

                    /* Border */
                    "& fieldset": {
                        borderColor: theme.colors.border.subtle,
                    },

                    "&:hover fieldset": {
                        borderColor: theme.colors.text.muted,
                    },

                    "&.Mui-focused fieldset": {
                        borderColor: theme.colors.accent.primary,
                        borderWidth: "1px",
                    },

                    "&.Mui-disabled": {
                        backgroundColor: theme.colors.background.muted,
                        color: theme.colors.text.muted,
                    },
                },

                /* Required asterisk — informative, not loud */
                "& .MuiFormLabel-asterisk": {
                    fontFamily: theme.typography.fontFamily.primary,
                    color: required
                        ? theme.colors.accent.active
                        : theme.colors.text.muted,
                },

                /* Helper / error text (future-safe) */
                "& .MuiFormHelperText-root": {
                    fontFamily: theme.typography.fontFamily.primary,
                    fontSize: theme.typography.fontSize.xs,
                    marginLeft: 0,
                    marginTop: theme.spacing.xs,
                },

                ...sx,
            }}
        />
    );
}
