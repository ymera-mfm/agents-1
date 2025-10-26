import React, { useMemo } from 'react';
import { useApp } from '../store/AppContext';
import { Cpu, Folder } from 'lucide-react';

export const MonitoringPage = () => {
  const { agents, projects } = useApp();

  const monitoringData = useMemo(() => {
    return {
      agents: agents.map((agent) => ({
        ...agent,
        statusColor:
          agent.status === 'working'
            ? '#10b981'
            : agent.status === 'thinking'
              ? '#f59e0b'
              : '#6b7280',
      })),
      projects: projects.map((project) => ({
        ...project,
        statusColor:
          project.status === 'in_progress'
            ? '#3b82f6'
            : project.status === 'completed'
              ? '#10b981'
              : '#a855f7',
      })),
    };
  }, [agents, projects]);

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Monitoring</h1>
          <p className="text-gray-400">Real-time monitoring of agents and projects</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Agent Status</h3>
            <div className="space-y-3">
              {monitoringData.agents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: `${agent.color}20` }}
                    >
                      <Cpu className="w-5 h-5" style={{ color: agent.color }} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{agent.name}</h4>
                      <p className="text-sm text-gray-400">
                        {agent.tasks} tasks • {agent.efficiency}% efficiency
                      </p>
                    </div>
                  </div>
                  <span
                    className="text-xs px-3 py-1 rounded-full capitalize"
                    style={{ backgroundColor: `${agent.statusColor}20`, color: agent.statusColor }}
                  >
                    {agent.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Project Status</h3>
            <div className="space-y-3">
              {monitoringData.projects.map((project) => (
                <div
                  key={project.id}
                  className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${project.statusColor}20` }}
                    >
                      <Folder className="w-5 h-5" style={{ color: project.statusColor }} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{project.name}</h4>
                      <p className="text-sm text-gray-400">{project.progress}% complete</p>
                    </div>
                  </div>
                  <span
                    className="text-xs px-3 py-1 rounded-full capitalize"
                    style={{
                      backgroundColor: `${project.statusColor}20`,
                      color: project.statusColor,
                    }}
                  >
                    {project.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonitoringPage;
