import React from 'react';
import { render } from '@testing-library/react';
import { AudioVisualizer3D } from '../../components/AudioVisualizer3D';

describe('AudioVisualizer3D', () => {
  it('renders without crashing', () => {
    const { container } = render(<AudioVisualizer3D />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<AudioVisualizer3D />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for AudioVisualizer3D
});
