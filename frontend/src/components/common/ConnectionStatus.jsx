import React from 'react';
import { useWebSocketStatus } from '../../hooks/useWebSocketStatus';
import { Wifi, RefreshCw, WifiOff } from 'lucide-react';

export const ConnectionStatus = () => {
  const status = useWebSocketStatus();
  const config = {
    connected: { icon: Wifi, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Connected' },
    connecting: {
      icon: RefreshCw,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/20',
      label: 'Connecting...',
    },
    disconnected: {
      icon: WifiOff,
      color: 'text-red-400',
      bg: 'bg-red-500/20',
      label: 'Disconnected',
    },
  };

  const c = config[status] || config.disconnected;
  const Icon = c.icon;

  return (
    <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg ${c.bg}`}>
      <Icon className={`w-4 h-4 ${c.color} ${status === 'connecting' ? 'animate-spin' : ''}`} />
      <span className={`text-xs font-medium ${c.color}`}>{c.label}</span>
    </div>
  );
};
