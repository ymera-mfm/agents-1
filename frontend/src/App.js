import React, { Suspense, lazy } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import { AppProvider, useApp } from './store/AppContext';
import { ParticleBackground } from './components/common/ParticleBackground';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { PerformanceDashboard } from './components/performance/PerformanceDashboard';

// Lazy load pages for better performance
const LoginPage = lazy(() => import('./features/auth/LoginPage'));
const Dashboard = lazy(() =>
  import('./features/dashboard/DashboardPage').then((module) => ({ default: module.DashboardPage }))
);
const AgentsPage = lazy(() =>
  import('./features/agents/AgentsPage').then((module) => ({ default: module.AgentsPage }))
);
const ProjectsPage = lazy(() =>
  import('./features/projects/ProjectsPage').then((module) => ({ default: module.ProjectsPage }))
);
const CollaborationPage = lazy(() =>
  import('./pages/CollaborationPage').then((module) => ({ default: module.CollaborationPage }))
);
const AnalyticsPage = lazy(() =>
  import('./features/analytics/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage }))
);
const ResourcesPage = lazy(() =>
  import('./pages/ResourcesPage').then((module) => ({ default: module.ResourcesPage }))
);
const SettingsPage = lazy(() => import('./features/settings/SettingsPage'));
const ProfilePage = lazy(() =>
  import('./features/profile/ProfilePage').then((module) => ({ default: module.ProfilePage }))
);
const MonitoringPage = lazy(() => import('./pages/MonitoringPage'));
const CommandPage = lazy(() =>
  import('./pages/CommandPage').then((module) => ({ default: module.CommandPage }))
);
const ProjectHistoryPage = lazy(() =>
  import('./features/projects/ProjectHistoryPage').then((module) => ({
    default: module.ProjectHistoryPage,
  }))
);
const Navigation = lazy(() => import('./components/Navigation'));

function AgentFlowApp() {
  const { page, user } = useApp();

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 relative">
        {/* Background layer - fixed canvas (z-0) */}
        <ParticleBackground />

        {/* Content must sit above the background */}
        <div className="relative z-10">
          {!user ? (
            <Suspense fallback={<LoadingSpinner />}>
              <LoginPage />
            </Suspense>
          ) : (
            <>
              <Suspense fallback={<LoadingSpinner />}>
                <Navigation />
                {page === 'dashboard' && <Dashboard />}
                {page === 'agents' && <AgentsPage />}
                {page === 'projects' && <ProjectsPage />}
                {page === 'profile' && <ProfilePage />}
                {page === 'monitoring' && <MonitoringPage />}
                {page === 'command' && <CommandPage />}
                {page === 'project-history' && <ProjectHistoryPage />}
                {page === 'collaboration' && <CollaborationPage />}
                {page === 'analytics' && <AnalyticsPage />}
                {page === 'resources' && <ResourcesPage />}
                {page === 'settings' && <SettingsPage />}
              </Suspense>
            </>
          )}
        </div>

        {/* Performance Dashboard (development only) */}
        <PerformanceDashboard />
      </div>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <AppProvider>
      <AgentFlowApp />
    </AppProvider>
  );
}

export default App;
