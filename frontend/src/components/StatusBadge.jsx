import React from 'react';
import { Pause, Activity, Zap, CheckCircle, AlertCircle } from 'lucide-react';

export const StatusBadge = ({ status }) => {
  const statusConfig = {
    idle: { icon: Pause, color: 'gray', label: 'Idle' },
    thinking: { icon: Activity, color: 'orange', label: 'Thinking' },
    working: { icon: Zap, color: 'blue', label: 'Working' },
    completed: { icon: CheckCircle, color: 'green', label: 'Completed' },
    error: { icon: AlertCircle, color: 'red', label: 'Error' },
  };

  const { color, label } = statusConfig[status] || statusConfig.idle;

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full bg-${color}-500 animate-pulse`} />
      <span className="text-sm text-gray-400">{label}</span>
    </div>
  );
};
