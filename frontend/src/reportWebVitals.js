/**
 * Web Vitals reporting for performance monitoring
 * Sends metrics to analytics endpoint in production
 */

import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  // Send to your analytics endpoint
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
    rating: metric.rating,
  });

  const url = `${process.env.REACT_APP_API_URL}/api/analytics/vitals`;

  // Use sendBeacon if available, fallback to fetch
  if (navigator.sendBeacon) {
    navigator.sendBeacon(url, body);
  } else {
    fetch(url, {
      body,
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
      },
    }).catch((error) => {
      // Silently fail in production to avoid disrupting user experience
      if (process.env.NODE_ENV !== 'production') {
        console.error('Failed to send web vitals:', error);
      }
    });
  }
}

export function reportWebVitals(onPerfEntry) {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    getCLS(onPerfEntry);
    getFID(onPerfEntry);
    getFCP(onPerfEntry);
    getLCP(onPerfEntry);
    getTTFB(onPerfEntry);
  }

  // In production, send to analytics
  if (
    process.env.REACT_APP_ENV === 'production' &&
    process.env.REACT_APP_PERFORMANCE_MONITORING === 'true'
  ) {
    getCLS(sendToAnalytics);
    getFID(sendToAnalytics);
    getFCP(sendToAnalytics);
    getLCP(sendToAnalytics);
    getTTFB(sendToAnalytics);
  }
}

export default reportWebVitals;
