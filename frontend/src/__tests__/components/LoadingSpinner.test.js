import React from 'react';
import { render } from '@testing-library/react';
import { LoadingSpinner } from '../../../components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders without crashing', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for LoadingSpinner
});
