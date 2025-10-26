import React from 'react';
import { Folder, Users, Calendar, MoreVertical } from 'lucide-react';

const statusConfig = {
  planning: { color: 'purple', label: 'Planning' },
  in_progress: { color: 'blue', label: 'In Progress' },
  on_hold: { color: 'yellow', label: 'On Hold' },
  completed: { color: 'green', label: 'Completed' },
};

export const ProjectCard = React.memo(({ project, onClick, onMenuClick }) => {
  const status = statusConfig[project.status] || statusConfig.planning;
  const assignedAgents = project.assignedAgents || [];

  return (
    <div
      onClick={() => onClick(project)}
      className="group relative overflow-hidden rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
      style={{
        background: 'rgba(20, 20, 20, 0.9)',
        backdropFilter: 'blur(25px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
      }}
      aria-label={`View ${project.name} details`}
      role="button"
      tabIndex="0"
      onKeyDown={(e) => e.key === 'Enter' && onClick(project)}
    >
      <div className="absolute top-0 left-0 right-0 h-1" style={{ background: status.color }} />
      <div className="p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Folder size={20} className="text-cyan-400" />
              <span className={`text-xs font-medium text-${status.color}-400`}>{status.label}</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-1 group-hover:text-cyan-400 transition-colors">
              {project.name}
            </h3>
            <p className="text-sm text-gray-400 line-clamp-2">
              {project.description || 'No description provided.'}
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMenuClick(e, project);
            }}
            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
            aria-label="Project menu"
          >
            <MoreVertical size={18} className="text-gray-400" />
          </button>
        </div>
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">Progress</span>
            <span className="text-cyan-400 font-semibold">{project.progress}%</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full bg-${status.color}-500 transition-all duration-500`}
              style={{ width: `${project.progress}%` }}
            />
          </div>
        </div>
        <div className="flex items-center justify-between pt-4 border-t border-gray-800">
          <div className="flex items-center gap-2 text-gray-400">
            <Users size={14} />
            <span>{assignedAgents.length} Agents</span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <Calendar size={14} />
            <span>{new Date(project.estimatedCompletion).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
});
