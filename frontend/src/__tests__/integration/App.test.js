import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock dependencies
jest.mock('../context/AppContext', () => ({
  AppProvider: ({ children }) => <div data-testid="app-provider">{children}</div>,
}));

jest.mock('../components/common/ErrorBoundary', () => ({
  ErrorBoundary: ({ children }) => <div data-testid="error-boundary">{children}</div>,
}));

jest.mock('../components/common/ParticleBackground', () => ({
  ParticleBackground: () => <div data-testid="particle-background">ParticleBackground</div>,
}));

jest.mock('../components/common/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}));

describe('App Component', () => {
  it('renders without crashing', () => {
    const { container } = render(<App />);
    expect(container).toBeInTheDocument();
  });

  it('provides application context', () => {
    render(<App />);
    expect(screen.getByTestId('app-provider')).toBeInTheDocument();
  });

  it('includes error boundary', () => {
    render(<App />);
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
  });
});
