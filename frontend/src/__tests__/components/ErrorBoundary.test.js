import React from 'react';
import { render } from '@testing-library/react';
import { ErrorBoundary } from '../../components/ErrorBoundary';

describe('ErrorBoundary', () => {
  it('renders without crashing', () => {
    const { container } = render(<ErrorBoundary />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ErrorBoundary />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ErrorBoundary
});
