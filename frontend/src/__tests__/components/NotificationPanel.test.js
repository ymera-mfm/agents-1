import React from 'react';
import { render } from '@testing-library/react';
import { NotificationPanel } from '../../../components/common/NotificationPanel';

describe('NotificationPanel', () => {
  it('renders without crashing', () => {
    const { container } = render(<NotificationPanel />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<NotificationPanel />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for NotificationPanel
});
