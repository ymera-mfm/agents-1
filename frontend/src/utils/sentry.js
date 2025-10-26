/**
 * Sentry error tracking configuration
 * Lazy-loaded only in production environment
 */

export const initSentry = async () => {
  if (process.env.REACT_APP_ENV === 'production' && process.env.REACT_APP_SENTRY_DSN) {
    // Lazy load Sentry only in production
    const [{ default: Sentry }, { BrowserTracing }] = await Promise.all([
      import('@sentry/react'),
      import('@sentry/tracing'),
    ]);

    Sentry.init({
      dsn: process.env.REACT_APP_SENTRY_DSN,
      integrations: [
        new BrowserTracing({
          // Set sampling rate for performance monitoring
          tracePropagationTargets: ['localhost', /^https:\/\/api\.agentflow\.com/],
        }),
      ],
      // Performance Monitoring
      tracesSampleRate: parseFloat(process.env.REACT_APP_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
      // Environment
      environment: process.env.REACT_APP_ENV || 'production',
      // Release tracking
      release: `agentflow@${process.env.REACT_APP_VERSION || '1.0.0'}`,
      // Filter out sensitive data
      beforeSend(event) {
        // Remove cookies and headers for privacy
        if (event.request) {
          delete event.request.cookies;
          delete event.request.headers;
        }
        // Filter out personal information from user data
        if (event.user) {
          delete event.user.email;
          delete event.user.ip_address;
        }
        return event;
      },
      // Ignore certain errors
      ignoreErrors: [
        // Browser extensions
        'top.GLOBALS',
        // Random plugins/extensions
        'originalCreateNotification',
        'canvas.contentDocument',
        'MyApp_RemoveAllHighlights',
        // Facebook related errors
        'fb_xd_fragment',
        // Network errors that are not actionable
        'NetworkError',
        'Non-Error promise rejection captured',
      ],
      // Additional options
      maxBreadcrumbs: 50,
      attachStacktrace: true,
    });
  }
};

export default initSentry;
