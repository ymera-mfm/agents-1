import React from 'react';
import { render } from '@testing-library/react';
import { DevTools } from '../../components/DevTools';

describe('DevTools', () => {
  it('renders without crashing', () => {
    const { container } = render(<DevTools />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<DevTools />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for DevTools
});
