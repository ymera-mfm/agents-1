import React, { useState, useMemo } from 'react';
import { useApp } from '../../store/AppContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Cpu, Search, Clock, PauseCircle } from 'lucide-react';

export const AgentsPage = () => {
  const { agents, loading } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  const filteredAgents = useMemo(() => {
    return agents
      .filter((a) => filter === 'all' || a.status === filter)
      .filter(
        (a) =>
          a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          a.type.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [agents, filter, searchTerm]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">AI Agents</h1>
            <p className="text-gray-400">Manage and monitor your autonomous AI workforce</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="relative">
              <Search
                size={20}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
              />
              <input
                type="text"
                placeholder="Search agents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-2 bg-transparent border-none text-white placeholder-gray-500 focus:outline-none"
              />
            </div>
          </div>

          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
          >
            <option value="all">All Status</option>
            <option value="working">Working</option>
            <option value="thinking">Thinking</option>
            <option value="idle">Idle</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <div
              key={agent.id}
              className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all hover:scale-105"
            >
              <div className="flex items-center justify-between mb-4">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center"
                  style={{ backgroundColor: `${agent.color}20` }}
                >
                  <Cpu className="w-8 h-8" style={{ color: agent.color }} />
                </div>
                <div className="flex flex-col items-end">
                  {agent.status === 'working' && (
                    <div className="flex items-center space-x-1 text-green-400">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-xs font-medium">Active</span>
                    </div>
                  )}
                  {agent.status === 'thinking' && (
                    <div className="flex items-center space-x-1 text-yellow-400">
                      <Clock className="w-3 h-3 animate-pulse" />
                      <span className="text-xs font-medium">Thinking</span>
                    </div>
                  )}
                  {agent.status === 'idle' && (
                    <div className="flex items-center space-x-1 text-gray-400">
                      <PauseCircle className="w-3 h-3" />
                      <span className="text-xs font-medium">Idle</span>
                    </div>
                  )}
                </div>
              </div>

              <h3 className="text-xl font-bold text-white mb-2">{agent.name}</h3>
              <p className="text-sm text-gray-400 capitalize mb-4">{agent.type} Specialist</p>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Efficiency</span>
                    <span className="text-white font-semibold">{agent.efficiency}%</span>
                  </div>
                  <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${agent.efficiency}%`, backgroundColor: agent.color }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-white/10">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">{agent.tasks}</div>
                    <div className="text-xs text-gray-400">Tasks</div>
                  </div>
                  <div className="h-8 w-px bg-white/10"></div>
                  <div className="text-center">
                    <div className="text-2xl font-bold" style={{ color: agent.color }}>
                      {agent.efficiency}%
                    </div>
                    <div className="text-xs text-gray-400">Success</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
