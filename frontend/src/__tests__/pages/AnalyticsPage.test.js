import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import AnalyticsPage from '../../pages/AnalyticsPage';

describe('AnalyticsPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <AnalyticsPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <AnalyticsPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
