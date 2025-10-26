import React, { useState } from 'react';
import { useApp } from '../store/AppContext';
import { Cpu, Send } from 'lucide-react';

export const CommandPage = () => {
  const { agents } = useApp();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [command, setCommand] = useState('');
  const [commandsHistory, setCommandsHistory] = useState([]);

  const handleSendCommand = () => {
    if (!selectedAgent || !command.trim()) {
      return;
    }

    const newCommand = {
      id: Date.now(),
      agentId: selectedAgent.id,
      agentName: selectedAgent.name,
      command,
      timestamp: new Date().toISOString(),
      status: 'sent',
    };

    setCommandsHistory((prev) => [newCommand, ...prev]);
    setCommand('');
  };

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Command Center</h1>
          <p className="text-gray-400">Send commands to your AI agents</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Select Agent</h3>
            <div className="space-y-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition ${
                    selectedAgent?.id === agent.id
                      ? 'border-cyan-500 bg-cyan-500/10'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${agent.color}20` }}
                    >
                      <Cpu className="w-5 h-5" style={{ color: agent.color }} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{agent.name}</h4>
                      <p className="text-sm text-gray-400">{agent.status}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Send Command</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Command</label>
                <textarea
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition"
                  rows="4"
                  placeholder="Enter command for the agent..."
                />
              </div>
              <button
                onClick={handleSendCommand}
                disabled={!selectedAgent || !command.trim()}
                className="w-full py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-600 hover:to-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                Send Command
              </button>
            </div>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Command History</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {commandsHistory.length === 0 ? (
                <p className="text-gray-400 text-center py-8">No commands sent yet</p>
              ) : (
                commandsHistory.map((cmd) => (
                  <div key={cmd.id} className="p-4 bg-white/5 rounded-lg border border-white/10">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-white">{cmd.agentName}</h4>
                      <span className="text-xs text-gray-400">
                        {new Date(cmd.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{cmd.command}</p>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        cmd.status === 'sent'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}
                    >
                      {cmd.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
