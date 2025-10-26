import React from 'react';
import { RefreshCw } from 'lucide-react';

export const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8">
    <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
  </div>
);
