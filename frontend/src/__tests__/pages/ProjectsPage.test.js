import React from 'react';
import { render } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ProjectsPage from '../../pages/ProjectsPage';

describe('ProjectsPage', () => {
  it('renders without crashing', () => {
    const { container } = render(
      <AppProvider>
        <ProjectsPage />
      </AppProvider>
    );
    expect(container).toBeInTheDocument();
  });

  it('matches snapshot', () => {
    const { container } = render(
      <AppProvider>
        <ProjectsPage />
      </AppProvider>
    );
    expect(container).toMatchSnapshot();
  });
});
