import React, { createContext, useContext, useState, useMemo, useCallback } from 'react';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';
import { cacheService } from '../services/cache';

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('login');
  const [agents, setAgents] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [collaborationSessions, setCollaborationSessions] = useState([]);
  const [resourceAllocations, setResourceAllocations] = useState({});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);

      // Mock data for demo
      const agentsData = [
        {
          id: 1,
          name: 'DataMiner Pro',
          status: 'working',
          type: 'data',
          efficiency: 94,
          tasks: 23,
          color: '#00f5ff',
        },
        {
          id: 2,
          name: 'CodeWeaver',
          status: 'thinking',
          type: 'dev',
          efficiency: 88,
          tasks: 15,
          color: '#ff3366',
        },
        {
          id: 3,
          name: 'CloudOrchestrator',
          status: 'idle',
          type: 'cloud',
          efficiency: 91,
          tasks: 8,
          color: '#00ff88',
        },
        {
          id: 4,
          name: 'SecurityGuard',
          status: 'working',
          type: 'security',
          efficiency: 96,
          tasks: 31,
          color: '#ffd700',
        },
      ];

      const projectsData = [
        {
          id: 1,
          name: 'E-Commerce Platform',
          description: 'Building a scalable e-commerce solution',
          status: 'in_progress',
          progress: 67,
          assignedAgents: [1, 2],
          requiredAgents: 2,
          team: 5,
          budget: 100000,
          spent: 67000,
          milestones: [
            {
              id: 1,
              name: 'Requirements Gathering',
              duration: 14,
              startDate: '2024-01-01',
              progress: 100,
              completed: true,
            },
            {
              id: 2,
              name: 'UI/UX Design',
              duration: 21,
              startDate: '2024-01-15',
              progress: 100,
              completed: true,
            },
            {
              id: 3,
              name: 'Backend Development',
              duration: 35,
              startDate: '2024-02-05',
              progress: 75,
              completed: false,
            },
          ],
          phases: [
            { id: 1, name: 'Analysis', status: 'completed', progress: 100, color: '#10b981' },
            { id: 2, name: 'Design', status: 'completed', progress: 100, color: '#3b82f6' },
            { id: 3, name: 'Development', status: 'in_progress', progress: 60, color: '#f59e0b' },
          ],
        },
      ];

      setAgents(agentsData);
      setProjects(projectsData);

      cacheService.set('agents', agentsData);
      cacheService.set('projects', projectsData);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(
    async (username, _password) => {
      try {
        setLoading(true);
        setError(null);

        // Mock login for demo
        const mockUser = {
          id: Date.now(),
          name: username,
          avatar: username[0].toUpperCase(),
          email: `${username}@agentflow.com`,
          bio: 'This is a demo user profile for the AgentFlow application.',
        };

        setUser(mockUser);
        setPage('dashboard');
        await loadData();
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [loadData]
  );

  const logout = useCallback(() => {
    setUser(null);
    setPage('login');
    apiService.setToken(null);
    websocketService.disconnect();
    cacheService.clear();
    setAgents([]);
    setProjects([]);
  }, []);

  const updateAgentStatus = useCallback((id, status) => {
    setAgents((prev) => prev.map((agent) => (agent.id === id ? { ...agent, status } : agent)));
  }, []);

  const handleResourceAllocation = useCallback((allocations) => {
    setResourceAllocations(allocations);
    setProjects((prev) =>
      prev.map((project) => ({
        ...project,
        assignedAgents: allocations[project.id] || project.assignedAgents,
      }))
    );
  }, []);

  const addCollaborationSession = useCallback((session) => {
    setCollaborationSessions((prev) => [...prev, session]);
  }, []);

  const value = useMemo(
    () => ({
      user,
      login,
      logout,
      page,
      setPage,
      agents,
      setAgents,
      projects,
      setProjects,
      loading,
      error,
      notifications,
      setNotifications,
      collaborationSessions,
      addCollaborationSession,
      resourceAllocations,
      handleResourceAllocation,
      updateAgentStatus,
    }),
    [
      user,
      page,
      agents,
      projects,
      loading,
      error,
      notifications,
      collaborationSessions,
      resourceAllocations,
      login,
      logout,
      addCollaborationSession,
      handleResourceAllocation,
      updateAgentStatus,
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
