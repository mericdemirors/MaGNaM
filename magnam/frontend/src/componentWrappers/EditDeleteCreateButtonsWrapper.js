import React, { useState } from "react";
import ButtonWrapper from "./ButtonWrapper";
import { useTheme } from "../context/ThemeContext";

export default function EditDeleteCreateButtonsWrapper({
    edit = false,
    on_edit = () => {},
    on_delete = () => {},
    on_cancel = () => {},
    on_create = () => {},
    edit_text = "Edit",
    delete_text = "Delete",
    cancel_text = "Cancel",
    create_text = "Create",
    at_profilepage = false,
}) {
    const { theme } = useTheme();

    // this variable holds the button_name user presses to disable it while it's assigned function runs
    const [pressed_button, set_pressed_button] = useState(null);

    const runAsync = async (fn, button_name) => {
        if (!fn) return;

        try {
            set_pressed_button(button_name);
            await fn();
        } finally {
            set_pressed_button(null);
        }
    };

    return (
        <div
            style={{
                display: "flex",
                alignItems: "center",
                gap: theme.spacing.lg,
                width: "fit-content",
                padding: theme.spacing.md,
            }}
        >
            {edit || at_profilepage ? (
                <>
                    <ButtonWrapper
                        onClick={() => runAsync(on_edit, "edit")}
                        text={edit_text}
                        disabled={pressed_button === "edit"}
                        sx={{ flex: 1 }}
                    />

                    <ButtonWrapper
                        onClick={on_delete}
                        text={delete_text}
                        visualVariant="danger"
                        sx={{ flex: 1 }}
                    />

                    <ButtonWrapper
                        onClick={on_cancel}
                        text={cancel_text}
                        visualVariant="outline"
                        sx={{ flex: 1 }}
                    />
                </>
            ) : (
                <>
                    <ButtonWrapper
                        onClick={() => runAsync(on_create, "create")}
                        text={create_text}
                        disabled={pressed_button === "create"}
                    />
                    <ButtonWrapper
                        onClick={on_cancel}
                        text={cancel_text}
                        visualVariant="outline"
                        sx={{ flex: 1 }}
                    />
                </>
            )}
        </div>
    );
}
