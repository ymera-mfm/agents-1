import React, { useState } from 'react';
import { useApp } from '../store/AppContext';
import { ConnectionStatus } from './common/ConnectionStatus';
import { NotificationPanel } from './common/NotificationPanel';
import {
  Activity,
  Zap,
  Cpu,
  Users,
  BarChart3,
  Settings,
  Bell,
  LogOut,
  Menu,
  X,
  Code,
  Calendar,
  MessageCircle,
  Folder,
} from 'lucide-react';

export const Navigation = () => {
  const { page, setPage, user, logout, notifications } = useApp();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'agents', label: 'Agents', icon: Cpu },
    { id: 'projects', label: 'Projects', icon: Folder },
    { id: 'profile', label: 'Profile', icon: Users },
    { id: 'monitoring', label: 'Monitoring', icon: BarChart3 },
    { id: 'command', label: 'Command', icon: Code },
    { id: 'project-history', label: 'Project History', icon: Calendar },
    { id: 'collaboration', label: 'Collaboration', icon: MessageCircle },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'resources', label: 'Resources', icon: Users },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/40 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/50">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
              AgentFlow
            </span>
          </div>

          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setPage(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                    page === item.id
                      ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/20'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex items-center space-x-4">
            <ConnectionStatus />

            <div className="relative">
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2 text-gray-400 hover:text-white transition"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                )}
              </button>
              <NotificationPanel isOpen={notifOpen} onClose={() => setNotifOpen(false)} />
            </div>

            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-white font-bold shadow-lg">
                {user?.avatar}
              </div>
              <button
                onClick={logout}
                className="text-gray-400 hover:text-red-400 transition"
                title="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden text-gray-400 hover:text-white"
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-black/60 backdrop-blur-xl">
          <div className="px-4 py-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setPage(item.id);
                    setMobileOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition ${
                    page === item.id
                      ? 'bg-cyan-500/20 text-cyan-400'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
