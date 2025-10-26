import React from 'react';
import { render } from '@testing-library/react';
import { ParticleBackground } from '../../../components/common/ParticleBackground';

describe('ParticleBackground', () => {
  it('renders without crashing', () => {
    const { container } = render(<ParticleBackground />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ParticleBackground />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ParticleBackground
});
