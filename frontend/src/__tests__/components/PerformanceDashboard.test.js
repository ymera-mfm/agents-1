import React from 'react';
import { render } from '@testing-library/react';
import { PerformanceDashboard } from '../../components/PerformanceDashboard';

describe('PerformanceDashboard', () => {
  it('renders without crashing', () => {
    const { container } = render(<PerformanceDashboard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<PerformanceDashboard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for PerformanceDashboard
});
