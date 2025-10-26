import React from 'react';
import { render } from '@testing-library/react';
import { ResourceManager } from '../../components/ResourceManager';

describe('ResourceManager', () => {
  it('renders without crashing', () => {
    const { container } = render(<ResourceManager />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ResourceManager />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ResourceManager
});
