import React from 'react';
import { useApp } from '../../store/AppContext';

export const NotificationPanel = ({ isOpen, onClose: _onClose }) => {
  const { notifications, setNotifications } = useApp();

  const markAsRead = (id) => {
    setNotifications(notifications.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, read: true })));
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="absolute right-0 top-16 w-80 backdrop-blur-xl bg-black/90 border border-white/10 rounded-xl shadow-2xl z-50">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Notifications</h3>
          <button onClick={markAllAsRead} className="text-sm text-cyan-400 hover:text-cyan-300">
            Mark all read
          </button>
        </div>
      </div>
      <div className="max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="p-4 text-center text-gray-400">No notifications</div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              onClick={() => markAsRead(notif.id)}
              className={`p-4 border-b border-white/10 hover:bg-white/5 cursor-pointer transition ${!notif.read ? 'bg-cyan-500/10' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-white font-medium">{notif.title}</p>
                  <p className="text-sm text-gray-400 mt-1">{notif.time}</p>
                </div>
                {!notif.read && <div className="w-2 h-2 bg-cyan-400 rounded-full mt-2"></div>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
