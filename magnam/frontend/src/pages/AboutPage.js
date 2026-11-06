import React, { useState, useEffect, useRef } from "react";
import { Masonry } from "@mui/lab";

import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import IntegerSliderWrapper from "../componentWrappers/IntegerSliderWrapper";
import RegisteredSlidersDisplayWrapper from "../componentWrappers/RegisteredSlidersDisplayWrapper";
import HasPermission from "../utils/HasPermission";
import ControlPanelWrapper from "../componentWrappers/ControlPanelWrapper";
import KanbanTaskWrapper from "../componentWrappers/KanbanTaskWrapper";
import LoadSpinnerWrapper from "../componentWrappers/LoadSpinnerWrapper";
import {
    setFetchAndSet,
    galleryFetchAndSet,
    handleIdLabelItemSelect,
    handleIdLabelItemSlotSelect,
    scrollDebounceHelper,
    constructRequestUrl,
    handleSortIdLabelItemSelect,
} from "../utils/helper_functions";
import {
    validateText,
    validateNumber,
    validatePKRelation,
} from "../utils/helper_validators";
import {
    AboutPageTextWrapperTR,
    AboutPageTextWrapperEN,
} from "../componentWrappers/AboutPageTextWrapper";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useTheme } from "../context/ThemeContext";
import {
    HorizontalDivider,
    SectionLabel,
} from "../componentWrappers/helper_components";
import {
    GALLERY_FETCH_TIMEOUT_DELAY,
    KANBAN_MIN_TAG_COUNT,
    KANBAN_MAX_TAG_COUNT,
    KANBAN_MIN_DESCRIPTION_LEN,
    KANBAN_MAX_DESCRIPTION_LEN,
    KANBAN_MIN_IMPORTANCE,
    KANBAN_MAX_IMPORTANCE,
} from "../globals";

function AboutPage() {
    const { theme } = useTheme();
    const logged_in_permission = HasPermission("logged_in");

    const abortRef = useRef(null); // to abort the previously send requests
    const fetchTimeout = useRef(null); // for preventing rapid request sending in back to back filter changes
    const [kanban_gallery, set_kanban_gallery] = useState([]);
    const [kanban_task_to_create, set_kanban_task_to_create] = useState({
        description: "",
        importance: 0,
        tags: [],
    });

    const [all_tags, set_all_tags] = useState([]); // will store all tags
    const [selected_tags, set_selected_tags] = useState([]); // will contain currently selected tags
    const [next_page, set_next_page] = useState(null);
    const [loading, set_loading] = useState(true);
    const [loading_more, set_loading_more] = useState(false);
    const [is_submitting_task, set_is_submitting_task] = useState(false);

    const [importance_range, set_importance_range] = useState([
        KANBAN_MIN_IMPORTANCE,
        KANBAN_MAX_IMPORTANCE,
    ]);

    // 0: we are not asking for confirmation
    // any other value: asking for confirmation to delete that kanban task
    const [asking_for_confirmation, set_asking_for_confirmation] = useState(0);
    const [gallery_error_message, set_gallery_error_message] = useState("");
    const [tags_error_message, set_tags_error_message] = useState("");
    const [
        kanban_task_create_error_message,
        set_kanban_task_create_error_message,
    ] = useState("");

    const all_sorts = [
        { id: "date", label: "date (+)" },
        { id: "-date", label: "date (-)" },
        { id: "importance", label: "importance (+)" },
        { id: "-importance", label: "importance (-)" },
        { id: "num_of_upvotes", label: "upvotes (+)" },
    ];
    const [selected_sorts, set_selected_sorts] = useState([
        "importance",
        "date",
    ]);

    // fetch all tags from API when page loads
    useEffect(() => {
        setFetchAndSet(
            "/api/kanban/tag/",
            set_all_tags,
            set_tags_error_message,
            "tags",
        );
    }, []);

    function construct_request_url() {
        const registered_ranges = [
            {
                range: importance_range,
                min_limit: KANBAN_MIN_IMPORTANCE,
                max_limit: KANBAN_MAX_IMPORTANCE,
                min_prefix: "importance_min",
                max_prefix: "importance_max",
            },
        ];

        return constructRequestUrl(
            "/api/kanban/kanban-gallery/",
            selected_tags,
            selected_sorts,
            registered_ranges,
        );
    }

    // Fetch kanban tasks
    async function fetch_kanban_tasks() {
        if (abortRef.current) {
            abortRef.current.abort();
        }

        const controller = new AbortController();
        abortRef.current = controller;

        set_kanban_gallery([]);
        set_next_page(null);

        galleryFetchAndSet(
            construct_request_url(),
            set_kanban_gallery,
            set_gallery_error_message,
            set_loading,
            set_next_page,
            "kanban_gallery",
            controller.signal,
        );
    }

    function fetch_kanban_tasks_with_delay() {
        // runs the fetch command after GALLERY_FETCH_TIMEOUT_DELAY ms of no activity
        clearTimeout(fetchTimeout.current);
        fetchTimeout.current = setTimeout(() => {
            fetch_kanban_tasks();
        }, GALLERY_FETCH_TIMEOUT_DELAY);
    }

    // Initial fetch
    useEffect(() => {
        fetch_kanban_tasks();
    }, []);

    // for unmount cleanup
    useEffect(() => {
        return () => {
            if (abortRef.current) {
                abortRef.current.abort();
            }
        };
    }, []);

    // Refetch kanban tasks when tags change
    useEffect(() => {
        fetch_kanban_tasks();
    }, [selected_tags, selected_sorts]);

    // Load more kanban tasks with current filters
    async function load_more_kanban_tasks() {
        if (!next_page || loading_more) return;

        galleryFetchAndSet(
            next_page,
            set_kanban_gallery,
            set_gallery_error_message,
            set_loading_more,
            set_next_page,
            "kanban_gallery",
        );
    }

    useEffect(() => {
        return scrollDebounceHelper(load_more_kanban_tasks);
    }, [next_page, loading_more]);

    async function handle_delete(kanban_task_id, is_confirmed = false) {
        if (!asking_for_confirmation) {
            set_asking_for_confirmation(kanban_task_id);
        } else if (!is_confirmed) {
            set_asking_for_confirmation(0);
        } else if (is_confirmed) {
            set_asking_for_confirmation(0);

            try {
                const delete_kanban_task_response = await apiFetch(
                    `/api/kanban/delete-task/${kanban_task_id}/`,
                    { method: "DELETE" },
                );
                const [
                    delete_kanban_task_success_data,
                    delete_kanban_task_error_message,
                    delete_kanban_task_ok,
                ] = await handleFetch(
                    "delete_task",
                    delete_kanban_task_response,
                );

                if (delete_kanban_task_ok) {
                    set_kanban_gallery((prev) =>
                        prev.filter((k) => k.id !== kanban_task_id),
                    );
                    set_gallery_error_message("");
                } else {
                    set_gallery_error_message(delete_kanban_task_error_message);
                }
            } catch (err) {
                set_gallery_error_message(
                    err.message || "Network error during kanban task deletion.",
                );
            }
        }
    }

    async function handle_vote(kanban_task_id, vote) {
        try {
            const vote_response = await apiFetch(
                `/api/kanban/vote-task/${kanban_task_id}/`,
                { method: "POST", body: JSON.stringify({ vote }) },
            );
            const [vote_success_data, vote_error_message, vote_ok] =
                await handleFetch("vote_task", vote_response);

            if (vote_ok) {
                const { new_vote, upvote_change, downvote_change } =
                    vote_success_data;

                set_kanban_gallery((prev) =>
                    prev.map((p) =>
                        p.id === kanban_task_id
                            ? {
                                  ...p,
                                  is_user_voted: new_vote ?? 0, // convert null to 0
                                  num_of_upvotes:
                                      p.num_of_upvotes + upvote_change,
                                  num_of_downvotes:
                                      p.num_of_downvotes + downvote_change,
                              }
                            : p,
                    ),
                );
            } else {
                set_gallery_error_message(vote_error_message);
            }
        } catch (err) {
            set_gallery_error_message(
                err.message || "Network error during kanban task voting.",
            );
        }
    }

    async function check_field_requirements() {
        const trimmed_description = kanban_task_to_create.description.trim();

        set_kanban_task_to_create((prev) => ({
            ...prev,
            description: trimmed_description,
        }));

        const isDescriptionValid = validateText({
            value: trimmed_description,
            fieldName: "Description",
            minLen: KANBAN_MIN_DESCRIPTION_LEN,
            maxLen: KANBAN_MAX_DESCRIPTION_LEN,
            required: true,
            error_handler: set_kanban_task_create_error_message,
        });

        const isTagsValid = validatePKRelation({
            value: kanban_task_to_create.tags,
            fieldName: "Tags",
            minCount: KANBAN_MIN_TAG_COUNT,
            maxCount: KANBAN_MAX_TAG_COUNT,
            required: true,
            error_handler: set_kanban_task_create_error_message,
        });

        const isImportanceValid = validateNumber({
            value: kanban_task_to_create.importance,
            fieldName: "Importance",
            minVal: KANBAN_MIN_IMPORTANCE,
            maxVal: KANBAN_MAX_IMPORTANCE,
            required: true,
            error_handler: set_kanban_task_create_error_message,
        });

        return isDescriptionValid && isTagsValid && isImportanceValid;
    }

    async function create_form_data() {
        if (!(await check_field_requirements())) return null;

        const form_data = new FormData();
        form_data.append("description", kanban_task_to_create.description);
        form_data.append("importance", kanban_task_to_create.importance);
        kanban_task_to_create.tags.forEach((tag_id) =>
            form_data.append("tags", tag_id),
        );

        return form_data;
    }

    async function handle_create() {
        const form_data = await create_form_data();
        if (!form_data) return;

        try {
            set_is_submitting_task(true);
            const create_kanban_task_response = await apiFetch(
                "/api/kanban/create-task/",
                { method: "POST", body: form_data },
            );
            const [
                create_kanban_task_success_data,
                create_kanban_task_error_message,
                create_kanban_task_ok,
            ] = await handleFetch("create_task", create_kanban_task_response);

            if (create_kanban_task_ok) {
                const kanban_task_created = {
                    id: create_kanban_task_success_data.id,
                    creator_id: create_kanban_task_success_data.creator_id,
                    description: create_kanban_task_success_data.description,
                    tags: create_kanban_task_success_data.tags ?? [],
                    importance: create_kanban_task_success_data.importance,
                    num_of_upvotes: 0,
                    num_of_downvotes: 0,
                    is_user_voted: 0,
                };

                set_kanban_gallery((prev_gallery) => [
                    kanban_task_created,
                    ...prev_gallery,
                ]);

                set_kanban_task_to_create({
                    description: "",
                    importance: 0,
                    tags: [],
                });
                set_gallery_error_message(""); // we also need to reset this for below explained case:
                // no task in the DB -> page loads -> 404 no task found error -> task created -> 404 gallery error still exists -> Masonry not rendered
                set_kanban_task_create_error_message("");
            } else {
                set_kanban_task_create_error_message(
                    create_kanban_task_error_message,
                );
            }
        } catch (err) {
            set_kanban_task_create_error_message(
                err.message || "Network error during kanban task creating.",
            );
        } finally {
            set_is_submitting_task(false);
        }
    }

    function render_sliders() {
        const ocfn = () => {
            fetch_kanban_tasks_with_delay();
        };
        const registered_sliders = [
            {
                label: "Importance",
                SliderType: IntegerSliderWrapper,
                range: importance_range,
                min: KANBAN_MIN_IMPORTANCE,
                max: KANBAN_MAX_IMPORTANCE,
                step: 1,
                on_change_fn: (v) => set_importance_range(v),
                on_commit_fn: ocfn,
            },
        ];

        return (
            <RegisteredSlidersDisplayWrapper
                registered_sliders={registered_sliders}
            />
        );
    }

    function render_gallery() {
        if (loading) return <LoadSpinnerWrapper loading={true} />;

        if (gallery_error_message)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    {gallery_error_message}
                </div>
            );

        if (!kanban_gallery.length)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    Collecting kanban tasks...
                </div>
            );

        return (
            <div
                style={{
                    width: "100%",
                    paddingInline: theme.spacing.lg,
                }}
            >
                <Masonry
                    key={kanban_gallery.length === 0 ? "empty" : "populated"}
                    columns={2}
                    spacing={theme.spacing.lg}
                >
                    {kanban_gallery.map((kanban_task) => {
                        return (
                            <div
                                key={kanban_task.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                            >
                                <KanbanTaskWrapper
                                    kanban_task={kanban_task}
                                    logged_in_permission={logged_in_permission}
                                    on_upvote={() => {
                                        handle_vote(kanban_task.id, 1);
                                    }}
                                    on_downvote={() => {
                                        handle_vote(kanban_task.id, -1);
                                    }}
                                    on_delete={() => {
                                        handle_delete(kanban_task.id);
                                    }}
                                />
                            </div>
                        );
                    })}
                </Masonry>

                <LoadSpinnerWrapper loading={loading_more} />
            </div>
        );
    }

    function render_creation_panel() {
        return (
            <div
                style={{
                    borderRadius: theme.radius.lg,
                    padding: theme.spacing.lg,
                    display: "flex",
                    flexDirection: "column",
                    gap: theme.spacing.md,
                    boxShadow: theme.colors.shadow.card,
                }}
            >
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "left",
                        marginTop: theme.spacing.sm,
                        marginBottom: theme.spacing.sm,
                    }}
                >
                    Create Task
                </div>

                {/* Description */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: theme.spacing.xs,
                    }}
                >
                    <TextInputWrapper
                        name="description"
                        label="Description"
                        multiline
                        rows={3}
                        required
                        value={kanban_task_to_create.description}
                        onChange={(e) =>
                            set_kanban_task_to_create((prev) => ({
                                ...prev,
                                description: e.target.value,
                            }))
                        }
                        maxLength={KANBAN_MAX_DESCRIPTION_LEN}
                    />
                </div>

                <HorizontalDivider />

                {/* Importance */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: theme.spacing.xs,
                    }}
                >
                    <SectionLabel text="Importance" />

                    <IntegerSliderWrapper
                        value={kanban_task_to_create.importance}
                        min={KANBAN_MIN_IMPORTANCE}
                        max={KANBAN_MAX_IMPORTANCE}
                        step={1}
                        onChange={(e, newValue) =>
                            set_kanban_task_to_create((prev) => ({
                                ...prev,
                                importance: newValue,
                            }))
                        }
                    />
                </div>

                <HorizontalDivider />

                {/* Tags */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: theme.spacing.sm,
                    }}
                >
                    <SectionLabel text="Tags" />

                    {tags_error_message ? (
                        <ErrorPopUpWrapper
                            error_message={tags_error_message}
                            on_close={() => set_tags_error_message("")}
                            error_title="Kanban Tag For Kanban Task Creation Error"
                        />
                    ) : (
                        <MultipleChoiceSelectionWrapper
                            all_choices={all_tags}
                            selected_choices={kanban_task_to_create.tags}
                            handle_choice_select={(tag_id) =>
                                handleIdLabelItemSlotSelect(
                                    tag_id,
                                    set_kanban_task_to_create,
                                    "tags",
                                )
                            }
                        />
                    )}
                </div>

                <HorizontalDivider />

                {/* Action */}
                <div
                    style={{
                        display: "flex",
                        justifyContent: "center",
                        marginTop: theme.spacing.sm,
                    }}
                >
                    <ButtonWrapper
                        onClick={handle_create}
                        text="Publish Task"
                        disabled={is_submitting_task}
                    />
                </div>

                {/* Creation error */}
                {kanban_task_create_error_message && (
                    <ErrorPopUpWrapper
                        error_message={kanban_task_create_error_message}
                        on_close={() =>
                            set_kanban_task_create_error_message("")
                        }
                        error_title="Create Task Error"
                    />
                )}
            </div>
        );
    }

    function render_main() {
        return (
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    minHeight: "100vh",
                    backgroundColor: theme.colors.background.app,
                    boxSizing: "border-box",
                }}
            >
                {/* Navigation Bar */}
                <div
                    style={{
                        position: "sticky",
                        top: 0,
                        zIndex: 1000,
                        width: "100%",
                        backgroundColor: theme.colors.background.app, // Ensure it has a solid background
                    }}
                >
                    <NavigationBarWrapper
                        logged_in_permission={logged_in_permission}
                    />
                </div>

                {/* Side-by-Side Text Section (Full Size) */}
                {/* <div
                    style={{
                        display: "flex",
                        width: "100%",
                        overflowY: "auto",
                        backgroundColor: theme.colors.background.app_darker,
                    }}
                >
                    {AboutPageTextWrapperEN()}

                    {AboutPageTextWrapperTR()}
                </div> */}
                {AboutPageTextWrapperTR()}

                <div style={{ paddingTop: theme.spacing.md }}>
                    <HorizontalDivider />
                </div>

                {/* Main content: Left controls + Right gallery */}
                <div
                    style={{
                        display: "flex",
                        padding: theme.spacing.md,
                        gap: theme.spacing.lg,
                        boxSizing: "border-box",
                        alignItems: "flex-start",
                    }}
                >
                    {/* Left column: Controls */}
                    <div
                        style={{
                            width: "25%",
                            display: "flex",
                            flexDirection: "column",
                            gap: theme.spacing.lg,
                            overflowY: "auto",
                            paddingRight: theme.spacing.md,
                        }}
                    >
                        <ControlPanelWrapper
                            at_kanbanpage={true}
                            tags_error_message={tags_error_message}
                            set_tags_error_message={() =>
                                set_tags_error_message("")
                            }
                            tags_error_title="Kanban Tag Error"
                            all_tags={all_tags}
                            selected_tags={selected_tags}
                            on_tag_select={(id) =>
                                handleIdLabelItemSelect(id, set_selected_tags)
                            }
                            all_sorts={all_sorts}
                            selected_sorts={selected_sorts}
                            on_sort_select={(id) =>
                                handleSortIdLabelItemSelect(
                                    id,
                                    set_selected_sorts,
                                )
                            }
                            sliders={render_sliders()}
                        />
                    </div>

                    {/* middle column: Gallery */}
                    <div
                        style={{
                            width: "60%",
                            flexGrow: 1,
                            overflowY: "auto",
                            overflowX: "hidden",
                            minHeight: theme.dimensions.xl,
                        }}
                    >
                        <h1
                            style={{
                                ...theme.styles.titleText,
                                margin: 0,
                                marginBottom: theme.spacing.md,
                            }}
                        >
                            Tasks
                        </h1>

                        {render_gallery()}
                    </div>

                    {/* Right column: Gallery */}
                    <div
                        style={{
                            width: "15%",
                            flexGrow: 1,
                        }}
                    >
                        {logged_in_permission && render_creation_panel()}
                    </div>

                    {/* accept and call the delete or reject and go back to standby mode */}
                    {asking_for_confirmation > 0 &&
                        (() => {
                            // Find the specific task object using the ID stored in state
                            const selectedTask = kanban_gallery.find(
                                (task) => task.id === asking_for_confirmation,
                            );

                            return (
                                <ConfirmationPopUpWrapper
                                    confirmation_title="Confirm Delete"
                                    /* Dynamically display description and importance */
                                    confirmation_message={
                                        selectedTask
                                            ? `Task "${selectedTask.description}" (Importance: ${selectedTask.importance}) will be deleted completely`
                                            : "This task will be deleted completely"
                                    }
                                    on_accept={() => {
                                        handle_delete(
                                            asking_for_confirmation,
                                            true,
                                        );
                                    }}
                                    on_reject={() => {
                                        set_asking_for_confirmation(0);
                                    }}
                                />
                            );
                        })()}
                </div>
            </div>
        );
    }

    return render_main();
}

export default AboutPage;
