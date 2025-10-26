import { configureStore } from '@reduxjs/toolkit';
import agentsReducer from '../features/agents/agentsSlice';
import projectsReducer from '../features/projects/projectsSlice';

export const store = configureStore({
  reducer: {
    agents: agentsReducer,
    projects: projectsReducer,
  },
});
