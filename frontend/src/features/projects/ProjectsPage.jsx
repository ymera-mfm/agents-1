import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { ProjectCard } from '../../components/ProjectCard';
import { ProjectDetailModal } from '../../components/ProjectDetailModal';
import { AddProjectModal } from '../../components/AddProjectModal';
import { fetchProjects, addProject, updateProject } from './projectsSlice';
import {
  Search,
  Plus,
  AlertCircle,
  Folder,
  Calendar,
  Activity,
  Pause,
  CheckCircle,
  TrendingUp,
  Edit,
  Trash2,
} from 'lucide-react';

export const ProjectsPage = () => {
  const dispatch = useDispatch();
  const projects = useSelector((state) => state.projects.data);
  const agents = useSelector((state) => state.agents.data);
  const [selectedProject, setSelectedProject] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showAddProject, setShowAddProject] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [menuProject, setMenuProject] = useState(null);

  useEffect(() => {
    dispatch(fetchProjects());
  }, [dispatch]);

  const filteredProjects = projects.filter((project) => {
    const matchesSearch =
      project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = filterStatus === 'all' || project.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const statusCounts = {
    all: projects.length,
    planning: projects.filter((p) => p.status === 'planning').length,
    in_progress: projects.filter((p) => p.status === 'in_progress').length,
    on_hold: projects.filter((p) => p.status === 'on_hold').length,
    completed: projects.filter((p) => p.status === 'completed').length,
  };

  const handleAddAgent = (projectId, agentId) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      const updatedAgents = [...(project.assignedAgents || []), agentId];
      dispatch(
        updateProject({
          id: projectId,
          updates: { assignedAgents: updatedAgents },
        })
      );
    }
  };

  const handleRemoveAgent = (projectId, agentId) => {
    const project = projects.find((p) => p.id === projectId);
    if (project) {
      const updatedAgents = (project.assignedAgents || []).filter((id) => id !== agentId);
      dispatch(
        updateProject({
          id: projectId,
          updates: { assignedAgents: updatedAgents },
        })
      );
    }
  };

  const handleUpdateProgress = (projectId, progress) => {
    dispatch(
      updateProject({
        id: projectId,
        updates: { progress },
      })
    );
  };

  return (
    <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-2">
          Project Management
        </h1>
        <p className="text-gray-400 text-lg">Monitor and manage your active projects</p>
      </div>

      <div
        className="mb-8 p-6 rounded-2xl"
        style={{
          background: 'rgba(20, 20, 20, 0.9)',
          backdropFilter: 'blur(25px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-400 focus:outline-none transition-colors md:w-48"
          >
            <option value="all">All Status</option>
            <option value="planning">Planning</option>
            <option value="in_progress">In Progress</option>
            <option value="on_hold">On Hold</option>
            <option value="completed">Completed</option>
          </select>
          <button
            onClick={() => setShowAddProject(true)}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-medium transition-colors"
          >
            <Plus size={20} />
            <span>New Project</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        {Object.entries(statusCounts).map(([status, count]) => {
          const statusConfig = {
            all: { icon: Folder, color: 'cyan' },
            planning: { icon: Calendar, color: 'purple' },
            in_progress: { icon: Activity, color: 'blue' },
            on_hold: { icon: Pause, color: 'yellow' },
            completed: { icon: CheckCircle, color: 'green' },
          };
          const { icon: Icon, color } = statusConfig[status];
          return (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
                filterStatus === status
                  ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                  : 'bg-gray-800/30 text-gray-400 border border-gray-700/30 hover:border-cyan-500/30'
              }`}
            >
              <Icon size={16} className={`text-${color}-400`} />
              <span>
                {status === 'in_progress'
                  ? 'In Progress'
                  : status.charAt(0).toUpperCase() + status.slice(1)}{' '}
                ({count})
              </span>
            </button>
          );
        })}
      </div>

      {filteredProjects.length === 0 ? (
        <div className="text-center py-20">
          <AlertCircle size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-500 text-lg">No projects found matching your criteria</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={setSelectedProject}
              onMenuClick={(e, project) => {
                e.stopPropagation();
                setMenuAnchor(e.currentTarget);
                setMenuProject(project);
              }}
            />
          ))}
        </div>
      )}

      {menuAnchor && menuProject && (
        <div
          className="absolute z-50 rounded-lg shadow-xl"
          style={{
            position: 'fixed',
            top: menuAnchor.getBoundingClientRect().top + window.scrollY + 40,
            left: menuAnchor.getBoundingClientRect().left + window.scrollX,
            background: 'rgba(20, 20, 20, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="py-1">
            <button
              onClick={() => {
                handleUpdateProgress(menuProject.id, Math.min(menuProject.progress + 10, 100));
                setMenuAnchor(null);
              }}
              className="flex items-center gap-2 px-4 py-2 w-full text-left hover:bg-white/10 text-white"
            >
              <TrendingUp size={16} />
              <span>Increase Progress</span>
            </button>
            <button
              onClick={() => {
                setSelectedProject(menuProject);
                setMenuAnchor(null);
              }}
              className="flex items-center gap-2 px-4 py-2 w-full text-left hover:bg-white/10 text-white"
            >
              <Edit size={16} />
              <span>Edit Project</span>
            </button>
            <button
              onClick={() => {
                setMenuAnchor(null);
              }}
              className="flex items-center gap-2 px-4 py-2 w-full text-left hover:bg-white/10 text-red-400"
            >
              <Trash2 size={16} />
              <span>Delete Project</span>
            </button>
          </div>
        </div>
      )}

      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          agents={agents}
          onClose={() => setSelectedProject(null)}
          onUpdate={(id, updates) => dispatch(updateProject({ id, updates }))}
          onAddAgent={handleAddAgent}
          onRemoveAgent={handleRemoveAgent}
        />
      )}

      {showAddProject && (
        <AddProjectModal
          onClose={() => setShowAddProject(false)}
          onAdd={(project) => dispatch(addProject(project))}
        />
      )}
    </div>
  );
};
