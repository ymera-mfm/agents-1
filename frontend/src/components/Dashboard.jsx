import React, { useMemo } from 'react';
import { useApp } from '../store/AppContext';
import { StatCard } from '../components/common/StatCard';
import { Agent3DView } from '../features/agents/Agent3DView';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Cpu, Layers, Activity, TrendingUp, Users } from 'lucide-react';

export const Dashboard = () => {
  const { agents, projects, loading } = useApp();

  const stats = useMemo(
    () => ({
      activeAgents: agents.filter((a) => a.status === 'working').length,
      activeProjects: projects.filter((p) => p.status === 'in_progress').length,
      totalTasks: agents.reduce((sum, a) => sum + (a.tasks || 0), 0),
      avgEfficiency:
        agents.length > 0
          ? (agents.reduce((sum, a) => sum + (a.efficiency || 0), 0) / agents.length).toFixed(0)
          : 0,
    }),
    [agents, projects]
  );

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-gray-400">Real-time insights into your AI operations</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard title="Active Agents" value={stats.activeAgents} icon={Cpu} color="#00f5ff" />
          <StatCard
            title="Active Projects"
            value={stats.activeProjects}
            icon={Layers}
            color="#ff3366"
          />
          <StatCard title="Total Tasks" value={stats.totalTasks} icon={Activity} color="#00ff88" />
          <StatCard
            title="Avg Efficiency"
            value={`${stats.avgEfficiency}%`}
            icon={TrendingUp}
            color="#ffd700"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Agent Network</h3>
            <div className="h-[400px] flex items-center justify-center">
              <Agent3DView agents={agents} />
            </div>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Agent Status</h3>
            <div className="space-y-3">
              {agents.map((agent) => (
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
                    style={{
                      backgroundColor: agent.status === 'working' ? '#10b98120' : '#6b728020',
                      color: agent.status === 'working' ? '#10b981' : '#6b7280',
                    }}
                  >
                    {agent.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-6">Active Projects</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                className="bg-white/5 rounded-xl p-6 hover:bg-white/10 transition-all hover:scale-105 group"
              >
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-white">{project.name}</h4>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400">
                    {project.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-400">Progress</span>
                      <span className="text-white font-semibold">{project.progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-400 to-blue-600 transition-all duration-500"
                        style={{ width: `${project.progress}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-white/10 text-gray-400 text-sm">
                    <div className="flex items-center gap-2">
                      <Users size={14} />
                      <span>{project.team}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
