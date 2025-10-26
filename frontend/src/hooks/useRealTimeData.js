import { useState, useEffect } from 'react';
import { websocketService } from '../services/websocket';

export const useRealTimeData = (channel, initialValue = []) => {
  const [data, setData] = useState(initialValue);

  useEffect(() => {
    const unsubscribe = websocketService.subscribe(channel, (newData) => {
      setData((prev) => [...prev.slice(-49), newData]);
    });
    return unsubscribe;
  }, [channel]);

  return data;
};
