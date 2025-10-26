import React from 'react';
import { render } from '@testing-library/react';
import { Project3DVisualization } from '../../../components/projects/Project3DVisualization';

describe('Project3DVisualization', () => {
  it('renders without crashing', () => {
    const { container } = render(<Project3DVisualization />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<Project3DVisualization />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for Project3DVisualization
});
