import React from 'react';
import { render } from '@testing-library/react';
import { ConnectionStatus } from '../../../components/common/ConnectionStatus';

describe('ConnectionStatus', () => {
  it('renders without crashing', () => {
    const { container } = render(<ConnectionStatus />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ConnectionStatus />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ConnectionStatus
});
