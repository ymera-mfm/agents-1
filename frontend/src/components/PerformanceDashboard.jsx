// components/PerformanceDashboard.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Activity, Cpu, Memory, Network, AlertTriangle } from 'lucide-react';

export const PerformanceDashboard = () => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memory: { used: 0, total: 0, percentage: 0 },
    cpu: 0,
    network: { requests: 0, latency: 0 },
    errors: 0,
  });

  const [alerts, setAlerts] = useState([]);
  const frameCount = useRef(0);
  const lastTime = useRef(performance.now());

  useEffect(() => {
    const monitorPerformance = () => {
      // FPS Monitoring
      frameCount.current++;
      const currentTime = performance.now();

      if (currentTime - lastTime.current >= 1000) {
        const fps = Math.round((frameCount.current * 1000) / (currentTime - lastTime.current));
        frameCount.current = 0;
        lastTime.current = currentTime;

        setMetrics((prev) => ({
          ...prev,
          fps,
          memory: window.performance?.memory
            ? {
                used: Math.round(window.performance.memory.usedJSHeapSize / 1048576),
                total: Math.round(window.performance.memory.totalJSHeapSize / 1048576),
                percentage: Math.round(
                  (window.performance.memory.usedJSHeapSize /
                    window.performance.memory.totalJSHeapSize) *
                    100
                ),
              }
            : prev.memory,
        }));

        // Check for performance alerts
        setMetrics((currentMetrics) => {
          if (fps < 30) {
            addAlert('low-fps', `Low FPS detected: ${fps}`, 'warning');
          }

          if (currentMetrics.memory.percentage > 80) {
            addAlert(
              'high-memory',
              `High memory usage: ${currentMetrics.memory.percentage}%`,
              'error'
            );
          }

          return currentMetrics;
        });
      }

      requestAnimationFrame(monitorPerformance);
    };

    const rafId = requestAnimationFrame(monitorPerformance);
    return () => cancelAnimationFrame(rafId);
  }, []);

  const addAlert = (id, message, severity) => {
    setAlerts((prev) => {
      const existing = prev.find((alert) => alert.id === id);
      if (existing) {
        return prev;
      }

      return [...prev, { id, message, severity, timestamp: Date.now() }];
    });
  };

  const MetricCard = ({ title, value, unit, icon: Icon, trend, threshold }) => (
    <div
      className={`backdrop-blur-xl bg-white/5 border rounded-xl p-4 ${
        value > threshold ? 'border-red-500/50' : 'border-white/10'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Icon className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">{title}</span>
        </div>
        {trend && (
          <span className={`text-xs ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-white">
        {value}
        <span className="text-sm text-gray-400 ml-1">{unit}</span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-white">Performance Monitor</h3>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              metrics.fps > 50 ? 'bg-green-500' : metrics.fps > 30 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-400">Live</span>
        </div>
      </div>

      {/* Performance Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="FPS" value={metrics.fps} unit="fps" icon={Activity} threshold={30} />
        <MetricCard
          title="Memory"
          value={metrics.memory.percentage}
          unit="%"
          icon={Memory}
          threshold={80}
        />
        <MetricCard title="CPU" value={metrics.cpu} unit="%" icon={Cpu} threshold={70} />
        <MetricCard
          title="Network"
          value={metrics.network.latency}
          unit="ms"
          icon={Network}
          threshold={100}
        />
      </div>

      {/* Memory Usage Visualization */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Memory Usage</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Used: {metrics.memory.used}MB</span>
            <span className="text-gray-400">Total: {metrics.memory.total}MB</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-500"
              style={{ width: `${metrics.memory.percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Performance Alerts */}
      {alerts.length > 0 && (
        <div className="backdrop-blur-xl bg-white/5 border border-red-500/20 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h4 className="text-lg font-semibold text-white">Performance Alerts</h4>
          </div>
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between p-2 bg-red-500/10 rounded"
              >
                <span className="text-red-400 text-sm">{alert.message}</span>
                <button
                  onClick={() => setAlerts((prev) => prev.filter((a) => a.id !== alert.id))}
                  className="text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Recommendations */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Optimization Suggestions</h4>
        <div className="space-y-3 text-sm">
          {metrics.fps < 45 && (
            <div className="flex items-center space-x-3 p-3 bg-yellow-500/10 rounded-lg">
              <Activity className="w-4 h-4 text-yellow-400" />
              <span className="text-yellow-400">
                Consider reducing 3D scene complexity for better FPS
              </span>
            </div>
          )}
          {metrics.memory.percentage > 70 && (
            <div className="flex items-center space-x-3 p-3 bg-orange-500/10 rounded-lg">
              <Memory className="w-4 h-4 text-orange-400" />
              <span className="text-orange-400">
                High memory usage detected. Check for memory leaks.
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
