// components/AgentCollaboration.jsx
import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, Video, Share, Zap, Brain, Users } from 'lucide-react';

const CollaborationSession = ({ agents, onSessionUpdate }) => {
  const [activeSession, setActiveSession] = useState(null);
  const [messages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);

  const startCollaboration = useCallback(
    (topic) => {
      const session = {
        id: Date.now(),
        topic,
        participants: agents,
        startTime: new Date(),
        decisions: [],
        actionItems: [],
      };

      setActiveSession(session);
      onSessionUpdate('started', session);
    },
    [agents, onSessionUpdate]
  );

  const analyzeConversation = useCallback(async (conversation) => {
    // Implement AI analysis for decision extraction and action item identification
    try {
      const response = await fetch('/api/analyze-conversation', {
        method: 'POST',
        body: JSON.stringify({ conversation }),
        headers: { 'Content-Type': 'application/json' },
      });

      return await response.json();
    } catch (error) {
      console.error('Analysis failed:', error);
      return { decisions: [], actionItems: [] };
    }
  }, []);

  const generateSummary = useCallback(
    async (_session) => {
      // AI-powered session summary generation
      const summary = await analyzeConversation(messages);
      setActiveSession((prev) => ({
        ...prev,
        decisions: summary.decisions,
        actionItems: summary.actionItems,
      }));
    },
    [messages, analyzeConversation]
  );

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">Agent Collaboration</h3>
          <p className="text-gray-400">Real-time AI agent teamwork and decision making</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => startCollaboration('Project Planning')}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition"
          >
            <Users className="w-4 h-4" />
            <span>Start Session</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Collaboration Interface */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-black/30 rounded-lg p-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex -space-x-2">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="w-8 h-8 rounded-full border-2 border-gray-800"
                    style={{ backgroundColor: agent.color }}
                  />
                ))}
              </div>
              <div className="flex-1">
                <div className="text-white font-semibold">Active Collaboration</div>
                <div className="text-gray-400 text-sm">{agents.length} agents participating</div>
              </div>
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`p-2 rounded-full ${
                  isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-white/10 text-gray-400'
                }`}
              >
                <div className="w-3 h-3 rounded-full bg-current" />
              </button>
            </div>

            {/* Message Feed */}
            <div className="h-64 overflow-y-auto space-y-3">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${
                      message.sender === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.sender === 'user'
                          ? 'bg-cyan-500/20 text-white'
                          : 'bg-white/10 text-white'
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor: message.agent?.color || '#6b7280',
                          }}
                        />
                        <span className="text-sm font-semibold">
                          {message.agent?.name || 'User'}
                        </span>
                      </div>
                      <p className="text-sm">{message.content}</p>
                      <div className="text-xs text-gray-400 mt-1">{message.timestamp}</div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* Decision & Action Tracking */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Brain className="w-4 h-4 text-purple-400" />
                <span className="text-white font-semibold">Decisions Made</span>
              </div>
              <div className="space-y-2">
                {activeSession?.decisions.map((decision, index) => (
                  <div key={index} className="text-sm text-gray-300">
                    • {decision}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span className="text-white font-semibold">Action Items</span>
              </div>
              <div className="space-y-2">
                {activeSession?.actionItems.map((item, index) => (
                  <div key={index} className="text-sm text-gray-300">
                    • {item.task} → {item.assignee}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Session Controls & Analytics */}
        <div className="space-y-4">
          <div className="bg-white/5 rounded-lg p-4">
            <h4 className="text-white font-semibold mb-3">Session Controls</h4>
            <div className="space-y-2">
              <button className="w-full flex items-center space-x-2 px-3 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20 transition">
                <MessageCircle className="w-4 h-4" />
                <span>Add Note</span>
              </button>
              <button className="w-full flex items-center space-x-2 px-3 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20 transition">
                <Video className="w-4 h-4" />
                <span>Record Session</span>
              </button>
              <button
                onClick={() => generateSummary(activeSession)}
                className="w-full flex items-center space-x-2 px-3 py-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg text-white hover:from-purple-600 hover:to-pink-700 transition"
              >
                <Share className="w-4 h-4" />
                <span>Generate Summary</span>
              </button>
            </div>
          </div>

          {/* Session Analytics */}
          <div className="bg-white/5 rounded-lg p-4">
            <h4 className="text-white font-semibold mb-3">Session Analytics</h4>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Duration</span>
                <span className="text-white">45m</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Messages</span>
                <span className="text-white">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Decisions</span>
                <span className="text-green-400">{activeSession?.decisions.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Actions</span>
                <span className="text-yellow-400">{activeSession?.actionItems.length || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollaborationSession;
