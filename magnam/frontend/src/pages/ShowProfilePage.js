import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Masonry } from "@mui/lab";

import CreateProfilePage from "./CreateProfilePage";
import HasPermission from "../utils/HasPermission";
import TextInputWrapper from "../componentWrappers/TextInputWrapper";
import CardWrapper from "../componentWrappers/CardWrapper";
import ButtonWrapper from "../componentWrappers/ButtonWrapper";
import SwitchWrapper from "../componentWrappers/SwitchWrapper";
import MultipleChoiceSelectionWrapper from "../componentWrappers/MultipleChoiceSelectionWrapper";
import ProfileDirectingWrapper from "../componentWrappers/ProfileDirectingWrapper";
import ErrorPopUpWrapper from "../componentWrappers/ErrorPopUpWrapper";
import ConfirmationPopUpWrapper from "../componentWrappers/ConfirmationPopUpWrapper";
import NavigationBarWrapper from "../componentWrappers/NavigationBarWrapper";
import { apiFetch, handleFetch } from "../utils/csrf";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { HorizontalDivider } from "../componentWrappers/helper_components";
import { setFetchAndSet } from "../utils/helper_functions";
import { validateText } from "../utils/helper_validators";
import {
    PROFILE_MESSAGE_MIN_LEN,
    PROFILE_MESSAGE_MAX_LEN,
    PROFILE_MAX_NAME_LEN,
} from "../globals";

function ShowProfilePage() {
    const {
        lastIncomingMessage,
        updateGlobalUnreadMessages,
        setAuthUnverified,
    } = useAuth();
    const navigate = useNavigate();
    const { theme } = useTheme();

    const { profile_id: profile_id_from_url } = useParams();

    const admin_permission = HasPermission("admin");
    const logged_in_permission = HasPermission("logged_in");
    const logged_in_owner_permission = HasPermission(
        "logged_in",
        profile_id_from_url,
    );

    const [profile, set_profile] = useState({
        id: -1,
        profile_name: "",
        email: "",
        image: null,
        wallet: 0,
        open_date: null,
        mangas_owned: null,
        mangas_collaborated: null,
        chapters_owned: null,
        chapters_collaborated: null,
        portfolios: null,
        profiles_following: [],
        profiles_blocked: [],
        mangas_following: [],
    });

    const [is_user_following, set_is_user_following] = useState(false);
    const [is_user_blocked, set_is_user_blocked] = useState(false);

    const [searched_profiles, set_searched_profiles] = useState([]);
    const [search_text, set_search_text] = useState("");

    const [all_profiles_messaging, set_all_profiles_messaging] = useState({});
    const [message_text, set_message_text] = useState("");
    const [selected_messaging_profile, set_selected_messaging_profile] =
        useState(null);
    const [profile_messages_dict, set_profile_messages_dict] = useState({});
    const MESSAGE_LIMIT_TO_APPEND_WEBSOCKET_MESSAGE = 8192;
    const selected_data = profile_messages_dict[selected_messaging_profile] || {
        messages: [],
        next: null,
        loading: false,
    };
    const messageScrollRef = useRef(null);
    const prevScrollHeightRef = useRef(null);
    const [message_only_with_follows, set_message_only_with_follows] =
        useState(true);
    const [all_profiles_following, set_all_profiles_following] = useState([]);
    const [show_edit, set_show_edit_page] = useState(false);

    const [text_search_error_message, set_text_search_error_message] =
        useState("");
    const [error_message, set_error_message] = useState("");
    const [messaging_error_message, set_messaging_error_message] = useState("");

    const [asking_for_confirmation, set_asking_for_confirmation] =
        useState(false);
    const [
        asking_for_reverification_confirmation,
        set_asking_for_reverification_confirmation,
    ] = useState(false);

    const get_profile_details = useCallback(
        async (signal) => {
            const options = signal
                ? { signal, method: "GET" }
                : { method: "GET" };

            try {
                const get_profile_response = await apiFetch(
                    `/api/profile/get-profile/${profile_id_from_url}/`,
                    options,
                );
                const [
                    get_profile_success_data,
                    get_profile_error_message,
                    get_profile_ok,
                ] = await handleFetch("get_profile", get_profile_response);

                if (get_profile_ok) {
                    set_profile({
                        id: get_profile_success_data.id,
                        profile_name:
                            get_profile_success_data.profile_name ?? "",
                        email: get_profile_success_data.user?.email ?? "",
                        image: get_profile_success_data.image ?? null,
                        wallet: get_profile_success_data.wallet ?? 0,
                        open_date: get_profile_success_data.open_date ?? null,
                        mangas_owned:
                            get_profile_success_data.mangas_owned ?? null,
                        mangas_collaborated:
                            get_profile_success_data.mangas_collaborated ??
                            null,
                        chapters_owned:
                            get_profile_success_data.chapters_owned ?? null,
                        chapters_collaborated:
                            get_profile_success_data.chapters_collaborated ??
                            null,
                        portfolios: get_profile_success_data.portfolios ?? null,
                        profiles_following:
                            get_profile_success_data.profiles_following ?? [],
                        profiles_blocked:
                            get_profile_success_data.profiles_blocked ?? [],
                        mangas_following:
                            get_profile_success_data.mangas_following ?? [],
                    });

                    set_is_user_following(
                        get_profile_success_data.is_user_following ?? false,
                    );
                    set_is_user_blocked(
                        get_profile_success_data.is_user_blocked ?? false,
                    );
                    set_show_edit_page(false);
                    set_error_message("");
                } else {
                    set_error_message(get_profile_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during profile fetch.",
                );
            }
        },
        [profile_id_from_url],
    );

    // call the get_profile_details when profile_id_in_url changes
    useEffect(() => {
        const controller = new AbortController();
        get_profile_details(controller.signal);

        return () => controller.abort();
    }, [profile_id_from_url, get_profile_details]);

    // fetch the profiles the current user messages and put them in a dict with their ids as keys
    const set_all_profiles_messaging_by_id = (dataArray) => {
        const byId = Object.fromEntries(dataArray.map((p) => [p.id, p]));
        set_all_profiles_messaging(byId);
    };
    useEffect(() => {
        setFetchAndSet(
            "/api/profile/profiles-messaging/",
            set_all_profiles_messaging_by_id,
            set_messaging_error_message,
            "messagings",
        );
    }, []);

    // fetch the profiles the current user follows
    useEffect(() => {
        setFetchAndSet(
            "/api/profile/profiles-following-symmetric/",
            set_all_profiles_following,
            set_messaging_error_message,
            "follows",
        );
    }, []);

    // fetch to get the initial message page
    useEffect(() => {
        // return if no profile selected or if selected one is already initialized
        if (
            !selected_messaging_profile ||
            profile_messages_dict[selected_messaging_profile]
        )
            return;

        // initialize the profile messaging cache
        set_profile_messages_dict((prev) => ({
            ...prev,
            [selected_messaging_profile]: {
                messages: [],
                next: null,
                loading: true,
            },
        }));

        const controller = new AbortController();
        fetch_message_page(
            `/api/profile/get-messages/${selected_messaging_profile}/`,
            controller.signal,
            true,
        );
        return () => controller.abort();
    }, [selected_messaging_profile]);

    function SubtractFromProfileUnreadMessages(profile_id, value) {
        set_all_profiles_messaging((prev) => {
            const profile = prev[profile_id];
            if (!profile) return prev;

            return {
                ...prev,
                [profile_id]: {
                    ...profile,
                    unread_messages: Math.max(
                        0,
                        (profile.unread_messages ?? 0) - value,
                    ),
                },
            };
        });
    }

    // marks the messages from senderId as read at messaging panel of messaging_profile profile
    // we need both messaging_profile and the senderId so both the receiver and sender can mark messages as read
    // message receiver calls it like setLocalMessagesRead(senderId, senderId, message.id);
    // this means "mark the messages from senderId at the senderId messaging panel"
    // message sender calls it like setLocalMessagesRead(receiverID, senderId, message.id);
    // this means "mark the messages from senderId at the receiverID messaging panel"
    async function setLocalMessagesRead(
        messaging_profile,
        senderId,
        upToMessageId,
    ) {
        set_profile_messages_dict((prev) => {
            const chatData = prev[messaging_profile];
            if (!chatData) return prev;

            const updatedMessages = chatData.messages.map((msg) => {
                if (
                    msg.sender === senderId &&
                    msg.id <= upToMessageId &&
                    !msg.is_read
                ) {
                    return { ...msg, is_read: true };
                }
                return msg;
            });

            return {
                ...prev,
                [messaging_profile]: {
                    ...chatData,
                    messages: updatedMessages,
                },
            };
        });
    }

    // only receiver calls this
    async function sendMessagesReadNotification(senderId, upToMessageId) {
        try {
            await apiFetch(
                `/api/profile/read-messages/${senderId}/${upToMessageId}/`,
                { method: "POST" },
            );
        } catch (err) {
            console.error("Failed to mark messages as read", err);
        }
    }

    useEffect(() => {
        if (!lastIncomingMessage) return;

        const message = lastIncomingMessage;

        // Ignore messages sent by me if they are not read message notificaions
        if (message.sender === profile.id && message.type !== "read_message")
            return;

        const senderId = message.sender;
        const receiverId = message.receiver;
        const isSelected = selected_messaging_profile === senderId;
        const cache = profile_messages_dict[senderId];
        const hasCache = !!cache;

        // if we sent a message and now got the confirmation that it's read
        // just flag the messages as read and that is
        if (message.type === "read_message") {
            // message sender gets a feedback from the receiver named "read_message"
            // and marks these messages as read:
            // message is from from senderId (himself)
            // message is at the messaging panel with receiverId (other parth)
            // and later than the message.id
            setLocalMessagesRead(receiverId, senderId, message.id);
            return;
        }

        // if we are here that means we are getting a message, not a "other side read the message" notification
        if (hasCache) {
            // if we already have the profile messages fetched, append the new ones
            if (
                profile_messages_dict[senderId].messages.length <
                MESSAGE_LIMIT_TO_APPEND_WEBSOCKET_MESSAGE
            ) {
                let isNearBottom = false;
                if (isSelected && messageScrollRef.current) {
                    const el = messageScrollRef.current;
                    const threshold = 150; // Threshold in pixels from the bottom
                    isNearBottom =
                        el.scrollHeight - el.scrollTop - el.clientHeight <=
                        threshold;
                }

                set_profile_messages_dict((prev) => ({
                    ...prev,
                    [senderId]: {
                        ...prev[senderId],
                        messages: [...prev[senderId].messages, message],
                    },
                }));

                // If the user is viewing this chat and was near bottom, scroll down
                if (isSelected && isNearBottom) {
                    setTimeout(scroll_to_bottom, 10);
                }
            } else {
                console.error(`Chat length (${MESSAGE_LIMIT_TO_APPEND_WEBSOCKET_MESSAGE} messages) is reached for incoming message appending.
                                No more incoming messages will be appended to the chat to protect from spams. Refresh the page if that's not a spam`);
            }
        }
        // if we are currently talking to the sender, delete the message from the unread count and set as read
        if (isSelected) {
            sendMessagesReadNotification(senderId, message.id);
            setLocalMessagesRead(senderId, senderId, message.id);
            updateGlobalUnreadMessages(-1);
        }
        // if we are currently NOT talking to the sender, increase the profile specific unread count
        else {
            SubtractFromProfileUnreadMessages(senderId, -1);
        }
    }, [lastIncomingMessage]);

    // Trigger sendMessagesReadNotification when the user opens/switches to a chat
    useEffect(() => {
        // 1. Ensure a profile is selected and messages are loaded
        if (!selected_messaging_profile || selected_data.messages.length === 0)
            return;

        const messages = selected_data.messages;
        const lastMessage = messages[messages.length - 1];
        // 2. Check if the last message was received by me
        // (If the sender ID is the profile I am looking at, then I am the receiver)
        const isReceivedByMe =
            lastMessage.sender === selected_messaging_profile;

        // 3. If received and unread, call sendMessagesReadNotification
        if (isReceivedByMe && lastMessage.is_read === false) {
            sendMessagesReadNotification(
                selected_messaging_profile,
                lastMessage.id,
            );
            setLocalMessagesRead(selected_messaging_profile, lastMessage.id);
        }
    }, [selected_messaging_profile, selected_data.messages.length]);

    // fetch to get the next pages
    async function fetch_message_page(
        request_url,
        signal,
        initial_scroll = false,
    ) {
        try {
            const get_messages_response = await apiFetch(request_url, {
                signal,
                method: "GET",
            });
            const [get_messages_data, get_messages_err, get_messages_ok] =
                await handleFetch("get_messages", get_messages_response);

            if (get_messages_ok) {
                set_profile_messages_dict((prev) => {
                    const prevData = prev[selected_messaging_profile] || {
                        messages: [],
                    };

                    let newMessages = get_messages_data.results.filter(
                        (m) => !prevData.messages.some((e) => e.id === m.id),
                    );

                    const messaging_profile = selected_messaging_profile
                        ? all_profiles_messaging[selected_messaging_profile]
                        : null;

                    if (messaging_profile?.unread_messages > 0) {
                        const decrement = Math.min(
                            newMessages.length,
                            messaging_profile.unread_messages,
                        );

                        // subtract the number of fetched messages from global unread message count at context
                        // set timeout so we update the global context after this call is done
                        setTimeout(() => {
                            updateGlobalUnreadMessages(-1 * decrement);
                        }, 0);

                        // subtract the number of fetched messages from unread message count from that profile
                        SubtractFromProfileUnreadMessages(
                            selected_messaging_profile,
                            newMessages.length,
                        );
                    }
                    return {
                        ...prev,
                        [selected_messaging_profile]: {
                            ...prevData,
                            messages: [
                                ...newMessages.reverse(),
                                ...prevData.messages,
                            ],
                            next: get_messages_data.next,
                            loading: false,
                        },
                    };
                });
                if (initial_scroll) {
                    setTimeout(scroll_to_bottom, 10);
                }
            } else {
                set_messaging_error_message(get_messages_err);
            }
        } catch (err) {
            set_messaging_error_message(
                err.message || "Network error during message fetch.",
            );
        }
    }

    function message_panel_scroll_up_trigger(
        scrollRef,
        triggerFn,
        offset = 50,
        delay = 200,
    ) {
        let timeout = null;

        const handleScroll = () => {
            const el = scrollRef.current;
            if (!el) return;

            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (el.scrollTop <= offset) {
                    triggerFn();
                }
            }, delay);
        };

        const el = scrollRef.current;
        if (!el) return () => {};

        el.addEventListener("scroll", handleScroll);
        return () => {
            clearTimeout(timeout);
            el.removeEventListener("scroll", handleScroll);
        };
    }

    async function load_older_messages() {
        // if no selected profile, or no next or while loading the next -> dont trigger the next page pull
        if (
            !selected_messaging_profile ||
            !selected_data?.next ||
            selected_data.loading
        )
            return;

        const el = messageScrollRef.current;
        if (!el) return;

        prevScrollHeightRef.current = el.scrollHeight;

        set_profile_messages_dict((prev) => ({
            ...prev,
            [selected_messaging_profile]: {
                ...prev[selected_messaging_profile],
                loading: true,
            },
        }));

        const controller = new AbortController();
        await fetch_message_page(selected_data.next, controller.signal);
    }

    useEffect(() => {
        if (!selected_messaging_profile || !messageScrollRef.current) return;
        return message_panel_scroll_up_trigger(
            messageScrollRef,
            load_older_messages,
        );
    }, [selected_messaging_profile, selected_data.messages.length]);

    // scroll to bottom when first load and profile select
    const scroll_to_bottom = useCallback(() => {
        requestAnimationFrame(() => {
            if (messageScrollRef.current) {
                messageScrollRef.current.scrollTop =
                    messageScrollRef.current.scrollHeight;
            }
        });
    }, [selected_messaging_profile]);

    useEffect(() => {
        if (selected_messaging_profile) {
            scroll_to_bottom();
        }
    }, [selected_messaging_profile]);

    useEffect(() => {
        const el = messageScrollRef.current;
        if (!el) return;
        if (prevScrollHeightRef.current === null) return;

        const newScrollHeight = el.scrollHeight;
        const diff = newScrollHeight - prevScrollHeightRef.current;

        el.scrollTop += diff;

        prevScrollHeightRef.current = null;
    }, [selected_data.messages.length]);

    async function handle_follow(
        target_profile_id = parseInt(profile_id_from_url),
        profile_name = "",
    ) {
        try {
            const follow_response = await apiFetch(
                `/api/profile/toggle-follow-profile/${target_profile_id}/`,
                { method: "POST" },
            );
            const [follow_success_data, follow_error_message, follow_ok] =
                await handleFetch("follow", follow_response);

            if (follow_ok) {
                // If follow request is coming from the messaging panel add the profile to the follows
                if (target_profile_id !== profile_id_from_url) {
                    set_all_profiles_following([
                        ...all_profiles_following,
                        { id: target_profile_id, profile_name: profile_name },
                    ]);
                } else // if we clicked the follow button on another profiles page
                {
                    set_is_user_following((prev) => !prev);
                }

                set_error_message("");
            } else {
                set_error_message(follow_error_message);
            }
        } catch (err) {
            set_error_message(
                err.message || "Network error during profile following.",
            );
        }
    }

    async function handle_block(is_confirmed = false) {
        // if we were waiting on the standby, now we need confirmation on the delete call
        if (!asking_for_confirmation) {
            set_asking_for_confirmation(true);
        }
        // if delete was called with not confirmation, abort and go back to standby
        else if (!is_confirmed) {
            set_asking_for_confirmation(false);
        } else if (
            is_confirmed
        ) // if confirmed, do the deletion and go back to standy
        {
            set_asking_for_confirmation(false);

            try {
                const block_response = await apiFetch(
                    `/api/profile/toggle-block-profile/${profile.id}/`,
                    { method: "POST" },
                );
                const [block_success_data, block_error_message, block_ok] =
                    await handleFetch("block", block_response);

                if (block_ok) {
                    set_is_user_blocked((prev) => !prev);
                    set_is_user_following(false);
                    set_error_message("");
                } else {
                    set_error_message(block_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message || "Network error during profile blocking.",
                );
            }
        }
    }

    async function handle_verification_reset(is_confirmed = false) {
        // if we were waiting on the standby, now we need confirmation on the delete call
        if (!asking_for_reverification_confirmation) {
            set_asking_for_reverification_confirmation(true);
        }
        // if delete was called with not confirmation, abort and go back to standby
        else if (!is_confirmed) {
            set_asking_for_reverification_confirmation(false);
        } else if (
            is_confirmed
        ) // if confirmed, do the deletion and go back to standy
        {
            set_asking_for_reverification_confirmation(false);

            try {
                const verification_reset_response = await apiFetch(
                    `/api/profile/reset-verification/`,
                    { method: "PATCH" },
                );
                const [
                    verification_reset_success_data,
                    verification_reset_error_message,
                    verification_reset_ok,
                ] = await handleFetch(
                    "reset_verification",
                    verification_reset_response,
                );

                if (verification_reset_ok) {
                    setAuthUnverified();
                    set_error_message("");
                } else {
                    set_error_message(verification_reset_error_message);
                }
            } catch (err) {
                set_error_message(
                    err.message ||
                        "Network error during verification resetting.",
                );
            }
        }
    }

    async function handle_text_search() {
        if (!search_text.trim()) {
            set_searched_profiles([]);
            set_text_search_error_message("");
            return;
        }
        set_searched_profiles([]);
        set_text_search_error_message("");

        const search_url = `/api/profile/search-profile/${encodeURIComponent(search_text.trim())}/`;
        await setFetchAndSet(
            search_url,
            set_searched_profiles,
            set_text_search_error_message,
            "text_search",
        );
    }

    async function handle_message_send() {
        if (!selected_messaging_profile || !message_text.trim()) return;

        const trimmed = message_text.trim();

        const isMessageValid = validateText({
            value: trimmed,
            fieldName: "Message",
            minLen: PROFILE_MESSAGE_MIN_LEN,
            maxLen: PROFILE_MESSAGE_MAX_LEN,
            required: true,
            error_handler: set_messaging_error_message,
        });
        if (!isMessageValid) return;

        const formData = new FormData();
        formData.append("message", trimmed.trim());

        try {
            const send_message_response = await apiFetch(
                `/api/profile/send-message/${selected_messaging_profile}/`,
                { method: "POST", body: formData },
            );
            const [
                send_message_success_data,
                send_message_err,
                send_message_ok,
            ] = await handleFetch("send_message", send_message_response);

            if (send_message_ok) {
                set_message_text("");
                set_messaging_error_message("");
                set_profile_messages_dict((prev) => ({
                    ...prev,
                    [selected_messaging_profile]: {
                        ...prev[selected_messaging_profile],
                        messages: [
                            ...prev[selected_messaging_profile].messages,
                            send_message_success_data,
                        ],
                    },
                }));
                setTimeout(scroll_to_bottom, 10);
            } else {
                set_messaging_error_message(send_message_err);
            }
        } catch (send_message_err) {
            set_messaging_error_message(
                send_message_err.message ||
                    "Network error while sending message.",
            );
        }
    }

    function render_text_search_inputs() {
        return (
            <div
                style={{
                    display: "flex",
                    alignItems: "flex-end",
                    gap: theme.spacing.sm,
                    padding: theme.spacing.sm,
                    flexDirection: "row", // Ensure side-by-side
                    alignItems: "stretch", // Forces children to fill vertical height
                }}
            >
                {/* Text input */}
                <div style={{ flex: 1 }}>
                    <TextInputWrapper
                        name="profile-search"
                        label="Search Profile by name or ID"
                        value={search_text}
                        onChange={(e) => set_search_text(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault(); // Prevents adding a new line in the textarea
                                handle_text_search();
                            }
                        }}
                        maxLength={PROFILE_MAX_NAME_LEN}
                        fullWidth
                    />
                </div>

                <ButtonWrapper onClick={handle_text_search} text={"🔎"} />
            </div>
        );
    }

    function render_text_search() {
        if (text_search_error_message)
            return (
                <div
                    style={{
                        ...theme.styles.titleText,
                        textAlign: "center",
                        paddingBlock: theme.spacing.xl,
                    }}
                >
                    {text_search_error_message}
                </div>
            );

        if (!searched_profiles.length) return null;

        return (
            <div
                style={{
                    width: "100%",
                    paddingInline: theme.spacing.md,
                    maxHeight: theme.dimensions.sm,
                    overflowY: "auto",
                }}
            >
                <Masonry columns={2} spacing={2}>
                    {searched_profiles.map((profile) => {
                        return (
                            <div
                                key={profile.id}
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    backgroundColor:
                                        theme.colors.background.app,
                                    borderRadius: theme.radius.md,
                                }}
                            >
                                <ProfileDirectingWrapper
                                    profile_id={profile.id}
                                    profile_name={profile.profile_name}
                                    profile_image={profile.image}
                                />
                            </div>
                        );
                    })}
                </Masonry>
            </div>
        );
    }

    function render_message_panel() {
        const messaging_profiles_array = Object.values(all_profiles_messaging);
        const message_profiles = message_only_with_follows
            ? messaging_profiles_array.filter((msg_profile) =>
                  all_profiles_following.some(
                      (follow) => follow.id === msg_profile.id,
                  ),
              )
            : messaging_profiles_array;

        const selected_profile_in_scope_selection =
            !!selected_messaging_profile &&
            message_profiles.some((p) => p.id === selected_messaging_profile);

        const total_unread_messages = messaging_profiles_array.reduce(
            (sum, p) => sum + (p.unread_messages ?? 0),
            0,
        );
        const scope_unread_messages = message_profiles.reduce(
            (sum, p) => sum + (p.unread_messages ?? 0),
            0,
        );
        const other_scope_unread_messages =
            total_unread_messages - scope_unread_messages;

        const messaging_profile = selected_messaging_profile
            ? all_profiles_messaging[selected_messaging_profile]
            : null;

        // keeping this for later use
        // const is_following_messaging_profile = !!messaging_profile && all_profiles_following.some((f) => f.id === messaging_profile.id);

        return (
            <div
                style={{
                    padding: theme.spacing.lg,
                    background: theme.colors.background.surface,
                    borderRadius: theme.radius.lg,
                    boxShadow: theme.colors.shadow.card,
                }}
            >
                {/* Header / Receiver Selection */}
                <div style={{ marginBottom: theme.spacing.md }}>
                    <div>
                        {messaging_error_message ? (
                            <ErrorPopUpWrapper
                                error_message={messaging_error_message}
                                on_close={() => set_messaging_error_message("")}
                                error_title="Profile Messaging Error"
                            />
                        ) : (
                            <div>
                                <div
                                    style={{
                                        display: "flex",
                                        flexDirection: "column",
                                        alignItems: "center",
                                        paddingBottom: theme.spacing.sm,
                                    }}
                                >
                                    <SwitchWrapper
                                        text={`Show only chats with friends`}
                                        checked={message_only_with_follows}
                                        onEnable={() => {
                                            set_message_only_with_follows(true);

                                            const next_scope =
                                                messaging_profiles_array.filter(
                                                    (p) =>
                                                        all_profiles_following.some(
                                                            (f) =>
                                                                f.id === p.id,
                                                        ),
                                                );

                                            const is_in_next_scope =
                                                next_scope.some(
                                                    (p) =>
                                                        p.id ===
                                                        selected_messaging_profile,
                                                );

                                            if (!is_in_next_scope) {
                                                set_selected_messaging_profile(
                                                    null,
                                                );
                                            }
                                        }}
                                        onDisable={() => {
                                            set_message_only_with_follows(
                                                false,
                                            );

                                            const next_scope =
                                                messaging_profiles_array;

                                            const is_in_next_scope =
                                                next_scope.some(
                                                    (p) =>
                                                        p.id ===
                                                        selected_messaging_profile,
                                                );

                                            if (!is_in_next_scope) {
                                                set_selected_messaging_profile(
                                                    null,
                                                );
                                            }
                                        }}
                                    />
                                </div>

                                <div
                                    style={{
                                        maxHeight: theme.dimensions.xxxs,
                                        overflowY: "auto",
                                        borderRadius: theme.radius.md,
                                    }}
                                >
                                    <MultipleChoiceSelectionWrapper
                                        all_choices={message_profiles.map(
                                            (p) => ({
                                                id: p.id,
                                                label: p.unread_messages
                                                    ? `${p.profile_name} • ${p.unread_messages}`
                                                    : p.profile_name,
                                            }),
                                        )}
                                        selected_choices={
                                            selected_messaging_profile
                                                ? [selected_messaging_profile]
                                                : []
                                        }
                                        handle_choice_select={(id) =>
                                            set_selected_messaging_profile(
                                                (prev) =>
                                                    prev === id ? null : id,
                                            )
                                        }
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Message Stream */}
                {selected_messaging_profile &&
                    selected_profile_in_scope_selection && (
                        <>
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "flex-end",
                                    gap: theme.spacing.sm,
                                    padding: theme.spacing.sm,
                                    flexDirection: "row", // Ensure side-by-side
                                    alignItems: "stretch", // Forces children to fill vertical height
                                }}
                            >
                                <div
                                    style={{
                                        flex: 1,
                                        backgroundColor:
                                            theme.colors.background.muted,
                                        borderRadius: theme.radius.lg,
                                    }}
                                >
                                    <ProfileDirectingWrapper
                                        profile_id={messaging_profile.id}
                                        profile_name={
                                            messaging_profile.profile_name
                                        }
                                        profile_image={messaging_profile.image}
                                    />
                                </div>
                            </div>

                            <div
                                style={{
                                    height: theme.dimensions.xxxs,
                                    overflowY: "auto",
                                    padding: theme.spacing.md,
                                    background: theme.colors.background.muted,
                                    borderRadius: theme.radius.md,
                                    border: `1px solid ${theme.colors.border.subtle}`,
                                    marginBottom: theme.spacing.md,
                                    // Adding these to help center the "no messages" text if needed
                                    display: "flex",
                                    flexDirection: "column",
                                }}
                                ref={messageScrollRef}
                            >
                                {selected_data.messages.length === 0 ? (
                                    /* Placeholder for empty state */
                                    <div
                                        style={{
                                            ...theme.styles.metadataText,
                                            textAlign: "center",
                                            marginTop: "auto",
                                            marginBottom: "auto",
                                            opacity: 0.7,
                                        }}
                                    >
                                        no messages sent/received
                                    </div>
                                ) : (
                                    /* Render messages */
                                    selected_data.messages.map((msg, index) => {
                                        const isMine =
                                            msg.sender === profile.id;
                                        const date = new Date(msg.timestamp);
                                        const formattedTime =
                                            date.toLocaleTimeString([], {
                                                hour: "2-digit",
                                                minute: "2-digit",
                                                hour12: false,
                                            }) +
                                            " " +
                                            date.toLocaleDateString([], {
                                                day: "2-digit",
                                                month: "2-digit",
                                            });

                                        return (
                                            <div
                                                key={index}
                                                style={{
                                                    display: "flex",
                                                    justifyContent: isMine
                                                        ? "flex-end"
                                                        : "flex-start",
                                                    marginBottom:
                                                        theme.spacing.xs,
                                                    flexShrink: 0, // Prevents the flex container from squishing messages
                                                }}
                                            >
                                                <div
                                                    style={{
                                                        maxWidth: "70%",
                                                        padding:
                                                            theme.spacing.sm,
                                                        borderRadius:
                                                            theme.radius.md,
                                                        background: isMine
                                                            ? theme.colors
                                                                  .background
                                                                  .app_darker
                                                            : theme.colors
                                                                  .background
                                                                  .app,
                                                        boxShadow:
                                                            theme.colors.shadow
                                                                .card,
                                                        ...theme.styles
                                                            .metadataText,
                                                    }}
                                                >
                                                    <div
                                                        style={{
                                                            ...theme.styles
                                                                .wrap_and_break,
                                                            color: theme.colors
                                                                .text.primary,
                                                        }}
                                                    >
                                                        {msg.message}
                                                    </div>
                                                    <div
                                                        style={{
                                                            marginTop:
                                                                theme.spacing
                                                                    .xs,
                                                            fontSize:
                                                                theme.typography
                                                                    .fontSize
                                                                    .xxs,
                                                            textAlign: "right",
                                                        }}
                                                    >
                                                        {formattedTime}
                                                        {isMine &&
                                                            (msg.is_read
                                                                ? " • read"
                                                                : " • sent")}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>

                            {/* Composer + Send */}
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "flex-end",
                                    gap: theme.spacing.sm,
                                    padding: theme.spacing.sm,
                                    flexDirection: "row", // Ensure side-by-side
                                    alignItems: "stretch", // Forces children to fill vertical height
                                }}
                            >
                                {/* Text input */}
                                <div style={{ flex: 1 }}>
                                    <TextInputWrapper
                                        name="message_text"
                                        label="Message"
                                        value={message_text}
                                        multiline
                                        fullWidth
                                        rows={2}
                                        maxLength={PROFILE_MESSAGE_MAX_LEN}
                                        onChange={(e) =>
                                            set_message_text(e.target.value)
                                        }
                                        onKeyDown={(e) => {
                                            if (
                                                e.key === "Enter" &&
                                                !e.shiftKey
                                            ) {
                                                e.preventDefault(); // Prevents adding a new line in the textarea
                                                handle_message_send();
                                            }
                                        }}
                                    />
                                </div>

                                <ButtonWrapper
                                    text="Send"
                                    onClick={handle_message_send}
                                    disabled={
                                        !selected_messaging_profile ||
                                        message_text.trim() === ""
                                    }
                                />
                            </div>
                        </>
                    )}
            </div>
        );
    }

    function render_main() {
        if (logged_in_owner_permission && show_edit) {
            return (
                <div>
                    <CreateProfilePage
                        id={profile.id}
                        profile_name={profile.profile_name}
                        email={profile.email}
                        image={profile.image}
                        edit={true}
                        cancel_edit_func={() => set_show_edit_page(false)}
                        edit_callback={get_profile_details}
                    />
                </div>
            );
        }

        const all_mangas = [
            ...(profile.mangas_owned || []),
            ...(profile.mangas_collaborated || []),
        ];
        const all_chapters = [
            ...(profile.chapters_owned || []),
            ...(profile.chapters_collaborated || []),
        ];

        const columnStyle = {
            padding: theme.spacing.md,
            display: "flex",
            flexDirection: "column",
            gap: theme.spacing.md,
        };

        const gridContainerStyle = {
            display: "grid",
            gridTemplateColumns: "20% 48% 32%",
            width: "100%",
        };

        const scrollableListStyle = {
            maxHeight: theme.dimensions.xl,
            overflowY: "auto",
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.background.surface,
            borderRadius: theme.radius.md,
        };

        return (
            <div
                style={{
                    backgroundColor: theme.colors.background.app,
                    minHeight: "100vh",
                }}
            >
                <div
                    style={{
                        position: "sticky",
                        top: 0,
                        zIndex: 1000,
                        width: "100%",
                        backgroundColor: theme.colors.background.app,
                    }}
                >
                    <NavigationBarWrapper
                        logged_in_permission={logged_in_permission}
                    />
                </div>

                <div
                    style={{
                        width: "100%",
                        padding: theme.spacing.md,
                    }}
                >
                    {/* SECTION 1: TOP 3 COLUMNS */}
                    <div style={gridContainerStyle}>
                        {/* LEFT: Image, Metadata, Actions */}
                        <div style={columnStyle}>
                            <div>
                                {/* Name + ID */}
                                <div
                                    style={{
                                        display: "flex",
                                        alignItems: "baseline",
                                        gap: theme.spacing.sm,
                                        flexWrap: "wrap",
                                    }}
                                >
                                    <span style={theme.styles.titleText}>
                                        {profile.profile_name}
                                    </span>

                                    <span style={theme.styles.subtitleText}>
                                        (@{profile.id})
                                    </span>
                                </div>
                            </div>

                            {profile.image && (
                                <img
                                    src={profile.image}
                                    alt={profile.profile_name}
                                    loading="lazy"
                                    style={{
                                        width: "100%",
                                        borderRadius: theme.radius.lg,
                                        objectFit: "cover",
                                    }}
                                />
                            )}

                            <div>
                                {logged_in_owner_permission &&
                                    profile.email && (
                                        <div
                                            style={{
                                                ...theme.styles.descriptionText,
                                                marginBottom: theme.spacing.xs,
                                            }}
                                        >
                                            {profile.email}
                                        </div>
                                    )}

                                <div
                                    style={{
                                        ...theme.styles.descriptionText,
                                        marginBottom: theme.spacing.xs,
                                    }}
                                >
                                    Created: {profile.open_date}
                                </div>

                                {logged_in_owner_permission && (
                                    <div
                                        style={{
                                            ...theme.styles.descriptionText,
                                            marginBottom: theme.spacing.xs,
                                        }}
                                    >
                                        Balance:{" "}
                                        {`${profile.wallet}${theme.coin}`}
                                    </div>
                                )}
                            </div>

                            {/* Actions */}
                            <div
                                style={{
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: theme.spacing.xs,
                                }}
                            >
                                {((logged_in_permission &&
                                    !logged_in_owner_permission) ||
                                    admin_permission) && (
                                    <>
                                        <SwitchWrapper
                                            text={"Follow"}
                                            checked={is_user_following}
                                            onEnable={() => {
                                                handle_follow(
                                                    profile_id_from_url,
                                                    profile.profile_name,
                                                );
                                            }}
                                            onDisable={() => {
                                                handle_follow(
                                                    profile_id_from_url,
                                                    profile.profile_name,
                                                );
                                            }}
                                            disabled={is_user_blocked}
                                        />
                                        <SwitchWrapper
                                            text={"Block"}
                                            checked={is_user_blocked}
                                            onEnable={() => {
                                                set_asking_for_confirmation(
                                                    true,
                                                );
                                            }}
                                            onDisable={() => {
                                                set_asking_for_confirmation(
                                                    true,
                                                );
                                            }}
                                            visualVariant={"danger"}
                                        />
                                    </>
                                )}
                                {logged_in_owner_permission && (
                                    <>
                                        <ButtonWrapper
                                            onClick={() => navigate(`/theme/`)}
                                            text="Customize Theme"
                                            visualVariant="outline"
                                        />
                                        <ButtonWrapper
                                            onClick={() =>
                                                set_show_edit_page(true)
                                            }
                                            text="Edit Profile"
                                            visualVariant="outline"
                                        />
                                        <ButtonWrapper
                                            onClick={() =>
                                                set_asking_for_reverification_confirmation(
                                                    true,
                                                )
                                            }
                                            text="Re-send Verification Mail"
                                            visualVariant="outline"
                                        />
                                    </>
                                )}
                            </div>
                        </div>
                        {/* MIDDLE: Followed Mangas Masonry */}
                        <div style={columnStyle}>
                            <div style={theme.styles.titleText}>
                                Followed Mangas
                            </div>

                            {profile.mangas_following?.length > 0 ? (
                                <div style={scrollableListStyle}>
                                    <Masonry columns={3} spacing={2}>
                                        {profile.mangas_following.map(
                                            (manga) => (
                                                <div
                                                    key={`manga_follow_${manga.id}`}
                                                >
                                                    <CardWrapper
                                                        title={manga.title}
                                                        to={`/manga/${manga.id}/`}
                                                        image={manga.image}
                                                        meta_data={[]}
                                                        sizeVariant="profile"
                                                    />
                                                </div>
                                            ),
                                        )}
                                    </Masonry>
                                </div>
                            ) : (
                                <p
                                    style={{
                                        color: theme.colors.text.muted,
                                        textAlign: "center",
                                        width: "100%",
                                    }}
                                >
                                    No mangas found
                                </p>
                            )}
                        </div>
                        {/* RIGHT: Search and Messaging */}
                        <div style={columnStyle}>
                            {logged_in_owner_permission && (
                                <>
                                    <div
                                        style={{
                                            marginBottom: theme.spacing.xs,
                                        }}
                                    >
                                        <div style={theme.styles.titleText}>
                                            Search & Chat Profiles
                                        </div>
                                    </div>

                                    <div
                                        style={{
                                            backgroundColor:
                                                theme.colors.background
                                                    .app_darker,
                                            borderRadius: theme.radius.lg,
                                            padding: theme.spacing.sm,
                                            display: "flex",
                                            flexDirection: "column",
                                            gap: theme.spacing.sm,
                                        }}
                                    >
                                        {render_text_search_inputs()}
                                        {render_text_search()}
                                        {render_message_panel()}
                                    </div>
                                </>
                            )}
                        </div>{" "}
                    </div>

                    <HorizontalDivider />

                    {/* SECTION 2: BOTTOM 3 COLUMNS */}
                    <div style={gridContainerStyle}>
                        {/* LEFT: Following & Blocked (Scrollable) */}
                        <div style={columnStyle}>
                            <div style={theme.styles.titleText}>
                                Followed / Blocked Profiles
                            </div>

                            {logged_in_owner_permission && (
                                <div>
                                    <div style={scrollableListStyle}>
                                        <p style={theme.styles.descriptionText}>
                                            {`Following (${profile.profiles_following?.length})`}
                                        </p>
                                        {profile.profiles_following?.map(
                                            (p) => (
                                                <div
                                                    key={`profile_follow_${p.id}`}
                                                    style={{
                                                        backgroundColor:
                                                            theme.colors
                                                                .background
                                                                .app_success,
                                                        borderRadius:
                                                            theme.radius.sm,
                                                    }}
                                                >
                                                    <ProfileDirectingWrapper
                                                        profile_id={p.id}
                                                        profile_name={
                                                            p.profile_name
                                                        }
                                                        profile_image={p.image}
                                                    />
                                                </div>
                                            ),
                                        )}
                                        <p style={theme.styles.descriptionText}>
                                            {`Blocked (${profile.profiles_blocked?.length})`}
                                        </p>
                                        {profile.profiles_blocked?.map((p) => (
                                            <div
                                                key={`profile_block_${p.id}`}
                                                style={{
                                                    backgroundColor:
                                                        theme.colors.background
                                                            .app_error,
                                                    borderRadius:
                                                        theme.radius.sm,
                                                }}
                                            >
                                                <ProfileDirectingWrapper
                                                    profile_id={p.id}
                                                    profile_name={
                                                        p.profile_name
                                                    }
                                                    profile_image={p.image}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* MIDDLE: Owned/Collab Mangas Masonry + Chapters List */}
                        <div style={columnStyle}>
                            <div style={theme.styles.titleText}>
                                Owned / Collaborated Mangas
                            </div>

                            {all_mangas.length > 0 ? (
                                <div style={scrollableListStyle}>
                                    <Masonry columns={3} spacing={2}>
                                        {all_mangas.map((manga) => (
                                            <div
                                                key={`manga_owned_or_collab_${manga.id}`}
                                            >
                                                <CardWrapper
                                                    title={manga.title}
                                                    to={`/manga/${manga.id}/`}
                                                    image={manga.image}
                                                    meta_data={[]}
                                                    sizeVariant="profile"
                                                />
                                            </div>
                                        ))}
                                    </Masonry>
                                </div>
                            ) : (
                                <p
                                    style={{
                                        color: theme.colors.text.muted,
                                        textAlign: "center",
                                        width: "100%",
                                    }}
                                >
                                    No mangas found
                                </p>
                            )}

                            <div
                                style={{
                                    marginTop: theme.spacing.md,
                                    paddingTop: theme.spacing.sm,
                                }}
                            >
                                <div style={theme.styles.titleText}>
                                    Owned / Collaborated Chapters
                                </div>
                                {all_chapters.length > 0 ? (
                                    <div style={scrollableListStyle}>
                                        <ul
                                            style={{
                                                listStyle: "none",
                                                padding: 0,
                                            }}
                                        >
                                            {all_chapters.map((c, i) => (
                                                <li
                                                    key={`chapter_${i}`}
                                                    style={{
                                                        marginBottom:
                                                            theme.spacing.xs,
                                                    }}
                                                >
                                                    <a
                                                        href={`/read-manga/${c.manga}/${c.id}/`}
                                                        style={{
                                                            textDecoration:
                                                                "none",
                                                            display: "block",
                                                        }} // Removes default link styling
                                                    >
                                                        <div
                                                            style={{
                                                                borderRadius:
                                                                    theme.radius
                                                                        .sm,
                                                                backgroundColor:
                                                                    theme.colors
                                                                        .background
                                                                        .muted,
                                                                borderTop: `1px solid ${theme.colors.border.subtle}`,
                                                                padding: `${theme.spacing.sm} ${theme.spacing.sm}`,
                                                                transition: `background-color ${theme.transition.normal}`,
                                                                cursor: "pointer",
                                                            }}
                                                        >
                                                            <span
                                                                style={{
                                                                    ...theme
                                                                        .styles
                                                                        .descriptionText,
                                                                    color: theme
                                                                        .colors
                                                                        .text
                                                                        .primary,
                                                                }}
                                                            >
                                                                {c.manga_title}
                                                            </span>
                                                            <span
                                                                style={{
                                                                    ...theme
                                                                        .styles
                                                                        .metadataText,
                                                                    color: theme
                                                                        .colors
                                                                        .text
                                                                        .secondary,
                                                                }}
                                                            >
                                                                — {c.title} (
                                                                {c.no})
                                                            </span>
                                                        </div>
                                                    </a>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ) : (
                                    <p
                                        style={{
                                            color: theme.colors.text.muted,
                                            textAlign: "center",
                                            width: "100%",
                                        }}
                                    >
                                        No Chapters found
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* RIGHT: Owned Portfolios */}
                        <div style={columnStyle}>
                            <div style={theme.styles.titleText}>Portfolios</div>

                            {profile.portfolios?.length > 0 ? (
                                <div style={scrollableListStyle}>
                                    <Masonry columns={2} spacing={2}>
                                        {profile.portfolios.map((portfolio) => (
                                            <div
                                                key={`portfolio_${portfolio.id}`}
                                            >
                                                <CardWrapper
                                                    title={portfolio.title}
                                                    to={`/portfolio/${portfolio.id}/`}
                                                    image={portfolio.image}
                                                    meta_data={[]}
                                                    sizeVariant="profile"
                                                />
                                            </div>
                                        ))}
                                    </Masonry>
                                </div>
                            ) : (
                                <p
                                    style={{
                                        color: theme.colors.text.muted,
                                        textAlign: "center",
                                        width: "100%",
                                    }}
                                >
                                    No portfolios found
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {error_message && (
                    <ErrorPopUpWrapper
                        error_message={error_message}
                        on_close={() => set_error_message("")}
                        error_title="Profile Error"
                    />
                )}
                {asking_for_confirmation && (
                    <ConfirmationPopUpWrapper
                        confirmation_title="Confirm Block"
                        confirmation_message={`User will be ${is_user_blocked ? "un" : ""}blocked`}
                        on_accept={() => handle_block(true)}
                        on_reject={() => set_asking_for_confirmation(false)}
                    />
                )}
                {asking_for_reverification_confirmation && (
                    <ConfirmationPopUpWrapper
                        confirmation_title="Re-verify Profile"
                        confirmation_message="If you confirm, a new verification token will be sent to your current mail. Please be sure to verify your profile."
                        on_accept={() => handle_verification_reset(true)}
                        on_reject={() =>
                            set_asking_for_reverification_confirmation(false)
                        }
                    />
                )}
            </div>
        );
    }

    return render_main();
}

export default ShowProfilePage;
