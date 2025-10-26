import React, { useEffect } from 'react';
import { X, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';

export const Toast = ({ message, onClose, type = 'success' }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const config = {
    success: { color: 'green', icon: CheckCircle2 },
    error: { color: 'red', icon: AlertCircle },
    warning: { color: 'yellow', icon: AlertTriangle },
  };

  const { color, icon: Icon } = config[type];

  return (
    <div
      className={`fixed top-20 right-4 z-50 p-4 rounded-xl border bg-${color}-500/10 border-${color}-500/30 text-${color}-400 flex items-center gap-3 shadow-lg backdrop-blur-xl`}
    >
      <Icon size={20} />
      <span>{message}</span>
      <button onClick={onClose} className="hover:opacity-70">
        <X size={18} />
      </button>
    </div>
  );
};
