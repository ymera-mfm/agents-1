import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { store } from './store';
import './styles/index.css';
import './styles/globals.css';
import App from './App';
import { initSentry } from './utils/sentry';
import { initAnalytics } from './utils/analytics';
import reportWebVitals from './reportWebVitals';
import { performanceMonitor } from './utils/performance';

// Initialize error tracking and monitoring in production
initSentry();
initAnalytics();

// Mark app initialization start
performanceMonitor.mark('app-init-start');

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);

// Mark app initialization complete
performanceMonitor.mark('app-init-end');
performanceMonitor.measure('app-initialization', 'app-init-start', 'app-init-end');

// Report web vitals for performance monitoring
reportWebVitals();
