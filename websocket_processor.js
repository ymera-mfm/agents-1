'use strict';

let messageCount = 0;
let latencies = [];

module.exports = {
  generateUserId,
  sendAgentMessage,
  measureLatency,
  printStats
};

function generateUserId(context, events, done) {
  // Note: Math.random() is sufficient for load testing purposes (generating test user IDs)
  // This is not used for security-sensitive operations
  context.vars.userId = 'user_' + Math.floor(Math.random() * 1000000);
  context.vars.agentId = 'agent_' + Math.floor(Math.random() * 10000);
  return done();
}

function sendAgentMessage(context, events, done) {
  // Note: Math.random() is sufficient for load testing purposes (choosing test actions)
  // This is not used for security-sensitive operations
  const message = {
    type: 'agent_message',
    from: context.vars.userId,
    to: context.vars.agentId,
    payload: {
      action: Math.random() > 0.5 ? 'execute' : 'status',
      timestamp: Date.now()
    }
  };
  
  context.ws.send(JSON.stringify(message));
  messageCount++;
  
  return done();
}

function measureLatency(context, events, done) {
  const startTime = Date.now();
  
  context.ws.on('message', (data) => {
    const endTime = Date.now();
    const latency = endTime - startTime;
    latencies.push(latency);
    
    if (latencies.length % 1000 === 0) {
      printStats();
    }
  });
  
  return done();
}

function printStats() {
  if (latencies.length === 0) return;
  
  latencies.sort((a, b) => a - b);
  
  const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
  const p50 = latencies[Math.floor(latencies.length * 0.5)];
  const p95 = latencies[Math.floor(latencies.length * 0.95)];
  const p99 = latencies[Math.floor(latencies.length * 0.99)];
  
  console.log('\n--- WebSocket Latency Stats ---');
  console.log('Total messages:', messageCount);
  console.log('Avg latency:', avg.toFixed(2), 'ms');
  console.log('P50 latency:', p50, 'ms');
  console.log('P95 latency:', p95, 'ms');
  console.log('P99 latency:', p99, 'ms');
  console.log('-------------------------------\n');
}
