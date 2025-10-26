import React, { useState } from 'react';
import { X, Zap, Code, Camera, Database, Shield } from 'lucide-react';

const agentTypes = [
  { id: 'code-analyzer', label: 'Code Analyzer', icon: Code, color: '#00f5ff' },
  { id: 'ui-designer', label: 'UI Designer', icon: Camera, color: '#ff00aa' },
  { id: 'backend-dev', label: 'Backend Dev', icon: Database, color: '#00ff88' },
  { id: 'security', label: 'Security', icon: Shield, color: '#ffaa00' },
  { id: 'optimizer', label: 'Optimizer', icon: Zap, color: '#aa00ff' },
];

export const AddAgentModal = ({ onClose, onAdd }) => {
  const [name, setName] = useState('');
  const [type, setType] = useState('code-analyzer');
  const [status, setStatus] = useState('idle');
  const [description, setDescription] = useState('');

  const handleSubmit = () => {
    const agentType = agentTypes.find((t) => t.id === type);
    const newAgent = {
      id: `agent-${Date.now()}`,
      name,
      type,
      status,
      description: description || `${name} is a specialized ${type.replace('-', ' ')}.`,
      tasksCompleted: 0,
      efficiency: 95,
      icon: agentType.icon.name,
      color: agentType.color,
    };
    onAdd(newAgent);
    onClose();
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50 p-4">
      <div
        className="w-full max-w-md rounded-2xl overflow-hidden"
        style={{
          background: 'rgba(15, 15, 15, 0.98)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">Add New Agent</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            >
              <X size={20} className="text-gray-400" />
            </button>
          </div>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Agent Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., CodeAnalyzer Alpha"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Agent Type</label>
            <div className="grid grid-cols-3 gap-3">
              {agentTypes.map((agentType) => (
                <button
                  key={agentType.id}
                  onClick={() => setType(agentType.id)}
                  className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all ${
                    type === agentType.id
                      ? 'border-cyan-400 bg-cyan-500/10'
                      : 'border-white/10 bg-white/5 hover:border-cyan-400/30'
                  }`}
                >
                  <agentType.icon size={24} style={{ color: agentType.color }} />
                  <span className="text-xs mt-2 text-gray-300">{agentType.label}</span>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Initial Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-400 focus:outline-none transition-colors"
            >
              <option value="idle">Idle</option>
              <option value="thinking">Thinking</option>
              <option value="working">Working</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the agent's specialty..."
              rows="3"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={onClose}
              className="px-6 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!name.trim()}
              className="px-6 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-medium transition-colors disabled:opacity-50"
            >
              Add Agent
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
