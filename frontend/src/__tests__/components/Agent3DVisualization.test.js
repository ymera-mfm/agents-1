import React from 'react';
import { render } from '@testing-library/react';
import { Agent3DVisualization } from '../../../components/agents/Agent3DVisualization';

describe('Agent3DVisualization', () => {
  it('renders without crashing', () => {
    const { container } = render(<Agent3DVisualization />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<Agent3DVisualization />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for Agent3DVisualization
});
