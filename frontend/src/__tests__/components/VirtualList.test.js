import React from 'react';
import { render } from '@testing-library/react';
import { VirtualList } from '../../../components/common/VirtualList';

describe('VirtualList', () => {
  it('renders without crashing', () => {
    const { container } = render(<VirtualList />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<VirtualList />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for VirtualList
});
