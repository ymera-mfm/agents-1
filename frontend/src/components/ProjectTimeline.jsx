// components/ProjectTimeline.jsx
import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, Users, Target, CheckCircle2 } from 'lucide-react';

const Milestone = ({ milestone, isActive }) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <motion.div
      drag="x"
      dragConstraints={{ left: 0, right: 300 }}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={() => setIsDragging(false)}
      whileHover={{ scale: 1.05 }}
      className={`
        relative p-4 rounded-lg border-l-4 cursor-move
        ${isActive ? 'bg-blue-500/20 border-blue-500' : 'bg-white/5 border-gray-600'}
        ${isDragging ? 'shadow-lg z-10' : ''}
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-semibold text-white">{milestone.name}</h4>
        <div className="flex items-center space-x-2">
          {milestone.completed && <CheckCircle2 className="w-4 h-4 text-green-500" />}
          <span className="text-xs text-gray-400">{milestone.duration}d</span>
        </div>
      </div>

      <div className="flex items-center space-x-4 text-sm text-gray-400">
        <div className="flex items-center space-x-1">
          <Calendar className="w-3 h-3" />
          <span>{milestone.startDate}</span>
        </div>
        <div className="flex items-center space-x-1">
          <Users className="w-3 h-3" />
          <span>{milestone.assignedTeam.length}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${milestone.progress}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </div>
    </motion.div>
  );
};

export const ProjectTimeline = ({ project, onMilestoneUpdate }) => {
  const [selectedMilestone] = useState(null);
  const timelineRef = useRef(null);

  const calculateCriticalPath = useCallback((milestones) => {
    // Implement critical path algorithm
    return milestones.filter((m) => m.critical);
  }, []);

  const criticalPath = calculateCriticalPath(project.milestones);

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">{project.name} Timeline</h3>
          <p className="text-gray-400">Drag milestones to adjust scheduling</p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Overall Progress</div>
            <div className="text-2xl font-bold text-white">{project.progress}%</div>
          </div>
          <div className="w-16 h-16">
            <svg viewBox="0 0 36 36" className="circular-chart">
              <path
                className="circle-bg"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <motion.path
                className="circle"
                strokeDasharray={`${project.progress}, 100`}
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
                initial={{ strokeDasharray: '0, 100' }}
                animate={{ strokeDasharray: `${project.progress}, 100` }}
                transition={{ duration: 1.5, ease: 'easeOut' }}
              />
              <text x="18" y="20.35" className="percentage">
                {project.progress}%
              </text>
            </svg>
          </div>
        </div>
      </div>

      {/* Timeline visualization */}
      <div ref={timelineRef} className="relative mb-8">
        {/* Time axis */}
        <div className="flex justify-between text-sm text-gray-400 mb-4 px-4">
          {project.timeline.map((date, index) => (
            <div key={index} className="text-center">
              <div>{date.month}</div>
              <div className="text-xs">{date.week}</div>
            </div>
          ))}
        </div>

        {/* Milestones */}
        <div className="space-y-3">
          <AnimatePresence>
            {project.milestones.map((milestone, index) => (
              <motion.div
                key={milestone.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.1 }}
              >
                <Milestone
                  milestone={milestone}
                  onUpdate={onMilestoneUpdate}
                  isActive={selectedMilestone?.id === milestone.id}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Critical path indicator */}
        {criticalPath.length > 0 && (
          <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center space-x-2 text-red-400 mb-2">
              <Target className="w-4 h-4" />
              <span className="font-semibold">Critical Path</span>
            </div>
            <div className="text-sm text-gray-400">
              {criticalPath.map((m) => m.name).join(' → ')}
            </div>
          </div>
        )}
      </div>

      {/* Resource allocation */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="bg-white/5 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <span className="text-white font-semibold">Team Allocation</span>
          </div>
          <div className="space-y-2">
            {project.teamAllocation.map((allocation) => (
              <div key={allocation.role} className="flex justify-between text-sm">
                <span className="text-gray-400">{allocation.role}</span>
                <span className="text-white">{allocation.count} members</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Clock className="w-4 h-4 text-green-400" />
            <span className="text-white font-semibold">Time Tracking</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Estimated</span>
              <span className="text-white">{project.estimatedDays}d</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Elapsed</span>
              <span className="text-white">{project.elapsedDays}d</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Remaining</span>
              <span className="text-orange-400">{project.remainingDays}d</span>
            </div>
          </div>
        </div>

        <div className="bg-white/5 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-blue-400" />
            <span className="text-white font-semibold">Deliverables</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Completed</span>
              <span className="text-green-400">{project.completedDeliverables}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pending</span>
              <span className="text-yellow-400">{project.pendingDeliverables}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total</span>
              <span className="text-white">{project.totalDeliverables}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
