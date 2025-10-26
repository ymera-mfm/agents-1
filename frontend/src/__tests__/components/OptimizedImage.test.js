import React from 'react';
import { render } from '@testing-library/react';
import { OptimizedImage } from '../../../components/common/OptimizedImage';

describe('OptimizedImage', () => {
  it('renders without crashing', () => {
    const { container } = render(<OptimizedImage />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<OptimizedImage />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for OptimizedImage
});
