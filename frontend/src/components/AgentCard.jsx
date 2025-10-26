import React from 'react';
import { StatusBadge } from './StatusBadge';
import { Code, Camera, Database, Shield, Zap } from 'lucide-react';

const iconMap = {
  Code: Code,
  Camera: Camera,
  Database: Database,
  Shield: Shield,
  Zap: Zap,
};

export const AgentCard = React.memo(({ agent, onClick }) => {
  const Icon = iconMap[agent.icon] || Zap;

  return (
    <div
      onClick={() => onClick(agent)}
      className="group relative overflow-hidden rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
      style={{
        background: 'rgba(20, 20, 20, 0.9)',
        backdropFilter: 'blur(25px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.37)',
      }}
      aria-label={`View ${agent.name} details`}
      role="button"
      tabIndex="0"
      onKeyDown={(e) => e.key === 'Enter' && onClick(agent)}
    >
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300"
        style={{
          background: `linear-gradient(135deg, ${agent.color}40, transparent)`,
        }}
      />
      <div className="relative p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div
            className="p-3 rounded-xl transition-transform group-hover:scale-110"
            style={{
              background: `${agent.color}20`,
              border: `1px solid ${agent.color}40`,
            }}
          >
            <Icon size={24} style={{ color: agent.color }} />
          </div>
          <StatusBadge status={agent.status} />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white mb-1">{agent.name}</h3>
          <p className="text-sm text-gray-400 font-mono">{agent.type.toUpperCase()}</p>
        </div>
        <p className="text-sm text-gray-500 leading-relaxed">{agent.description}</p>
        <div className="flex items-center justify-between pt-4 border-t border-gray-800">
          <div>
            <div className="text-2xl font-bold" style={{ color: agent.color }}>
              {agent.tasksCompleted}
            </div>
            <div className="text-xs text-gray-500">Tasks</div>
          </div>
          <div>
            <div className="text-2xl font-bold" style={{ color: agent.color }}>
              {agent.efficiency}%
            </div>
            <div className="text-xs text-gray-500">Efficiency</div>
          </div>
        </div>
      </div>
    </div>
  );
});
