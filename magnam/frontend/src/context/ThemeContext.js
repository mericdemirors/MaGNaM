import React, { createContext, useContext, useMemo, useState } from "react";

const ThemeContext = createContext();

const lightColors = {
    background: {
        app: "#F7F9F8",
        app_darker: "#f0fff7ff",
        app_error: "#ffbbbbff",
        app_error_darker: "#fda2a2ff",
        app_success: "#bdffbbff",
        app_success_darker: "#b4fda2ff",
        app_confirmation: "#bbcdffff",
        app_confirmation_darker: "#a2b3fdff",
        surface: "#FFFFFF",
        muted: "#EEF2F1",
        muted_second: "#b8b8b8",
    },

    text: {
        primary: "#4f6660ff",
        secondary: "#4A5A56",
        muted: "#7D8A86",
        light_outline: "#F7F9F8",
        dark_outline: "#1b1d1cff",
    },

    accent: {
        primary: "#9FD3C7",
        secondary: "#d1eee7ff",
        hover: "#8BC3B7",
        active: "#78B2A7",
        error: "#d39f9fff",
        success: "#a3d39fff",
        error_hover: "#c38b8bff",
        confirmation: "#6e89ffff",
        confirmation_hover: "#b4b9ffff",
    },

    border: {
        subtle: "rgba(0,0,0,0.06)",
    },

    shadow: {
        card: "0 4px 12px rgba(0,0,0,0.06)",
        hover: "0 6px 18px rgba(0,0,0,0.08)",
    },
};

const darkColors = {
    background: {
        app: "#2c2c2cff",
        app_darker: "#111111ff",
        app_error: "#521c1cff",
        app_error_darker: "#380f0fff",
        app_success: "#022b00ff",
        app_success_darker: "#021301ff",
        app_confirmation: "#222f55ff",
        app_confirmation_darker: "#141d38ff",
        surface: "#242424ff",
        muted: "#474747ff",
        muted_second: "rgb(94, 94, 94)",
    },

    text: {
        primary: "#cececeff",
        secondary: "#a1a1a1ff",
        muted: "#949494ff",
        light_outline: "#1b1d1cff",
        dark_outline: "#F7F9F8",
    },

    accent: {
        primary: "#247464ff",
        secondary: "#122b26ff",
        hover: "#2f8675ff",
        active: "#3a9c89ff",
        error: "#4e1616ff",
        success: "#091d07ff",
        error_hover: "#631e1eff",
        confirmation: "#161f47ff",
        confirmation_hover: "#1e2a5eff",
    },

    border: {
        subtle: "rgba(255, 255, 255, 0.06)",
    },

    shadow: {
        card: "0 4px 12px rgba(160, 160, 160, 0.06)",
        hover: "0 6px 18px rgba(160, 160, 160, 0.08)",
    },
};

// 1 rem = 16 px
const buildBaseTheme = (mode) => {
    const colors = mode === "light" ? lightColors : darkColors;

    const theme = {
        mode,

        colors,

        typography: {
            fontFamily: {
                primary: `"CCWildWordsLower Regular", "Noto Sans JP", sans-serif`,
                secondary: `"CCWildWordsLower Regular", sans-serif`,
            },

            fontSize: {
                xxxs: "0.625rem", // 10px
                xxs: "0.75rem", // 12px
                xs: "0.875rem", // 14px
                sm: "1rem", // 16px
                md: "1.125rem", // 18px
                lg: "1.375rem", // 22px
                xl: "1.5rem", // 24px
            },

            fontWeight: {
                regular: 400,
                medium: 500,
                bold: 700,
            },

            lineHeight: {
                tight: 1.2,
                normal: 1.5,
                relaxed: 1.7,
            },
        },

        spacing: {
            xs: "0.25rem", // 4px
            sm: "0.5rem", // 8px
            md: "1rem", // 16px
            lg: "1.5rem", // 24px
            xl: "2rem", // 32px
            xxl: "2.5rem", // 40px
            xxxl: "6rem", // 96px
            xxxxl: "10rem", // 160px
        },

        radius: {
            sm: "0.375rem", // 6px
            md: "0.625rem", // 10px
            lg: "1rem", // 16px
        },

        transition: {
            fast: "0.15s ease",
            normal: "0.25s ease",
            slow: "0.4s ease",
        },

        dimensions: {
            xxxs: "clamp(12rem, 20vw, 15rem)", // 240
            xxs: "clamp(16rem, 25vw, 20rem)", // 320
            xs: "clamp(18rem, 28vw, 22rem)", // ~360
            sm: "clamp(20rem, 30vw, 25rem)", // 400
            md: "clamp(24rem, 35vw, 30rem)", // 480
            lg: "clamp(28rem, 40vw, 35rem)", // 560
            xl: "clamp(32rem, 45vw, 40rem)", // 640
            xxl: "clamp(36rem, 50vw, 45rem)", // 720
            xxxl: "clamp(48rem, 60vw, 60rem)", // 960
            xxxxl: "clamp(60rem, 70vw, 80rem)", // 1280
        },

        styles: {},
    };

    theme.coin = "🪙";

    return theme;
};

// we do this seperatelly because we want the updates on the theme.colors or theme.typography to be used here
const buildComputedStyles = (theme) => {
    const wrap_and_break = {
        wordWrap: "break-word",
        whiteSpace: "pre-wrap",
        overflowWrap: "anywhere",
        wordBreak: "break-word",
    };

    const baseText = {
        color: theme.colors.text.primary,
        fontFamily: theme.typography.fontFamily.primary,
        fontSize: theme.typography.fontSize.md,
        fontWeight: theme.typography.fontWeight.regular,
        lineHeight: theme.typography.lineHeight.normal,
        textAlign: "left",
        ...wrap_and_break,
    };

    return {
        wrap_and_break,
        baseText,
        titleText: {
            ...baseText,
            fontSize: theme.typography.fontSize.xl,
            fontWeight: theme.typography.fontWeight.bold,
            textAlign: "center",
        },

        subtitleText: {
            ...baseText,
            fontSize: theme.typography.fontSize.lg,
            fontWeight: theme.typography.fontWeight.medium,
        },

        descriptionText: {
            ...baseText,
            lineHeight: theme.typography.lineHeight.tight,
            color: theme.colors.text.secondary,
        },

        metadataText: {
            ...baseText,
            lineHeight: theme.typography.lineHeight.tight,
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.text.muted,
        },

        linkText: {
            ...baseText,
            color: theme.colors.accent.primary,
            fontStyle: "italic",
            textDecoration: "underline",
            cursor: "pointer",
        },

        tagText: {
            ...baseText,
            color: theme.colors.text.secondary,
            textAlign: "center",
        },

        textShadow: `
            -1px -1px 0 ${theme.colors.text.light_outline},
             1px -1px 0 ${theme.colors.text.light_outline},
            -1px  1px 0 ${theme.colors.text.light_outline},
             1px  1px 0 ${theme.colors.text.light_outline}
        `,
    };
};

// overwrites the targer dict values with the source dict values
const deepMerge = (target, source) => {
    const output = { ...target };

    Object.keys(source).forEach((key) => {
        if (
            typeof source[key] === "object" &&
            source[key] !== null &&
            !Array.isArray(source[key])
        ) {
            output[key] = deepMerge(target[key] || {}, source[key]);
        } else {
            output[key] = source[key];
        }
    });

    return output;
};

export const ThemeProvider = ({ children }) => {
    const [mode, setMode] = useState(() => {
        const storedMode = localStorage.getItem("themeMode");

        return storedMode === "dark" ? "dark" : "light";
    });

    const [customThemeEnabled, setCustomThemeEnabled] = useState(() => {
        return JSON.parse(localStorage.getItem("customThemeEnabled")) || false;
    });

    const [customTheme, setCustomTheme] = useState(() => {
        return JSON.parse(localStorage.getItem("customTheme")) || {};
    });

    const baseTheme = useMemo(() => {
        return buildBaseTheme(mode);
    }, [mode]);

    const theme = useMemo(() => {
        const mergedTheme = customThemeEnabled
            ? deepMerge(baseTheme, customTheme)
            : baseTheme;

        // we build the styles and other things now so they use the updated values from the custom theme
        mergedTheme.styles = buildComputedStyles(mergedTheme);

        mergedTheme.spinner_style = {
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: `${mergedTheme.spacing.sm} 0`,
        };

        return mergedTheme;
    }, [baseTheme, customTheme, customThemeEnabled]);

    const toggleMode = () => {
        setMode((prev) => {
            const nextMode = prev === "light" ? "dark" : "light";

            localStorage.setItem("themeMode", nextMode);

            return nextMode;
        });
    };

    const toggleCustomTheme = () => {
        setCustomThemeEnabled((prev) => {
            const next = !prev;

            localStorage.setItem("customThemeEnabled", JSON.stringify(next));

            return next;
        });
    };

    const updateThemeValue = (path, value) => {
        setCustomTheme((prev) => {
            const updated = structuredClone(prev);

            let current = updated;

            for (let i = 0; i < path.length - 1; i++) {
                const key = path[i];

                if (!current[key]) {
                    current[key] = {};
                }

                current = current[key];
            }

            current[path[path.length - 1]] = value;

            localStorage.setItem("customTheme", JSON.stringify(updated));

            return updated;
        });
    };

    const resetCustomTheme = () => {
        setCustomTheme({});

        localStorage.removeItem("customTheme");
    };

    const getBaseTheme = (mode = "light") => {
        return buildBaseTheme(mode);
    };

    const importCustomTheme = (importedTheme) => {
        setCustomTheme(importedTheme);
        localStorage.setItem("customTheme", JSON.stringify(importedTheme));
    };

    const exportThemeKey = () => {
        try {
            // 1. Create a deep copy
            const themeToExport = structuredClone(customTheme);
            // 2. Safely delete the fontFamily key if it exists
            if (themeToExport?.typography?.fontFamily) {
                delete themeToExport.typography.fontFamily;
                // If typography is now completely empty, delete it too
                if (Object.keys(themeToExport.typography).length === 0) {
                    delete themeToExport.typography;
                }
            }

            return btoa(JSON.stringify(themeToExport));
        } catch (error) {
            console.error(error);
            return "";
        }
    };

    const importThemeKey = (key) => {
        try {
            const parsed = JSON.parse(atob(key));
            importCustomTheme(parsed);
            return true;
        } catch (error) {
            console.error(error);
            return false;
        }
    };

    return (
        <ThemeContext.Provider
            value={{
                theme,
                mode,
                customThemeEnabled,
                customTheme,
                toggleMode,
                toggleCustomTheme,
                updateThemeValue,
                resetCustomTheme,
                getBaseTheme,
                importCustomTheme,
                exportThemeKey,
                importThemeKey,
            }}
        >
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => useContext(ThemeContext);
