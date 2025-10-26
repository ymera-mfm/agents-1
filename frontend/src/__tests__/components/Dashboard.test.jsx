import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Dashboard } from '../../pages/Dashboard';
import { AppProvider } from '../../context/AppContext';

// Mock the context
const mockContextValue = {
  agents: [
    {
      id: 1,
      name: 'Test Agent',
      status: 'working',
      tasks: 5,
      efficiency: 95,
      color: '#00f5ff',
    },
  ],
  projects: [
    {
      id: 1,
      name: 'Test Project',
      status: 'in_progress',
    },
  ],
  loading: false,
  user: { id: 1, name: 'Test User' },
};

const DashboardWrapper = () => (
  <AppProvider value={mockContextValue}>
    <Dashboard />
  </AppProvider>
);

describe('Dashboard Page', () => {
  test('renders dashboard without crashing', () => {
    render(<DashboardWrapper />);
    expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
  });

  test('displays stat cards', () => {
    render(<DashboardWrapper />);

    // Check for stat card elements
    const statElements = screen.queryAllByText(/active|tasks|efficiency/i);
    expect(statElements.length).toBeGreaterThan(0);
  });

  test('shows loading state when loading is true', () => {
    const loadingContext = {
      ...mockContextValue,
      loading: true,
    };

    render(
      <AppProvider value={loadingContext}>
        <Dashboard />
      </AppProvider>
    );

    // Should show loading spinner or indicator
    const loadingElement =
      screen.getByRole('status', { hidden: true }) || screen.getByTestId('loading-spinner');
    expect(loadingElement).toBeInTheDocument();
  });

  test('displays agent information', () => {
    render(<DashboardWrapper />);

    // Check if agent name is displayed
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });
});
