import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Users, X, PlayCircle, PauseCircle, Send, Brain, CheckCircle2, Target } from 'lucide-react';

export const CollaborationSession = ({ agents, onSessionUpdate }) => {
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionTopic, setSessionTopic] = useState('');
  const [showTopicInput, setShowTopicInput] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (activeSession && isRecording) {
      const interval = setInterval(() => {
        const randomAgent = agents[Math.floor(Math.random() * agents.length)];
        const sampleMessages = [
          'I have analyzed the data and found some interesting patterns.',
          'Should we prioritize performance optimization?',
          'The security scan is complete. Everything looks good.',
          'I recommend we split this into smaller tasks.',
          'Database migration is 75% complete.',
          'Let us schedule a checkpoint review.',
        ];

        const newMessage = {
          id: Date.now() + Math.random(),
          agent: randomAgent,
          sender: 'agent',
          content: sampleMessages[Math.floor(Math.random() * sampleMessages.length)],
          timestamp: new Date().toLocaleTimeString(),
        };

        setMessages((prev) => [...prev, newMessage]);
      }, 8000);

      return () => clearInterval(interval);
    }
  }, [activeSession, isRecording, agents]);

  const startCollaboration = useCallback(
    (topic) => {
      const session = {
        id: Date.now(),
        topic: topic || 'General Discussion',
        participants: agents,
        startTime: new Date(),
        decisions: [],
        actionItems: [],
      };

      setActiveSession(session);
      setMessages([]);
      setIsRecording(true);
      setShowTopicInput(false);
      if (onSessionUpdate) {
        onSessionUpdate('started', session);
      }
    },
    [agents, onSessionUpdate]
  );

  const endSession = useCallback(() => {
    setIsRecording(false);
    setActiveSession(null);
    setMessages([]);
  }, []);

  const sendMessage = useCallback(() => {
    if (!inputMessage.trim()) {
      return;
    }

    const newMessage = {
      id: Date.now(),
      sender: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputMessage('');
  }, [inputMessage]);

  const generateSummary = useCallback(() => {
    const decisions = [
      'Prioritize backend optimization for Q2',
      'Implement new security protocols',
      'Schedule weekly progress reviews',
    ];

    const actionItems = [
      { task: 'Database optimization', assignee: 'DataMiner Pro' },
      { task: 'Security audit', assignee: 'SecurityGuard' },
      { task: 'Code review', assignee: 'CodeWeaver' },
    ];

    setActiveSession((prev) => ({
      ...prev,
      decisions,
      actionItems,
    }));
  }, []);

  return (
    <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-white">Agent Collaboration</h3>
          <p className="text-gray-400">Real-time AI agent teamwork and decision making</p>
        </div>

        <div className="flex items-center space-x-3">
          {!activeSession ? (
            <button
              onClick={() => setShowTopicInput(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition"
            >
              <Users className="w-4 h-4" />
              <span>Start Session</span>
            </button>
          ) : (
            <button
              onClick={endSession}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition"
            >
              <X className="w-4 h-4" />
              <span>End Session</span>
            </button>
          )}
        </div>
      </div>

      {showTopicInput && !activeSession && (
        <div className="mb-6 p-4 bg-white/5 rounded-lg border border-white/10">
          <label className="block text-sm font-medium text-gray-300 mb-2">Session Topic</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={sessionTopic}
              onChange={(e) => setSessionTopic(e.target.value)}
              placeholder="Enter collaboration topic..."
              className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
            <button
              onClick={() => startCollaboration(sessionTopic)}
              className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
            >
              Start
            </button>
            <button
              onClick={() => setShowTopicInput(false)}
              className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {!activeSession && !showTopicInput ? (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">
            Start a collaboration session to enable real-time agent teamwork
          </p>
        </div>
      ) : (
        activeSession && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-black/30 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="flex -space-x-2">
                    {agents.map((agent) => (
                      <div
                        key={agent.id}
                        className="w-8 h-8 rounded-full border-2 border-gray-800"
                        style={{ backgroundColor: agent.color }}
                        title={agent.name}
                      />
                    ))}
                  </div>
                  <div className="flex-1">
                    <div className="text-white font-semibold">{activeSession.topic}</div>
                    <div className="text-gray-400 text-sm">
                      {agents.length} agents participating
                    </div>
                  </div>
                  <button
                    onClick={() => setIsRecording(!isRecording)}
                    className={`p-2 rounded-full ${
                      isRecording
                        ? 'bg-red-500 text-white animate-pulse'
                        : 'bg-white/10 text-gray-400'
                    }`}
                    title={isRecording ? 'Recording' : 'Paused'}
                  >
                    {isRecording ? (
                      <PauseCircle className="w-5 h-5" />
                    ) : (
                      <PlayCircle className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="bg-black/30 rounded-lg p-4 h-96 overflow-y-auto">
                <div className="space-y-3">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-3 ${
                        message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                      }`}
                    >
                      {message.sender === 'agent' ? (
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: message.agent.color }}
                        >
                          <Brain className="w-4 h-4 text-white" />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center flex-shrink-0">
                          <span className="text-white text-sm font-bold">U</span>
                        </div>
                      )}
                      <div className={`flex-1 ${message.sender === 'user' ? 'text-right' : ''}`}>
                        {message.sender === 'agent' && (
                          <div className="text-xs text-gray-400 mb-1">{message.agent.name}</div>
                        )}
                        <div
                          className={`inline-block px-4 py-2 rounded-lg ${
                            message.sender === 'user'
                              ? 'bg-cyan-500/20 text-cyan-100'
                              : 'bg-white/5 text-white'
                          }`}
                        >
                          {message.content}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{message.timestamp}</div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
                <button
                  onClick={sendMessage}
                  className="px-4 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <h4 className="text-white font-semibold mb-3">Session Info</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Duration</span>
                    <span className="text-white">
                      {Math.floor((new Date() - activeSession.startTime) / 60000)}m
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Messages</span>
                    <span className="text-white">{messages.length}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <h4 className="text-white font-semibold mb-3">Quick Actions</h4>
                <div className="space-y-2">
                  <button
                    onClick={generateSummary}
                    className="w-full py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition text-sm"
                  >
                    Generate Summary
                  </button>
                  <button className="w-full py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition text-sm">
                    Export Transcript
                  </button>
                </div>
              </div>

              {activeSession.decisions && activeSession.decisions.length > 0 && (
                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                  <h4 className="text-green-400 font-semibold mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Decisions
                  </h4>
                  <ul className="space-y-2 text-sm">
                    {activeSession.decisions.map((decision, index) => (
                      <li key={index} className="text-green-300">
                        • {decision}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {activeSession.actionItems && activeSession.actionItems.length > 0 && (
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                  <h4 className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Action Items
                  </h4>
                  <div className="space-y-2 text-sm">
                    {activeSession.actionItems.map((item, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-blue-300">{item.task}</span>
                        <span className="text-xs text-gray-400">{item.assignee}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      )}
    </div>
  );
};
