import { writable } from "svelte/store";
import type { StreamMessage } from "./types";

export function createSSEConnection(url: string, onMessage: (msg: StreamMessage) => void) {
    const connected = writable(false);
    const eventSource = new EventSource(url);

    eventSource.onopen = () => connected.set(true);
    eventSource.onerror = () => connected.set(false);
    eventSource.onmessage = (e) => {
        try {
            const parsed = JSON.parse(e.data) as StreamMessage;
            onMessage(parsed);
        } catch (error) {
            console.error("Failed to parse SSE message:", error);
        }
    };

    function close() {
        eventSource.close();
        connected.set(false);
    }

    return { connected, close };
}