import React from 'react';
import { render } from '@testing-library/react';
import { PredictiveAnalytics } from '../../components/PredictiveAnalytics';

describe('PredictiveAnalytics', () => {
  it('renders without crashing', () => {
    const { container } = render(<PredictiveAnalytics />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<PredictiveAnalytics />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for PredictiveAnalytics
});
