import React from "react";
import { createRoot } from "react-dom/client";
import { GoogleOAuthProvider } from "@react-oauth/google";

import HomePage from "./HomePage";
import { ThemeProvider, useTheme } from "../context/ThemeContext";
import { AuthProvider } from "../context/AuthContext";
// I dont know if MangaViewerSettingsProvider context needs to be here since its not a global context
// but I guess tying it to MangaViewerWrapper seperately on ReadMangaPage and ShowPortfolioPage is wrong
// chatgpt and gemini said it can create duplicates or something like that so I'm wrapping this context globally
import { MangaViewerSettingsProvider } from "../context/MangaViewerSettingsContext";

const App = () => {
    const { theme } = useTheme();
    return (
        <div
            style={{
                backgroundColor: theme.colors.background.app,
                minHeight: "100vh",
                minWidth: "1200px",
                display: "flex",
                flexDirection: "column",
                fontFamily: theme.typography.fontFamily.primary,
            }}
        >
            <HomePage />
        </div>
    );
};

// Render root with AuthProvider
const appDiv = document.getElementById("app");
const root = createRoot(appDiv);
root.render(
    <GoogleOAuthProvider clientId={window.__CONFIG__.GOOGLE_CLIENT_ID}>
        <AuthProvider>
            <ThemeProvider>
                <MangaViewerSettingsProvider>
                    <App />
                </MangaViewerSettingsProvider>
            </ThemeProvider>
        </AuthProvider>
    </GoogleOAuthProvider>,
);
