import React from "react";

import RegisterPanel from "./RegisterPanel";
import LoginPanel from "./LoginPanel";
import GoogleLoginButton from "./GoogleLoginButton";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import { useTheme } from "../context/ThemeContext";

function AccountPage() {
    const { theme } = useTheme();
    return (
        <div
            style={{
                minHeight: "100vh",
                backgroundColor: theme.colors.background.app,
                display: "flex",
                flexDirection: "column", // Stack items vertically
                alignItems: "center", // Center children horizontally
                justifyContent: "center",
                padding: theme.spacing.xl,
                boxSizing: "border-box",
                gap: theme.spacing.xl, // Add space between button and panels
            }}
        >
            {/* Panels row */}
            <div
                style={{
                    display: "flex",
                    alignItems: "stretch",
                    gap: theme.spacing.xl,
                }}
            >
                <RegisterPanel />

                <div
                    style={{
                        width: theme.spacing.lg,
                        backgroundColor: theme.colors.accent.primary,
                        borderRadius: theme.radius.sm,
                    }}
                />

                <LoginPanel />
            </div>

            {/* Google login */}
            <div>
                <GoogleLoginButton />
            </div>

            {/* Guest Button */}
            <div>
                <ButtonWrapper text="Continue as Guest" to="/" />
            </div>
        </div>
    );
}

export default AccountPage;
