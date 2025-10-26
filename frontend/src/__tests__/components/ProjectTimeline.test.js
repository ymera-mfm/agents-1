import React from 'react';
import { render } from '@testing-library/react';
import { ProjectTimeline } from '../../components/ProjectTimeline';

describe('ProjectTimeline', () => {
  it('renders without crashing', () => {
    const { container } = render(<ProjectTimeline />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ProjectTimeline />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ProjectTimeline
});
