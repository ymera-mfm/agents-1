import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Navigation from '../../components/Navigation';
import { AppProvider } from '../../context/AppContext';

// Mock the context with a logged-in user
const mockContextValue = {
  user: {
    id: 1,
    name: 'Test User',
    avatar: 'T',
    email: 'test@agentflow.com',
  },
  page: 'dashboard',
  setPage: jest.fn(),
  logout: jest.fn(),
};

// Wrapper component with context
const NavigationWrapper = ({ children }) => (
  <AppProvider value={mockContextValue}>{children}</AppProvider>
);

describe('Navigation Component', () => {
  test('renders navigation component', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    // Check if logo/brand is present
    const brandElement =
      screen.queryByText(/agentflow/i) || screen.queryByRole('img', { name: /logo/i });
    expect(brandElement).toBeTruthy();
  });

  test('displays user information when logged in', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    // User name or avatar should be visible
    const userElement = screen.queryByText(/test user/i) || screen.queryByText('T');
    expect(userElement).toBeTruthy();
  });

  test('has navigation links', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    // Check for common navigation elements
    const navElement = screen.getByRole('navigation');
    expect(navElement).toBeInTheDocument();
  });
});
