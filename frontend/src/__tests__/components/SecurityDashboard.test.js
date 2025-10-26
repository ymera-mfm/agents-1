import React from 'react';
import { render } from '@testing-library/react';
import { SecurityDashboard } from '../../components/SecurityDashboard';

describe('SecurityDashboard', () => {
  it('renders without crashing', () => {
    const { container } = render(<SecurityDashboard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<SecurityDashboard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for SecurityDashboard
});
