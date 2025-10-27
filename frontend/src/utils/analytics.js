/**
 * Analytics utility for tracking user events and page views
 * Google Analytics integration for production environment
 */

import api from '../services/api';
import logger from '../services/logger';

// Session ID for tracking metrics
const SESSION_ID = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const initAnalytics = () => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    // Google Analytics example
    if (window.gtag) {
      window.gtag('config', process.env.REACT_APP_ANALYTICS_ID, {
        send_page_view: false, // We'll handle page views manually
      });
    }
  }
  
  // Initialize Web Vitals reporting
  initWebVitals();
};

export const trackPageView = (path) => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    if (window.gtag) {
      window.gtag('event', 'page_view', {
        page_path: path,
        page_title: document.title,
      });
    }
  }
};

export const trackEvent = (category, action, label, value) => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    if (window.gtag) {
      window.gtag('event', action, {
        event_category: category,
        event_label: label,
        value: value,
      });
    }
  }
};

export const trackUserTiming = (category, variable, time, label) => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    if (window.gtag) {
      window.gtag('event', 'timing_complete', {
        name: variable,
        value: time,
        event_category: category,
        event_label: label,
      });
    }
  }
};

export const trackException = (description, fatal = false) => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    if (window.gtag) {
      window.gtag('event', 'exception', {
        description: description,
        fatal: fatal,
      });
    }
  }
};

/**
 * Report Web Vitals to backend for centralized analysis
 * Supports CLS, LCP, FID, FCP, TTFB metrics
 */
export const reportWebVitalsToBackend = async (metric) => {
  try {
    const metricData = {
      name: metric.name,
      value: metric.value,
      id: metric.id,
      sessionId: SESSION_ID,
      rating: metric.rating,
      delta: metric.delta,
      navigationType: metric.navigationType,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    // Send to backend asynchronously
    await api.post('/api/v1/metrics/frontend', metricData);
    
    logger.debug('Web Vital reported to backend', metricData);
  } catch (error) {
    // Silently fail to avoid impacting user experience
    logger.error('Failed to report Web Vital to backend', error);
  }
};

/**
 * Initialize Web Vitals monitoring
 * Uses web-vitals library for accurate performance measurements
 */
export const initWebVitals = () => {
  if (typeof window === 'undefined') {
    return;
  }

  // Dynamically import web-vitals to avoid blocking initial load
  import('web-vitals')
    .then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      // Cumulative Layout Shift
      getCLS(reportWebVitalsToBackend);
      
      // First Input Delay
      getFID(reportWebVitalsToBackend);
      
      // First Contentful Paint
      getFCP(reportWebVitalsToBackend);
      
      // Largest Contentful Paint
      getLCP(reportWebVitalsToBackend);
      
      // Time to First Byte
      getTTFB(reportWebVitalsToBackend);
      
      logger.info('Web Vitals monitoring initialized');
    })
    .catch((error) => {
      logger.warn('Failed to initialize Web Vitals', error);
    });
};

const analyticsExport = {
  initAnalytics,
  trackPageView,
  trackEvent,
  trackUserTiming,
  trackException,
  reportWebVitalsToBackend,
  initWebVitals,
};

export default analyticsExport;
