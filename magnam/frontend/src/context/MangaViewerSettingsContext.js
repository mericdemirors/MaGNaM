import React, {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";

const MangaViewerSettingsContext = createContext(null);

function useLocalStorageState(key, defaultValue) {
    const [value, setValue] = useState(() => {
        try {
            const stored = localStorage.getItem(key);

            if (stored !== null) {
                return JSON.parse(stored);
            }

            return defaultValue;
        } catch {
            return defaultValue;
        }
    });

    useEffect(() => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch {}
    }, [key, value]);

    return [value, setValue];
}

export function MangaViewerSettingsProvider({ children }) {
    const [isShowingCoverPages, setIsShowingCoverPages] = useLocalStorageState(
        "mangaviewersettings_isShowingCoverPages",
        true,
    );

    const [isPagedMode, setIsPagedMode] = useLocalStorageState(
        "mangaviewersettings_isPagedMode",
        false,
    );

    const [isShowingProgressBar, setIsShowingProgressBar] =
        useLocalStorageState("mangaviewersettings_isShowingProgressBar", true);

    const [viewer_width, set_viewer_width] = useLocalStorageState(
        "mangaviewersettings_viewer_width",
        35,
    );

    const [viewer_height, set_viewer_height] = useLocalStorageState(
        "mangaviewersettings_viewer_height",
        80,
    );

    const [page_gap, set_page_gap] = useLocalStorageState(
        "mangaviewersettings_page_gap",
        20,
    );

    const value = useMemo(
        () => ({
            isShowingCoverPages,
            setIsShowingCoverPages,

            isPagedMode,
            setIsPagedMode,

            isShowingProgressBar,
            setIsShowingProgressBar,

            viewer_width,
            set_viewer_width,

            viewer_height,
            set_viewer_height,

            page_gap,
            set_page_gap,
        }),
        [
            isShowingCoverPages,
            isPagedMode,
            isShowingProgressBar,
            viewer_width,
            viewer_height,
            page_gap,
        ],
    );

    return (
        <MangaViewerSettingsContext.Provider value={value}>
            {children}
        </MangaViewerSettingsContext.Provider>
    );
}

export function useMangaViewerSettings() {
    const context = useContext(MangaViewerSettingsContext);

    if (!context) {
        throw new Error(
            "useMangaViewerSettings must be used inside MangaViewerSettingsProvider",
        );
    }

    return context;
}
