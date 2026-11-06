import React from "react";
import { useTheme } from "../context/ThemeContext";

import ButtonWrapper from "./ButtonWrapper";
import MultipleChoiceSelectionWrapper from "./MultipleChoiceSelectionWrapper";
import ErrorPopUpWrapper from "./ErrorPopUpWrapper";
import { HorizontalDivider, SectionLabel } from "./helper_components";

/**
 * ControlPanelWrapper
 * -------------------
 * Secondary exploration controls.
 * Calm, structured, non-dominant.
 */
export default function ControlPanelWrapper({
    /* Create action */
    create_permission = false,
    create_button_text = "",
    create_button_to = "",
    at_kanbanpage = false,

    /* Tags */
    tags_error_message = "",
    set_tags_error_message = () => {},
    tags_error_title = "Tag Error",
    all_tags = [],
    selected_tags = [],
    on_tag_select = () => {},

    /* Sorting */
    all_sorts = [],
    selected_sorts = [],
    on_sort_select = () => {},

    /* Extra sliders */
    sliders = null,
}) {
    const { theme } = useTheme();

    return (
        <div
            style={{
                background: theme.colors.background.surface,
                borderRadius: theme.radius.md,
                padding: theme.spacing.md,
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.lg,
            }}
        >
            {/* Create */}
            {/* we dont have the 'create button' mode for the kanbans in the control panel
            so we directly remove it when we are at kanbans */}
            {create_permission && !at_kanbanpage && (
                <div>
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "center",
                        }}
                    >
                        <ButtonWrapper
                            to={create_button_to}
                            text={create_button_text}
                        />
                    </div>

                    <div
                        style={{
                            marginTop: theme.spacing.md,
                            marginBottom: theme.spacing.md,
                        }}
                    >
                        <HorizontalDivider />
                    </div>
                </div>
            )}

            {/* Tags */}
            <div>
                {tags_error_message ? (
                    <ErrorPopUpWrapper
                        error_message={tags_error_message}
                        on_close={set_tags_error_message}
                        error_title={tags_error_title}
                    />
                ) : (
                    <div>
                        <SectionLabel text="Tags" />
                        <MultipleChoiceSelectionWrapper
                            all_choices={all_tags}
                            selected_choices={selected_tags}
                            handle_choice_select={on_tag_select}
                        />

                        <div
                            style={{
                                marginTop: theme.spacing.md,
                                marginBottom: theme.spacing.md,
                            }}
                        >
                            <HorizontalDivider />
                        </div>
                    </div>
                )}
            </div>

            {/* Sorting */}
            <div>
                <SectionLabel text="Sorting & Filtering" />

                <MultipleChoiceSelectionWrapper
                    all_choices={all_sorts}
                    selected_choices={selected_sorts}
                    handle_choice_select={on_sort_select}
                />
            </div>

            {/* Sliders */}
            {sliders && <div>{sliders}</div>}
        </div>
    );
}
