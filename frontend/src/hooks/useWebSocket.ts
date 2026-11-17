import { useEffect, useRef, useState } from "react";
import { API_BASE_URL, getAccessToken } from "../api/client";
import type { WsEventMessage } from "../types/api";

export type WsStatus = "connected" | "reconnecting" | "disconnected";

function buildWsUrl(token: string): string {
  const base = API_BASE_URL.replace(/^http/i, "ws").replace(/\/+$/, "");
  return `${base}/ws/tasks?token=${encodeURIComponent(token)}`;
}

export function useWebSocket(
  enabled: boolean,
  onEvent: (msg: WsEventMessage) => void
): WsStatus {
  const [status, setStatus] = useState<WsStatus>(
    enabled ? "reconnecting" : "disconnected"
  );
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!enabled) {
      setStatus("disconnected");
      return;
    }

    let isUnmounted = false;
    let ws: WebSocket | null = null;
    let heartbeatTimer: number | null = null;
    let reconnectTimer: number | null = null;
    let attempt = 0;

    function clearTimers() {
      if (heartbeatTimer !== null) {
        window.clearInterval(heartbeatTimer);
        heartbeatTimer = null;
      }
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    }

    function connect() {
      if (isUnmounted) return;
      const token = getAccessToken();
      if (!token) {
        setStatus("disconnected");
        return;
      }

      ws = new WebSocket(buildWsUrl(token));

      ws.onopen = () => {
        if (isUnmounted) return;
        attempt = 0;
        setStatus("connected");
        heartbeatTimer = window.setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        if (isUnmounted) return;
        try {
          const parsed = JSON.parse(event.data) as WsEventMessage;
          if (parsed.event === "pong" || parsed.event === "connected") {
            return;
          }
          onEventRef.current(parsed);
        } catch {
          // Ignore non-JSON frames
        }
      };

      ws.onclose = () => {
        clearTimers();
        if (isUnmounted) return;
        setStatus("reconnecting");
        const delay = Math.min(1000 * 2 ** attempt, 15000);
        attempt += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();

    return () => {
      isUnmounted = true;
      clearTimers();
      ws?.close();
    };
  }, [enabled]);

  return status;
}
