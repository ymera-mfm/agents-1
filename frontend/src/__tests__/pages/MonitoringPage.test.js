import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import MonitoringPage from '../../pages/MonitoringPage';

describe('MonitoringPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <MonitoringPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <MonitoringPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
