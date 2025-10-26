import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Cpu,
  Database,
  Globe,
  Server,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { usePerformanceMonitor } from '../hooks/usePerformanceMonitor';
import { cacheService } from '../services/cache';
import { logger } from '../utils/logger';

// Monitoring Dashboard Component
export const MonitoringDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('1h');
  const [alerts, setAlerts] = useState([]);
  const [systemHealth, setSystemHealth] = useState('healthy');

  const performanceMetrics = usePerformanceMonitor();

  // Mock real-time data (in production, this would come from your monitoring service)
  const [realtimeData, setRealtimeData] = useState({
    cpuUsage: [],
    memoryUsage: [],
    networkLatency: [],
    errorRate: [],
    requestsPerSecond: [],
    activeUsers: 0,
    totalRequests: 0,
    errorCount: 0,
    uptime: 0,
  });

  // Generate mock monitoring data
  useEffect(() => {
    const generateMockData = () => {
      const now = Date.now();
      const dataPoints = 20;

      const cpuData = Array.from({ length: dataPoints }, (_, i) => ({
        timestamp: now - (dataPoints - i) * 60000,
        value: Math.random() * 100,
        time: new Date(now - (dataPoints - i) * 60000).toLocaleTimeString(),
      }));

      const memoryData = Array.from({ length: dataPoints }, (_, i) => ({
        timestamp: now - (dataPoints - i) * 60000,
        value: 30 + Math.random() * 40,
        time: new Date(now - (dataPoints - i) * 60000).toLocaleTimeString(),
      }));

      const latencyData = Array.from({ length: dataPoints }, (_, i) => ({
        timestamp: now - (dataPoints - i) * 60000,
        value: 50 + Math.random() * 200,
        time: new Date(now - (dataPoints - i) * 60000).toLocaleTimeString(),
      }));

      const errorData = Array.from({ length: dataPoints }, (_, i) => ({
        timestamp: now - (dataPoints - i) * 60000,
        value: Math.random() * 5,
        time: new Date(now - (dataPoints - i) * 60000).toLocaleTimeString(),
      }));

      const requestData = Array.from({ length: dataPoints }, (_, i) => ({
        timestamp: now - (dataPoints - i) * 60000,
        value: 10 + Math.random() * 50,
        time: new Date(now - (dataPoints - i) * 60000).toLocaleTimeString(),
      }));

      setRealtimeData((prev) => ({
        ...prev,
        cpuUsage: cpuData,
        memoryUsage: memoryData,
        networkLatency: latencyData,
        errorRate: errorData,
        requestsPerSecond: requestData,
        activeUsers: Math.floor(Math.random() * 1000) + 100,
        totalRequests: Math.floor(Math.random() * 10000) + 50000,
        errorCount: Math.floor(Math.random() * 50),
        uptime: 99.9 - Math.random() * 0.5,
      }));
    };

    generateMockData();
    const interval = setInterval(generateMockData, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Generate alerts based on metrics
  useEffect(() => {
    const newAlerts = [];

    if (performanceMetrics.memory.used > 80) {
      newAlerts.push({
        id: 'memory-high',
        type: 'warning',
        message: `High memory usage: ${performanceMetrics.memory.used}MB`,
        timestamp: new Date().toISOString(),
      });
    }

    if (performanceMetrics.fps < 30) {
      newAlerts.push({
        id: 'fps-low',
        type: 'error',
        message: `Low FPS detected: ${performanceMetrics.fps}`,
        timestamp: new Date().toISOString(),
      });
    }

    if (performanceMetrics.errorCount > 5) {
      newAlerts.push({
        id: 'errors-high',
        type: 'error',
        message: `High error count: ${performanceMetrics.errorCount}`,
        timestamp: new Date().toISOString(),
      });
    }

    setAlerts(newAlerts);

    // Update system health
    if (newAlerts.some((alert) => alert.type === 'error')) {
      setSystemHealth('critical');
    } else if (newAlerts.some((alert) => alert.type === 'warning')) {
      setSystemHealth('warning');
    } else {
      setSystemHealth('healthy');
    }
  }, [performanceMetrics]);

  // Metric cards data
  const metricCards = useMemo(
    () => [
      {
        title: 'Performance Score',
        value: performanceMetrics.performanceScore || 0,
        unit: '%',
        icon: TrendingUp,
        color:
          performanceMetrics.performanceScore > 80
            ? 'text-green-400'
            : performanceMetrics.performanceScore > 60
              ? 'text-yellow-400'
              : 'text-red-400',
        bgColor:
          performanceMetrics.performanceScore > 80
            ? 'bg-green-500/20'
            : performanceMetrics.performanceScore > 60
              ? 'bg-yellow-500/20'
              : 'bg-red-500/20',
      },
      {
        title: 'Memory Usage',
        value: performanceMetrics.memory.used || 0,
        unit: 'MB',
        icon: Database,
        color: performanceMetrics.memory.used > 80 ? 'text-red-400' : 'text-blue-400',
        bgColor: performanceMetrics.memory.used > 80 ? 'bg-red-500/20' : 'bg-blue-500/20',
      },
      {
        title: 'FPS',
        value: performanceMetrics.fps || 0,
        unit: '',
        icon: Zap,
        color: performanceMetrics.fps > 50 ? 'text-green-400' : 'text-yellow-400',
        bgColor: performanceMetrics.fps > 50 ? 'bg-green-500/20' : 'bg-yellow-500/20',
      },
      {
        title: 'Active Users',
        value: realtimeData.activeUsers,
        unit: '',
        icon: Globe,
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/20',
      },
      {
        title: 'Error Count',
        value: performanceMetrics.errorCount || 0,
        unit: '',
        icon: AlertTriangle,
        color: performanceMetrics.errorCount > 0 ? 'text-red-400' : 'text-green-400',
        bgColor: performanceMetrics.errorCount > 0 ? 'bg-red-500/20' : 'bg-green-500/20',
      },
      {
        title: 'Uptime',
        value: realtimeData.uptime.toFixed(2),
        unit: '%',
        icon: CheckCircle,
        color: realtimeData.uptime > 99 ? 'text-green-400' : 'text-yellow-400',
        bgColor: realtimeData.uptime > 99 ? 'bg-green-500/20' : 'bg-yellow-500/20',
      },
    ],
    [performanceMetrics, realtimeData]
  );

  // Cache statistics
  const cacheStats = cacheService.getStats();

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'performance', label: 'Performance', icon: Cpu },
    { id: 'errors', label: 'Errors', icon: AlertTriangle },
    { id: 'cache', label: 'Cache', icon: Database },
    { id: 'logs', label: 'Logs', icon: Server },
  ];

  const timeRanges = [
    { value: '1h', label: '1 Hour' },
    { value: '6h', label: '6 Hours' },
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
  ];

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* System Health Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">System Health</h3>
          <div
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
              systemHealth === 'healthy'
                ? 'bg-green-500/20 text-green-400'
                : systemHealth === 'warning'
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-red-500/20 text-red-400'
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                systemHealth === 'healthy'
                  ? 'bg-green-400'
                  : systemHealth === 'warning'
                    ? 'bg-yellow-400'
                    : 'bg-red-400'
              }`}
            />
            <span className="capitalize">{systemHealth}</span>
          </div>
        </div>

        {alerts.length > 0 && (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded border-l-4 ${
                  alert.type === 'error'
                    ? 'bg-red-500/10 border-red-500 text-red-300'
                    : 'bg-yellow-500/10 border-yellow-500 text-yellow-300'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{alert.message}</span>
                  <span className="text-xs opacity-60">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metricCards.map((metric, index) => (
          <div key={index} className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">{metric.title}</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {metric.value}
                  {metric.unit}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                <metric.icon className={`w-6 h-6 ${metric.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Real-time Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">CPU Usage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={realtimeData.cpuUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Memory Usage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={realtimeData.memoryUsage}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#10B981"
                fill="#10B981"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Network Latency</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={realtimeData.networkLatency}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Line type="monotone" dataKey="value" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Requests per Second</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={realtimeData.requestsPerSecond}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Bar dataKey="value" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics Table */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-2 text-gray-400">Metric</th>
                <th className="text-left py-2 text-gray-400">Current</th>
                <th className="text-left py-2 text-gray-400">Target</th>
                <th className="text-left py-2 text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="text-gray-300">
              <tr className="border-b border-gray-700">
                <td className="py-2">First Contentful Paint</td>
                <td className="py-2">{performanceMetrics.renderTime?.toFixed(2) || 0}ms</td>
                <td className="py-2">&lt; 1000ms</td>
                <td className="py-2">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      (performanceMetrics.renderTime || 0) < 1000
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {(performanceMetrics.renderTime || 0) < 1000 ? 'Good' : 'Poor'}
                  </span>
                </td>
              </tr>
              <tr className="border-b border-gray-700">
                <td className="py-2">Frame Rate</td>
                <td className="py-2">{performanceMetrics.fps || 0} FPS</td>
                <td className="py-2">&gt; 60 FPS</td>
                <td className="py-2">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      (performanceMetrics.fps || 0) > 60
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}
                  >
                    {(performanceMetrics.fps || 0) > 60 ? 'Excellent' : 'Fair'}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2">Memory Usage</td>
                <td className="py-2">{performanceMetrics.memory.used || 0}MB</td>
                <td className="py-2">&lt; 100MB</td>
                <td className="py-2">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      (performanceMetrics.memory.used || 0) < 100
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {(performanceMetrics.memory.used || 0) < 100 ? 'Good' : 'High'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderCacheTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Hit Rate</h3>
          <p className="text-3xl font-bold text-green-400">{cacheStats.hitRate}%</p>
          <p className="text-sm text-gray-400 mt-1">Cache efficiency</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Total Hits</h3>
          <p className="text-3xl font-bold text-blue-400">{cacheStats.hits}</p>
          <p className="text-sm text-gray-400 mt-1">Successful requests</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Cache Size</h3>
          <p className="text-3xl font-bold text-purple-400">{cacheStats.memorySize}</p>
          <p className="text-sm text-gray-400 mt-1">Items in memory</p>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Cache Management</h3>
          <button
            onClick={() => {
              cacheService.clear();
              logger.info('Cache cleared manually');
            }}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
          >
            Clear Cache
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">Cache Statistics</h4>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex justify-between">
                <span>Total Requests:</span>
                <span>{cacheStats.hits + cacheStats.misses}</span>
              </div>
              <div className="flex justify-between">
                <span>Cache Hits:</span>
                <span className="text-green-400">{cacheStats.hits}</span>
              </div>
              <div className="flex justify-between">
                <span>Cache Misses:</span>
                <span className="text-red-400">{cacheStats.misses}</span>
              </div>
              <div className="flex justify-between">
                <span>Memory Cache Size:</span>
                <span>{cacheStats.memorySize} items</span>
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-2">Cache Health</h4>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-3 h-3 rounded-full ${cacheStats.hitRate > 80 ? 'bg-green-400' : cacheStats.hitRate > 60 ? 'bg-yellow-400' : 'bg-red-400'}`}
                />
                <span className="text-sm text-gray-300">
                  {cacheStats.hitRate > 80
                    ? 'Excellent'
                    : cacheStats.hitRate > 60
                      ? 'Good'
                      : 'Poor'}{' '}
                  hit rate
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div
                  className={`w-3 h-3 rounded-full ${cacheStats.memorySize < 50 ? 'bg-green-400' : 'bg-yellow-400'}`}
                />
                <span className="text-sm text-gray-300">
                  {cacheStats.memorySize < 50 ? 'Normal' : 'High'} memory usage
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">System Monitoring</h1>
            <p className="text-gray-400 mt-1">Real-time system health and performance metrics</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="bg-gray-800 text-white border border-gray-700 rounded px-3 py-2 text-sm"
            >
              {timeRanges.map((range) => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 bg-gray-800 p-1 rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'performance' && renderPerformanceTab()}
        {activeTab === 'cache' && renderCacheTab()}
        {activeTab === 'errors' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Error Tracking</h3>
            <p className="text-gray-400">
              Error tracking dashboard would be implemented here with real error data.
            </p>
          </div>
        )}
        {activeTab === 'logs' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">System Logs</h3>
            <p className="text-gray-400">
              Log viewer would be implemented here with real log data.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MonitoringDashboard;
