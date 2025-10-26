import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import CollaborationPage from '../../pages/CollaborationPage';

describe('CollaborationPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <CollaborationPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <CollaborationPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
