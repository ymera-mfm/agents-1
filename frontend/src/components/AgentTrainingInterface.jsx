// components/AgentTrainingInterface.jsx
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Square, Upload, Download, Brain, Target, Zap } from 'lucide-react';

export const AgentTrainingInterface = ({ agent }) => {
  const [trainingSession, setTrainingSession] = useState(null);
  const [trainingData, setTrainingData] = useState([]);
  const [isTraining, setIsTraining] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef();

  const trainingConfigs = {
    basic: {
      name: 'Basic Training',
      duration: '30 minutes',
      datasets: ['common-crawl', 'wikipedia'],
      parameters: {
        learningRate: 0.001,
        batchSize: 32,
        epochs: 10,
      },
    },
    advanced: {
      name: 'Advanced Specialization',
      duration: '2 hours',
      datasets: ['domain-specific', 'technical-docs'],
      parameters: {
        learningRate: 0.0005,
        batchSize: 16,
        epochs: 25,
      },
    },
    custom: {
      name: 'Custom Training',
      duration: 'Variable',
      datasets: ['user-uploaded'],
      parameters: {
        learningRate: 0.0001,
        batchSize: 8,
        epochs: 50,
      },
    },
  };

  const startTraining = async (config) => {
    setIsTraining(true);
    setProgress(0);

    const session = {
      id: Date.now(),
      config,
      startTime: new Date(),
      status: 'running',
      metrics: [],
    };

    setTrainingSession(session);

    // Simulate training progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsTraining(false);
          setTrainingSession((prev) => ({
            ...prev,
            status: 'completed',
            endTime: new Date(),
          }));
          return 100;
        }
        return prev + 1;
      });
    }, 100);
  };

  const stopTraining = () => {
    setIsTraining(false);
    setTrainingSession((prev) => ({
      ...prev,
      status: 'stopped',
      endTime: new Date(),
    }));
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const newTrainingData = files.map((file) => ({
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      uploadDate: new Date(),
    }));

    setTrainingData((prev) => [...prev, ...newTrainingData]);
  };

  const TrainingMetrics = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white/5 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-cyan-400 mb-1">{progress}%</div>
        <div className="text-xs text-gray-400">Progress</div>
      </div>
      <div className="bg-white/5 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-green-400 mb-1">
          {trainingSession?.metrics.length || 0}
        </div>
        <div className="text-xs text-gray-400">Epochs</div>
      </div>
      <div className="bg-white/5 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-purple-400 mb-1">{trainingData.length}</div>
        <div className="text-xs text-gray-400">Datasets</div>
      </div>
      <div className="bg-white/5 rounded-lg p-4 text-center">
        <div className="text-2xl font-bold text-yellow-400 mb-1">
          {trainingSession?.config.parameters.learningRate}
        </div>
        <div className="text-xs text-gray-400">Learning Rate</div>
      </div>
    </div>
  );

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">Agent Training</h3>
          <p className="text-gray-400">Train and optimize {agent.name}'s capabilities</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center space-x-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white hover:bg-white/10 transition"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Data</span>
          </button>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            multiple
            className="hidden"
            accept=".json,.csv,.txt"
          />
        </div>
      </div>

      {/* Training Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {Object.entries(trainingConfigs).map(([key, config]) => (
          <motion.div
            key={key}
            className={`p-6 rounded-xl border-2 cursor-pointer transition ${
              trainingSession?.config.name === config.name
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-white/10 bg-white/5 hover:border-white/20'
            }`}
            whileHover={{ scale: 1.02 }}
            onClick={() => !isTraining && startTraining(config)}
          >
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center">
                <Brain className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <h4 className="text-lg font-semibold text-white">{config.name}</h4>
                <p className="text-sm text-gray-400">{config.duration}</p>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Learning Rate</span>
                <span className="text-white">{config.parameters.learningRate}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Batch Size</span>
                <span className="text-white">{config.parameters.batchSize}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Epochs</span>
                <span className="text-white">{config.parameters.epochs}</span>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-1">
              {config.datasets.map((dataset) => (
                <span key={dataset} className="px-2 py-1 bg-white/5 rounded text-xs text-gray-400">
                  {dataset}
                </span>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Training Progress */}
      {isTraining && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-semibold text-white">Training in Progress</h4>
            <button
              onClick={stopTraining}
              className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
            >
              <Square className="w-4 h-4" />
              <span>Stop Training</span>
            </button>
          </div>

          <TrainingMetrics />

          <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
            <motion.div
              className="h-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-gray-400 mb-1">Current Epoch</div>
              <div className="text-white font-semibold">
                {Math.floor(progress / 10)} / {trainingSession?.config.parameters.epochs}
              </div>
            </div>
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-gray-400 mb-1">Time Elapsed</div>
              <div className="text-white font-semibold">{Math.floor(progress / 2)} minutes</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Training Data Management */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-white mb-4">Training Datasets</h4>

        <AnimatePresence>
          {trainingData.length > 0 ? (
            <div className="space-y-2">
              {trainingData.map((file, _index) => (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                      <Download className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <div className="text-white font-medium">{file.name}</div>
                      <div className="text-sm text-gray-400">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-400">
                      {file.uploadDate.toLocaleDateString()}
                    </span>
                    <button className="text-red-400 hover:text-red-300">×</button>
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Upload className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <div>No training data uploaded</div>
              <div className="text-sm">Upload datasets to start training</div>
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* Performance Metrics */}
      <div>
        <h4 className="text-lg font-semibold text-white mb-4">Performance Metrics</h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white/5 rounded-lg text-center">
            <Target className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-white">94%</div>
            <div className="text-sm text-gray-400">Accuracy</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg text-center">
            <Zap className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-white">1.2s</div>
            <div className="text-sm text-gray-400">Response Time</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg text-center">
            <Brain className="w-8 h-8 text-purple-400 mx-auto mb-2" />
            <div className="text-2xl font-bold text-white">87%</div>
            <div className="text-sm text-gray-400">Learning Efficiency</div>
          </div>
        </div>
      </div>
    </div>
  );
};
