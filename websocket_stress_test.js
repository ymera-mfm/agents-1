const WebSocket = require('ws');
const { performance } = require('perf_hooks');

class WebSocketStressTest {
  constructor(url, numConnections, messagesPerConnection) {
    this.url = url;
    this.numConnections = numConnections;
    this.messagesPerConnection = messagesPerConnection;
    this.connections = [];
    this.stats = {
      connected: 0,
      failed: 0,
      messagesSent: 0,
      messagesReceived: 0,
      latencies: [],
      errors: []
    };
  }

  async run() {
    console.log(`Starting WebSocket stress test...`);
    console.log(`Target: ${this.url}`);
    console.log(`Connections: ${this.numConnections}`);
    console.log(`Messages per connection: ${this.messagesPerConnection}`);
    
    const startTime = performance.now();
    
    // Create connections in batches to avoid overwhelming the system
    const batchSize = 100;
    for (let i = 0; i < this.numConnections; i += batchSize) {
      const batch = Math.min(batchSize, this.numConnections - i);
      await this.createConnectionBatch(batch);
      await this.sleep(100); // Small delay between batches
    }
    
    console.log(`All connections established. Starting message exchange...`);
    
    // Send messages from all connections
    await this.sendMessages();
    
    // Wait for responses
    await this.sleep(5000);
    
    // Close all connections
    await this.closeAllConnections();
    
    const endTime = performance.now();
    const duration = (endTime - startTime) / 1000;
    
    this.printResults(duration);
  }

  async createConnectionBatch(count) {
    const promises = [];
    
    for (let i = 0; i < count; i++) {
      promises.push(this.createConnection());
    }
    
    await Promise.allSettled(promises);
  }

  createConnection() {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.url);
      
      ws.on('open', () => {
        this.stats.connected++;
        this.connections.push(ws);
        
        // Subscribe to channels
        ws.send(JSON.stringify({
          type: 'subscribe',
          channel: 'agents'
        }));
        
        resolve(ws);
      });
      
      ws.on('message', (data) => {
        this.stats.messagesReceived++;
        
        try {
          const message = JSON.parse(data);
          if (message.timestamp) {
            const latency = Date.now() - message.timestamp;
            this.stats.latencies.push(latency);
          }
        } catch (e) {
          // Ignore parse errors
        }
      });
      
      ws.on('error', (error) => {
        this.stats.failed++;
        this.stats.errors.push(error.message);
        reject(error);
      });
      
      ws.on('close', () => {
        // Connection closed
      });
      
      // Timeout after 10 seconds
      setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          this.stats.failed++;
          reject(new Error('Connection timeout'));
        }
      }, 10000);
    });
  }

  async sendMessages() {
    const promises = [];
    
    for (const ws of this.connections) {
      if (ws.readyState === WebSocket.OPEN) {
        promises.push(this.sendMessagesFromConnection(ws));
      }
    }
    
    await Promise.allSettled(promises);
  }

  async sendMessagesFromConnection(ws) {
    for (let i = 0; i < this.messagesPerConnection; i++) {
      if (ws.readyState === WebSocket.OPEN) {
        // Note: Math.random() is sufficient for load testing purposes (generating test data)
        // This is not used for security-sensitive operations
        const message = {
          type: 'agent_message',
          from: `test_user_${Math.random()}`,
          to: `agent_${Math.floor(Math.random() * 100)}`,
          payload: {
            action: 'execute',
            data: { test: true },
            timestamp: Date.now()
          }
        };
        
        ws.send(JSON.stringify(message));
        this.stats.messagesSent++;
        
        await this.sleep(10); // Small delay between messages
      }
    }
  }

  async closeAllConnections() {
    for (const ws of this.connections) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    }
    
    await this.sleep(1000); // Wait for graceful closure
  }

  printResults(duration) {
    console.log('\n========================================');
    console.log('WEBSOCKET STRESS TEST RESULTS');
    console.log('========================================');
    console.log(`Duration: ${duration.toFixed(2)}s`);
    console.log(`Connections attempted: ${this.numConnections}`);
    console.log(`Connections successful: ${this.stats.connected}`);
    console.log(`Connections failed: ${this.stats.failed}`);
    console.log(`Success rate: ${(this.stats.connected / this.numConnections * 100).toFixed(2)}%`);
    console.log(`Messages sent: ${this.stats.messagesSent}`);
    console.log(`Messages received: ${this.stats.messagesReceived}`);
    console.log(`Messages/sec: ${(this.stats.messagesSent / duration).toFixed(2)}`);
    
    if (this.stats.latencies.length > 0) {
      this.stats.latencies.sort((a, b) => a - b);
      const avg = this.stats.latencies.reduce((a, b) => a + b, 0) / this.stats.latencies.length;
      const p50 = this.stats.latencies[Math.floor(this.stats.latencies.length * 0.5)];
      const p95 = this.stats.latencies[Math.floor(this.stats.latencies.length * 0.95)];
      const p99 = this.stats.latencies[Math.floor(this.stats.latencies.length * 0.99)];
      
      console.log('\nLatency Statistics:');
      console.log(`  Average: ${avg.toFixed(2)}ms`);
      console.log(`  P50: ${p50}ms`);
      console.log(`  P95: ${p95}ms`);
      console.log(`  P99: ${p99}ms`);
    }
    
    if (this.stats.errors.length > 0) {
      console.log('\nErrors encountered:');
      const errorCounts = {};
      this.stats.errors.forEach(err => {
        errorCounts[err] = (errorCounts[err] || 0) + 1;
      });
      Object.entries(errorCounts).forEach(([error, count]) => {
        console.log(`  ${error}: ${count}`);
      });
    }
    
    console.log('========================================\n');
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Run the test
if (require.main === module) {
  const url = process.env.WS_URL || 'ws://localhost:8000/ws';
  const connections = parseInt(process.env.CONNECTIONS || '100', 10);
  const messages = parseInt(process.env.MESSAGES || '10', 10);
  
  const test = new WebSocketStressTest(url, connections, messages);
  test.run().catch(console.error);
}

module.exports = WebSocketStressTest;
