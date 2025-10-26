import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchDashboardStats } from './dashboardSlice';
import {
  Users,
  Folder,
  Zap,
  Activity,
  TrendingUp,
  BarChart3,
  Database,
  Server,
  GitBranch,
  AlertCircle,
} from 'lucide-react';

export const DashboardPage = () => {
  const dispatch = useDispatch();
  const { stats, status, error } = useSelector((state) => state.dashboard);

  useEffect(() => {
    dispatch(fetchDashboardStats());
  }, [dispatch]);

  if (status === 'loading') {
    return (
      <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
        <div className="text-center py-20">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
        <div className="text-center py-20">
          <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => dispatch(fetchDashboardStats())}
            className="mt-4 px-6 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-2">
          Dashboard
        </h1>
        <p className="text-gray-400 text-lg">Overview of your AI workforce and projects</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          {
            label: 'Total Agents',
            value: stats?.totalAgents || 0,
            icon: Users,
            color: 'text-cyan-400',
            trend: '+12%',
          },
          {
            label: 'Active Agents',
            value: `${stats?.activeAgents || 0}/${stats?.totalAgents || 0}`,
            icon: Zap,
            color: 'text-blue-400',
            trend: '+5%',
          },
          {
            label: 'Total Projects',
            value: stats?.totalProjects || 0,
            icon: Folder,
            color: 'text-purple-400',
            trend: '+3',
          },
          {
            label: 'Active Projects',
            value: `${stats?.activeProjects || 0}/${stats?.totalProjects || 0}`,
            icon: Activity,
            color: 'text-green-400',
            trend: '+2',
          },
        ].map((stat, index) => (
          <div
            key={index}
            className="p-6 rounded-2xl transition-all hover:scale-105"
            style={{
              background: 'rgba(20, 20, 20, 0.9)',
              backdropFilter: 'blur(25px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <stat.icon size={24} className={`${stat.color} mb-3`} />
            <div className={`text-3xl font-bold ${stat.color} mb-1`}>{stat.value}</div>
            <div className="text-sm text-gray-500">{stat.label}</div>
            <div className="text-xs text-green-400 flex items-center mt-2">
              <TrendingUp size={14} className="mr-1" />
              {stat.trend}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div
          className="p-6 rounded-2xl"
          style={{
            background: 'rgba(20, 20, 20, 0.9)',
            backdropFilter: 'blur(25px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Activity size={20} className="text-cyan-400" />
            Recent Activity
          </h3>
          <div className="space-y-3">
            {stats?.recentActivities?.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start space-x-3 p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
              >
                <div
                  className="w-2 h-2 rounded-full mt-2 flex-shrink-0"
                  style={{ backgroundColor: activity.type === 'agent' ? '#00f5ff' : '#ff00aa' }}
                />
                <div className="flex-1">
                  <p className="text-gray-300 text-sm">{activity.text}</p>
                  <p className="text-gray-500 text-xs mt-1">{activity.time}</p>
                </div>
              </div>
            )) || <div className="text-center py-8 text-gray-500">No recent activities found.</div>}
          </div>
        </div>

        <div
          className="p-6 rounded-2xl"
          style={{
            background: 'rgba(20, 20, 20, 0.9)',
            backdropFilter: 'blur(25px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Server size={20} className="text-cyan-400" />
            System Status
          </h3>
          <div className="space-y-4">
            {stats?.systemStatus &&
              Object.entries(stats.systemStatus).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {key === 'api' && <GitBranch size={18} className="text-cyan-400" />}
                    {key === 'database' && <Database size={18} className="text-purple-400" />}
                    {key === 'queue' && <BarChart3 size={18} className="text-blue-400" />}
                    <div>
                      <div className="text-gray-300 font-medium">
                        {key.charAt(0).toUpperCase() + key.slice(1)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {value.status.charAt(0).toUpperCase() + value.status.slice(1)}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-gray-300 font-medium">
                      {value.responseTime || value.uptime || value.tasksPerMin}
                    </div>
                    <div className="text-xs text-gray-500">
                      {value.responseTime ? 'Response Time' : value.uptime ? 'Uptime' : 'Tasks/Min'}
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      <div
        className="p-6 rounded-2xl"
        style={{
          background: 'rgba(20, 20, 20, 0.9)',
          backdropFilter: 'blur(25px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-cyan-400" />
          Agent Performance
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'CodeAnalyzer Alpha', value: 98, color: 'bg-cyan-500' },
            { label: 'UIDesigner Beta', value: 92, color: 'bg-pink-500' },
            { label: 'BackendDev Gamma', value: 95, color: 'bg-green-500' },
            { label: 'SecurityGuard Delta', value: 89, color: 'bg-yellow-500' },
          ].map((agent, index) => (
            <div key={index} className="p-4 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{agent.label}</span>
                <span className="text-lg font-bold text-white">{agent.value}%</span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full ${agent.color} rounded-full`}
                  style={{ width: `${agent.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
