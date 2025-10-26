import React from 'react';
import { render } from '@testing-library/react';
import { AgentNetwork3D } from '../../components/AgentNetwork3D';

describe('AgentNetwork3D', () => {
  it('renders without crashing', () => {
    const { container } = render(<AgentNetwork3D />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AgentNetwork3D />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AgentNetwork3D
});
