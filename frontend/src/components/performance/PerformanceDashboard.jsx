/**
 * Performance Dashboard Component
 * Displays real-time performance metrics and recommendations
 */

import React, { useState, useEffect } from 'react';
import { performanceMonitor } from '../../utils/performance/monitor';
import { bundleAnalyzer } from '../../utils/performance/bundleAnalyzer';
import { cacheService } from '../../services/cache';

export function PerformanceDashboard() {
  const [metrics, setMetrics] = useState({});
  const [webVitals, setWebVitals] = useState({});
  const [bundleAnalysis, setBundleAnalysis] = useState(null);
  const [cacheStats, setCacheStats] = useState({});
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Update metrics every 5 seconds
    const updateMetrics = () => {
      setMetrics(performanceMonitor.getMetrics());
      setWebVitals(performanceMonitor.getWebVitals());
      setCacheStats(cacheService.getStats());
    };

    updateMetrics();
    const interval = setInterval(updateMetrics, 5000);

    // Analyze bundle on mount
    const analysis = bundleAnalyzer.analyzeChunks();
    setBundleAnalysis(analysis);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) {
      return '0 B';
    }
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatTime = (ms) => {
    if (!ms) {
      return '0ms';
    }
    return ms < 1000 ? `${ms.toFixed(2)}ms` : `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 9999,
          padding: '12px 20px',
          backgroundColor: '#4F46E5',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}
      >
        ⚡ Perf {isVisible ? '▼' : '▲'}
      </button>

      {/* Dashboard Panel */}
      {isVisible && (
        <div
          style={{
            position: 'fixed',
            bottom: '80px',
            right: '20px',
            width: '400px',
            maxHeight: '600px',
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '12px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
            zIndex: 9998,
            overflow: 'auto',
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px',
              borderBottom: '1px solid #E5E7EB',
              backgroundColor: '#F9FAFB',
              borderRadius: '12px 12px 0 0',
            }}
          >
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold' }}>
              ⚡ Performance Monitor
            </h3>
          </div>

          {/* Web Vitals Section */}
          <div style={{ padding: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
              🎯 Core Web Vitals
            </h4>
            <div style={{ display: 'grid', gap: '8px' }}>
              {Object.entries(webVitals).map(([key, value]) => (
                <div
                  key={key}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>{key}</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>{formatTime(value)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bundle Analysis */}
          {bundleAnalysis && (
            <div style={{ padding: '16px', borderTop: '1px solid #E5E7EB' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
                📦 Bundle Analysis
              </h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>Total Size</span>
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: '600',
                      color: bundleAnalysis.totalSize > 500000 ? '#EF4444' : '#10B981',
                    }}
                  >
                    {formatBytes(bundleAnalysis.totalSize)}
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>Chunks</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>
                    {bundleAnalysis.chunks.length}
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>Compression</span>
                  <span style={{ fontSize: '13px', fontWeight: '600' }}>
                    {(bundleAnalysis.compressionRatio * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Cache Stats */}
          <div style={{ padding: '16px', borderTop: '1px solid #E5E7EB' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
              💾 Cache Performance
            </h4>
            <div style={{ display: 'grid', gap: '8px' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px',
                  backgroundColor: '#F9FAFB',
                  borderRadius: '6px',
                }}
              >
                <span style={{ fontSize: '13px', color: '#6B7280' }}>Hit Rate</span>
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: '600',
                    color: cacheStats.hitRate > 70 ? '#10B981' : '#EF4444',
                  }}
                >
                  {cacheStats.hitRate?.toFixed(1) || 0}%
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px',
                  backgroundColor: '#F9FAFB',
                  borderRadius: '6px',
                }}
              >
                <span style={{ fontSize: '13px', color: '#6B7280' }}>Hits / Misses</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>
                  {cacheStats.hits || 0} / {cacheStats.misses || 0}
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px',
                  backgroundColor: '#F9FAFB',
                  borderRadius: '6px',
                }}
              >
                <span style={{ fontSize: '13px', color: '#6B7280' }}>Memory Size</span>
                <span style={{ fontSize: '13px', fontWeight: '600' }}>
                  {cacheStats.memorySize || 0} items
                </span>
              </div>
            </div>
          </div>

          {/* Render Performance */}
          {metrics.render && (
            <div style={{ padding: '16px', borderTop: '1px solid #E5E7EB' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
                ⚛️ Render Performance
              </h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>Avg Render</span>
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: '600',
                      color: metrics.render.average > 16 ? '#EF4444' : '#10B981',
                    }}
                  >
                    {formatTime(metrics.render.average)}
                  </span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px',
                    backgroundColor: '#F9FAFB',
                    borderRadius: '6px',
                  }}
                >
                  <span style={{ fontSize: '13px', color: '#6B7280' }}>Max Render</span>
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: '600',
                      color: metrics.render.max > 50 ? '#EF4444' : '#F59E0B',
                    }}
                  >
                    {formatTime(metrics.render.max)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {bundleAnalysis?.recommendations && bundleAnalysis.recommendations.length > 0 && (
            <div style={{ padding: '16px', borderTop: '1px solid #E5E7EB' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px' }}>
                💡 Recommendations
              </h4>
              <div style={{ display: 'grid', gap: '8px' }}>
                {bundleAnalysis.recommendations.slice(0, 3).map((rec, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '8px',
                      backgroundColor:
                        rec.priority === 'high'
                          ? '#FEE2E2'
                          : rec.priority === 'medium'
                            ? '#FEF3C7'
                            : '#DBEAFE',
                      borderRadius: '6px',
                      fontSize: '12px',
                    }}
                  >
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>{rec.message}</div>
                    <div style={{ color: '#6B7280' }}>{rec.suggestion}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div
            style={{
              padding: '16px',
              borderTop: '1px solid #E5E7EB',
              display: 'flex',
              gap: '8px',
            }}
          >
            <button
              onClick={() => {
                performanceMonitor.clearMetrics();
                cacheService.clear();
                window.location.reload();
              }}
              style={{
                flex: 1,
                padding: '8px',
                backgroundColor: '#EF4444',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
              }}
            >
              Clear & Reload
            </button>
            <button
              onClick={() => {
                if (process.env.NODE_ENV === 'development') {
                  // eslint-disable-next-line no-console
                  console.log('Performance Metrics:', metrics);
                  // eslint-disable-next-line no-console
                  console.log('Web Vitals:', webVitals);
                  // eslint-disable-next-line no-console
                  console.log('Bundle Analysis:', bundleAnalysis);
                  // eslint-disable-next-line no-console
                  console.log('Cache Stats:', cacheStats);
                }
              }}
              style={{
                flex: 1,
                padding: '8px',
                backgroundColor: '#4F46E5',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
              }}
            >
              Log to Console
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default PerformanceDashboard;
