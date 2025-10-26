import React from 'react';
import { render } from '@testing-library/react';
import { ParticleEffects } from '../../components/ParticleEffects';

describe('ParticleEffects', () => {
  it('renders without crashing', () => {
    const { container } = render(<ParticleEffects />);
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(<ParticleEffects />);
    expect(container).toMatchSnapshot();
  });

  // Add more specific tests for ParticleEffects
});
