import React from 'react';
import { render } from '@testing-library/react';
import { AgentTrainingInterface } from '../../components/AgentTrainingInterface';

describe('AgentTrainingInterface', () => {
  it('renders without crashing', () => {
    const { container } = render(<AgentTrainingInterface />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AgentTrainingInterface />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AgentTrainingInterface
});
