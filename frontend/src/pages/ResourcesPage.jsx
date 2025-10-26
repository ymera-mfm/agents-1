import React from 'react';
import { useApp } from '../store/AppContext';
import { ResourceManager } from '../components/ResourceManager';

export const ResourcesPage = () => {
  const { projects, agents, handleResourceAllocation } = useApp();

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <ResourceManager
          projects={projects}
          agents={agents}
          onResourceAllocation={handleResourceAllocation}
        />
      </div>
    </div>
  );
};
