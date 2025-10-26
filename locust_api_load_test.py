"""
Locust Load Testing Script for YMERA API
Tests API endpoints under various load conditions
"""

from locust import HttpUser, task, between, events
import random
import json
import time
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
        self.login()
    
    def login(self):
        """Authenticate and get JWT token"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": f"testuser_{random.randint(1, 1000)}",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(10)  # Weight: 10 (most common operation)
    def get_health(self):
        """Health check - lightest endpoint"""
        self.client.get("/api/v1/health")
    
    @task(8)
    def get_system_info(self):
        """Get system information"""
        self.client.get("/api/v1/system/info")
    
    @task(7)
    def list_agents(self):
        """List all agents"""
        response = self.client.get("/api/v1/agents?page=1&page_size=20")
        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("agents"):
                self.agent_ids = [a["id"] for a in data["data"]["agents"][:5]]
    
    @task(5)
    def get_agent_details(self):
        """Get specific agent details"""
        if self.agent_ids:
            agent_id = random.choice(self.agent_ids)
            self.client.get(f"/api/v1/agents/{agent_id}")
        else:
            # Fallback to known test agent
            self.client.get("/api/v1/agents/test_agent_123")
    
    @task(3)
    def create_agent(self):
        """Create new agent"""
        agent_data = {
            "agent_id": f"load_test_agent_{random.randint(1, 100000)}",
            "name": f"Load Test Agent {random.randint(1, 1000)}",
            "type": random.choice(["coder", "analyst", "monitor", "coordinator"]),
            "config": {
                "max_tasks": random.randint(5, 20),
                "timeout": random.randint(30, 300)
            }
        }
        response = self.client.post("/api/v1/agents", json=agent_data)
        if response.status_code == 200:
            new_agent_id = response.json().get("data", {}).get("id")
            if new_agent_id:
                self.agent_ids.append(new_agent_id)
    
    @task(2)
    def update_agent(self):
        """Update agent configuration"""
        if self.agent_ids:
            agent_id = random.choice(self.agent_ids)
            update_data = {
                "name": f"Updated Agent {random.randint(1, 1000)}",
                "config": {
                    "max_tasks": random.randint(10, 50),
                    "timeout": random.randint(60, 600)
                }
            }
            self.client.put(f"/api/v1/agents/{agent_id}", json=update_data)
    
    @task(1)
    def delete_agent(self):
        """Delete agent"""
        if len(self.agent_ids) > 3:  # Keep at least 3 agents
            agent_id = self.agent_ids.pop()
            self.client.delete(f"/api/v1/agents/{agent_id}")
    
    @task(6)
    def list_projects(self):
        """List projects"""
        self.client.get("/api/v1/projects?page=1&page_size=10")
    
    @task(4)
    def get_metrics(self):
        """Get system metrics"""
        self.client.get("/api/v1/metrics")
    
    @task(3)
    def search_agents(self):
        """Search agents"""
        search_query = random.choice(["coder", "analyst", "test", "monitor"])
        self.client.get(f"/api/v1/agents/search?q={search_query}")


class HeavyUser(HttpUser):
    """
    Simulates heavy users performing resource-intensive operations
    """
    wait_time = between(2, 8)
    
    def on_start(self):
        self.client.verify = False
        self.token = None
        self.login()
    
    def login(self):
        """Authenticate"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": f"heavyuser_{random.randint(1, 100)}",
            "password": "testpass123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(3)
    def bulk_agent_creation(self):
        """Create multiple agents in batch"""
        agents = [
            {
                "agent_id": f"bulk_agent_{random.randint(1, 1000000)}_{i}",
                "name": f"Bulk Agent {i}",
                "type": "coder"
            }
            for i in range(10)
        ]
        self.client.post("/api/v1/agents/bulk", json={"agents": agents})
    
    @task(2)
    def export_data(self):
        """Export large datasets"""
        self.client.get("/api/v1/agents/export?format=json")
    
    @task(1)
    def analytics_query(self):
        """Complex analytics query"""
        params = {
            "start_date": "2025-10-01",
            "end_date": "2025-10-26",
            "group_by": "type",
            "metrics": "count,avg_execution_time,success_rate"
        }
        self.client.get("/api/v1/analytics", params=params)


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Collect custom metrics on each request"""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test - log start time"""
    print(f"Load test started at {datetime.now()}")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Finalize test - generate summary report"""
    print(f"\nLoad test completed at {datetime.now()}")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"P95 response time: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99 response time: {environment.stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")


# Run configuration
if __name__ == "__main__":
    import os
    os.system("""
    locust -f locust_api_load_test.py \
        --host=https://staging-api.ymera.com \
        --users=10000 \
        --spawn-rate=100 \
        --run-time=1h \
        --html=load_test_report.html \
        --csv=load_test_results
    """)
