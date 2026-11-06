import { useEffect } from "react";

export function useMessageWebSocket(profileId, onNewMessage) {
    useEffect(() => {
        if (!profileId) return;

        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        const socket = new WebSocket(
            `${protocol}://${window.location.host}/ws/messages/${profileId}/`,
        );

        /* package is something like this
            event:
            message { target: WebSocket, isTrusted: true,
            data:
                '{"message_id": 100
                    "sender_id": 3
                    "receiver_id": 6
                    "message": "text_here"
                    "timestamp": "2025-12-20T17:06:05.626303+00:00"
                    "is_read": false}'
        */

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onNewMessage(data);
        };

        return () => socket.close();
    }, [profileId, onNewMessage]);
}
