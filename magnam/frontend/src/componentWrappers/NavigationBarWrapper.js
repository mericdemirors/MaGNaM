import React from "react";
import { Link, useNavigate } from "react-router-dom";

import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import { useTheme } from "../context/ThemeContext";
import ButtonWrapper from "./ButtonWrapper";
import ProfileDirectingWrapper from "./ProfileDirectingWrapper";
import LogoutButton from "../pages/LogoutButton";
import { useAuth } from "../context/AuthContext";

import MagnamIconPNG from "../../static/images/favicon.webp";
import IconButton from "@mui/material/IconButton";
import DarkModeOutlinedIcon from "@mui/icons-material/DarkModeOutlined";
import LightModeOutlinedIcon from "@mui/icons-material/LightModeOutlined";

export default function NavigationBarWrapper({
    logged_in_permission,
    profile_balance = -1,
}) {
    const { theme, toggleMode } = useTheme();
    const { authInfo } = useAuth();
    const navigate = useNavigate();

    const navLinks = [
        { text: "Portfolios", to: "/portfolio/" },
        { text: "Mangas", to: "/manga/" },
        { text: "Competitions", to: "/competition/" },
        { text: "What, Why, How is Magnam", to: "/about/" },
    ];

    return (
        <AppBar
            position="static"
            sx={{
                backgroundColor: theme.colors.background.app_darker,
                boxShadow: theme.colors.shadow.card,
            }}
        >
            <Toolbar
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    px: theme.spacing.md,
                }}
            >
                {/* LEFT: Logo & Home */}
                <Link
                    to="/"
                    style={{
                        display: "flex",
                        alignItems: "center",
                        textDecoration: "none",
                    }}
                >
                    <img
                        src={MagnamIconPNG}
                        alt="Magnam Home"
                        style={{
                            height: 48,
                            width: 48,
                            borderRadius: theme.radius.sm,
                            transition: theme.transition.fast,
                        }}
                    />
                </Link>

                {/* CENTER: Nav Links */}
                <div style={{ display: "flex", gap: theme.spacing.lg }}>
                    {navLinks.map((link) => (
                        <ButtonWrapper
                            key={link.text}
                            to={link.to}
                            text={link.text}
                            visualVariant="ghost"
                            sx={{
                                ...theme.styles.subtitleText,
                            }}
                        />
                    ))}
                </div>

                {/* RIGHT: Profile / Login */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: theme.spacing.md,
                    }}
                >
                    {/* Light/Dark mode switch */}
                    <IconButton
                        onClick={toggleMode}
                        sx={{
                            color: theme.colors.text.secondary,
                            transition: theme.transition.fast,
                            "&:hover": {
                                color: theme.colors.accent.primary,
                                backgroundColor: "transparent",
                            },
                        }}
                        aria-label="Toggle light/dark mode"
                    >
                        {theme.mode === "light" ? (
                            <DarkModeOutlinedIcon />
                        ) : (
                            <LightModeOutlinedIcon />
                        )}
                    </IconButton>

                    {logged_in_permission ? (
                        <>
                            <div
                                style={{
                                    ...theme.styles.subtitleText,
                                    color: theme.colors.text.muted,
                                }}
                            >
                                {!authInfo.is_verified &&
                                    "⚠️ mail not verified"}
                            </div>

                            <ProfileDirectingWrapper
                                profile_id={authInfo.profile_id}
                                profile_name={authInfo.profile_name}
                                profile_image={authInfo.profile_image}
                            />

                            {authInfo.unread_messages > 0 && (
                                <div
                                    onClick={() =>
                                        navigate(
                                            `/profile/${authInfo.profile_id}/`,
                                        )
                                    }
                                    style={{
                                        ...theme.styles.metadataText,
                                        color: theme.colors.text.muted,
                                        cursor: "pointer",
                                    }}
                                >
                                    {authInfo.unread_messages} 💬
                                </div>
                            )}

                            {profile_balance !== -1 && (
                                <div
                                    style={{
                                        ...theme.styles.metadataText,
                                        color: theme.colors.text.muted,
                                    }}
                                >
                                    {profile_balance}
                                    {theme.coin}
                                </div>
                            )}

                            <LogoutButton />
                        </>
                    ) : (
                        <ButtonWrapper to="/account/" text="Register / Login" />
                    )}
                </div>
            </Toolbar>
        </AppBar>
    );
}
