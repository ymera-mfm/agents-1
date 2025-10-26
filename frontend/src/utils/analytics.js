/**
 * Analytics utility for tracking user events and page views
 * Google Analytics integration for production environment
 */

export const initAnalytics = () => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_ANALYTICS_ID) {
    // Google Analytics example
    if (window.gtag) {
      window.gtag('config', process.env.REACT_APP_ANALYTICS_ID, {
        send_page_view: false, // We'll handle page views manually
      });
    }
  }
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

const analyticsExport = {
  initAnalytics,
  trackPageView,
  trackEvent,
  trackUserTiming,
  trackException,
};

export default analyticsExport;
