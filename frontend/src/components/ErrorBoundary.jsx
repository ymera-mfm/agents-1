// components/ErrorBoundary.jsx
import React from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(_error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });

    // Log error to monitoring service
    this.logError(error, errorInfo);
  }

  logError = (error, errorInfo) => {
    const errorData = {
      message: error.toString(),
      stack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // Send to error tracking service
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorData),
    }).catch(console.error);
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 to-black p-4">
          <div className="max-w-md w-full backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>

            <h2 className="text-2xl font-bold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 mb-6">
              We encountered an unexpected error. Our team has been notified.
            </p>

            <div className="space-y-3">
              <button
                onClick={this.handleReset}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-cyan-500/20 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500/30 transition"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>

              <button
                onClick={this.handleGoHome}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white hover:bg-white/10 transition"
              >
                <Home className="w-4 h-4" />
                <span>Go Home</span>
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-6 text-left">
                <summary className="text-sm text-gray-400 cursor-pointer">
                  Error Details (Development)
                </summary>
                <div className="mt-2 p-3 bg-black/50 rounded-lg overflow-auto max-h-40">
                  <pre className="text-xs text-red-400">
                    {this.state.error && this.state.error.toString()}
                    {'\n'}
                    {this.state.errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// hooks/useErrorHandler.js
// eslint-disable-next-line import/first
import { useCallback } from 'react';

export const useErrorHandler = () => {
  const handleError = useCallback((error, context = {}) => {
    const errorData = {
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
      url: window.location.href,
    };

    // Send to error tracking service
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorData),
    }).catch(console.error);

    // Show user-friendly notification
    console.error('Application Error:', error);
  }, []);

  return { handleError };
};
