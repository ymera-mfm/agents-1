// Chat System Configuration
// Comprehensive configuration for live chatting, messaging, and real-time communication

import env from './env';

export const chatConfig = {
  // Chat System
  system: {
    enabled: env.enableRealTimeCollaboration,
    protocol: 'websocket',
    encryption: env.httpsOnly,
    compression: true,
    version: '1.0.0',
  },

  // Connection Configuration
  connection: {
    url: env.wsUrl,
    autoConnect: true,
    reconnect: {
      enabled: true,
      maxAttempts: env.wsReconnectAttempts,
      delay: env.wsReconnectDelay,
      backoffMultiplier: 2,
      maxDelay: 30000, // 30 seconds
    },
    heartbeat: {
      enabled: true,
      interval: env.wsHeartbeatInterval,
      timeout: 5000, // 5 seconds
      maxMissed: 3,
    },
    authentication: {
      required: true,
      method: 'jwt',
      tokenRefresh: true,
      refreshInterval: 3300000, // 55 minutes (before 1 hour expiry)
    },
  },

  // Message Configuration
  messages: {
    maxLength: 10000, // characters
    maxSize: env.wsMaxMessageSize,
    allowedTypes: [
      'text',
      'file',
      'image',
      'code',
      'link',
      'system',
      'command',
    ],
    
    formatting: {
      markdown: true,
      codeHighlighting: true,
      emoji: true,
      mentions: true,
      links: true,
    },

    attachments: {
      enabled: true,
      maxSize: 10485760, // 10MB
      maxPerMessage: 5,
      allowedTypes: [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json',
        'application/zip',
      ],
    },

    persistence: {
      enabled: true,
      storage: 'database',
      retention: 2592000000, // 30 days
      encryption: env.httpsOnly,
    },

    delivery: {
      confirmDelivery: true,
      confirmRead: true,
      typing: {
        enabled: true,
        timeout: 3000, // 3 seconds
        throttle: 1000, // 1 second
      },
    },
  },

  // Conversation Types
  conversations: {
    types: {
      direct: {
        id: 'direct',
        name: 'Direct Message',
        maxParticipants: 2,
        allowInvite: false,
        allowLeave: false,
        persistent: true,
      },
      group: {
        id: 'group',
        name: 'Group Chat',
        maxParticipants: 50,
        allowInvite: true,
        allowLeave: true,
        persistent: true,
        roles: ['owner', 'admin', 'member'],
      },
      channel: {
        id: 'channel',
        name: 'Channel',
        maxParticipants: 1000,
        allowInvite: true,
        allowLeave: true,
        persistent: true,
        public: true,
        roles: ['owner', 'admin', 'moderator', 'member'],
      },
      agent: {
        id: 'agent',
        name: 'Agent Chat',
        maxParticipants: 2, // user + agent
        allowInvite: false,
        allowLeave: false,
        persistent: true,
        features: ['commands', 'code_execution', 'file_operations'],
      },
      support: {
        id: 'support',
        name: 'Support Chat',
        maxParticipants: 10,
        allowInvite: true,
        allowLeave: true,
        persistent: true,
        features: ['ticket_integration', 'priority', 'sla'],
      },
    },

    defaults: {
      type: 'direct',
      notifications: true,
      sound: true,
      desktop: env.isProduction,
    },
  },

  // User Presence
  presence: {
    enabled: true,
    statuses: [
      { id: 'online', name: 'Online', color: '#10b981' },
      { id: 'away', name: 'Away', color: '#f59e0b' },
      { id: 'busy', name: 'Busy', color: '#ef4444' },
      { id: 'offline', name: 'Offline', color: '#6b7280' },
    ],
    autoAway: {
      enabled: true,
      timeout: 300000, // 5 minutes
    },
    showLastSeen: true,
    broadcastStatus: true,
  },

  // Notifications
  notifications: {
    enabled: true,
    
    types: {
      mention: {
        enabled: true,
        sound: true,
        desktop: true,
        priority: 'high',
      },
      direct: {
        enabled: true,
        sound: true,
        desktop: true,
        priority: 'high',
      },
      group: {
        enabled: true,
        sound: false,
        desktop: true,
        priority: 'medium',
      },
      channel: {
        enabled: true,
        sound: false,
        desktop: false,
        priority: 'low',
      },
    },

    batching: {
      enabled: true,
      interval: 3000, // 3 seconds
      maxBatch: 10,
    },

    desktop: {
      enabled: 'Notification' in window,
      requestPermission: true,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      silent: false,
      requireInteraction: false,
      tag: 'agentflow-chat',
    },

    sound: {
      enabled: true,
      volume: 0.5,
      sounds: {
        message: '/sounds/message.mp3',
        mention: '/sounds/mention.mp3',
        typing: '/sounds/typing.mp3',
      },
    },

    doNotDisturb: {
      enabled: true,
      schedule: {
        start: '22:00',
        end: '08:00',
      },
      allowMentions: true,
      allowDirect: true,
    },
  },

  // Moderation
  moderation: {
    enabled: true,
    
    filtering: {
      enabled: env.isProduction,
      profanity: true,
      spam: true,
      links: false,
      customWords: [],
    },

    rateLimit: {
      enabled: env.isProduction,
      maxMessages: 10,
      windowMs: 10000, // 10 seconds
      action: 'throttle', // 'throttle', 'block', 'warn'
    },

    permissions: {
      canDelete: ['owner', 'admin', 'moderator'],
      canEdit: ['owner', 'member'],
      canPin: ['owner', 'admin', 'moderator'],
      canInvite: ['owner', 'admin', 'member'],
      canKick: ['owner', 'admin', 'moderator'],
      canBan: ['owner', 'admin'],
    },

    reporting: {
      enabled: true,
      reasons: ['spam', 'harassment', 'inappropriate', 'other'],
      action: 'notify_moderators',
    },
  },

  // Search & History
  search: {
    enabled: true,
    indexing: {
      enabled: true,
      realtime: false,
      fields: ['content', 'sender', 'timestamp'],
    },
    filters: {
      byUser: true,
      byDate: true,
      byType: true,
      byConversation: true,
    },
    results: {
      maxResults: 50,
      highlightMatches: true,
      showContext: true,
    },
  },

  history: {
    enabled: true,
    loadBehavior: 'on-demand', // 'on-demand', 'auto', 'infinite-scroll'
    pageSize: 50,
    maxLoad: 500,
    caching: {
      enabled: true,
      strategy: 'lru',
      maxSize: 100, // conversations
    },
  },

  // Agent Chat Features
  agentChat: {
    enabled: env.enableAIAssistance,
    
    commands: {
      enabled: true,
      prefix: '/',
      autocomplete: true,
      commands: [
        { name: 'help', description: 'Show available commands' },
        { name: 'status', description: 'Get agent status' },
        { name: 'execute', description: 'Execute agent task' },
        { name: 'stop', description: 'Stop current task' },
        { name: 'logs', description: 'View agent logs' },
        { name: 'files', description: 'List agent files' },
      ],
    },

    codeExecution: {
      enabled: true,
      languages: ['javascript', 'python', 'bash'],
      timeout: 30000, // 30 seconds
      sandbox: true,
    },

    fileOperations: {
      enabled: true,
      upload: true,
      download: true,
      maxSize: 10485760, // 10MB
    },

    suggestions: {
      enabled: true,
      contextual: true,
      maxSuggestions: 3,
    },
  },

  // UI Configuration
  ui: {
    theme: {
      primary: env.primaryColor,
      dark: true,
      customizable: true,
    },

    layout: {
      sidebar: 'left', // 'left', 'right', 'none'
      messageAlignment: 'left', // 'left', 'right', 'sender'
      showAvatars: true,
      showTimestamps: true,
      compactMode: false,
    },

    input: {
      multiline: true,
      autocomplete: true,
      spellcheck: true,
      placeholder: 'Type a message...',
      maxHeight: 200, // pixels
      shortcuts: {
        enabled: true,
        send: 'Enter',
        newLine: 'Shift+Enter',
        mention: '@',
        emoji: ':',
      },
    },

    messages: {
      grouping: true,
      groupTimeout: 300000, // 5 minutes
      dateHeaders: true,
      scrollBehavior: 'smooth',
      unreadIndicator: true,
      reactions: {
        enabled: true,
        emojis: ['👍', '❤️', '😂', '😮', '😢', '🎉'],
      },
    },
  },

  // Performance
  performance: {
    virtualScrolling: {
      enabled: true,
      bufferSize: 20,
    },
    lazyLoading: {
      enabled: true,
      images: true,
      videos: true,
    },
    imageOptimization: {
      enabled: true,
      maxWidth: 800,
      maxHeight: 600,
      quality: 0.85,
    },
    messageBatching: {
      enabled: true,
      interval: 100, // milliseconds
      maxBatch: 50,
    },
  },

  // Analytics
  analytics: {
    enabled: env.analyticsEnabled,
    track: [
      'messages_sent',
      'messages_received',
      'conversations_created',
      'users_active',
      'response_time',
      'engagement_rate',
    ],
    privacy: {
      anonymize: env.isProduction,
      excludeContent: true,
    },
  },

  // Integration
  integration: {
    webhooks: {
      enabled: env.isProduction,
      events: [
        'message.sent',
        'message.received',
        'conversation.created',
        'user.joined',
        'user.left',
      ],
      timeout: 5000, // 5 seconds
      retries: 3,
    },

    bots: {
      enabled: true,
      maxPerConversation: 5,
      permissions: ['read', 'write', 'delete'],
    },

    api: {
      enabled: true,
      endpoints: {
        conversations: '/api/v1/chat/conversations',
        messages: '/api/v1/chat/messages',
        users: '/api/v1/chat/users',
        search: '/api/v1/chat/search',
      },
    },
  },

  // Development & Testing
  development: {
    mockChat: env.mockApi,
    verboseLogging: env.debugMode,
    simulateTyping: false,
    simulateDelay: false,
    showDebugInfo: env.isDevelopment,
  },
};

// Helper functions
export const getConversationType = (typeId) => {
  return chatConfig.conversations.types[typeId];
};

export const canUserPerformAction = (user, action, _conversation) => {
  const permissions = chatConfig.moderation.permissions[action];
  return permissions && permissions.includes(user.role);
};

export const isMessageAllowed = (message) => {
  return (
    message.content.length <= chatConfig.messages.maxLength &&
    chatConfig.messages.allowedTypes.includes(message.type)
  );
};

export default chatConfig;
