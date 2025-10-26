import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ProfilePage from '../../pages/ProfilePage';

describe('ProfilePage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <ProfilePage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <ProfilePage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
