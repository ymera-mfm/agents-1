import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';

export const AddProjectModal = ({ onClose, onAdd }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('planning');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [assignedAgents, setAssignedAgents] = useState([]);

  const handleSubmit = () => {
    const newProject = {
      name,
      description,
      status,
      startDate,
      estimatedCompletion: endDate,
      progress: 0,
      assignedAgents,
    };
    onAdd(newProject);
    onClose();
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-50 p-4">
      <div
        className="w-full max-w-2xl rounded-2xl overflow-hidden"
        style={{
          background: 'rgba(15, 15, 15, 0.98)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-white">Create New Project</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-gray-400" />
            </button>
          </div>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Project Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., E-Commerce Platform"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-400 focus:outline-none transition-colors"
              >
                <option value="planning">Planning</option>
                <option value="in_progress">In Progress</option>
                <option value="on_hold">On Hold</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the project goals and scope..."
              rows="4"
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors resize-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-400 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Estimated Completion</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-400 focus:outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Assigned Agents</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {assignedAgents.map((agentId) => (
                <div
                  key={agentId}
                  className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-white"
                >
                  <span>{agentId}</span>
                  <button
                    onClick={() => setAssignedAgents(assignedAgents.filter((id) => id !== agentId))}
                    className="p-0.5 rounded-full hover:bg-white/10"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <select
                value=""
                onChange={(e) => {
                  if (e.target.value && !assignedAgents.includes(e.target.value)) {
                    setAssignedAgents([...assignedAgents, e.target.value]);
                  }
                }}
                className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
              >
                <option value="">Select an agent</option>
                <option value="agent-001">CodeAnalyzer Alpha</option>
                <option value="agent-002">UIDesigner Beta</option>
                <option value="agent-003">BackendDev Gamma</option>
              </select>
              <button className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white transition-colors">
                <Plus size={18} />
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-6 border-t border-gray-800">
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
              Create Project
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
