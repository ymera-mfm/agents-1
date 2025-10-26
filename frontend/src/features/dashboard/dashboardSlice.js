import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { collection, getDocs } from 'firebase/firestore';
import { db } from '../../utils/firebase';

export const fetchDashboardStats = createAsyncThunk('dashboard/fetchStats', async () => {
  const [agentsSnapshot, projectsSnapshot] = await Promise.all([
    getDocs(collection(db, 'agents')),
    getDocs(collection(db, 'projects')),
  ]);

  const agents = agentsSnapshot.docs.map((doc) => doc.data());
  const projects = projectsSnapshot.docs.map((doc) => doc.data());

  return {
    totalAgents: agents.length,
    activeAgents: agents.filter((a) => a.status === 'working' || a.status === 'thinking').length,
    idleAgents: agents.filter((a) => a.status === 'idle').length,
    completedAgents: agents.filter((a) => a.status === 'completed').length,
    totalProjects: projects.length,
    activeProjects: projects.filter((p) => p.status === 'in_progress').length,
    recentActivities: [
      { id: 1, text: 'Agent Alpha completed code analysis', time: '2m ago', type: 'agent' },
      { id: 2, text: 'Project Beta entered testing phase', time: '15m ago', type: 'project' },
      { id: 3, text: 'Agent Gamma optimized queries', time: '1h ago', type: 'agent' },
      { id: 4, text: 'Deployment scheduled for Project Delta', time: '3h ago', type: 'project' },
    ],
    systemStatus: {
      api: { status: 'operational', responseTime: '45ms' },
      database: { status: 'healthy', uptime: '99.9%' },
      queue: { status: 'active', tasksPerMin: 234 },
    },
  };
});

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: {
    stats: null,
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardStats.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.stats = action.payload;
      })
      .addCase(fetchDashboardStats.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  },
});

export default dashboardSlice.reducer;
