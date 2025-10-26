import React from 'react';
import { render } from '@testing-library/react';
import { Agent3DView } from '../../../components/agents/Agent3DView';

describe('Agent3DView', () => {
  it('renders without crashing', () => {
    const { container } = render(<Agent3DView />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<Agent3DView />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for Agent3DView
});
