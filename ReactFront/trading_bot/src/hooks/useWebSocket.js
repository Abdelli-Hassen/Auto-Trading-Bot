import { useState, useEffect, useRef } from 'react';

export function useWebSocket(url) {
  const [data, setData] = useState({
    status: null,
    prices: {},
    timestamp: null
  });
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    let reconnectInterval;
    
    const connect = () => {
      ws.current = new WebSocket(url);
      
      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket Connected');
      };
      
      ws.current.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setData(parsed);
        } catch (e) {
          console.error("Failed to parse WS message", e);
        }
      };
      
      ws.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket Disconnected. Reconnecting...');
        reconnectInterval = setTimeout(connect, 3000);
      };
      
      ws.current.onerror = (err) => {
        console.error('WebSocket Error', err);
        ws.current.close();
      };
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      clearTimeout(reconnectInterval);
    };
  }, [url]);

  return { data, isConnected };
}
