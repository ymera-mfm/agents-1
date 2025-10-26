import React from 'react';
import { render } from '@testing-library/react';
import { AdvancedAnalytics } from '../../components/AdvancedAnalytics';

describe('AdvancedAnalytics', () => {
  it('renders without crashing', () => {
    const { container } = render(<AdvancedAnalytics />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AdvancedAnalytics />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AdvancedAnalytics
});
