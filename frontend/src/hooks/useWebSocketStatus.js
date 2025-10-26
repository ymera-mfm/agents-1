import { useState, useEffect } from 'react';
import { websocketService } from '../services/websocket';

export const useWebSocketStatus = () => {
  const [status, setStatus] = useState('disconnected');

  useEffect(() => {
    const unsubscribe = websocketService.subscribeToStatus(setStatus);
    return unsubscribe;
  }, []);

  return status;
};
