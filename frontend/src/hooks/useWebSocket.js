import { useEffect, useRef, useCallback } from 'react';
import { INTERVALS } from '../constants/time';

export const useWebSocket = (url, onMessage) => {
  const ws = useRef(null);
  const reconnectTimeout = useRef();
  const messageQueue = useRef([]);
  const isConnected = useRef(false);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        isConnected.current = true;

        // Process any queued messages
        while (messageQueue.current.length > 0 && isConnected.current) {
          const message = messageQueue.current.shift();
          ws.current.send(JSON.stringify(message));
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onclose = () => {
        isConnected.current = false;

        // Attempt reconnect with exponential backoff
        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, INTERVALS.FAST_POLL);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
    }
  }, [url, onMessage]);

  const sendMessage = useCallback((message) => {
    if (isConnected.current && ws.current) {
      ws.current.send(JSON.stringify(message));
    } else {
      // Queue message if not connected
      messageQueue.current.push(message);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { sendMessage, disconnect, isConnected: isConnected.current };
};
