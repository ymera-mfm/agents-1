// components/DeploymentDashboard.jsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, RefreshCw, CheckCircle, XCircle, Clock, Settings } from 'lucide-react';

export const DeploymentDashboard = () => {
  const [deployments, setDeployments] = useState([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentProgress, setDeploymentProgress] = useState(0);

  const deploymentStages = [
    { name: 'Code Compilation', duration: 30 },
    { name: 'Dependency Installation', duration: 45 },
    { name: 'Testing', duration: 60 },
    { name: 'Asset Optimization', duration: 30 },
    { name: 'Deployment', duration: 45 },
  ];

  const startDeployment = async () => {
    setIsDeploying(true);
    setDeploymentProgress(0);

    const deployment = {
      id: Date.now(),
      version: `v1.${deployments.length + 1}.0`,
      startTime: new Date(),
      status: 'running',
      stages: deploymentStages.map((stage) => ({ ...stage, status: 'pending' })),
    };

    setDeployments((prev) => [deployment, ...prev]);

    // Simulate deployment process
    for (let i = 0; i < deploymentStages.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, deploymentStages[i].duration * 10));

      setDeployments((prev) =>
        prev.map((dep) =>
          dep.id === deployment.id
            ? {
                ...dep,
                stages: dep.stages.map((stage, index) =>
                  index === i ? { ...stage, status: 'completed' } : stage
                ),
              }
            : dep
        )
      );

      setDeploymentProgress(((i + 1) / deploymentStages.length) * 100);
    }

    // Finalize deployment
    setDeployments((prev) =>
      prev.map((dep) =>
        dep.id === deployment.id
          ? {
              ...dep,
              status: 'completed',
              endTime: new Date(),
              success: true,
            }
          : dep
      )
    );

    setIsDeploying(false);
    setDeploymentProgress(0);
  };

  const cancelDeployment = () => {
    setIsDeploying(false);
    setDeploymentProgress(0);

    setDeployments((prev) =>
      prev.map((dep) =>
        dep.status === 'running' ? { ...dep, status: 'cancelled', endTime: new Date() } : dep
      )
    );
  };

  const DeploymentStage = ({ stage }) => (
    <div className="flex items-center space-x-3 p-3 bg-white/5 rounded-lg">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center ${
          stage.status === 'completed'
            ? 'bg-green-500/20 text-green-400'
            : stage.status === 'running'
              ? 'bg-cyan-500/20 text-cyan-400 animate-pulse'
              : 'bg-gray-500/20 text-gray-400'
        }`}
      >
        {stage.status === 'completed' ? (
          <CheckCircle className="w-4 h-4" />
        ) : stage.status === 'running' ? (
          <RefreshCw className="w-4 h-4" />
        ) : (
          <Clock className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1">
        <div className="text-white font-medium">{stage.name}</div>
        <div className="text-sm text-gray-400">{stage.duration}s estimated</div>
      </div>

      {stage.status === 'running' && (
        <div className="w-20 bg-gray-700 rounded-full h-2">
          <motion.div
            className="h-2 rounded-full bg-cyan-500"
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: stage.duration / 10, ease: 'linear' }}
          />
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white">Deployment Center</h3>
          <p className="text-gray-400">Manage application deployments and CI/CD pipelines</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={startDeployment}
            disabled={isDeploying}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>{isDeploying ? 'Deploying...' : 'Deploy Now'}</span>
          </button>

          {isDeploying && (
            <button
              onClick={cancelDeployment}
              className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
            >
              <Square className="w-4 h-4" />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>

      {/* Current Deployment Progress */}
      {isDeploying && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-white">Deployment in Progress</h4>
            <div className="text-cyan-400 font-semibold">{deploymentProgress.toFixed(0)}%</div>
          </div>

          <div className="w-full bg-gray-700 rounded-full h-3 mb-6">
            <motion.div
              className="h-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600"
              initial={{ width: 0 }}
              animate={{ width: `${deploymentProgress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          <div className="space-y-3">
            {deployments[0]?.stages.map((stage, index) => (
              <DeploymentStage
                key={index}
                stage={stage}
                index={index}
                currentStage={deploymentProgress / (100 / deploymentStages.length)}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Deployment History */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <h4 className="text-lg font-semibold text-white mb-4">Deployment History</h4>

        <div className="space-y-3">
          <AnimatePresence>
            {deployments.map((deployment) => (
              <motion.div
                key={deployment.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center justify-between p-4 bg-white/5 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      deployment.status === 'completed'
                        ? 'bg-green-500/20'
                        : deployment.status === 'running'
                          ? 'bg-cyan-500/20 animate-pulse'
                          : 'bg-red-500/20'
                    }`}
                  >
                    {deployment.status === 'completed' ? (
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    ) : deployment.status === 'running' ? (
                      <RefreshCw className="w-6 h-6 text-cyan-400" />
                    ) : (
                      <XCircle className="w-6 h-6 text-red-400" />
                    )}
                  </div>

                  <div>
                    <div className="text-white font-semibold">{deployment.version}</div>
                    <div className="text-sm text-gray-400">
                      {deployment.startTime.toLocaleString()}
                      {deployment.endTime && ` - ${deployment.endTime.toLocaleTimeString()}`}
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div
                    className={`text-sm font-semibold ${
                      deployment.status === 'completed'
                        ? 'text-green-400'
                        : deployment.status === 'running'
                          ? 'text-cyan-400'
                          : 'text-red-400'
                    }`}
                  >
                    {deployment.status.charAt(0).toUpperCase() + deployment.status.slice(1)}
                  </div>
                  <div className="text-xs text-gray-400">
                    {deployment.stages.filter((s) => s.status === 'completed').length} /{' '}
                    {deployment.stages.length} stages
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {deployments.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <Settings className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <div>No deployments yet</div>
              <div className="text-sm">Start your first deployment to see history</div>
            </div>
          )}
        </div>
      </div>

      {/* Environment Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Environment Settings</h4>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Environment</label>
              <select className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500">
                <option>Production</option>
                <option>Staging</option>
                <option>Development</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Build Command</label>
              <input
                type="text"
                defaultValue="npm run build"
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Node Version</label>
              <select className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500">
                <option>18.x</option>
                <option>20.x</option>
                <option>16.x</option>
              </select>
            </div>
          </div>
        </div>

        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Deployment Statistics</h4>

          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
              <span className="text-gray-400">Total Deployments</span>
              <span className="text-white font-semibold">{deployments.length}</span>
            </div>

            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
              <span className="text-gray-400">Success Rate</span>
              <span className="text-green-400 font-semibold">
                {deployments.filter((d) => d.status === 'completed').length > 0
                  ? `${((deployments.filter((d) => d.status === 'completed').length / deployments.length) * 100).toFixed(0)}%`
                  : '0%'}
              </span>
            </div>

            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
              <span className="text-gray-400">Average Duration</span>
              <span className="text-cyan-400 font-semibold">
                {deploymentStages.reduce((sum, stage) => sum + stage.duration, 0)}s
              </span>
            </div>

            <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
              <span className="text-gray-400">Last Deployment</span>
              <span className="text-white font-semibold">{deployments[0]?.version || 'None'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
