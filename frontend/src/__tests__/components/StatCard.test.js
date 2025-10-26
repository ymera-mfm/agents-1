import React from 'react';
import { render } from '@testing-library/react';
import { StatCard } from '../../../components/common/StatCard';

describe('StatCard', () => {
  it('renders without crashing', () => {
    const { container } = render(<StatCard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<StatCard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for StatCard
});
