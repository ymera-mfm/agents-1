import React from 'react';
import { render } from '@testing-library/react';
import { DeploymentDashboard } from '../../components/DeploymentDashboard';

describe('DeploymentDashboard', () => {
  it('renders without crashing', () => {
    const { container } = render(<DeploymentDashboard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<DeploymentDashboard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for DeploymentDashboard
});
