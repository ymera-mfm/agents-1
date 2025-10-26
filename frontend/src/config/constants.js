import { PauseCircle, Activity, CheckCircle2, BarChart3, Palette, Code, Zap } from 'lucide-react';

export const PROJECT_STATUS = {
  planning: { color: '#a855f7', label: 'Planning', icon: PauseCircle },
  in_progress: { color: '#3b82f6', label: 'In Progress', icon: Activity },
  completed: { color: '#10b981', label: 'Completed', icon: CheckCircle2 },
};

export const PHASE_TYPES = {
  analysis: { color: '#10b981', icon: BarChart3, geometry: 'sphere' },
  design: { color: '#3b82f6', icon: Palette, geometry: 'octahedron' },
  development: { color: '#f59e0b', icon: Code, geometry: 'torus' },
  testing: { color: '#a855f7', icon: Activity, geometry: 'dodecahedron' },
  deployment: { color: '#06b6d4', icon: Zap, geometry: 'tetrahedron' },
};
