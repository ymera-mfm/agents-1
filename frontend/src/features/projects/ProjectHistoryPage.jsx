import React, { useState, useMemo } from 'react';
import { useApp } from '../../store/AppContext';
import { Search, Folder, Calendar, Clock, X } from 'lucide-react';

export const ProjectHistoryPage = () => {
  const { projects } = useApp();
  const [selectedProject, setSelectedProject] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredProjects = useMemo(() => {
    return projects.filter(
      (p) =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [projects, searchTerm]);

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-white mb-2">Project History</h1>
          <p className="text-gray-400">View the history of project updates and milestones</p>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-4">
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-2 bg-transparent border-none text-white placeholder-gray-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              onClick={() => setSelectedProject(project)}
              className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition cursor-pointer"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Folder size={18} className="text-cyan-400" />
                    <span className="text-xs px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 capitalize">
                      {project.status.replace('_', ' ')}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{project.name}</h3>
                  <p className="text-sm text-gray-400 line-clamp-2">{project.description}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Progress</span>
                  <span className="font-bold text-cyan-400">{project.progress}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 to-blue-600 transition-all duration-500"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {selectedProject && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="relative w-full max-w-4xl rounded-3xl overflow-hidden bg-black/95 border border-white/10 max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-800">
                <button
                  onClick={() => setSelectedProject(null)}
                  className="absolute top-6 right-6 p-2 rounded-lg hover:bg-white/10 transition"
                >
                  <X size={20} className="text-gray-400" />
                </button>
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-4 rounded-xl bg-cyan-500/20 border border-cyan-500/40">
                    <Folder size={32} className="text-cyan-400" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-3xl font-bold text-white mb-1">{selectedProject.name}</h2>
                    <p className="text-gray-400">{selectedProject.description}</p>
                  </div>
                </div>
              </div>

              <div className="p-8">
                <h3 className="text-2xl font-bold text-white mb-6">Project History</h3>
                <div className="space-y-4">
                  {selectedProject.milestones?.map((milestone) => (
                    <div
                      key={milestone.id}
                      className="p-4 bg-white/5 rounded-lg border border-white/10"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-white">{milestone.name}</h4>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${
                            milestone.completed
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-yellow-500/20 text-yellow-400'
                          }`}
                        >
                          {milestone.completed ? 'Completed' : 'In Progress'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-400 mb-2">
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{milestone.startDate}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{milestone.duration} days</span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full transition-all duration-500"
                          style={{ width: `${milestone.progress}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
