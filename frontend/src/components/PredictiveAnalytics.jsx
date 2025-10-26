// components/PredictiveAnalytics.jsx
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Brain, TrendingUp, AlertTriangle, Target, Zap, Users, CheckCircle } from 'lucide-react';

export const PredictiveAnalytics = ({ projects, agents, historicalData: _historicalData }) => {
  const [timeframe, setTimeframe] = useState('30d');

  // AI-powered predictions
  const predictions = useMemo(() => {
    const basePredictions = {
      projectCompletion: [],
      resourceNeeds: [],
      riskAssessment: [],
      efficiencyTrends: [],
      insights: [],
    };

    // Predict project completion dates
    projects.forEach((project) => {
      const currentProgress = project.progress;
      const daysElapsed = project.elapsedDays || 1;
      const estimatedCompletion = (100 / currentProgress) * daysElapsed;
      const predictedCompletion = new Date();
      predictedCompletion.setDate(
        predictedCompletion.getDate() + (estimatedCompletion - daysElapsed)
      );

      basePredictions.projectCompletion.push({
        project: project.name,
        predictedDate: predictedCompletion.toISOString().split('T')[0],
        confidence: Math.min(85 + project.progress / 2, 95),
        status: estimatedCompletion - daysElapsed < 7 ? 'on-track' : 'at-risk',
      });
    });

    // Predict resource needs
    const totalWorkload = agents.reduce((sum, agent) => sum + agent.tasks, 0);
    const avgEfficiency = agents.reduce((sum, agent) => sum + agent.efficiency, 0) / agents.length;

    basePredictions.resourceNeeds = {
      currentLoad: totalWorkload,
      predictedLoad: Math.round(totalWorkload * 1.15), // 15% growth prediction
      recommendedAgents: Math.ceil((totalWorkload * 1.15) / (avgEfficiency * 10)),
      timeline: 'next-30-days',
    };

    // Risk assessment
    basePredictions.riskAssessment = projects.map((project) => ({
      project: project.name,
      riskLevel: project.progress < 30 ? 'high' : project.progress < 60 ? 'medium' : 'low',
      factors: [
        project.progress < 25 && 'Slow start',
        project.budget - project.spent < project.budget * 0.2 && 'Budget concerns',
        project.team < 3 && 'Understaffed',
      ].filter(Boolean),
      mitigation:
        project.progress < 30
          ? 'Accelerate initial phase'
          : project.budget - project.spent < project.budget * 0.2
            ? 'Review expenses'
            : 'Continue current pace',
    }));

    // AI-generated insights
    basePredictions.insights = [
      {
        type: 'efficiency',
        message: 'Agent efficiency peaks between 10 AM - 2 PM',
        impact: 'high',
        recommendation: 'Schedule critical tasks during peak hours',
      },
      {
        type: 'resource',
        message: 'Data processing agents are 40% more efficient with current workload',
        impact: 'medium',
        recommendation: 'Consider increasing data agent allocation',
      },
      {
        type: 'collaboration',
        message: 'Projects with 3+ agents show 25% faster completion',
        impact: 'high',
        recommendation: 'Maintain optimal team sizes for complex projects',
      },
    ];

    return basePredictions;
  }, [projects, agents]);

  const RiskIndicator = ({ level }) => {
    const config = {
      high: { color: 'text-red-400', bg: 'bg-red-500/20', label: 'High Risk' },
      medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', label: 'Medium Risk' },
      low: { color: 'text-green-400', bg: 'bg-green-500/20', label: 'Low Risk' },
    };

    const { color, bg, label } = config[level] || config.low;

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${bg} ${color}`}>{label}</span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Brain className="w-6 h-6" />
            <span>AI Predictive Analytics</span>
          </h3>
          <p className="text-gray-400">AI-powered insights and future projections</p>
        </div>

        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
        >
          <option value="7d">Next 7 Days</option>
          <option value="30d">Next 30 Days</option>
          <option value="90d">Next 90 Days</option>
        </select>
      </div>

      {/* Prediction Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project Completion Predictions */}
        <motion.div
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
          whileHover={{ scale: 1.02 }}
        >
          <div className="flex items-center space-x-2 mb-4">
            <Target className="w-5 h-5 text-cyan-400" />
            <h4 className="text-lg font-semibold text-white">Completion Forecast</h4>
          </div>

          <div className="space-y-3">
            {predictions.projectCompletion.slice(0, 3).map((prediction, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
              >
                <div>
                  <div className="text-white font-medium">{prediction.project}</div>
                  <div className="text-sm text-gray-400">{prediction.predictedDate}</div>
                </div>
                <div className="text-right">
                  <div
                    className={`text-sm font-semibold ${
                      prediction.status === 'on-track' ? 'text-green-400' : 'text-yellow-400'
                    }`}
                  >
                    {prediction.confidence}% confidence
                  </div>
                  <RiskIndicator level={prediction.status === 'on-track' ? 'low' : 'medium'} />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Resource Predictions */}
        <motion.div
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
          whileHover={{ scale: 1.02 }}
        >
          <div className="flex items-center space-x-2 mb-4">
            <Users className="w-5 h-5 text-green-400" />
            <h4 className="text-lg font-semibold text-white">Resource Forecast</h4>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Current Load</span>
              <span className="text-white font-semibold">
                {predictions.resourceNeeds.currentLoad} tasks
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-gray-400">Predicted Load</span>
              <span className="text-yellow-400 font-semibold">
                {predictions.resourceNeeds.predictedLoad} tasks
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-gray-400">Recommended Agents</span>
              <span className="text-cyan-400 font-semibold">
                +{predictions.resourceNeeds.recommendedAgents}
              </span>
            </div>

            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 transition-all duration-500"
                style={{
                  width: `${(predictions.resourceNeeds.currentLoad / predictions.resourceNeeds.predictedLoad) * 100}%`,
                }}
              />
            </div>
          </div>
        </motion.div>

        {/* Risk Assessment */}
        <motion.div
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
          whileHover={{ scale: 1.02 }}
        >
          <div className="flex items-center space-x-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h4 className="text-lg font-semibold text-white">Risk Assessment</h4>
          </div>

          <div className="space-y-3">
            {predictions.riskAssessment
              .filter((r) => r.riskLevel !== 'low')
              .map((assessment, index) => (
                <div key={index} className="p-3 bg-white/5 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-white font-medium">{assessment.project}</div>
                    <RiskIndicator level={assessment.riskLevel} />
                  </div>

                  <div className="text-sm text-gray-400 space-y-1">
                    {assessment.factors.map((factor, i) => (
                      <div key={i}>• {factor}</div>
                    ))}
                  </div>

                  <div className="text-sm text-cyan-400 mt-2">💡 {assessment.mitigation}</div>
                </div>
              ))}

            {predictions.riskAssessment.filter((r) => r.riskLevel !== 'low').length === 0 && (
              <div className="text-center py-4 text-gray-400">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
                <div>All projects are low risk</div>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* AI Insights */}
      <motion.div
        className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center space-x-2 mb-6">
          <Zap className="w-5 h-5 text-purple-400" />
          <h4 className="text-lg font-semibold text-white">AI-Generated Insights</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {predictions.insights.map((insight, index) => (
            <motion.div
              key={index}
              className={`p-4 rounded-lg border ${
                insight.impact === 'high'
                  ? 'border-purple-500/50 bg-purple-500/10'
                  : insight.impact === 'medium'
                    ? 'border-blue-500/50 bg-blue-500/10'
                    : 'border-gray-500/50 bg-gray-500/10'
              }`}
              whileHover={{ scale: 1.05 }}
            >
              <div className="flex items-start space-x-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    insight.impact === 'high'
                      ? 'bg-purple-500/20'
                      : insight.impact === 'medium'
                        ? 'bg-blue-500/20'
                        : 'bg-gray-500/20'
                  }`}
                >
                  <Brain
                    className={`w-4 h-4 ${
                      insight.impact === 'high'
                        ? 'text-purple-400'
                        : insight.impact === 'medium'
                          ? 'text-blue-400'
                          : 'text-gray-400'
                    }`}
                  />
                </div>

                <div className="flex-1">
                  <div className="text-white font-medium mb-1">{insight.message}</div>
                  <div className="text-sm text-gray-400">{insight.recommendation}</div>

                  <div className="flex items-center space-x-2 mt-2">
                    <div
                      className={`text-xs px-2 py-1 rounded-full ${
                        insight.impact === 'high'
                          ? 'bg-purple-500/20 text-purple-400'
                          : insight.impact === 'medium'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {insight.impact} impact
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Efficiency Trends */}
      <motion.div
        className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center space-x-2 mb-6">
          <TrendingUp className="w-5 h-5 text-green-400" />
          <h4 className="text-lg font-semibold text-white">Efficiency Trends & Projections</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h5 className="text-white font-semibold">Performance Metrics</h5>
            {[
              { metric: 'Task Completion Rate', current: 94, trend: '+2.1%' },
              { metric: 'Average Response Time', current: 1.2, trend: '-0.3s', unit: 's' },
              { metric: 'Error Rate', current: 0.8, trend: '-0.4%', unit: '%' },
              { metric: 'Agent Utilization', current: 78, trend: '+5.2%', unit: '%' },
            ].map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
              >
                <span className="text-gray-400">{item.metric}</span>
                <div className="text-right">
                  <div className="text-white font-semibold">
                    {item.current}
                    {item.unit || '%'}
                  </div>
                  <div
                    className={`text-xs ${
                      item.trend.startsWith('+') ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {item.trend}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            <h5 className="text-white font-semibold">Projections</h5>
            <div className="p-4 bg-gradient-to-br from-cyan-500/10 to-blue-600/10 rounded-lg">
              <div className="text-cyan-400 font-semibold mb-2">Next 30 Days</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Expected Projects</span>
                  <span className="text-white">+3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Resource Growth</span>
                  <span className="text-green-400">+15%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Efficiency Target</span>
                  <span className="text-yellow-400">92%</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-gradient-to-br from-purple-500/10 to-pink-600/10 rounded-lg">
              <div className="text-purple-400 font-semibold mb-2">AI Recommendations</div>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• Scale data processing capacity by 25%</li>
                <li>• Implement advanced caching for 40% faster responses</li>
                <li>• Train 2 additional AI agents for customer support</li>
              </ul>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
