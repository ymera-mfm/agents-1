// components/AdvancedAnalytics.jsx
import React, { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, Users, Target, Zap, Calendar } from 'lucide-react';

export const AdvancedAnalytics = ({ projects, agents }) => {
  const [selectedMetric, setSelectedMetric] = useState('efficiency');

  // Calculate advanced metrics
  const analyticsData = useMemo(() => {
    const data = {
      efficiency: [],
      workload: [],
      projectHealth: [],
      teamPerformance: [],
      summary: {
        totalProjects: projects.length,
        activeAgents: agents.filter((a) => a.status === 'working').length,
        avgEfficiency: 0,
        completionRate: 0,
        onTimeDelivery: 0,
      },
    };

    // Efficiency trends
    agents.forEach((agent) => {
      data.efficiency.push({
        name: agent.name,
        efficiency: agent.efficiency,
        tasks: agent.tasks,
        color: agent.color,
      });
    });

    // Project health
    projects.forEach((project) => {
      data.projectHealth.push({
        name: project.name,
        progress: project.progress,
        health:
          project.progress > 80
            ? 100
            : project.progress > 50
              ? 75
              : project.progress > 25
                ? 50
                : 25,
        budget: (project.spent / project.budget) * 100,
      });
    });

    // Calculate summary metrics
    data.summary.avgEfficiency = agents.reduce((sum, a) => sum + a.efficiency, 0) / agents.length;
    data.summary.completionRate =
      (projects.filter((p) => p.progress === 100).length / projects.length) * 100;
    data.summary.onTimeDelivery = 85; // This would come from actual project data

    return data;
  }, [projects, agents]);

  const MetricCard = ({ title, value, change, icon: Icon, color }) => (
    <motion.div
      className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg`} style={{ backgroundColor: `${color}20` }}>
          <Icon className="w-6 h-6" style={{ color }} />
        </div>
        {change && (
          <span
            className={`text-sm font-semibold px-2 py-1 rounded ${
              change > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}
          >
            {change > 0 ? '+' : ''}
            {change}%
          </span>
        )}
      </div>
      <h3 className="text-3xl font-bold text-white mb-1">{value}</h3>
      <p className="text-gray-400 text-sm">{title}</p>
    </motion.div>
  );

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="backdrop-blur-xl bg-black/80 border border-white/20 rounded-lg p-3">
          <p className="text-white font-semibold">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white">Advanced Analytics</h3>
          <p className="text-gray-400">Comprehensive insights into your AI operations</p>
        </div>

        <div className="flex space-x-2">
          {['efficiency', 'workload', 'health', 'performance'].map((metric) => (
            <button
              key={metric}
              onClick={() => setSelectedMetric(metric)}
              className={`px-4 py-2 rounded-lg transition ${
                selectedMetric === metric
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'bg-white/5 text-gray-400 hover:text-white'
              }`}
            >
              {metric.charAt(0).toUpperCase() + metric.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Projects"
          value={analyticsData.summary.totalProjects}
          change={12}
          icon={Target}
          color="#00f5ff"
        />
        <MetricCard
          title="Active Agents"
          value={analyticsData.summary.activeAgents}
          change={8}
          icon={Users}
          color="#ff3366"
        />
        <MetricCard
          title="Avg Efficiency"
          value={`${analyticsData.summary.avgEfficiency.toFixed(1)}%`}
          change={5}
          icon={Zap}
          color="#00ff88"
        />
        <MetricCard
          title="On-Time Delivery"
          value={`${analyticsData.summary.onTimeDelivery}%`}
          change={3}
          icon={Calendar}
          color="#ffd700"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Efficiency */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-6">Agent Efficiency</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.efficiency}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
              <XAxis dataKey="name" stroke="#9ca3af" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#9ca3af" />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="efficiency" name="Efficiency" radius={[4, 4, 0, 0]}>
                {analyticsData.efficiency.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Project Health */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-6">Project Health</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.projectHealth}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="health"
                stroke="#00f5ff"
                strokeWidth={3}
                dot={{ fill: '#00f5ff', r: 4 }}
                name="Health Score"
              />
              <Line
                type="monotone"
                dataKey="progress"
                stroke="#00ff88"
                strokeWidth={2}
                dot={{ fill: '#00ff88', r: 3 }}
                name="Progress"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Distribution */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-6">Performance Distribution</h4>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={analyticsData.efficiency}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="tasks" fill="#8884d8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="efficiency" fill="#82ca9d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex flex-col justify-center">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'High Performers', value: 35 },
                    { name: 'Average', value: 45 },
                    { name: 'Needs Improvement', value: 20 },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  <Cell fill="#00ff88" />
                  <Cell fill="#00f5ff" />
                  <Cell fill="#ff3366" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="text-center text-sm text-gray-400 mt-2">Performance Distribution</div>
          </div>
        </div>
      </div>

      {/* Trend Analysis */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-6 flex items-center space-x-2">
          <TrendingUp className="w-5 h-5" />
          <span>Trend Analysis</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="p-4 bg-white/5 rounded-lg">
            <div className="text-gray-400 mb-1">Efficiency Trend</div>
            <div className="text-green-400 font-semibold">+5.2% this month</div>
            <div className="text-gray-500 text-xs mt-1">Consistent improvement</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg">
            <div className="text-gray-400 mb-1">Project Completion</div>
            <div className="text-cyan-400 font-semibold">12% faster delivery</div>
            <div className="text-gray-500 text-xs mt-1">Compared to last quarter</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg">
            <div className="text-gray-400 mb-1">Resource Utilization</div>
            <div className="text-yellow-400 font-semibold">78% optimal</div>
            <div className="text-gray-500 text-xs mt-1">+8% from last month</div>
          </div>
        </div>
      </div>
    </div>
  );
};
