import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import LoginPage from '../../pages/LoginPage';

describe('LoginPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <LoginPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <LoginPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
