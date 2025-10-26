import React, { memo } from 'react';

export const StatCard = memo(({ title, value, change, icon: Icon, color }) => (
  <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all hover:scale-105 hover:shadow-xl group">
    <div className="flex items-center justify-between mb-4">
      <div className="p-3 rounded-lg" style={{ backgroundColor: `${color}20` }}>
        <Icon className="w-6 h-6" style={{ color }} />
      </div>
      {change !== undefined && (
        <span
          className={`text-sm font-semibold px-2 py-1 rounded ${change > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}
        >
          {change > 0 ? '+' : ''}
          {change}%
        </span>
      )}
    </div>
    <h3 className="text-3xl font-bold text-white mb-1">{value}</h3>
    <p className="text-gray-400 text-sm">{title}</p>
  </div>
));
