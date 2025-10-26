import React from 'react';
import { render } from '@testing-library/react';
import { AgentCollaboration } from '../../components/AgentCollaboration';

describe('AgentCollaboration', () => {
  it('renders without crashing', () => {
    const { container } = render(<AgentCollaboration />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AgentCollaboration />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AgentCollaboration
});
