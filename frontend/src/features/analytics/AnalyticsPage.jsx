import React, { useMemo } from 'react';
import { useApp } from '../../store/AppContext';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

export const AnalyticsPage = () => {
  const { projects, agents } = useApp();

  const analyticsData = useMemo(
    () => ({
      projectDistribution: [
        {
          name: 'Planning',
          value: projects.filter((p) => p.status === 'planning').length,
          color: '#a855f7',
        },
        {
          name: 'In Progress',
          value: projects.filter((p) => p.status === 'in_progress').length,
          color: '#3b82f6',
        },
        {
          name: 'Completed',
          value: projects.filter((p) => p.status === 'completed').length,
          color: '#10b981',
        },
      ],
      agentPerformance: agents.map((agent) => ({
        name: agent.name,
        efficiency: agent.efficiency,
        tasks: agent.tasks,
      })),
      budgetOverview: projects.map((p) => ({
        name: p.name,
        budget: p.budget / 1000,
        spent: p.spent / 1000,
      })),
    }),
    [projects, agents]
  );

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Analytics</h1>
          <p className="text-gray-400">Comprehensive insights and performance metrics</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Project Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData.projectDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {analyticsData.projectDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-6">Agent Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.agentPerformance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
                <XAxis dataKey="name" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Bar dataKey="efficiency" fill="#00f5ff" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 lg:col-span-2">
            <h3 className="text-xl font-bold text-white mb-6">Budget Overview</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.budgetOverview}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
                <XAxis dataKey="name" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Bar dataKey="budget" fill="#3b82f6" radius={[8, 8, 0, 0]} name="Budget (k)" />
                <Bar dataKey="spent" fill="#10b981" radius={[8, 8, 0, 0]} name="Spent (k)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
