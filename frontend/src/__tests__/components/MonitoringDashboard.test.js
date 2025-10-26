import React from 'react';
import { render } from '@testing-library/react';
import { MonitoringDashboard } from '../../components/MonitoringDashboard';

describe('MonitoringDashboard', () => {
  it('renders without crashing', () => {
    const { container } = render(<MonitoringDashboard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<MonitoringDashboard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for MonitoringDashboard
});
