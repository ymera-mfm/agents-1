import React from 'react';
import { render } from '@testing-library/react';
import { Toast } from '../../../components/common/Toast';

describe('Toast', () => {
  it('renders without crashing', () => {
    const { container } = render(<Toast />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<Toast />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for Toast
});
