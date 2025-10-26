import React from 'react';
import { render } from '@testing-library/react';
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton';

describe('LoadingSkeleton', () => {
  it('renders without crashing', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for LoadingSkeleton
});
