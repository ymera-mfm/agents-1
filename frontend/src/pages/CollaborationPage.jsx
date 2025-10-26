import React, { useCallback } from 'react';
import { useApp } from '../store/AppContext';
import { CollaborationSession } from '../features/collaboration/CollaborationSession';

export const CollaborationPage = () => {
  const { agents, addCollaborationSession } = useApp();

  const handleSessionUpdate = useCallback(
    (event, session) => {
      if (event === 'started') {
        addCollaborationSession(session);
      }
    },
    [addCollaborationSession]
  );

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <CollaborationSession agents={agents} onSessionUpdate={handleSessionUpdate} />
      </div>
    </div>
  );
};
