/* ! GLOBAL VARIABLE FORMAT:

    is_authenticated: false
    profile_id: null
    profile_name: null
    profile_image: null
    is_admin: false

    ACCESS:
    const { authInfo, updateGlobalUnreadMessages, resetUnreadMessages } = useAuth();
    console.log(authInfo.unread_messages);
    updateGlobalUnreadMessages();
    resetUnreadMessages();
*/
import React, {
    createContext,
    useContext,
    useEffect,
    useState,
    useCallback,
} from "react";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useMessageWebSocket } from "../utils/useMessageWebSocket";

// Keys for localStorage
const AUTH_STORAGE_KEY = "authInfo";

// Default auth info
const defaultAuthInfo = {
    is_authenticated: false,
    profile_id: null,
    profile_name: null,
    profile_image: null,
    is_admin: false,
    is_verified: false,
    unread_messages: 0,
};

// Create the context
const AuthContext = createContext(null);

// Helper to load auth info from localStorage
function loadAuthInfo() {
    try {
        const data = localStorage.getItem(AUTH_STORAGE_KEY);
        return data ? JSON.parse(data) : defaultAuthInfo;
    } catch (e) {
        console.error("Failed to load auth info", e);
        return defaultAuthInfo;
    }
}

// Helper to save auth info to localStorage
function saveAuthInfo(authInfo) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authInfo));
}

// Helper to clear auth info from localStorage
function clearAuthInfo() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function AuthProvider({ children }) {
    const [authInfo, setAuthInfo] = useState(loadAuthInfo);
    const [lastIncomingMessage, setLastIncomingMessage] = useState(null);

    // --- Fetch fresh auth info from backend ---
    async function refreshAuth() {
        try {
            await apiFetch("/api/profile/csrf/", { method: "GET" });

            const me_response = await apiFetch("/api/profile/me/", {
                method: "GET",
            });
            const [me_success_data, me_error_message, me_ok] =
                await handleFetch("me", me_response);

            if (me_ok) {
                const newAuth = {
                    is_authenticated: true,
                    profile_id: me_success_data.profile.id,
                    profile_name: me_success_data.profile.profile_name,
                    profile_image: me_success_data.profile.image || null,
                    is_admin: me_success_data.is_admin,
                    is_verified: me_success_data.is_verified,
                    unread_messages: me_success_data.unread_messages || 0,
                };

                setAuthInfo(newAuth);
                saveAuthInfo(newAuth);
            } else {
                // Not authenticated or error
                setAuthInfo(defaultAuthInfo);
                clearAuthInfo();
                return;
            }
        } catch (error) {
            console.error("Failed to refresh auth:", error);
            setAuthInfo(defaultAuthInfo);
            clearAuthInfo();
        }
    }

    // --- Logout helper ---
    function logout() {
        setAuthInfo(defaultAuthInfo);
        clearAuthInfo();
    }

    // --- Increment unread messages ---
    function updateGlobalUnreadMessages(count = 1) {
        setAuthInfo((prev) => {
            const updated = {
                ...prev,
                unread_messages: prev.unread_messages + count,
            };
            saveAuthInfo(updated);
            return updated;
        });
    }

    // --- Reset unread messages ---
    function resetUnreadMessages() {
        setAuthInfo((prev) => {
            const updated = { ...prev, unread_messages: 0 };
            saveAuthInfo(updated);
            return updated;
        });
    }

    // Fetch auth info on first mount
    useEffect(() => {
        refreshAuth();
    }, []);

    const handleIncomingMessage = useCallback((message) => {
        // Broadcast first
        setLastIncomingMessage(message);

        // Then do default global behavior
        setAuthInfo((prev) => {
            const updated = {
                ...prev,
                unread_messages: prev.unread_messages + 1,
            };
            saveAuthInfo(updated);
            return updated;
        });
    }, []);

    function setAuthUnverified() {
        setAuthInfo((prev) => {
            const updated = {
                ...prev,
                is_verified: false,
            };
            saveAuthInfo(updated);
            return updated;
        });
    }

    useMessageWebSocket(authInfo.profile_id, handleIncomingMessage);

    return (
        <AuthContext.Provider
            value={{
                authInfo,
                logout,
                refreshAuth,
                updateGlobalUnreadMessages,
                resetUnreadMessages,
                setAuthUnverified,
                lastIncomingMessage,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

// Hook to use auth anywhere in the app
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
