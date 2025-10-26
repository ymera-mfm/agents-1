// store/index.js
import { configureStore, createSlice } from '@reduxjs/toolkit';
import { useSelector, useDispatch } from 'react-redux';
import dashboardReducer from '../features/dashboard/dashboardSlice';

const agentsSlice = createSlice({
  name: 'agents',
  initialState: {
    items: [],
    loading: false,
    error: null,
    selectedAgent: null,
    filters: { status: 'all', searchTerm: '' },
  },
  reducers: {
    setAgents: (state, action) => {
      state.items = action.payload;
    },
    updateAgentStatus: (state, action) => {
      const { id, status } = action.payload;
      const agent = state.items.find((agent) => agent.id === id);
      if (agent) {
        agent.status = status;
      }
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
  },
});

const projectsSlice = createSlice({
  name: 'projects',
  initialState: {
    items: [],
    activeProject: null,
    viewMode: 'grid',
  },
  reducers: {
    setProjects: (state, action) => {
      state.items = action.payload;
    },
    updateProjectProgress: (state, action) => {
      const { id, progress } = action.payload;
      const project = state.items.find((project) => project.id === id);
      if (project) {
        project.progress = progress;
      }
    },
  },
});

export const store = configureStore({
  reducer: {
    agents: agentsSlice.reducer,
    projects: projectsSlice.reducer,
    dashboard: dashboardReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export const useAppSelector = useSelector;
export const useAppDispatch = useDispatch;
