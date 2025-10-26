import React from 'react';
import { render } from '@testing-library/react';
import { AgentCard } from '../../../components/agents/AgentCard';

describe('AgentCard', () => {
  it('renders without crashing', () => {
    const { container } = render(<AgentCard />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AgentCard />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AgentCard
});
