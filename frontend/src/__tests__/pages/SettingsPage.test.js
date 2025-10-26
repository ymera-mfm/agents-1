import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import SettingsPage from '../../pages/SettingsPage';

describe('SettingsPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <SettingsPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <SettingsPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
