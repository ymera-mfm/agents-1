// components/ResourceManager.jsx
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Users, Cpu, Calendar, TrendingUp, AlertTriangle } from 'lucide-react';

export const ResourceManager = ({ projects, agents, onResourceAllocation }) => {
  const [selectedResource, setSelectedResource] = useState(null);
  const [allocations, setAllocations] = useState({});

  // Calculate resource utilization
  const resourceUtilization = useMemo(() => {
    const utilization = {
      agents: {},
      projects: {},
      overall: 0,
    };

    // Calculate agent utilization
    agents.forEach((agent) => {
      const agentProjects = projects.filter((p) => p.assignedAgents?.includes(agent.id));
      utilization.agents[agent.id] = {
        current: agentProjects.length,
        capacity: 3, // Max projects per agent
        utilization: (agentProjects.length / 3) * 100,
      };
    });

    // Calculate project resource needs
    projects.forEach((project) => {
      utilization.projects[project.id] = {
        requiredAgents: project.requiredAgents || 1,
        allocatedAgents: project.assignedAgents?.length || 0,
        satisfaction: ((project.assignedAgents?.length || 0) / (project.requiredAgents || 1)) * 100,
      };
    });

    // Overall utilization
    const totalUtilization = Object.values(utilization.agents).reduce(
      (sum, agent) => sum + agent.utilization,
      0
    );
    utilization.overall = totalUtilization / agents.length;

    return utilization;
  }, [projects, agents]);

  const overallocatedAgents = useMemo(() => {
    return agents.filter((agent) => resourceUtilization.agents[agent.id]?.utilization > 100);
  }, [agents, resourceUtilization]);

  const underallocatedProjects = useMemo(() => {
    return projects.filter(
      (project) => resourceUtilization.projects[project.id]?.satisfaction < 50
    );
  }, [projects, resourceUtilization]);

  const handleDragStart = (agent, project) => {
    setSelectedResource({ type: 'agent', agent, sourceProject: project });
  };

  const handleDrop = (targetProject) => {
    if (selectedResource && selectedResource.type === 'agent') {
      const newAllocations = { ...allocations };

      // Remove from source project
      if (selectedResource.sourceProject) {
        const sourceAllocations = newAllocations[selectedResource.sourceProject.id] || [];
        newAllocations[selectedResource.sourceProject.id] = sourceAllocations.filter(
          (id) => id !== selectedResource.agent.id
        );
      }

      // Add to target project
      const targetAllocations = newAllocations[targetProject.id] || [];
      if (!targetAllocations.includes(selectedResource.agent.id)) {
        newAllocations[targetProject.id] = [...targetAllocations, selectedResource.agent.id];
      }

      setAllocations(newAllocations);
      onResourceAllocation(newAllocations);
    }

    setSelectedResource(null);
  };

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">Resource Management</h3>
          <p className="text-gray-400">Optimize agent allocation across projects</p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Overall Utilization</div>
            <div className="text-2xl font-bold text-white">
              {resourceUtilization.overall.toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* Resource Alerts */}
      {(overallocatedAgents.length > 0 || underallocatedProjects.length > 0) && (
        <div className="mb-6 space-y-3">
          {overallocatedAgents.length > 0 && (
            <div className="flex items-center space-x-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <div>
                <div className="text-red-400 font-semibold">Overallocated Agents</div>
                <div className="text-red-300 text-sm">
                  {overallocatedAgents.map((a) => a.name).join(', ')} are assigned to too many
                  projects
                </div>
              </div>
            </div>
          )}

          {underallocatedProjects.length > 0 && (
            <div className="flex items-center space-x-3 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              <div>
                <div className="text-yellow-400 font-semibold">Under-resourced Projects</div>
                <div className="text-yellow-300 text-sm">
                  {underallocatedProjects.map((p) => p.name).join(', ')} need more agents
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Resources */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center space-x-2">
            <Users className="w-5 h-5" />
            <span>Available Agents</span>
          </h4>

          <div className="space-y-3">
            {agents.map((agent) => {
              const utilization = resourceUtilization.agents[agent.id];
              return (
                <motion.div
                  key={agent.id}
                  draggable
                  onDragStart={() => handleDragStart(agent)}
                  className={`p-4 rounded-lg border-2 cursor-move ${
                    utilization?.utilization > 100
                      ? 'border-red-500/50 bg-red-500/10'
                      : utilization?.utilization > 80
                        ? 'border-yellow-500/50 bg-yellow-500/10'
                        : 'border-white/10 bg-white/5'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileDrag={{ scale: 1.05, opacity: 0.8 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${agent.color}20` }}
                      >
                        <Cpu className="w-5 h-5" style={{ color: agent.color }} />
                      </div>
                      <div>
                        <div className="font-semibold text-white">{agent.name}</div>
                        <div className="text-sm text-gray-400 capitalize">{agent.type}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Utilization</div>
                      <div
                        className={`font-semibold ${
                          utilization?.utilization > 100
                            ? 'text-red-400'
                            : utilization?.utilization > 80
                              ? 'text-yellow-400'
                              : 'text-green-400'
                        }`}
                      >
                        {utilization?.utilization.toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(utilization?.utilization || 0, 100)}%`,
                        backgroundColor:
                          utilization?.utilization > 100
                            ? '#ef4444'
                            : utilization?.utilization > 80
                              ? '#eab308'
                              : '#10b981',
                      }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Project Requirements */}
        <div className="space-y-4">
          <h4 className="text-lg font-semibold text-white flex items-center space-x-2">
            <Calendar className="w-5 h-5" />
            <span>Project Requirements</span>
          </h4>

          <div className="space-y-3">
            {projects.map((project) => {
              const requirements = resourceUtilization.projects[project.id];
              return (
                <motion.div
                  key={project.id}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={() => handleDrop(project)}
                  className={`p-4 rounded-lg border-2 ${
                    requirements?.satisfaction < 50
                      ? 'border-yellow-500/50 bg-yellow-500/10'
                      : 'border-white/10 bg-white/5'
                  }`}
                  whileHover={{ scale: 1.01 }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <div className="font-semibold text-white">{project.name}</div>
                      <div className="text-sm text-gray-400">
                        {requirements?.allocatedAgents || 0} / {requirements?.requiredAgents || 1}{' '}
                        agents
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Satisfaction</div>
                      <div
                        className={`font-semibold ${
                          requirements?.satisfaction < 50 ? 'text-yellow-400' : 'text-green-400'
                        }`}
                      >
                        {requirements?.satisfaction.toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="w-full bg-gray-700 rounded-full h-2 mb-3">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 transition-all duration-500"
                      style={{ width: `${requirements?.satisfaction || 0}%` }}
                    />
                  </div>

                  {/* Assigned Agents */}
                  <div className="flex flex-wrap gap-2">
                    {agents
                      .filter((agent) => allocations[project.id]?.includes(agent.id))
                      .map((agent) => (
                        <div
                          key={agent.id}
                          className="flex items-center space-x-2 px-2 py-1 bg-white/5 rounded text-sm"
                        >
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: agent.color }}
                          />
                          <span className="text-white">{agent.name}</span>
                        </div>
                      ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Resource Optimization Suggestions */}
      <div className="mt-6 p-4 bg-white/5 rounded-lg">
        <h4 className="text-lg font-semibold text-white mb-3 flex items-center space-x-2">
          <TrendingUp className="w-5 h-5" />
          <span>Optimization Suggestions</span>
        </h4>

        <div className="space-y-2 text-sm text-gray-300">
          {overallocatedAgents.length > 0 && (
            <div>• Reallocate work from overloaded agents to balance utilization</div>
          )}
          {underallocatedProjects.length > 0 && (
            <div>• Assign more agents to under-resourced projects</div>
          )}
          {resourceUtilization.overall < 60 && (
            <div>• Consider taking on more projects - current utilization is low</div>
          )}
        </div>
      </div>
    </div>
  );
};
