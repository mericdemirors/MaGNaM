import React, { useState, useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import HasPermission from "../utils/HasPermission";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import SwitchWrapper from "../componentWrappers/SwitchWrapper";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ThemeFontUploadField from "../componentWrappers/ThemeFontUploadField";

const ContinuousPreviewBox = ({ value, theme }) => {
    const [isScaled, setIsScaled] = useState(false);

    useEffect(() => {
        const seconds = parseFloat(value) || 0.5;
        const intervalTime = seconds * 4000;

        const interval = setInterval(() => {
            setIsScaled((prev) => !prev);
        }, intervalTime);

        return () => clearInterval(interval);
    }, [value]);

    return (
        <div
            style={{
                width: theme.spacing.xl,
                height: theme.spacing.xl,
                borderRadius: theme.radius.md,
                background: theme.colors.accent.primary,
                transition: `transform ${value}`,
                transform: isScaled ? "scale(1.2)" : "scale(1)",
            }}
        />
    );
};

const ThemeColorField = ({
    theme,
    label,
    value,
    defaultValue,
    updateTheme,
    description,
    display,
}) => {
    const normalizeColor = (color) => {
        return String(color).trim().toLowerCase();
    };

    // #2c2c2cff -> #2c2c2c
    const toPickerColor = (color) => {
        const normalized = normalizeColor(color);

        // rgba hex
        if (/^#([0-9a-f]{8})$/i.test(normalized)) {
            return normalized.slice(0, 7);
        }

        // rgb/rgba unsupported by picker
        if (normalized.startsWith("rgb(") || normalized.startsWith("rgba(")) {
            return "#000000";
        }

        return normalized;
    };

    const appliedThemeValue = normalizeColor(value);
    const defaultThemeValue = normalizeColor(defaultValue);

    const [inputValue, setInputValue] = React.useState(appliedThemeValue);

    React.useEffect(() => {
        setInputValue(appliedThemeValue);
    }, [appliedThemeValue]);

    const normalizedInputValue = normalizeColor(inputValue);
    const hasUnsavedChanges = normalizedInputValue !== appliedThemeValue;
    const isCustomized = appliedThemeValue !== defaultThemeValue;

    let buttonVariant = "ghost";
    let buttonText = "Default";

    if (hasUnsavedChanges) {
        buttonVariant = "danger";
        buttonText = "Click to Save";
    } else if (isCustomized) {
        buttonVariant = "soft";
        buttonText = "Saved";
    }

    const applyChanges = () => {
        updateTheme(normalizedInputValue);
    };

    const renderedDisplay =
        typeof display === "function"
            ? display({
                  theme,
                  value: normalizedInputValue,
                  defaultValue,
              })
            : display;

    return (
        <div
            style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: theme.spacing.lg,
                padding: theme.spacing.lg,
                background: isCustomized
                    ? theme.colors.background.app
                    : theme.colors.background.surface,
                borderRadius: theme.radius.md,
            }}
        >
            {/* Info */}
            <div
                style={{
                    width: theme.dimensions.md,
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.xs,
                }}
            >
                <div style={theme.styles.subtitleText}>{label}</div>

                <div
                    style={{
                        ...theme.styles.metadataText,
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                    }}
                >
                    {description}
                </div>

                <div style={theme.styles.descriptionText}>
                    Default: {defaultThemeValue}
                </div>

                <div style={theme.styles.descriptionText}>
                    Current: {appliedThemeValue}
                </div>
            </div>

            {/* Native Color Picker */}
            <input
                type="color"
                value={toPickerColor(inputValue)}
                onChange={(e) => setInputValue(e.target.value)}
                style={{
                    width: "8rem",
                    height: "8rem",
                    padding: 0,
                    border: `1px solid ${theme.colors.border.subtle}`,
                    borderRadius: theme.radius.md,
                    background: theme.colors.background.muted,
                    cursor: "pointer",
                    overflow: "hidden",
                }}
            />

            {/* Save Button */}
            <ButtonWrapper
                text={buttonText}
                onClick={applyChanges}
                visualVariant={buttonVariant}
            />

            {/* Reset Button */}
            {isCustomized && (
                <ButtonWrapper
                    text="Cancel"
                    onClick={() => {
                        setInputValue(defaultThemeValue);
                        updateTheme(defaultThemeValue);
                    }}
                    visualVariant="danger"
                />
            )}

            {/* Preview */}
            <div
                style={{
                    minWidth: theme.dimensions.lg,
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    background: theme.colors.background.app,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                }}
            >
                {renderedDisplay}
            </div>
        </div>
    );
};

const ThemeInputField = ({
    theme,
    label,
    value,
    defaultValue,
    updateTheme,
    description,
    suffix = "",
    prefix = "",
    display,
}) => {
    const pruneNumeric = (val) => {
        const parsed = parseFloat(
            String(val)
                .replace(",", ".")
                .replace(/[^0-9.-]/g, ""),
        );

        if (isNaN(parsed)) {
            return 0;
        }

        return parsed;
    };

    const appliedThemeValue = pruneNumeric(value);
    const defaultNumericValue = pruneNumeric(defaultValue);

    const [inputValue, setInputValue] = React.useState(
        String(appliedThemeValue),
    );

    React.useEffect(() => {
        setInputValue(String(appliedThemeValue));
    }, [appliedThemeValue]);

    const inputNumericValue = pruneNumeric(inputValue);
    const hasUnsavedChanges = inputNumericValue !== appliedThemeValue;
    const isCustomized = appliedThemeValue !== defaultNumericValue;

    let buttonVariant = "ghost";
    let buttonText = "Default";
    if (hasUnsavedChanges) {
        buttonVariant = "danger";
        buttonText = "Click to Save";
    } else if (isCustomized) {
        buttonVariant = "soft";
        buttonText = "Saved";
    }

    const applyChanges = () => {
        let parsed = inputNumericValue;

        parsed = Math.max(0.1, Math.min(10000, parsed));

        updateTheme(`${prefix}${parsed}${suffix}`);
    };

    const renderedDisplay =
        typeof display === "function"
            ? display({
                  theme,
                  value: `${prefix}${inputNumericValue}${suffix}`,
                  defaultValue,
              })
            : display;

    return (
        <div
            style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                gap: theme.spacing.lg,
                padding: theme.spacing.lg,
                background: isCustomized
                    ? theme.colors.background.app
                    : theme.colors.background.surface,
                borderRadius: theme.radius.md,
            }}
        >
            {/* Info */}
            <div
                style={{
                    width: theme.dimensions.md,
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.xs,
                }}
            >
                <div style={theme.styles.subtitleText}>{label}</div>

                <div
                    style={{
                        ...theme.styles.metadataText,
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                    }}
                >
                    {description}
                </div>

                <div style={theme.styles.descriptionText}>
                    Default: {defaultNumericValue}
                </div>

                <div style={theme.styles.descriptionText}>
                    Current: {appliedThemeValue}
                </div>
            </div>

            {/* Text Input */}
            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                style={{
                    flex: 1,
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    border: `1px solid ${theme.colors.border.subtle}`,
                    background: theme.colors.background.muted,
                    color: theme.colors.text.primary,
                    fontSize: theme.typography.fontSize.md,
                }}
            />

            {/* Save Button */}
            <ButtonWrapper
                text={buttonText}
                onClick={applyChanges}
                visualVariant={buttonVariant}
            />

            {/* Reset Button */}
            {isCustomized && (
                <ButtonWrapper
                    text={"Cancel"}
                    onClick={() => {
                        setInputValue(defaultNumericValue);
                        updateTheme(`${prefix}${defaultNumericValue}${suffix}`);
                    }}
                    visualVariant={"danger"}
                />
            )}

            {/* Preview */}
            <div
                style={{
                    minWidth: theme.dimensions.lg,
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    background: theme.colors.background.app,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                }}
            >
                {renderedDisplay}
            </div>
        </div>
    );
};

const CreateThemePage = () => {
    const {
        theme,
        customThemeEnabled,
        toggleCustomTheme,
        updateThemeValue,
        resetCustomTheme,
        getBaseTheme,
        exportThemeKey,
        importThemeKey,
    } = useTheme();

    const logged_in_permission = HasPermission("logged_in");

    const defaultTheme = React.useMemo(() => {
        return getBaseTheme(theme.mode);
    }, [theme.mode]);

    const [themeKeyInput, setThemeKeyInput] = React.useState("");
    const [theme_key_error_message, set_theme_key_error_message] = useState("");

    const sectionStyle = (theme) => ({
        background: theme.colors.background.surface,
        borderRadius: theme.radius.md,
        padding: theme.spacing.md,
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing.lg,
    });

    function render_switch() {
        return (
            <div
                style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    paddingTop: theme.spacing.xxxxl,
                    paddingBottom: theme.spacing.xxxxl,
                    width: "100%",
                }}
            >
                <div
                    style={{
                        ...theme.styles.titleText,
                        color: customThemeEnabled
                            ? theme.colors.accent.primary
                            : theme.colors.text.primary,
                    }}
                >
                    {customThemeEnabled
                        ? "Welcome to Customization!"
                        : "Just a little tiny switch..."}
                </div>

                <SwitchWrapper
                    text=""
                    checked={customThemeEnabled}
                    onEnable={toggleCustomTheme}
                    onDisable={toggleCustomTheme}
                    visualVariant="soft"
                    sx={{
                        transform: "scale(8)",
                        margin: "0 15rem",
                    }}
                />
            </div>
        );
    }

    function render_theme_key_section() {
        const row_style = {
            display: "flex",
            flexDirection: "row",
            gap: theme.spacing.xs,
            padding: theme.spacing.md,
            background: theme.colors.background.surface,
            borderRadius: theme.radius.md,
        };
        const text_area_style = {
            flex: 1,
            padding: theme.spacing.md,
            borderRadius: theme.radius.md,
            border: `1px solid ${theme.colors.border.subtle}`,
            background: theme.colors.background.muted,
            color: theme.colors.text.primary,
            fontSize: theme.typography.fontSize.md,
            width: "100%",
            minHeight: theme.spacing.xxl,
        };

        return (
            <div style={sectionStyle(theme)}>
                <div style={theme.styles.titleText}>
                    Theme Sharing (Share your custom theme with friends)
                </div>

                {/* Theme Key Section */}
                <div style={row_style}>
                    <textarea
                        readOnly
                        value={exportThemeKey()}
                        style={text_area_style}
                    />

                    <ButtonWrapper
                        text="Copy Your Theme Key"
                        onClick={() => {
                            navigator.clipboard.writeText(exportThemeKey());
                        }}
                        visualVariant={customThemeEnabled ? "soft" : "outline"}
                        sx={{ width: theme.dimensions.xxxs }}
                    />
                </div>
                <div style={row_style}>
                    <textarea
                        value={themeKeyInput}
                        onChange={(e) => setThemeKeyInput(e.target.value)}
                        placeholder="Paste your friend's theme key here, and then click the button"
                        style={text_area_style}
                    />

                    <ButtonWrapper
                        text="Paste a Theme Key to Apply"
                        onClick={() => {
                            const success = importThemeKey(themeKeyInput);
                            if (!success) {
                                set_theme_key_error_message(
                                    "Invalid theme key",
                                );
                            }
                        }}
                        visualVariant={customThemeEnabled ? "soft" : "outline"}
                        sx={{ width: theme.dimensions.xxxs }}
                    />
                </div>
            </div>
        );
    }

    function render_theme_fields() {
        return (
            <>
                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>Background Colors</div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                        }}
                    >
                        {Object.keys(theme.colors.background).map((key) => (
                            <ThemeColorField
                                key={`backgroundcolor-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.colors.background[key]}
                                defaultValue={
                                    defaultTheme.colors.background[key]
                                }
                                description={`Background color for ${key}`}
                                updateTheme={(value) =>
                                    updateThemeValue(
                                        ["colors", "background", key],
                                        value,
                                    )
                                }
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            width: "4rem",
                                            height: "4rem",
                                            background: value,
                                        }}
                                    />
                                )}
                            />
                        ))}
                    </div>
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}> Text Colors </div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                        }}
                    >
                        {Object.keys(theme.colors.text).map((key) => (
                            <ThemeColorField
                                key={`textcolor-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.colors.text[key]}
                                defaultValue={defaultTheme.colors.text[key]}
                                description={`Text color for ${key}`}
                                updateTheme={(value) =>
                                    updateThemeValue(
                                        ["colors", "text", key],
                                        value,
                                    )
                                }
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            fontFamily:
                                                theme.typography.fontFamily
                                                    .primary,
                                            color: value,
                                        }}
                                    >
                                        Taste the rainbow!
                                    </div>
                                )}
                            />
                        ))}
                    </div>
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>Accent Colors</div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                        }}
                    >
                        {Object.keys(theme.colors.accent).map((key) => (
                            <ThemeColorField
                                key={`accentcolor-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.colors.accent[key]}
                                defaultValue={defaultTheme.colors.accent[key]}
                                description={`Accent color for ${key}`}
                                updateTheme={(value) =>
                                    updateThemeValue(
                                        ["colors", "accent", key],
                                        value,
                                    )
                                }
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            width: "4rem",
                                            height: "4rem",
                                            background: value,
                                        }}
                                    />
                                )}
                            />
                        ))}
                    </div>
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>Border Colors</div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                        }}
                    >
                        {Object.keys(theme.colors.border).map((key) => (
                            <ThemeColorField
                                key={`bordercolor-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.colors.border[key]}
                                defaultValue={defaultTheme.colors.border[key]}
                                description={`Border color for ${key}`}
                                updateTheme={(value) =>
                                    updateThemeValue(
                                        ["colors", "border", key],
                                        value,
                                    )
                                }
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            width: "4rem",
                                            height: "4rem",
                                            background: value,
                                        }}
                                    />
                                )}
                            />
                        ))}
                    </div>
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Font Upload (select your own font)
                    </div>

                    <ThemeFontUploadField
                        theme={theme}
                        label="Custom Font"
                        value={theme.typography.fontFamily.primary}
                        defaultValue={
                            defaultTheme.typography.fontFamily.primary
                        }
                        description="Upload a custom font file (.ttf, .woff, .woff2)"
                        updateTheme={(value) =>
                            updateThemeValue(
                                ["typography", "fontFamily", "primary"],
                                value,
                            )
                        }
                        display={() => (
                            <div
                                style={{
                                    ...theme.styles.descriptionText,
                                    fontFamily:
                                        theme.typography.fontFamily.primary,
                                }}
                            >
                                ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                <br />
                                abcdefghijklmnopqrstuvwxyz
                                <br />
                                0123456789
                                <br />
                                !?.,;:()[]{}+-=
                            </div>
                        )}
                    />
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Font Size (how big texts are)
                    </div>

                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.md,
                        }}
                    >
                        {Object.keys(theme.typography.fontSize).map((key) => (
                            <ThemeInputField
                                key={`fontsize-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.typography.fontSize[key]}
                                defaultValue={
                                    defaultTheme.typography.fontSize[key]
                                }
                                description={`Font size with ${key} size`}
                                updateTheme={(value) =>
                                    updateThemeValue(
                                        ["typography", "fontSize", key],
                                        value,
                                    )
                                }
                                suffix="rem"
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            fontFamily:
                                                theme.typography.fontFamily
                                                    .primary,
                                            fontSize: value,
                                            color: theme.colors.text.primary,
                                        }}
                                    >
                                        Look at the size of it!
                                    </div>
                                )}
                            />
                        ))}
                    </div>
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Font Weight (how thick texts are)
                    </div>

                    {Object.keys(theme.typography.fontWeight).map((key) => (
                        <ThemeInputField
                            key={`fontweight-${key}`}
                            theme={theme}
                            label={key}
                            value={theme.typography.fontWeight[key]}
                            defaultValue={
                                defaultTheme.typography.fontWeight[key]
                            }
                            description={`Font weight with ${key} size`}
                            updateTheme={(value) =>
                                updateThemeValue(
                                    ["typography", "fontWeight", key],
                                    value,
                                )
                            }
                            display={({ value, theme }) => (
                                <div
                                    style={{
                                        fontFamily:
                                            theme.typography.fontFamily.primary,
                                        fontWeight: value,
                                        color: theme.colors.text.primary,
                                    }}
                                >
                                    It's getting kinda thicc!
                                </div>
                            )}
                        />
                    ))}
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Line Height (how separate texts are)
                    </div>

                    {Object.keys(theme.typography.lineHeight).map((key) => (
                        <ThemeInputField
                            key={`lineweight-${key}`}
                            theme={theme}
                            label={key}
                            value={theme.typography.lineHeight[key]}
                            defaultValue={
                                defaultTheme.typography.lineHeight[key]
                            }
                            description={`Line height with ${key} size`}
                            updateTheme={(value) =>
                                updateThemeValue(
                                    ["typography", "lineHeight", key],
                                    value,
                                )
                            }
                            display={({ value, theme }) => (
                                <div
                                    style={{
                                        fontFamily:
                                            theme.typography.fontFamily.primary,
                                        lineHeight: value,
                                        color: theme.colors.text.primary,
                                        fontSize: theme.typography.fontSize.sm,
                                    }}
                                >
                                    Why are we
                                    <br />
                                    falling apart?
                                </div>
                            )}
                        />
                    ))}
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Spacing (how separate website items are)
                    </div>

                    {Object.keys(theme.spacing).map((key) => (
                        <ThemeInputField
                            key={`spacing-${key}`}
                            theme={theme}
                            label={key}
                            value={theme.spacing[key]}
                            defaultValue={defaultTheme.spacing[key]}
                            description={`Spacing size with ${key} size`}
                            updateTheme={(value) =>
                                updateThemeValue(["spacing", key], value)
                            }
                            suffix="rem"
                            display={({ value, theme }) => (
                                <div
                                    style={{
                                        display: "flex",
                                        gap: value,
                                    }}
                                >
                                    <div
                                        style={{
                                            width: theme.spacing.xxl,
                                            height: theme.spacing.xxl,
                                            background:
                                                theme.colors.accent.primary,
                                        }}
                                    />

                                    <div
                                        style={{
                                            width: theme.spacing.xxl,
                                            height: theme.spacing.xxl,
                                            background:
                                                theme.colors.accent.primary,
                                        }}
                                    />
                                </div>
                            )}
                        />
                    ))}
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Radius (how rounds website items are)
                    </div>

                    {Object.keys(theme.radius).map((key) => (
                        <ThemeInputField
                            key={`radius-${key}`}
                            theme={theme}
                            label={key}
                            value={theme.radius[key]}
                            defaultValue={defaultTheme.radius[key]}
                            description={`Border radius with ${key} size`}
                            updateTheme={(value) =>
                                updateThemeValue(["radius", key], value)
                            }
                            suffix="rem"
                            display={({ value, theme }) => (
                                <div
                                    style={{
                                        width: theme.spacing.xxl,
                                        height: theme.spacing.xxl,
                                        borderRadius: value,
                                        background: theme.colors.accent.primary,
                                    }}
                                />
                            )}
                        />
                    ))}
                </div>

                <div style={sectionStyle(theme)}>
                    <div style={theme.styles.titleText}>
                        Transition (how fast website items are)
                    </div>

                    {Object.keys(theme.transition).map((key) => (
                        <ThemeInputField
                            key={`transition-${key}`}
                            theme={theme}
                            label={key}
                            value={theme.transition[key]}
                            defaultValue={defaultTheme.transition[key]}
                            description={`Transition speed with ${key} speed`}
                            updateTheme={(value) =>
                                updateThemeValue(["transition", key], value)
                            }
                            suffix="s ease"
                            display={({ value, theme }) => (
                                <ContinuousPreviewBox
                                    value={value}
                                    theme={theme}
                                />
                            )}
                        />
                    ))}
                </div>

                {/* This is disabled because it doesnt make sense to show this to user */}
                {/* <div style={sectionStyle(theme)}>
                        <div style={theme.styles.titleText}>
                            Dimensions (how big website things are)
                        </div>

                        {Object.keys(theme.dimensions).map((key) => (
                            <ThemeInputField
                                key={`dimensions-${key}`}
                                theme={theme}
                                label={key}
                                value={theme.dimensions[key]}
                                defaultValue={defaultTheme.dimensions[key]}
                                description={`Dimension ${key} with ${key} size`}
                                updateTheme={(value) =>
                                    updateThemeValue(["dimensions", key], value)
                                }
                                display={({ value, theme }) => (
                                    <div
                                        style={{
                                            width: value,
                                            height: value,
                                            background:
                                                theme.colors.accent.primary,
                                            borderRadius: theme.radius.sm,
                                        }}
                                    />
                                )}
                            />
                        ))}
                    </div> */}
            </>
        );
    }

    function render_main() {
        if (!logged_in_permission) {
            return null;
        }
        return (
            <div
                style={{
                    background: theme.colors.background.app,
                    minHeight: "100vh",
                }}
            >
                <NavigationBarWrapper
                    logged_in_permission={logged_in_permission}
                />

                {render_switch()}

                {/* Theme Customization Section */}
                {customThemeEnabled && (
                    <div
                        style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.xl,
                            padding: theme.spacing.xl,
                            margin: "0 auto",
                        }}
                    >
                        <div
                            style={{
                                ...sectionStyle(theme),
                                // display: "grid",
                                // gridTemplateColumns: "1fr 1fr",
                            }}
                        >
                            {/* <div
                                style={{
                                    ...theme.styles.descriptionText,
                                }}
                            >
                                This is an development tool, you can still do
                                basic customizations BUT be careful. It's very
                                easy to break because we give you the freedom to
                                do so. DONT use Theme Keys from unknowns, DONT
                                use fonts from unknowns. IF and ONLY IF anything
                                happens to go crazy and explode all over the
                                place: here is the reset button (there is also
                                one at the bottom of the page, you can use both.
                                We put two buttons so you can fix the even worst
                                fuckups):
                            </div> */}

                            <div
                                style={{
                                    ...theme.styles.descriptionText,
                                }}
                            >
                                Bu bir geliştirici sayfasıdır, basit
                                özelleştirmeler yapabilirsiniz, ANCAK dikkatli
                                olun. Ayarlar çok kolay bir şekilde bozulabilir
                                çünkü özelleştirmelerde sizi herhangi bir
                                şekilde kısıtlamak istemedik. Bilinmeyen
                                kaynaklardan Tema Anahtarları KULLANMAYIN,
                                bilinmeyen kaynaklardan font tipleri
                                KULLANMAYIN. Eğer bir şey kontrolden çıkarsa ve
                                elinize yüzünüze bulaştırırsanız: tam buraya bir
                                sıfırlama düğmesi koyuyoruz (sayfanın en altında
                                da bir tane var, ikisini de kullanabilirsiniz.
                                En rezil hataları bile düzeltebilmeniz için iki
                                düğme koyduk):
                            </div>
                        </div>

                        <ButtonWrapper
                            text="Reset Custom Theme"
                            onClick={resetCustomTheme}
                            visualVariant="danger"
                        />

                        <div
                            style={{
                                display: "flex",
                                flexDirection: "column",
                                gap: theme.spacing.lg,
                                padding: theme.spacing.lg,
                            }}
                        >
                            {render_theme_key_section()}

                            {render_theme_fields()}

                            <ButtonWrapper
                                text="Reset Custom Theme"
                                onClick={resetCustomTheme}
                                visualVariant="danger"
                            />
                        </div>
                    </div>
                )}

                {theme_key_error_message && (
                    <ErrorPopUpWrapper
                        error_message={theme_key_error_message}
                        on_close={() => set_theme_key_error_message("")}
                        error_title="Theme Key Error"
                        sx={{
                            minWidth: "4rem",
                            minHeight: "4rem",
                        }}
                    />
                )}
            </div>
        );
    }

    return render_main();
};
export default CreateThemePage;
