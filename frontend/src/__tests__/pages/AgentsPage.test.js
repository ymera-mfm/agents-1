import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import AgentsPage from '../../pages/AgentsPage';

describe('AgentsPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <AgentsPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <AgentsPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
