import React, {
    useRef,
    useState,
    useEffect,
    useMemo,
    useCallback,
} from "react";
import { Virtualizer } from "virtua";
import SwitchWrapper from "../componentWrappers/SwitchWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import LoadSpinnerWrapper from "../componentWrappers/LoadSpinnerWrapper";
import { useTheme } from "../context/ThemeContext";
import { useMangaViewerSettings } from "../context/MangaViewerSettingsContext";
import { HorizontalDivider, SectionLabel } from "./helper_components";
// infinite viewer code is based on https://inokawa.github.io/virtua/?path=/story/basics-virtualizer--bi-directional-infinite-scrolling

export default function MangaViewerWrapper({
    initial_page_to_load_in = -1, // which page to load in
    handle_bookmark_submit = async () => {}, // function to set bookmark
    items, // flat list of items to display
    current_chapter_index, // current chapter being displayed
    preload_prev = () => 0, // function to prepend items, returns number of pages added
    preload_next = () => 0, // function to append items, returns number of pages added
    update_UI_selected_chapter = () => {}, // function to change current_chapter_index on ReadMangaPage
    mark_chapter_as_read = async () => {}, // function to mark chapters as read
    shift = false, // boolean flag to anchor while prepending to the infinite view
    threshold = 3, // number of pages from edge to trigger preload
    isViewingPortfolioWork = false, // force disables cover page features for portfolio works
}) {
    const { theme } = useTheme();

    // panel settings
    const [isShowingPanel, setIsShowingPanel] = useState(true);

    const {
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
    } = useMangaViewerSettings();

    // filtered list of items to display (cover pages optionally hidden)
    const filtered_items = useMemo(() => {
        return isShowingCoverPages && !isViewingPortfolioWork
            ? items
            : items.filter((item) => item.props.chapter_page !== 0);
    }, [items, isShowingCoverPages, isViewingPortfolioWork]);
    const total_item_count = filtered_items.length;

    // progress bar
    const [progress_bar_page, set_progress_bar_page] = useState(0);
    const [progress_bar_page_count, set_progress_bar_page_count] = useState(0);

    // viewer state
    const viewerContainerRef = useRef(null);
    const infinite_ref = useRef(null);
    const ready = useRef(false); // starts as false, is set to true after infinite mode viewer is loaded the first time

    // store the initial bookmark index in a ref so the ready effect doesn't re-run every time current_item_index changes
    const initial_index_ref = useRef(
        initial_page_to_load_in >= 0 ? initial_page_to_load_in : 0,
    );
    const [current_item_index, set_current_item_index] = useState(
        initial_index_ref.current,
    );
    const current_item_key_ref = useRef(null); // used to recover position after cover-page toggle
    const pre_toggle_key_ref = useRef(null); // snapshot taken just before isShowingCoverPages changes

    // scroll tracking refs
    const infinite_lastScrollOffsetRef = useRef(0);
    const lastTrackedIndexRef = useRef(-1);
    const blockInfiniteScrollTriggers = useRef(false);

    // loading states for prev/next chapter fetches
    const [prependingItems, setPrependingItems] = useState(false);
    const [appendingItems, setAppendingItems] = useState(false);

    const get_item_key = useCallback((item) => {
        if (!item) return null;
        return `${item.props.chapter_index}-${item.props.chapter_page}`;
    }, []);

    // ─── Auto-adjust image dimensions ────────────────────────────────────────────

    // calculates image dimensions and selects the frequent one
    const handleAutoAdjustDimensions = async () => {
        const currentChapterPages = filtered_items.filter(
            (item) =>
                item.props?.chapter_page !== 0 &&
                Number(item.props?.chapter_index) ===
                    Number(current_chapter_index),
        );

        const STEP_INTERVAL = 2;
        const sampledPages = currentChapterPages.filter(
            (_, i) => i % STEP_INTERVAL === 0,
        );

        const imageSources = sampledPages
            .map((item) => item.props?.children?.props?.src)
            .filter(Boolean);

        if (imageSources.length === 0) return;

        const results = await Promise.all(
            imageSources.map(
                (src) =>
                    new Promise((resolve) => {
                        const img = new Image();
                        img.src = src;
                        img.onload = () =>
                            resolve({
                                width: img.naturalWidth,
                                height: img.naturalHeight,
                            });
                        img.onerror = () => resolve(null);
                    }),
            ),
        );

        const dimensionFrequency = {};
        results.forEach((d) => {
            if (!d) return;
            const key = `${d.width}x${d.height}`;
            if (!dimensionFrequency[key]) {
                dimensionFrequency[key] = {
                    count: 0,
                    width: d.width,
                    height: d.height,
                    aspectRatio: d.width / d.height,
                };
            }
            dimensionFrequency[key].count += 1;
        });

        let mostFrequentPair = null;
        let maxCount = 0;
        Object.values(dimensionFrequency).forEach((pair) => {
            if (pair.count > maxCount) {
                maxCount = pair.count;
                mostFrequentPair = pair;
            }
        });

        if (mostFrequentPair && viewerContainerRef.current) {
            const containerHeightPx = viewerContainerRef.current.clientHeight;
            const containerWidthPx = viewerContainerRef.current.clientWidth;
            const targetHeightPx = containerHeightPx * 0.8;
            const targetWidthPx = targetHeightPx * mostFrequentPair.aspectRatio;
            const finalWidth = Math.min(
                100,
                Math.max(
                    25,
                    Math.round((targetWidthPx / containerWidthPx) * 100),
                ),
            );
            const finalHeight = Math.min(
                100,
                Math.max(
                    25,
                    Math.round((targetHeightPx / containerHeightPx) * 100),
                ),
            );
            set_viewer_width(finalWidth);
            set_viewer_height(finalHeight);
        }
    };

    // ─── Paged mode navigation ────────────────────────────────────────────────────

    const goToNextPage = useCallback(() => {
        if (current_item_index >= total_item_count - 1) return;
        const nextIndex = current_item_index + 1;
        set_current_item_index(nextIndex);

        if (!appendingItems && nextIndex + threshold > total_item_count) {
            setAppendingItems(true);
            preload_next();
            setAppendingItems(false);
        }
    }, [
        current_item_index,
        total_item_count,
        threshold,
        appendingItems,
        preload_next,
    ]);

    const goToPrevPage = useCallback(() => {
        if (current_item_index <= 0) return;
        const nextIndex = current_item_index - 1;
        set_current_item_index(nextIndex);

        if (!prependingItems && nextIndex - threshold < 0) {
            setPrependingItems(true);

            // preload_prev returns the number of image pages added.
            const result = preload_prev();

            if (isPagedMode && result > 0) {
                // The prepended chapter adds `result` image pages plus 1 cover div.
                const addedElements =
                    isShowingCoverPages && !isViewingPortfolioWork
                        ? result + 1
                        : result;
                set_current_item_index((prev) => prev + addedElements);
            }

            setPrependingItems(false);
        }
    }, [
        current_item_index,
        threshold,
        prependingItems,
        preload_prev,
        isPagedMode,
        isShowingCoverPages,
        isViewingPortfolioWork,
    ]);

    // ─── Keyboard shortcuts ───────────────────────────────────────────────────────

    // Esc closes the panel
    useEffect(() => {
        function handle_escape_keydown(e) {
            if (e.key === "Escape") setIsShowingPanel(false);
        }
        window.addEventListener("keydown", handle_escape_keydown);
        return () =>
            window.removeEventListener("keydown", handle_escape_keydown);
    }, []);

    // Arrow keys advance pages in paged mode
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (!isPagedMode) return;
            const activeTag = document.activeElement.tagName.toLowerCase();
            if (["input", "textarea"].includes(activeTag)) return;
            if (e.key === "ArrowRight") {
                e.preventDefault();
                goToNextPage();
            } else if (e.key === "ArrowLeft") {
                e.preventDefault();
                goToPrevPage();
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isPagedMode, goToNextPage, goToPrevPage]);

    // ─── Sync helpers ─────────────────────────────────────────────────────────────

    // Scrolls the Virtualizer to a target index and updates all related refs.
    const syncInfiniteScrollToIndex = useCallback(
        ({
            infiniteRef,
            blockTriggersRef,
            lastScrollOffsetRef,
            setCurrentItemIndex,
            targetIndex,
        }) => {
            if (!infiniteRef.current) return;
            requestAnimationFrame(() => {
                if (!infiniteRef.current) return;
                blockTriggersRef.current = true;
                infiniteRef.current.scrollToIndex(targetIndex, {
                    align: "start",
                });
                // Two rAFs: first lets the Virtualizer commit the scroll
                // second lets the browser paint so scrollOffset is accurate.
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (!infiniteRef.current) return;
                        // Capture offset first, then unblock so onScroll's delta
                        // calculation starts from the correct baseline.
                        lastScrollOffsetRef.current =
                            infiniteRef.current.scrollOffset ?? 0;
                        setCurrentItemIndex(targetIndex);
                        blockTriggersRef.current = false;
                    });
                });
            });
        },
        [],
    );

    // Updates current_item_index for paged mode while blocking scroll side-effects.
    const syncPagedViewToIndex = useCallback(
        ({ setCurrentItemIndex, blockTriggersRef, targetIndex }) => {
            requestAnimationFrame(() => {
                blockTriggersRef.current = true;
                requestAnimationFrame(() => {
                    setCurrentItemIndex(targetIndex);
                    blockTriggersRef.current = false;
                });
            });
        },
        [],
    );

    // ─── Initial scroll to bookmark position ─────────────────────────────────────

    // only runs once when infinite mode viewer becomes available for the first time
    useEffect(() => {
        if (isPagedMode || !infinite_ref.current || ready.current) return;
        syncInfiniteScrollToIndex({
            infiniteRef: infinite_ref,
            blockTriggersRef: blockInfiniteScrollTriggers,
            lastScrollOffsetRef: infinite_lastScrollOffsetRef,
            setCurrentItemIndex: set_current_item_index,
            targetIndex: current_item_index,
        });
        ready.current = true;
    }, [isPagedMode, syncInfiniteScrollToIndex]);

    // ─── Sync from paged → infinite on mode switch ────────────────────────────────

    // When switching from paged mode to infinite, the Virtualizer needs an explicit
    // scrollToIndex because it has no knowledge of the paged state.
    useEffect(() => {
        if (isPagedMode || !infinite_ref.current) return;
        if (current_item_index < 0 || current_item_index >= total_item_count)
            return;
        syncInfiniteScrollToIndex({
            infiniteRef: infinite_ref,
            blockTriggersRef: blockInfiniteScrollTriggers,
            lastScrollOffsetRef: infinite_lastScrollOffsetRef,
            setCurrentItemIndex: set_current_item_index,
            targetIndex: current_item_index,
        });
    }, [isPagedMode]);
    // Intentionally omit current_item_index from deps — we only want this to fire
    // when the mode actually toggles, not on every page change.

    // ─── Track current item and trigger side-effects ──────────────────────────────

    // update interface state with scroll
    // mark a chapter as read only when the user is on the last page of that chapter
    useEffect(() => {
        const item = filtered_items[current_item_index];
        if (!item) return;
        current_item_key_ref.current = get_item_key(item);

        const chapter = item.props.chapter_index;
        const chapter_page = item.props.chapter_page;

        // Find the last page that belongs to this chapter
        const lastPageIndexInChapter = filtered_items.reduce(
            (lastIdx, fi, idx) =>
                fi.props.chapter_index === chapter ? idx : lastIdx,
            -1,
        );
        const isLastPageOfChapter =
            lastPageIndexInChapter !== -1 &&
            current_item_index === lastPageIndexInChapter;

        if (isLastPageOfChapter) {
            const chapter_id = item.props.chapter_id ?? chapter;
            mark_chapter_as_read(chapter_id);
        }

        // update progress bar
        set_progress_bar_page(chapter_page);

        // update selected chapter in parent UI
        if (current_chapter_index !== chapter)
            update_UI_selected_chapter(chapter);

        // update page count when chapter changes or count is still unset
        if (
            current_chapter_index !== chapter ||
            progress_bar_page_count === 0
        ) {
            set_progress_bar_page_count(
                filtered_items.filter(
                    (fi) => fi.props.chapter_index === chapter,
                ).length,
            );
        }
    }, [
        current_item_index,
        current_chapter_index,
        filtered_items,
        progress_bar_page_count,
        mark_chapter_as_read,
        update_UI_selected_chapter,
        get_item_key,
    ]);

    // ─── Preload adjacent pages for paged mode ────────────────────────────────────

    // Pre-decodes the neighbouring images so they don't flicker when first displayed.
    useEffect(() => {
        const preloadImage = async (index) => {
            if (!isPagedMode) return;
            const item = filtered_items[index];
            if (!item) return;
            if (item.props.chapter_page === 0) return; // cover pages are divs, not imgs

            const src = item.props?.children?.props?.src;
            if (!src) return;

            const img = new Image();
            img.src = src;
            if (img.decode) {
                try {
                    await img.decode();
                } catch {
                    // silently ignore — image may already be cached or unavailable
                }
            }
        };

        preloadImage(current_item_index + 1);
        preloadImage(current_item_index - 1);
    }, [current_item_index, isPagedMode, filtered_items]);

    // ─── Preserve reader position when cover-pages toggle ────────────────────────

    // we need a way to preserve the currently displayed page when cover pages are toggled on and off
    // there are few problems that needs to be considered here:
    // 1- toggling isShowingCoverPages means filtered_items will be updated
    // 2- filtered_items being updated means current_item_index wont be valid anymore we cant trust it
    // 3- so we have to trust the current_item_ref which we keep up to date while scrolling via effect
    // Main problem I had is this: filtered_items being updated also breaks the 'filtered_items.findLastIndex' search
    // so I also cant blindly trust the current_item_key_ref. Its also important to notice that these updates trigger the scroll effect above which updates the current_item_key_ref making it less trustworthy
    useEffect(() => {
        // Restore reader position after the cover-page filter changes.
        //
        // Why pre_toggle_key_ref instead of current_item_key_ref:
        //   Both this effect and the tracking effect (which writes current_item_key_ref)
        //   run after the same render. React does not guarantee their relative order,
        //   so current_item_key_ref may already have been overwritten with whatever
        //   the tracking effect resolved for the *new* filtered_items — which would
        //   give us the wrong key. pre_toggle_key_ref is written synchronously in the
        //   event handler, before any state change is enqueued, so it is always a
        //   reliable snapshot of where the user actually was.
        const savedKey = pre_toggle_key_ref.current;
        if (!savedKey) return;

        // Find the item with the saved key in the already-updated filtered_items.
        const newIndex = filtered_items.findIndex(
            (item) => get_item_key(item) === savedKey,
        );

        // If the exact page was a cover page that is now hidden, fall back to the
        // first page of the same chapter (chapter_page === 1).
        let targetIndex = newIndex;
        if (targetIndex === -1) {
            const [savedChapterIndex] = savedKey.split("-");
            targetIndex = filtered_items.findIndex(
                (item) =>
                    String(item.props.chapter_index) === savedChapterIndex &&
                    item.props.chapter_page === 1,
            );
        }

        if (targetIndex === -1) return; // chapter not loaded at all — nothing to do

        if (isPagedMode) {
            syncPagedViewToIndex({
                setCurrentItemIndex: set_current_item_index,
                blockTriggersRef: blockInfiniteScrollTriggers,
                targetIndex,
            });
        } else {
            syncInfiniteScrollToIndex({
                infiniteRef: infinite_ref,
                blockTriggersRef: blockInfiniteScrollTriggers,
                lastScrollOffsetRef: infinite_lastScrollOffsetRef,
                setCurrentItemIndex: set_current_item_index,
                targetIndex,
            });
        }

        pre_toggle_key_ref.current = null;
    }, [
        isShowingCoverPages,
        filtered_items,
        isPagedMode,
        get_item_key,
        syncPagedViewToIndex,
        syncInfiniteScrollToIndex,
    ]);

    // ─── Render helpers ───────────────────────────────────────────────────────────

    function render_panel_slider(text, child) {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: theme.spacing.md,
                    width: "100%",
                }}
            >
                <span
                    style={{
                        ...theme.styles.metadataText,
                        paddingBottom: theme.spacing.lg,
                    }}
                >
                    {text}
                </span>
                <div style={{ flexGrow: 1 }}>{child}</div>
            </div>
        );
    }

    function render_panel() {
        return (
            <div
                style={{
                    borderRadius: theme.radius.md,
                    display: "flex",
                    flexDirection: "column",
                    flexWrap: "nowrap",
                    alignItems: "flex-start",
                    gap: theme.spacing.md,
                    padding: theme.spacing.md,
                    width: "100%",
                    height: "100%",
                    background: theme.colors.background.surface,
                }}
            >
                <SwitchWrapper
                    text={"Panel"}
                    checked={isShowingPanel}
                    onEnable={() => setIsShowingPanel(true)}
                    onDisable={() => setIsShowingPanel(false)}
                    visualVariant="soft"
                />

                <HorizontalDivider />
                <SectionLabel text="Style" />
                <SwitchWrapper
                    text={"Paged Reading"}
                    checked={isPagedMode}
                    onEnable={() => setIsPagedMode(true)}
                    onDisable={() => setIsPagedMode(false)}
                    visualVariant="soft"
                />

                <HorizontalDivider />
                <SectionLabel text="Size" />

                {render_panel_slider(
                    "width",
                    <IntegerSliderWrapper
                        value={viewer_width}
                        min={25}
                        max={100}
                        step={1}
                        onChange={(e, newValue) => set_viewer_width(newValue)}
                    />,
                )}
                {render_panel_slider(
                    "height",
                    <IntegerSliderWrapper
                        value={viewer_height}
                        min={25}
                        max={100}
                        step={1}
                        onChange={(e, newValue) => set_viewer_height(newValue)}
                    />,
                )}

                <ButtonWrapper
                    onClick={handleAutoAdjustDimensions}
                    text="Auto Page Size"
                    visualVariant="soft"
                />

                <HorizontalDivider />
                <SectionLabel text="Pages" />
                <SwitchWrapper
                    text={"Progress Bar"}
                    checked={isShowingProgressBar}
                    onEnable={() => setIsShowingProgressBar(true)}
                    onDisable={() => setIsShowingProgressBar(false)}
                    visualVariant="soft"
                />
                {!isViewingPortfolioWork ? (
                    <SwitchWrapper
                        text={"Cover Pages"}
                        checked={isShowingCoverPages}
                        onEnable={() => {
                            pre_toggle_key_ref.current =
                                current_item_key_ref.current;
                            setIsShowingCoverPages(true);
                        }}
                        onDisable={() => {
                            pre_toggle_key_ref.current =
                                current_item_key_ref.current;
                            setIsShowingCoverPages(false);
                        }}
                        visualVariant="soft"
                    />
                ) : null}

                {!isPagedMode
                    ? render_panel_slider(
                          "page gap",
                          <IntegerSliderWrapper
                              value={page_gap}
                              min={0}
                              max={100}
                              step={5}
                              onChange={(e, newValue) => set_page_gap(newValue)}
                          />,
                      )
                    : null}

                {!isViewingPortfolioWork ? (
                    <>
                        <HorizontalDivider />
                        <ButtonWrapper
                            onClick={() => {
                                // Find the first page of the current chapter in the list
                                const firstPageGlobalIndex =
                                    filtered_items.findIndex(
                                        (item) =>
                                            Number(item.props.chapter_index) ===
                                            Number(current_chapter_index),
                                    );
                                if (firstPageGlobalIndex === -1) return;
                                // Local page index = distance from first page of this chapter
                                const localPageIndex =
                                    current_item_index - firstPageGlobalIndex;
                                handle_bookmark_submit(
                                    current_chapter_index,
                                    localPageIndex,
                                );
                            }}
                            text="Put Bookmark"
                        />
                    </>
                ) : null}
            </div>
        );
    }

    function render_progress_bar() {
        const minPage =
            isShowingCoverPages && !isViewingPortfolioWork
                ? Math.min(0, progress_bar_page_count)
                : Math.min(1, progress_bar_page_count);
        const maxPage =
            progress_bar_page_count -
            (isShowingCoverPages && !isViewingPortfolioWork ? 1 : 0);
        return (
            <IntegerSliderWrapper
                value={progress_bar_page}
                min={minPage}
                max={maxPage}
                step={1}
                onChange={() => {}}
                showValue="off"
                showLimits={false}
                showThumb={false}
            />
        );
    }

    function render_infinite_viewer() {
        return (
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                }}
            >
                <LoadSpinnerWrapper loading={prependingItems} />

                <div
                    style={{
                        width: `${viewer_width}%`,
                        height: `${viewer_height}%`,
                        overflowX: "auto",
                        overflowY: "auto",
                        overflowAnchor: "none",
                    }}
                >
                    <Virtualizer
                        ref={infinite_ref}
                        shift={shift}
                        startMargin={5}
                        onScroll={() => {
                            if (
                                !ready.current ||
                                !infinite_ref.current ||
                                total_item_count === 0 ||
                                blockInfiniteScrollTriggers.current
                            )
                                return;

                            const startOffset =
                                infinite_ref.current.scrollOffset;
                            const delta =
                                startOffset -
                                infinite_lastScrollOffsetRef.current;
                            infinite_lastScrollOffsetRef.current = startOffset;
                            const endOffset =
                                startOffset + infinite_ref.current.viewportSize;
                            const middleOffset = (startOffset + endOffset) / 2;

                            // Update current_item_index when the middle-of-viewport item changes
                            const middle_item_index =
                                infinite_ref.current.findItemIndex(
                                    middleOffset,
                                );
                            if (
                                middle_item_index !==
                                lastTrackedIndexRef.current
                            ) {
                                lastTrackedIndexRef.current = middle_item_index;
                                set_current_item_index(middle_item_index);
                            }

                            // Preload next chapter when near the bottom (scrolling down)
                            if (
                                delta > 0 &&
                                !appendingItems &&
                                infinite_ref.current.findItemIndex(endOffset) +
                                    threshold >
                                    total_item_count
                            ) {
                                setAppendingItems(true);
                                preload_next();
                                setAppendingItems(false);
                            }
                            // Preload prev chapter when near the top (scrolling up)
                            else if (
                                delta < 0 &&
                                !prependingItems &&
                                infinite_ref.current.findItemIndex(
                                    startOffset,
                                ) -
                                    threshold <
                                    0
                            ) {
                                setPrependingItems(true);
                                preload_prev();
                                setPrependingItems(false);
                            }
                        }}
                    >
                        {filtered_items.map((item) => (
                            <div
                                key={get_item_key(item)}
                                style={{ marginBottom: `${page_gap}px` }}
                            >
                                {item}
                            </div>
                        ))}
                    </Virtualizer>

                    {isShowingProgressBar ? (
                        <div
                            style={{
                                position: "sticky",
                                height: theme.spacing.lg,
                                bottom: 0,
                            }}
                        >
                            {render_progress_bar()}
                        </div>
                    ) : null}
                </div>

                <LoadSpinnerWrapper loading={appendingItems} />
            </div>
        );
    }

    function render_paged_reader() {
        // 1. Default to standard index tracking
        let itemToRender = filtered_items[current_item_index];

        // 2. Visual Lock: If a toggle just happened, locate the item by its unique key
        // to bypass the single-frame index alignment mismatch
        if (pre_toggle_key_ref.current) {
            const matchedItem = filtered_items.find(
                (item) => get_item_key(item) === pre_toggle_key_ref.current,
            );

            if (matchedItem) {
                itemToRender = matchedItem;
            } else {
                // Fallback if the exact page was a cover page that is now hidden
                const [savedChapterIndex] =
                    pre_toggle_key_ref.current.split("-");
                const fallbackItem = filtered_items.find(
                    (item) =>
                        String(item.props.chapter_index) ===
                            savedChapterIndex && item.props.chapter_page === 1,
                );
                if (fallbackItem) itemToRender = fallbackItem;
            }
        }

        // Handle clicking the left 20% or right 20% of the screen
        const handlePagedClick = (e) => {
            // Prevent triggering page turns if clicking on UI elements like input/buttons inside the panel
            if (e.target.closest("button, input, select, textarea")) return;
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = e.clientX - rect.left; // relative x position
            const width = rect.width;

            const thresholdLeft = width * 0.2;
            const thresholdRight = width * 0.8;
            if (clickX <= thresholdLeft) {
                goToPrevPage();
            } else if (clickX >= thresholdRight) {
                goToNextPage();
            }
        };

        return (
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "flex-start",
                    overflow: "hidden",
                    position: "relative",
                    paddingTop: theme.spacing.md,
                }}
            >
                {prependingItems || appendingItems ? (
                    <LoadSpinnerWrapper loading={true} />
                ) : (
                    <div
                        onClick={handlePagedClick}
                        style={{
                            width: `${viewer_width}%`,
                            height: `${viewer_height}%`,
                            position: "relative",
                            overflow: "hidden",
                        }}
                    >
                        {/* Render the safely locked element */}
                        {itemToRender}

                        {isShowingProgressBar ? (
                            <div
                                style={{
                                    position: "absolute",
                                    left: 0,
                                    bottom: 0,
                                    width: "100%",
                                    zIndex: 5,
                                }}
                            >
                                {render_progress_bar()}
                            </div>
                        ) : null}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div
            style={{
                display: "flex",
                width: "100%",
                height: "100vh",
                overflow: "hidden",
                position: "relative",
            }}
        >
            {/* Panel overlay */}
            <div
                style={{
                    position: "absolute",
                    top: theme.spacing.lg,
                    left: theme.spacing.lg,
                    width: isShowingPanel ? "20%" : "0%",
                    padding: isShowingPanel ? theme.spacing.sm : 0,
                    overflow: "hidden",
                    zIndex: 20,
                    visibility: isShowingPanel ? "visible" : "hidden",
                    borderRadius: theme.radius.md,
                    boxShadow: theme.colors.shadow.card,
                    backdropFilter: "blur(8px)",
                }}
            >
                {render_panel()}
            </div>

            {/* Viewer */}
            <div
                ref={viewerContainerRef}
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "flex-start",
                    zIndex: 1,
                }}
            >
                {isPagedMode ? render_paged_reader() : render_infinite_viewer()}
            </div>

            {/* Floating panel toggle when panel is closed */}
            {!isShowingPanel && (
                <div
                    style={{
                        position: "absolute",
                        top: theme.spacing.xxl,
                        left: theme.spacing.xxl,
                        zIndex: 10,
                    }}
                >
                    <SwitchWrapper
                        text={"Panel"}
                        checked={isShowingPanel}
                        onEnable={() => setIsShowingPanel(true)}
                        onDisable={() => setIsShowingPanel(false)}
                        visualVariant="soft"
                    />
                </div>
            )}
        </div>
    );
}
