import React, { useState } from 'react';
import { X, MessageSquare, Settings, Zap, Activity, Camera, Database } from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export const AgentDetailModal = ({ agent, onClose, onStatusChange }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([
    {
      sender: 'agent',
      text: `Hello! I'm ${agent.name}. How can I assist you today?`,
    },
  ]);

  const sendMessage = () => {
    if (!message.trim()) {
      return;
    }
    setChatHistory((prev) => [
      ...prev,
      { sender: 'user', text: message },
      { sender: 'agent', text: `Processing: "${message}"...` },
    ]);
    setMessage('');
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Zap },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'stats', label: 'Stats', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const Icon = agent.icon === 'Code' ? Zap : agent.icon === 'Camera' ? Camera : Database;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-2xl rounded-3xl overflow-hidden"
        style={{
          background: 'rgba(15, 15, 15, 0.98)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 25px 80px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div className="relative p-8 border-b border-gray-800">
          <div
            className="absolute inset-0 opacity-10"
            style={{
              background: `linear-gradient(135deg, ${agent.color}, transparent)`,
            }}
          />
          <button
            onClick={onClose}
            className="absolute top-6 right-6 p-2 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Close"
          >
            <X size={20} className="text-gray-400" />
          </button>
          <div className="relative flex items-center gap-4">
            <div
              className="p-4 rounded-2xl"
              style={{
                background: `${agent.color}20`,
                border: `1px solid ${agent.color}40`,
              }}
            >
              <Icon size={32} style={{ color: agent.color }} />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-white mb-1">{agent.name}</h2>
              <p className="text-gray-400 font-mono">{agent.type.toUpperCase()}</p>
            </div>
          </div>
        </div>

        <div className="flex border-b border-gray-800">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-gray-400 hover:text-cyan-400'
              }`}
              aria-current={activeTab === tab.id}
            >
              <tab.icon size={18} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="p-8">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <StatusBadge status={agent.status} />
                <div className="mt-2">
                  <select
                    value={agent.status}
                    onChange={(e) => onStatusChange(agent.id, e.target.value)}
                    className="mt-4 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
                  >
                    <option value="idle">Idle</option>
                    <option value="thinking">Thinking</option>
                    <option value="working">Working</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
                <p className="mt-4 text-gray-300 leading-relaxed">{agent.description}</p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
                  <div className="text-2xl font-bold" style={{ color: agent.color }}>
                    {agent.tasksCompleted}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Tasks Completed</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
                  <div className="text-2xl font-bold" style={{ color: agent.color }}>
                    {agent.efficiency}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Efficiency</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
                  <div className="text-2xl font-bold text-green-400">99.2%</div>
                  <div className="text-xs text-gray-500 mt-1">Uptime</div>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'chat' && (
            <div className="space-y-4">
              <div className="h-64 overflow-y-auto space-y-3 mb-4 border border-white/10 rounded-lg p-4">
                {chatHistory.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs p-3 rounded-lg ${
                        msg.sender === 'user'
                          ? 'bg-cyan-500/20 text-cyan-100'
                          : 'bg-gray-800/50 text-gray-300'
                      }`}
                    >
                      {msg.text}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type your message..."
                  className="flex-1 px-4 py-2 bg-gray-800/50 border border-cyan-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
                />
                <button
                  onClick={sendMessage}
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:shadow-lg hover:shadow-cyan-500/50 transition-all"
                >
                  Send
                </button>
              </div>
            </div>
          )}
          {activeTab === 'stats' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-2xl font-bold text-cyan-400">156</div>
                  <div className="text-sm text-gray-400">Tasks Completed</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-2xl font-bold text-green-400">98%</div>
                  <div className="text-sm text-gray-400">Success Rate</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-2xl font-bold text-blue-400">24.5h</div>
                  <div className="text-sm text-gray-400">Total Active Time</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-2xl font-bold text-purple-400">4.2/5</div>
                  <div className="text-sm text-gray-400">Avg Rating</div>
                </div>
              </div>
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-300">Recent Tasks</h3>
                {['Code optimization', 'Bug fix analysis', 'Feature implementation'].map(
                  (task, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg"
                    >
                      <span className="text-gray-300">{task}</span>
                      <span className="text-green-400 text-sm">Completed</span>
                    </div>
                  )
                )}
              </div>
            </div>
          )}
          {activeTab === 'settings' && (
            <div className="space-y-4">
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-300 mb-4">Agent Configuration</h3>
                {[
                  { label: 'Auto-assign tasks', checked: true },
                  { label: 'Priority mode', checked: false },
                  { label: 'Notifications', checked: true },
                ].map((setting, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg"
                  >
                    <span className="text-gray-300">{setting.label}</span>
                    <button
                      className={`w-12 h-6 rounded-full transition-colors ${
                        setting.checked ? 'bg-cyan-500' : 'bg-gray-600'
                      }`}
                    >
                      <div
                        className={`w-5 h-5 bg-white rounded-full transition-transform ${
                          setting.checked ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
