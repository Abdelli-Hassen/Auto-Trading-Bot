import { useState, useEffect, useRef } from 'react';

export function useWebSocket(url) {
  const [data, setData] = useState({ status: null, prices: {}, timestamp: null });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef      = useRef(null);
  const timerRef   = useRef(null);
  const attempts   = useRef(0);
  const unmounted  = useRef(false);

  useEffect(() => {
    unmounted.current = false;

    const connect = () => {
      if (unmounted.current) return;

      // Exponential backoff: 3s → 6s → 12s → max 30s
      const delay = Math.min(3000 * Math.pow(1.5, attempts.current), 30000);

      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          if (unmounted.current) { ws.close(); return; }
          setIsConnected(true);
          attempts.current = 0; // reset backoff on success
        };

        ws.onmessage = (event) => {
          try { setData(JSON.parse(event.data)); } catch { /* ignore */ }
        };

        ws.onclose = () => {
          if (unmounted.current) return;
          setIsConnected(false);
          attempts.current += 1;
          timerRef.current = setTimeout(connect, delay);
        };

        ws.onerror = () => {
          // onerror is always followed by onclose, so we handle reconnect there
          ws.close();
        };
      } catch {
        // WebSocket constructor can throw (e.g. invalid URL)
        attempts.current += 1;
        timerRef.current = setTimeout(connect, delay);
      }
    };

    connect();

    return () => {
      unmounted.current = true;
      clearTimeout(timerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [url]);

  return { data, isConnected };
}
