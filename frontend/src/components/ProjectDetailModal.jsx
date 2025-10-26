import React, { useState } from 'react';
import {
  X,
  FolderOpen,
  Users,
  Clock,
  CheckCircle,
  Pause,
  Activity,
  Edit,
  Download,
  Upload,
  Trash2,
  Plus,
  BarChart3,
  FileText,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { AgentCard } from './AgentCard';

const statusConfig = {
  planning: { color: 'purple', label: 'Planning', icon: Pause },
  in_progress: { color: 'blue', label: 'In Progress', icon: Activity },
  on_hold: { color: 'yellow', label: 'On Hold', icon: Pause },
  completed: { color: 'green', label: 'Completed', icon: CheckCircle },
};

export const ProjectDetailModal = ({
  project,
  agents,
  onClose,
  onUpdate: _onUpdate,
  onAddAgent,
  onRemoveAgent,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [newAgentId, setNewAgentId] = useState('');
  const status = statusConfig[project.status] || statusConfig.planning;

  const assignedAgents = project.assignedAgents
    ? project.assignedAgents.map((id) => agents.find((a) => a.id === id)).filter(Boolean)
    : [];

  const availableAgents = agents.filter((agent) => !project.assignedAgents?.includes(agent.id));

  const handleAddAgent = () => {
    if (newAgentId) {
      onAddAgent(project.id, newAgentId);
      setNewAgentId('');
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FolderOpen },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'files', label: 'Files', icon: BarChart3 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div
        className="relative w-full max-w-4xl rounded-3xl overflow-hidden max-h-[90vh] overflow-y-auto"
        style={{
          background: 'rgba(15, 15, 15, 0.98)',
          backdropFilter: 'blur(40px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="sticky top-0 z-10 p-6 border-b border-gray-800 bg-gray-900/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-cyan-500/20 border border-cyan-500/40">
                <status.icon size={24} className={`text-${status.color}-400`} />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">{project.name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <StatusBadge status={project.status} />
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <X size={20} className="text-gray-400" />
            </button>
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

        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white mb-2">Description</h3>
                <p className="text-gray-400">{project.description || 'No description provided.'}</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-sm text-gray-400 mb-1">Progress</div>
                  <div className="text-2xl font-bold text-cyan-400">{project.progress}%</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-sm text-gray-400 mb-1">Assigned Agents</div>
                  <div className="text-2xl font-bold text-cyan-400">{assignedAgents.length}</div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-sm text-gray-400 mb-1">Start Date</div>
                  <div className="text-xl font-bold text-white">
                    {new Date(project.startDate).toLocaleDateString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-sm text-gray-400 mb-1">Completion Date</div>
                  <div className="text-xl font-bold text-white">
                    {new Date(project.estimatedCompletion).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-4">Progress</h3>
                <div className="h-4 bg-gray-800 rounded-full overflow-hidden mb-2">
                  <div
                    className={`h-full bg-${status.color}-500 transition-all duration-500`}
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm text-gray-400">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-white mb-4">Assigned Agents</h3>
              {assignedAgents.length === 0 ? (
                <p className="text-gray-400">No agents assigned to this project.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {assignedAgents.map((agent) => (
                    <div key={agent.id} className="relative">
                      <AgentCard agent={agent} onClick={() => {}} />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRemoveAgent(project.id, agent.id);
                        }}
                        className="absolute top-2 right-2 p-1 bg-red-500/20 rounded-full hover:bg-red-500/30 transition-colors"
                        aria-label={`Remove ${agent.name}`}
                      >
                        <Trash2 size={16} className="text-red-400" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6">
                <h4 className="text-lg font-bold text-white mb-3">Add Agent</h4>
                <div className="flex gap-2">
                  <select
                    value={newAgentId}
                    onChange={(e) => setNewAgentId(e.target.value)}
                    className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white"
                  >
                    <option value="">Select an agent</option>
                    {availableAgents.map((agent) => (
                      <option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.type})
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddAgent}
                    disabled={!newAgentId}
                    className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white transition-colors disabled:opacity-50"
                  >
                    <Plus size={18} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white mb-4">Project Timeline</h3>
              <div className="space-y-6">
                {[
                  { date: project.startDate, label: 'Project Start', status: 'completed' },
                  {
                    date: new Date(
                      new Date(project.startDate).setDate(new Date(project.startDate).getDate() + 7)
                    ),
                    label: 'Requirements Gathering',
                    status: 'completed',
                  },
                  {
                    date: new Date(
                      new Date(project.startDate).setDate(
                        new Date(project.startDate).getDate() + 14
                      )
                    ),
                    label: 'Development',
                    status: project.progress > 30 ? 'completed' : 'in_progress',
                  },
                  {
                    date: new Date(
                      new Date(project.startDate).setDate(
                        new Date(project.startDate).getDate() + 21
                      )
                    ),
                    label: 'Testing',
                    status: project.progress > 60 ? 'completed' : 'pending',
                  },
                  {
                    date: project.estimatedCompletion,
                    label: 'Project Completion',
                    status: project.progress === 100 ? 'completed' : 'pending',
                  },
                ].map((item, index) => {
                  const itemStatus = {
                    completed: { color: 'green', icon: CheckCircle },
                    in_progress: { color: 'blue', icon: Activity },
                    pending: { color: 'gray', icon: Clock },
                  }[item.status];
                  return (
                    <div key={index} className="flex items-start gap-4">
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center border-2 border-${itemStatus.color}-500`}
                        >
                          <itemStatus.icon size={16} className={`text-${itemStatus.color}-400`} />
                        </div>
                        {index < 4 && (
                          <div
                            className="h-full w-0.5 bg-gray-700 flex-1"
                            style={{ height: '40px' }}
                          />
                        )}
                      </div>
                      <div className="pb-6">
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className={`font-medium ${item.status === 'completed' ? 'text-white' : 'text-gray-400'}`}
                          >
                            {item.label}
                          </span>
                          <span className="text-sm text-gray-500">
                            {new Date(item.date).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full bg-${itemStatus.color}-500`}
                            style={{ width: item.status === 'completed' ? '100%' : '0%' }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === 'files' && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white mb-4">Project Files</h3>
              <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center">
                <Upload size={48} className="mx-auto text-gray-500 mb-4" />
                <p className="text-gray-400 mb-2">Drag and drop files here</p>
                <p className="text-sm text-gray-500">or</p>
                <button className="mt-4 px-6 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors">
                  Browse Files
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                {['design.pdf', 'requirements.docx', 'api_spec.yaml'].map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-4 rounded-lg bg-white/5 border border-white/10"
                  >
                    <FileText size={24} className="text-cyan-400" />
                    <div className="flex-1">
                      <div className="font-medium text-white">{file}</div>
                      <div className="text-xs text-gray-500">Added 2 days ago</div>
                    </div>
                    <button className="p-1 rounded-lg hover:bg-white/10 transition-colors">
                      <Download size={18} className="text-gray-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 left-0 right-0 p-4 border-t border-gray-800 bg-gray-900/80 backdrop-blur-xl">
          <div className="flex justify-end gap-2">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors">
              <Trash2 size={18} />
              <span>Delete</span>
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors">
              <Download size={18} />
              <span>Export</span>
            </button>
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white transition-colors">
              <Edit size={18} />
              <span>Save Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
