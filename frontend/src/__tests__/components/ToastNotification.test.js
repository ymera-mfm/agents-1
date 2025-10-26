import React from 'react';
import { render } from '@testing-library/react';
import { ToastNotification } from '../../../components/common/ToastNotification';

describe('ToastNotification', () => {
  it('renders without crashing', () => {
    const { container } = render(<ToastNotification />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ToastNotification />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ToastNotification
});
