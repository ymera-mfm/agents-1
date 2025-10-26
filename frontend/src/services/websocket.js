import { CONFIG } from '../config/config';

class WebSocketService {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.subscribers = new Map();
    this.connectionStatus = 'disconnected';
    this.statusCallbacks = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.heartbeatInterval = null;
    this.messageQueue = [];
  }

  connect(token) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.connectionStatus = 'connecting';
    this.notifyStatusChange();

    try {
      this.ws = new WebSocket(`${this.url}?token=${token}`);

      this.ws.onopen = () => {
        this.connectionStatus = 'connected';
        this.reconnectAttempts = 0;
        this.notifyStatusChange();
        this.startHeartbeat();
        this.flushMessageQueue();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        this.connectionStatus = 'disconnected';
        this.notifyStatusChange();
        this.stopHeartbeat();
        this.attemptReconnect(token);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.attemptReconnect(token);
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  attemptReconnect(token) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      setTimeout(() => this.connect(token), delay);
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.messageQueue.push(data);
    }
  }

  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift();
      this.ws.send(JSON.stringify(message));
    }
  }

  subscribe(channel, callback) {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set());
    }
    this.subscribers.get(channel).add(callback);

    return () => {
      const channelSubscribers = this.subscribers.get(channel);
      if (channelSubscribers) {
        channelSubscribers.delete(callback);
        if (channelSubscribers.size === 0) {
          this.subscribers.delete(channel);
        }
      }
    };
  }

  subscribeToStatus(callback) {
    this.statusCallbacks.add(callback);
    callback(this.connectionStatus);
    return () => this.statusCallbacks.delete(callback);
  }

  notifyStatusChange() {
    this.statusCallbacks.forEach((callback) => callback(this.connectionStatus));
  }

  handleMessage(data) {
    const { channel, payload } = data;
    const channelSubscribers = this.subscribers.get(channel);
    if (channelSubscribers) {
      channelSubscribers.forEach((callback) => {
        try {
          callback(payload);
        } catch (error) {
          console.error('Subscriber callback error:', error);
        }
      });
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus = 'disconnected';
    this.notifyStatusChange();
  }
}

export const websocketService = new WebSocketService(CONFIG.WS_URL);
