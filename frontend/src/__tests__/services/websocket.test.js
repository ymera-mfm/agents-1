import { websocketService } from '../../services/websocket';

describe('WebSocket Service', () => {
  let mockWebSocket;

  beforeEach(() => {
    mockWebSocket = {
      send: jest.fn(),
      close: jest.fn(),
      readyState: WebSocket.OPEN,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    };
    global.WebSocket = jest.fn(() => mockWebSocket);
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  describe('connect', () => {
    it('establishes WebSocket connection', () => {
      websocketService.connect('test-token');
      expect(WebSocket).toHaveBeenCalledWith(expect.stringContaining('?token=test-token'));
    });

    it('does not create duplicate connections', () => {
      websocketService.connect('test-token');
      websocketService.connect('test-token');
      expect(WebSocket).toHaveBeenCalledTimes(1);
    });

    it('updates connection status on open', () => {
      const statusCallback = jest.fn();
      websocketService.subscribeToStatus(statusCallback);

      websocketService.connect('test-token');

      // Simulate onopen event
      const onopen =
        mockWebSocket.addEventListener.mock.calls.find((call) => call[0] === 'open')?.[1] ||
        mockWebSocket.onopen;

      if (onopen) {
        onopen();
      }

      expect(websocketService.connectionStatus).toBe('connected');
    });
  });

  describe('send', () => {
    it('sends message when connected', () => {
      websocketService.ws = mockWebSocket;
      websocketService.send({ type: 'test', data: 'test data' });

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ type: 'test', data: 'test data' })
      );
    });

    it('queues messages when disconnected', () => {
      websocketService.ws = { ...mockWebSocket, readyState: WebSocket.CLOSED };
      websocketService.send({ type: 'test' });

      expect(websocketService.messageQueue).toHaveLength(1);
      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });
  });

  describe('subscribe', () => {
    it('subscribes to channel messages', () => {
      const callback = jest.fn();
      const unsubscribe = websocketService.subscribe('test-channel', callback);

      expect(typeof unsubscribe).toBe('function');
      expect(websocketService.subscribers.has('test-channel')).toBe(true);
    });

    it('receives messages for subscribed channel', () => {
      const callback = jest.fn();
      websocketService.subscribe('test-channel', callback);

      websocketService.handleMessage({
        channel: 'test-channel',
        payload: { data: 'test' },
      });

      expect(callback).toHaveBeenCalledWith({ data: 'test' });
    });

    it('unsubscribes from channel', () => {
      const callback = jest.fn();
      const unsubscribe = websocketService.subscribe('test-channel', callback);

      unsubscribe();

      websocketService.handleMessage({
        channel: 'test-channel',
        payload: { data: 'test' },
      });

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('heartbeat', () => {
    it('sends ping messages periodically', () => {
      websocketService.ws = mockWebSocket;
      websocketService.startHeartbeat();

      jest.advanceTimersByTime(30000);

      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }));
    });

    it('stops heartbeat on disconnect', () => {
      websocketService.ws = mockWebSocket;
      websocketService.startHeartbeat();
      websocketService.stopHeartbeat();

      jest.advanceTimersByTime(30000);

      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });
  });

  describe('reconnection', () => {
    it('attempts reconnection on disconnect', () => {
      const connectSpy = jest.spyOn(websocketService, 'connect');
      websocketService.attemptReconnect('test-token');

      jest.advanceTimersByTime(1000);

      expect(connectSpy).toHaveBeenCalledWith('test-token');
    });

    it('uses exponential backoff for reconnection', () => {
      websocketService.reconnectAttempts = 2;
      const connectSpy = jest.spyOn(websocketService, 'connect');

      websocketService.attemptReconnect('test-token');

      // Should wait 2^2 * 1000 = 4000ms
      jest.advanceTimersByTime(3999);
      expect(connectSpy).not.toHaveBeenCalled();

      jest.advanceTimersByTime(1);
      expect(connectSpy).toHaveBeenCalled();
    });

    it('stops reconnection after max attempts', () => {
      websocketService.reconnectAttempts = 5;
      const connectSpy = jest.spyOn(websocketService, 'connect');

      websocketService.attemptReconnect('test-token');

      jest.advanceTimersByTime(100000);
      expect(connectSpy).not.toHaveBeenCalled();
    });
  });

  describe('disconnect', () => {
    it('closes WebSocket connection', () => {
      websocketService.ws = mockWebSocket;
      websocketService.disconnect();

      expect(mockWebSocket.close).toHaveBeenCalled();
      expect(websocketService.ws).toBeNull();
      expect(websocketService.connectionStatus).toBe('disconnected');
    });
  });
});
