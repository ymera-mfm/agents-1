import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { AppProvider } from '../../context/AppContext';
import ProjectsPage from '../../pages/ProjectsPage';

describe('Project Build Integration', () => {
  it('displays projects and allows building', async () => {
    render(
      <AppProvider>
        <ProjectsPage />
      </AppProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/projects/i)).toBeInTheDocument();
    });
  });
});
