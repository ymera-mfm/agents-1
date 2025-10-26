import { createSlice } from '@reduxjs/toolkit';

const initialAgents = [
  {
    id: 'agent-001',
    name: 'CodeAnalyzer Alpha',
    type: 'code-analyzer',
    status: 'working',
    description: 'Advanced code analysis and optimization specialist',
    tasksCompleted: 247,
    efficiency: 98.5,
    icon: 'Code',
    color: '#00f5ff',
  },
  {
    id: 'agent-002',
    name: 'UIDesigner Beta',
    type: 'ui-designer',
    status: 'thinking',
    description: 'Creative interface design and user experience expert',
    tasksCompleted: 156,
    efficiency: 96.2,
    icon: 'Camera',
    color: '#ff00aa',
  },
  {
    id: 'agent-003',
    name: 'BackendDev Gamma',
    type: 'backend-dev',
    status: 'idle',
    description: 'Backend systems and API development specialist',
    tasksCompleted: 189,
    efficiency: 99.1,
    icon: 'Database',
    color: '#00ff88',
  },
];

const agentsSlice = createSlice({
  name: 'agents',
  initialState: initialAgents,
  reducers: {
    updateStatus: (state, action) => {
      const { id, status } = action.payload;
      return state.map((agent) => (agent.id === id ? { ...agent, status } : agent));
    },
    addAgent: (state, action) => {
      state.push(action.payload);
    },
    removeAgent: (state, action) => {
      return state.filter((agent) => agent.id !== action.payload);
    },
  },
});

export const { updateStatus, addAgent, removeAgent } = agentsSlice.actions;
export default agentsSlice.reducer;
