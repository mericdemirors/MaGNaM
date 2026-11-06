import React from "react";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { saveFont, loadFont } from "../utils/fontStorage";
import { injectFontFromBlob } from "../utils/fontInjector";

const ThemeFontUploadField = ({
    theme,
    label,
    value,
    defaultValue,
    updateTheme,
    description,
    display,
}) => {
    const [file, setFile] = React.useState(null);
    const [fontName, setFontName] = React.useState(value);

    const appliedFont = value;
    const defaultFont = defaultValue;

    const isCustomized = appliedFont !== defaultFont;
    const hasUnsavedChanges = fontName && fontName !== appliedFont;

    let buttonVariant = "ghost";
    let buttonText = "Default";
    if (hasUnsavedChanges) {
        buttonVariant = "danger";
        buttonText = "Click to Save";
    } else if (isCustomized) {
        buttonVariant = "soft";
        buttonText = "Saved";
    }

    // Restore font on refresh
    React.useEffect(() => {
        const restore = async () => {
            if (!value?.startsWith("custom_font_")) return;

            const blob = await loadFont(value);
            if (!blob) return;

            injectFontFromBlob(value, blob);
        };

        restore();
    }, [value]);

    const handleFileUpload = async (e) => {
        const uploadedFile = e.target.files[0];
        if (!uploadedFile) return;

        const generatedName = `custom_font_${Date.now()}`;

        await saveFont(generatedName, uploadedFile);
        injectFontFromBlob(generatedName, uploadedFile);

        setFile(uploadedFile);
        setFontName(generatedName);
    };

    const applyChanges = () => {
        if (!fontName) return;
        updateTheme(fontName);
    };

    const revertChanges = () => {
        setFile(null);
        setFontName(defaultFont);
        updateTheme(defaultFont);
    };

    const previewText =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 .,!?(){}[]-+";

    const renderedDisplay =
        typeof display === "function"
            ? display({ theme, value: appliedFont, defaultValue })
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
                    Default: {defaultFont}
                </div>

                <div style={theme.styles.descriptionText}>
                    Current: {appliedFont}
                </div>
            </div>

            {/* Upload */}
            <input
                type="file"
                accept=".ttf,.otf,.woff,.woff2"
                onChange={handleFileUpload}
            />

            {/* Actions */}
            <ButtonWrapper
                text={buttonText}
                onClick={applyChanges}
                visualVariant={buttonVariant}
            />

            {isCustomized && (
                <ButtonWrapper
                    text="Cancel"
                    onClick={revertChanges}
                    visualVariant="danger"
                />
            )}

            {/* Preview */}
            <div
                style={{
                    minWidth: theme.dimensions.xl,
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    background: theme.colors.background.app,
                }}
            >
                {renderedDisplay}
            </div>
        </div>
    );
};

export default ThemeFontUploadField;
