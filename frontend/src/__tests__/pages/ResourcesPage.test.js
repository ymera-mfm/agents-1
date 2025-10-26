import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ResourcesPage from '../../pages/ResourcesPage';

describe('ResourcesPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <ResourcesPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <ResourcesPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
