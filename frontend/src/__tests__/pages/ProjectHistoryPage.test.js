import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ProjectHistoryPage from '../../pages/ProjectHistoryPage';

describe('ProjectHistoryPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <ProjectHistoryPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <ProjectHistoryPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
