import React from 'react';
import { render } from '@testing-library/react';
import { ErrorBoundaryAlt } from '../../../components/common/ErrorBoundaryAlt';

describe('ErrorBoundaryAlt', () => {
  it('renders without crashing', () => {
    const { container } = render(<ErrorBoundaryAlt />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ErrorBoundaryAlt />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ErrorBoundaryAlt
});
