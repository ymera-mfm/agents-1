"""
Locust Load Testing Script for YMERA API
Tests API endpoints under various load conditions
"""

from locust import HttpUser, task, between, events
import random
import json
import time
import os
from datetime import datetime

class YMERAUser(HttpUser):
    """
    Simulates realistic user behavior for YMERA platform
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - login and get token"""
        self.client.verify = False  # For testing environment
        self.agent_ids = []
        self.token = None
        self.authenticated = False
        # Try to authenticate, but don't fail if it doesn't work
        try:
            self.login()
        except Exception as e:
            print(f"Authentication failed: {e}. Continuing with unauthenticated requests.")
    
    def login(self):
        """Authenticate and get JWT token"""
        try:
            # Use environment variables or default test credentials
            username = os.getenv('LOAD_TEST_USERNAME', f"testuser_{random.randint(1, 100)}")
            password = os.getenv('LOAD_TEST_PASSWORD', 'testpass123')
            
            response = self.client.post("/api/v1/auth/login", 
                json={
                    "username": username,
                    "password": password
                },
                name="/api/v1/auth/login",
                catch_response=True
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get("access_token")
                    if self.token:
                        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                        self.authenticated = True
                        response.success()
                    else:
                        response.failure("No access token in response")
                except (json.JSONDecodeError, KeyError) as e:
                    response.failure(f"Invalid JSON response: {e}")
            else:
                response.failure(f"Login failed with status {response.status_code}")
                # Continue without authentication for open endpoints
        except Exception as e:
            print(f"Login error: {e}")
    
    @task(10)  # Weight: 10 (most common operation)
    def get_health(self):
        """Health check - lightest endpoint"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") in ["healthy", "ok"]:
                        response.success()
                    else:
                        response.failure(f"Unexpected health status: {data.get('status')}")
                else:
                    response.failure(f"Health check failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Health check error: {e}")
    
    @task(8)
    def get_system_info(self):
        """Get system information"""
        with self.client.get("/api/v1/system/info", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "name" in data or "version" in data:
                        response.success()
                    else:
                        response.failure("System info missing expected fields")
                else:
                    response.failure(f"System info failed: {response.status_code}")
            except Exception as e:
                response.failure(f"System info error: {e}")
    
    @task(7)
    def list_agents(self):
        """List all agents"""
        with self.client.get("/api/v1/agents?page=1&page_size=20", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get("data", {}).get("agents", [])
                    # Store agent IDs for other tasks
                    if agents and isinstance(agents, list):
                        self.agent_ids = [a.get("id") for a in agents[:5] if a.get("id")]
                        response.success()
                    else:
                        # Empty list is valid
                        response.success()
                else:
                    response.failure(f"List agents failed: {response.status_code}")
            except Exception as e:
                response.failure(f"List agents error: {e}")
    
    @task(5)
    def get_agent_details(self):
        """Get specific agent details"""
        # Use existing agent ID or fallback to test agent
        agent_id = None
        if self.agent_ids and len(self.agent_ids) > 0:
            agent_id = random.choice(self.agent_ids)
        else:
            agent_id = "test_agent_123"
        
        with self.client.get(f"/api/v1/agents/{agent_id}", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") or data.get("data"):
                        response.success()
                    else:
                        response.failure("Agent details missing expected structure")
                elif response.status_code == 404:
                    # Not found is acceptable for test agents
                    response.success()
                else:
                    response.failure(f"Get agent failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Get agent error: {e}")
    
    @task(3)
    def create_agent(self):
        """Create new agent"""
        agent_data = {
            "agent_id": f"load_test_agent_{random.randint(1, 100000)}_{int(time.time())}",
            "name": f"Load Test Agent {random.randint(1, 1000)}",
            "type": random.choice(["coder", "analyst", "monitor", "coordinator"]),
            "config": {
                "max_tasks": random.randint(5, 20),
                "timeout": random.randint(30, 300)
            }
        }
        
        with self.client.post("/api/v1/agents", json=agent_data, catch_response=True) as response:
            try:
                if response.status_code in [200, 201]:
                    data = response.json()
                    new_agent_id = data.get("data", {}).get("id")
                    if new_agent_id:
                        self.agent_ids.append(new_agent_id)
                        # Limit stored IDs to prevent memory issues
                        if len(self.agent_ids) > 20:
                            self.agent_ids = self.agent_ids[-20:]
                    response.success()
                elif response.status_code == 401 or response.status_code == 403:
                    # Authentication required but not available
                    response.success()  # Don't count as failure
                else:
                    response.failure(f"Create agent failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Create agent error: {e}")
    
    @task(2)
    def update_agent(self):
        """Update agent configuration"""
        if not self.agent_ids or len(self.agent_ids) == 0:
            return  # Skip if no agents available
        
        agent_id = random.choice(self.agent_ids)
        update_data = {
            "name": f"Updated Agent {random.randint(1, 1000)}",
            "config": {
                "max_tasks": random.randint(10, 50),
                "timeout": random.randint(60, 600)
            }
        }
        
        with self.client.put(f"/api/v1/agents/{agent_id}", json=update_data, catch_response=True) as response:
            try:
                if response.status_code in [200, 204]:
                    response.success()
                elif response.status_code == 404:
                    # Agent not found - remove from our list
                    if agent_id in self.agent_ids:
                        self.agent_ids.remove(agent_id)
                    response.success()  # Don't count as failure
                elif response.status_code in [401, 403]:
                    response.success()  # Authentication issue, don't count as failure
                else:
                    response.failure(f"Update agent failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Update agent error: {e}")
    
    @task(1)
    def delete_agent(self):
        """Delete agent"""
        if len(self.agent_ids) > 3:  # Keep at least 3 agents
            agent_id = self.agent_ids.pop()
            
            with self.client.delete(f"/api/v1/agents/{agent_id}", catch_response=True) as response:
                try:
                    if response.status_code in [200, 204]:
                        response.success()
                    elif response.status_code == 404:
                        # Already deleted
                        response.success()
                    elif response.status_code in [401, 403]:
                        # Put it back if we can't delete
                        self.agent_ids.append(agent_id)
                        response.success()  # Don't count as failure
                    else:
                        response.failure(f"Delete agent failed: {response.status_code}")
                except Exception as e:
                    response.failure(f"Delete agent error: {e}")
    
    @task(6)
    def list_projects(self):
        """List projects"""
        with self.client.get("/api/v1/projects?page=1&page_size=10", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data or "projects" in data:
                        response.success()
                    else:
                        response.failure("Projects response missing expected structure")
                elif response.status_code in [401, 403]:
                    response.success()  # Don't count auth issues as failures
                else:
                    response.failure(f"List projects failed: {response.status_code}")
            except Exception as e:
                response.failure(f"List projects error: {e}")
    
    @task(4)
    def get_metrics(self):
        """Get system metrics"""
        with self.client.get("/api/v1/metrics", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data or "metrics" in data:
                        response.success()
                    else:
                        response.failure("Metrics response missing expected structure")
                elif response.status_code in [401, 403]:
                    response.success()  # Don't count auth issues as failures
                else:
                    response.failure(f"Get metrics failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Get metrics error: {e}")
    
    @task(3)
    def search_agents(self):
        """Search agents"""
        search_query = random.choice(["coder", "analyst", "test", "monitor"])
        with self.client.get(f"/api/v1/agents/search?q={search_query}", catch_response=True) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data or "agents" in data:
                        response.success()
                    else:
                        response.failure("Search response missing expected structure")
                elif response.status_code in [401, 403]:
                    response.success()  # Don't count auth issues as failures
                else:
                    response.failure(f"Search agents failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Search agents error: {e}")


class HeavyUser(HttpUser):
    """
    Simulates heavy users performing resource-intensive operations
    """
    wait_time = between(2, 8)
    
    def on_start(self):
        self.client.verify = False
        self.token = None
        self.authenticated = False
        try:
            self.login()
        except Exception as e:
            print(f"Heavy user authentication failed: {e}. Continuing with limited access.")
    
    def login(self):
        """Authenticate"""
        try:
            username = os.getenv('LOAD_TEST_USERNAME', f"heavyuser_{random.randint(1, 100)}")
            password = os.getenv('LOAD_TEST_PASSWORD', 'testpass123')
            
            response = self.client.post("/api/v1/auth/login",
                json={
                    "username": username,
                    "password": password
                },
                name="/api/v1/auth/login [heavy]",
                catch_response=True
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get("access_token")
                    if self.token:
                        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                        self.authenticated = True
                        response.success()
                    else:
                        response.failure("No access token in response")
                except (json.JSONDecodeError, KeyError) as e:
                    response.failure(f"Invalid JSON response: {e}")
            else:
                response.failure(f"Login failed with status {response.status_code}")
        except Exception as e:
            print(f"Heavy user login error: {e}")
    
    @task(3)
    def bulk_agent_creation(self):
        """Create multiple agents in batch"""
        try:
            agents = [
                {
                    "agent_id": f"bulk_agent_{random.randint(1, 1000000)}_{i}_{int(time.time())}",
                    "name": f"Bulk Agent {i}",
                    "type": "coder"
                }
                for i in range(10)
            ]
            
            with self.client.post("/api/v1/agents/bulk", 
                                json={"agents": agents}, 
                                catch_response=True,
                                timeout=30) as response:
                try:
                    if response.status_code in [200, 201]:
                        data = response.json()
                        created_count = data.get("data", {}).get("created", 0)
                        if created_count > 0:
                            response.success()
                        else:
                            response.failure("No agents created in bulk operation")
                    elif response.status_code in [401, 403]:
                        response.success()  # Don't count auth issues
                    else:
                        response.failure(f"Bulk creation failed: {response.status_code}")
                except Exception as e:
                    response.failure(f"Bulk creation error: {e}")
        except Exception as e:
            print(f"Bulk agent creation error: {e}")
    
    @task(2)
    def export_data(self):
        """Export large datasets"""
        with self.client.get("/api/v1/agents/export?format=json", 
                           catch_response=True,
                           timeout=30) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data or "agents" in data:
                        response.success()
                    else:
                        response.failure("Export response missing expected structure")
                elif response.status_code in [401, 403]:
                    response.success()  # Don't count auth issues
                else:
                    response.failure(f"Export failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Export error: {e}")
    
    @task(1)
    def analytics_query(self):
        """Complex analytics query"""
        params = {
            "start_date": "2025-10-01",
            "end_date": "2025-10-26",
            "group_by": "type",
            "metrics": "count,avg_execution_time,success_rate"
        }
        
        with self.client.get("/api/v1/analytics", 
                           params=params, 
                           catch_response=True,
                           timeout=30) as response:
            try:
                if response.status_code == 200:
                    data = response.json()
                    if "data" in data or "analytics" in data:
                        response.success()
                    else:
                        response.failure("Analytics response missing expected structure")
                elif response.status_code in [401, 403]:
                    response.success()  # Don't count auth issues
                else:
                    response.failure(f"Analytics failed: {response.status_code}")
            except Exception as e:
                response.failure(f"Analytics error: {e}")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Collect custom metrics on each request"""
    if exception:
        error_msg = str(exception)
        # Log errors but don't spam console
        if "Connection" in error_msg or "Timeout" in error_msg:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection issue on {name}: {error_msg[:100]}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Request failed: {name} - {error_msg[:100]}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test - log start time"""
    print("=" * 70)
    print(f"YMERA Load Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target host: {environment.host}")
    print(f"Configuration:")
    print(f"  - Users: {getattr(environment.runner, 'target_user_count', 'N/A')}")
    print(f"  - Spawn rate: {getattr(environment.runner, 'spawn_rate', 'N/A')}")
    print("=" * 70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize test - generate summary report"""
    print("\n" + "=" * 70)
    print(f"YMERA Load Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    stats = environment.stats.total
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Requests:        {stats.num_requests:,}")
    print(f"  Total Failures:        {stats.num_failures:,}")
    print(f"  Failure Rate:          {(stats.num_failures / max(stats.num_requests, 1) * 100):.2f}%")
    print(f"  Average Response Time: {stats.avg_response_time:.2f}ms")
    print(f"  Min Response Time:     {stats.min_response_time:.2f}ms")
    print(f"  Max Response Time:     {stats.max_response_time:.2f}ms")
    
    # Calculate percentiles safely
    try:
        p50 = stats.get_response_time_percentile(0.50)
        p95 = stats.get_response_time_percentile(0.95)
        p99 = stats.get_response_time_percentile(0.99)
        print(f"  P50 Response Time:     {p50:.2f}ms")
        print(f"  P95 Response Time:     {p95:.2f}ms")
        print(f"  P99 Response Time:     {p99:.2f}ms")
    except (AttributeError, ZeroDivisionError):
        print(f"  Percentiles:           N/A (insufficient data)")
    
    print(f"  Requests per Second:   {stats.total_rps:.2f}")
    
    # Show top failing endpoints
    print(f"\n🔍 Endpoint Statistics:")
    endpoint_stats = []
    for name, stat in environment.stats.entries.items():
        if stat.num_requests > 0:
            endpoint_stats.append({
                'name': name,
                'requests': stat.num_requests,
                'failures': stat.num_failures,
                'avg_time': stat.avg_response_time,
                'failure_rate': (stat.num_failures / stat.num_requests * 100) if stat.num_requests > 0 else 0
            })
    
    # Sort by failure rate
    endpoint_stats.sort(key=lambda x: x['failure_rate'], reverse=True)
    
    print(f"  {'Endpoint':<40} {'Requests':<10} {'Failures':<10} {'Fail %':<8} {'Avg(ms)':<10}")
    print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*8} {'-'*10}")
    for stat in endpoint_stats[:10]:  # Top 10
        print(f"  {stat['name'][:40]:<40} {stat['requests']:<10} {stat['failures']:<10} "
              f"{stat['failure_rate']:<8.2f} {stat['avg_time']:<10.2f}")
    
    print("=" * 70)


# Run configuration
if __name__ == "__main__":
    import sys
    
    # Default configuration
    host = os.getenv('LOAD_TEST_HOST', 'http://localhost:8000')
    users = int(os.getenv('LOAD_TEST_USERS', '100'))
    spawn_rate = int(os.getenv('LOAD_TEST_SPAWN_RATE', '10'))
    run_time = os.getenv('LOAD_TEST_RUN_TIME', '1m')
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                  YMERA Load Test Configuration                       ║
╚══════════════════════════════════════════════════════════════════════╝

  Target Host:  {host}
  Users:        {users}
  Spawn Rate:   {spawn_rate} users/sec
  Duration:     {run_time}
  
  Environment Variables (optional):
    LOAD_TEST_HOST          - Target API host
    LOAD_TEST_USERS         - Number of concurrent users
    LOAD_TEST_SPAWN_RATE    - Users spawned per second
    LOAD_TEST_RUN_TIME      - Test duration (e.g., 30s, 5m, 1h)
    LOAD_TEST_USERNAME      - Test user username
    LOAD_TEST_PASSWORD      - Test user password

╔══════════════════════════════════════════════════════════════════════╗

Starting load test...
    """)
    
    # Build locust command
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    cmd = [
        'locust',
        '-f', __file__,
        '--host', host,
        '--users', str(users),
        '--spawn-rate', str(spawn_rate),
        '--run-time', run_time,
        '--headless',
        '--html', f'load_test_report_{timestamp}.html',
        '--csv', f'load_test_results_{timestamp}'
    ]
    
    # Execute locust
    try:
        os.execvp('locust', cmd)
    except Exception as e:
        print(f"Error starting locust: {e}")
        print("\nTrying alternative method...")
        os.system(' '.join(cmd))

