import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
import numpy as np
import json
from collections import defaultdict, deque

from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import os

from config import settings

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class AgentCapability(str, Enum):
    """Agent capability types"""
    DATA_PROCESSING = "data_processing"
    ML_TRAINING = "ml_training"
    ML_INFERENCE = "ml_inference"
    API_INTEGRATION = "api_integration"
    REAL_TIME_ANALYSIS = "real_time_analysis"
    BATCH_PROCESSING = "batch_processing"
    NLP_PROCESSING = "nlp_processing"
    IMAGE_PROCESSING = "image_processing"
    DOCUMENT_PROCESSING = "document_processing"


class AgentPerformanceLevel(str, Enum):
    """Agent performance classifications"""
    EXCELLENT = "excellent"  # Top 10%
    GOOD = "good"           # Top 25%
    FAIR = "fair"           # Average
    POOR = "poor"           # Below average
    FAILING = "failing"     # Bottom 10%


@dataclass
class AgentProfile:
    """Comprehensive agent profile for orchestration"""
    agent_id: str
    capabilities: List[AgentCapability]
    performance_metrics: Dict[str, float]
    current_load: float
    max_capacity: float
    performance_level: AgentPerformanceLevel
    last_updated: datetime
    specializations: List[str] = None
    availability_schedule: Dict[str, bool] = None
    hardware_specs: Dict[str, any] = None
    cost_per_hour: float = 0.0
    success_rate_by_task: Dict[str, float] = None


@dataclass
class TaskRequirement:
    """Task requirements and constraints"""
    task_id: str
    required_capabilities: List[AgentCapability]
    priority: TaskPriority
    deadline: Optional[datetime]
    estimated_duration: float
    resource_requirements: Dict[str, float]
    data_locality: Optional[str] = None
    tenant_id: str = None
    sla_requirements: Dict[str, float] = None


@dataclass
class TaskAssignment:
    """Task assignment result"""
    task_id: str
    agent_id: str
    confidence_score: float
    estimated_completion_time: datetime
    alternative_agents: List[str]
    assignment_reason: str


class IntelligentAgentOrchestrator:
    """
    Production-Ready Intelligent Agent Orchestration System
    
    Features:
    - ML-based task allocation
    - Dynamic load balancing
    - Performance prediction
    - Capacity planning
    - Cost optimization
    - SLA-aware scheduling
    - Predictive maintenance
    - Multi-objective optimization
    """

    def __init__(
        self,
        ai_service=None,
        model_dir: str = "./ml_models/orchestration"
    ):
        self.ai_service = ai_service
        self.model_dir = model_dir
        
        # ML Models
        self.task_allocator = self._load_or_create_model('task_allocator')
        self.performance_predictor = self._load_or_create_model('performance_predictor')
        self.failure_predictor = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Agent management
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.agent_clusters: Dict[str, List[str]] = {}  # Cluster ID -> Agent IDs
        
        # Performance tracking
        self.task_history: deque = deque(maxlen=10000)
        self.agent_performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Load distribution
        self.load_balancer_strategy = settings.ai.agent_orchestration.task_allocation_strategy
        self.rebalance_threshold = settings.ai.agent_orchestration.load_distribution_max_imbalance
        
        # Training configuration
        self.min_training_samples = settings.ai.agent_orchestration.ml_model_min_training_samples
        self.retrain_interval = settings.ai.agent_orchestration.ml_model_retrain_interval
        self.last_training_time = None
        
        # Capacity planning
        self.capacity_forecast_horizon = settings.ai.agent_orchestration.capacity_planning_forecast_horizon
        self.capacity_buffer = settings.ai.agent_orchestration.capacity_planning_min_capacity_buffer
        
        # Optimization weights
        self.optimization_weights = {
            'performance': 0.4,
            'cost': 0.3,
            'availability': 0.2,
            'sla_compliance': 0.1
        }
        
        logger.info("Enhanced IntelligentAgentOrchestrator initialized")

    def _load_or_create_model(self, model_name: str):
        """Load existing model or create new one"""
        model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
        
        if os.path.exists(model_path):
            try:
                logger.info(f"Loading ML model: {model_name}")
                return joblib.load(model_path)
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
        
        logger.info(f"Creating new ML model: {model_name}")
        return RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

    def _save_model(self, model, model_name: str):
        """Save trained model"""
        os.makedirs(self.model_dir, exist_ok=True)
        model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        logger.info(f"Model saved: {model_name}")

    def update_agent_profile(self, profile: AgentProfile):
        """Update or register agent profile"""
        self.agent_profiles[profile.agent_id] = profile
        
        # Update clusters
        self._update_agent_clusters()
        
        logger.debug(f"Agent profile updated: {profile.agent_id}")

    def _update_agent_clusters(self):
        """Cluster agents by capabilities and performance"""
        if len(self.agent_profiles) < 3:
            return
        
        try:
            # Create feature vectors for clustering
            agent_ids = list(self.agent_profiles.keys())
            features = []
            
            for agent_id in agent_ids:
                profile = self.agent_profiles[agent_id]
                feature_vector = self._create_agent_feature_vector(profile)
                features.append(feature_vector)
            
            # Perform clustering
            n_clusters = min(5, len(agent_ids) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(features)
            
            # Store cluster assignments
            self.agent_clusters.clear()
            for idx, agent_id in enumerate(agent_ids):
                cluster_id = f"cluster_{cluster_labels[idx]}"
                if cluster_id not in self.agent_clusters:
                    self.agent_clusters[cluster_id] = []
                self.agent_clusters[cluster_id].append(agent_id)
            
            logger.info(f"Agent clustering updated: {len(self.agent_clusters)} clusters")
            
        except Exception as e:
            logger.error(f"Agent clustering failed: {e}", exc_info=True)

    def _create_agent_feature_vector(self, profile: AgentProfile) -> List[float]:
        """Create feature vector for agent"""
        features = []
        
        # Capability encoding (one-hot)
        all_capabilities = list(AgentCapability)
        for cap in all_capabilities:
            features.append(1.0 if cap in profile.capabilities else 0.0)
        
        # Performance metrics
        metrics = profile.performance_metrics
        features.extend([
            metrics.get('success_rate', 0.0),
            metrics.get('avg_response_time', 0.0) / 1000.0,  # Normalize
            metrics.get('throughput', 0.0) / 100.0,  # Normalize
            metrics.get('error_rate', 0.0),
            profile.current_load / max(profile.max_capacity, 1.0)
        ])
        
        # Performance level encoding
        perf_levels = list(AgentPerformanceLevel)
        for level in perf_levels:
            features.append(1.0 if profile.performance_level == level else 0.0)
        
        return features

    async def assign_task(self, task: TaskRequirement) -> TaskAssignment:
        """
        Intelligently assign task to optimal agent using multi-criteria optimization
        """
        try:
            # Find candidate agents
            candidates = self._find_candidate_agents(task)
            
            if not candidates:
                raise ValueError("No suitable agents available for task")
            
            # Score all candidates
            agent_scores = await self._score_agents_for_task(candidates, task)
            
            # Select best agent
            best_agent_id = max(agent_scores.items(), key=lambda x: x[1]['total_score'])[0]
            best_score = agent_scores[best_agent_id]
            
            # Get alternatives
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
            alternatives = [aid for aid, _ in sorted_agents[1:4]]  # Top 3 alternatives
            
            # Predict completion time
            estimated_completion = await self._predict_completion_time(best_agent_id, task)
            
            # Update agent load
            self._update_agent_load(best_agent_id, task.estimated_duration)
            
            # Record assignment
            self._record_task_assignment(task.task_id, best_agent_id, best_score['total_score'])
            
            return TaskAssignment(
                task_id=task.task_id,
                agent_id=best_agent_id,
                confidence_score=best_score['total_score'],
                estimated_completion_time=estimated_completion,
                alternative_agents=alternatives,
                assignment_reason=best_score['reason']
            )
            
        except Exception as e:
            logger.error(f"Task assignment failed: {e}", exc_info=True)
            raise

    def _find_candidate_agents(self, task: TaskRequirement) -> List[str]:
        """Find agents capable of handling the task"""
        candidates = []
        
        for agent_id, profile in self.agent_profiles.items():
            # Check capability match
            if not all(cap in profile.capabilities for cap in task.required_capabilities):
                continue
            
            # Check availability
            if profile.current_load >= profile.max_capacity * 0.95:
                continue
            
            # Check resource requirements
            if task.resource_requirements:
                if not self._check_resource_availability(profile, task.resource_requirements):
                    continue
            
            candidates.append(agent_id)
        
        return candidates

    def _check_resource_availability(
        self,
        profile: AgentProfile,
        requirements: Dict[str, float]
    ) -> bool:
        """Check if agent has required resources"""
        if not profile.hardware_specs:
            return True
        
        for resource, required in requirements.items():
            available = profile.hardware_specs.get(resource, float('inf'))
            if available < required:
                return False
        
        return True

    async def _score_agents_for_task(
        self,
        candidates: List[str],
        task: TaskRequirement
    ) -> Dict[str, Dict]:
        """Score agents using multiple criteria"""
        scores = {}
        
        for agent_id in candidates:
            profile = self.agent_profiles[agent_id]
            
            # Performance score
            perf_score = await self._calculate_performance_score(profile, task)
            
            # Cost score
            cost_score = self._calculate_cost_score(profile, task)
            
            # Availability score
            avail_score = self._calculate_availability_score(profile)
            
            # SLA compliance score
            sla_score = self._calculate_sla_score(profile, task)
            
            # Calculate weighted total
            total_score = (
                perf_score * self.optimization_weights['performance'] +
                cost_score * self.optimization_weights['cost'] +
                avail_score * self.optimization_weights['availability'] +
                sla_score * self.optimization_weights['sla_compliance']
            )
            
            scores[agent_id] = {
                'total_score': total_score,
                'performance_score': perf_score,
                'cost_score': cost_score,
                'availability_score': avail_score,
                'sla_score': sla_score,
                'reason': self._generate_assignment_reason(perf_score, cost_score, avail_score, sla_score)
            }
        
        return scores

    async def _calculate_performance_score(
        self,
        profile: AgentProfile,
        task: TaskRequirement
    ) -> float:
        """Calculate performance score for agent-task pair"""
        # Base score from historical performance
        base_score = profile.performance_metrics.get('success_rate', 0.5)
        
        # Task-specific success rate
        if profile.success_rate_by_task:
            task_type = task.required_capabilities[0].value if task.required_capabilities else 'default'
            task_score = profile.success_rate_by_task.get(task_type, base_score)
            base_score = (base_score + task_score) / 2.0
        
        # Adjust for current load
        load_factor = 1.0 - (profile.current_load / profile.max_capacity)
        
        # Performance level bonus
        level_bonus = {
            AgentPerformanceLevel.EXCELLENT: 0.2,
            AgentPerformanceLevel.GOOD: 0.1,
            AgentPerformanceLevel.FAIR: 0.0,
            AgentPerformanceLevel.POOR: -0.1,
            AgentPerformanceLevel.FAILING: -0.2
        }.get(profile.performance_level, 0.0)
        
        # ML prediction
        ml_score = await self._predict_task_success(profile, task)
        
        # Combine scores
        final_score = (base_score * 0.4 + ml_score * 0.4 + level_bonus + 0.5) * load_factor
        
        return max(0.0, min(1.0, final_score))

    async def _predict_task_success(
        self,
        profile: AgentProfile,
        task: TaskRequirement
    ) -> float:
        """Use ML to predict task success probability"""
        try:
            # Create feature vector
            features = self._create_task_agent_features(profile, task)
            
            # Ensure model is trained
            if not hasattr(self.performance_predictor, 'n_features_in_'):
                return 0.5  # Default if model not trained
            
            # Predict
            features_scaled = self.scaler.transform([features])
            prediction = self.performance_predictor.predict(features_scaled)[0]
            
            return max(0.0, min(1.0, prediction))
            
        except Exception as e:
            logger.debug(f"ML prediction failed, using fallback: {e}")
            return 0.5

    def _create_task_agent_features(
        self,
        profile: AgentProfile,
        task: TaskRequirement
    ) -> List[float]:
        """Create feature vector for task-agent pair"""
        features = []
        
        # Agent features
        features.extend([
            profile.current_load / max(profile.max_capacity, 1.0),
            profile.performance_metrics.get('success_rate', 0.5),
            profile.performance_metrics.get('avg_response_time', 1000.0) / 1000.0,
            profile.performance_metrics.get('error_rate', 0.0),
        ])
        
        # Task features
        priority_encoding = {
            TaskPriority.CRITICAL: 1.0,
            TaskPriority.HIGH: 0.75,
            TaskPriority.NORMAL: 0.5,
            TaskPriority.LOW: 0.25,
            TaskPriority.BACKGROUND: 0.0
        }
        features.append(priority_encoding.get(task.priority, 0.5))
        features.append(task.estimated_duration / 3600.0)  # Normalize to hours
        
        # Capability match score
        match_score = len(set(task.required_capabilities) & set(profile.capabilities)) / max(len(task.required_capabilities), 1)
        features.append(match_score)
        
        return features

    def _calculate_cost_score(
        self,
        profile: AgentProfile,
        task: TaskRequirement
    ) -> float:
        """Calculate cost efficiency score"""
        if profile.cost_per_hour == 0:
            return 1.0
        
        estimated_cost = (task.estimated_duration / 3600.0) * profile.cost_per_hour
        
        # Normalize cost (assuming max cost of $10/hour)
        cost_score = 1.0 - min(estimated_cost / 10.0, 1.0)
        
        return cost_score

    def _calculate_availability_score(self, profile: AgentProfile) -> float:
        """Calculate availability score"""
        # Based on current load
        load_score = 1.0 - (profile.current_load / profile.max_capacity)
        
        # Time since last update (freshness)
        time_delta = (datetime.utcnow() - profile.last_updated).total_seconds()
        freshness_score = max(0.0, 1.0 - (time_delta / 300.0))  # 5 min threshold
        
        return (load_score * 0.7 + freshness_score * 0.3)

    def _calculate_sla_score(
        self,
        profile: AgentProfile,
        task: TaskRequirement
    ) -> float:
        """Calculate SLA compliance score"""
        if not task.sla_requirements or not task.deadline:
            return 1.0
        
        # Check if agent can meet deadline
        estimated_completion = datetime.utcnow() + timedelta(seconds=task.estimated_duration)
        time_buffer = (task.deadline - estimated_completion).total_seconds()
        
        if time_buffer < 0:
            return 0.0  # Cannot meet deadline
        
        # Score based on time buffer
        buffer_hours = time_buffer / 3600.0
        score = min(buffer_hours / 24.0, 1.0)  # Normalize to 24 hours
        
        return score

    def _generate_assignment_reason(
        self,
        perf: float,
        cost: float,
        avail: float,
        sla: float
    ) -> str:
        """Generate human-readable assignment reason"""
        reasons = []
        
        if perf > 0.8:
            reasons.append("excellent performance history")
        if cost > 0.8:
            reasons.append("cost-effective")
        if avail > 0.8:
            reasons.append("high availability")
        if sla > 0.9:
            reasons.append("meets SLA requirements")
        
        if not reasons:
            reasons.append("best available option")
        
        return ", ".join(reasons)

    async def _predict_completion_time(
        self,
        agent_id: str,
        task: TaskRequirement
    ) -> datetime:
        """Predict when task will complete"""
        profile = self.agent_profiles[agent_id]
        
        # Base estimate
        base_duration = task.estimated_duration
        
        # Adjust for agent performance
        perf_factor = profile.performance_metrics.get('avg_response_time', 1000) / 1000.0
        
        # Adjust for current load
        load_factor = 1.0 + (profile.current_load / profile.max_capacity) * 0.5
        
        # Calculate adjusted duration
        adjusted_duration = base_duration * perf_factor * load_factor
        
        return datetime.utcnow() + timedelta(seconds=adjusted_duration)

    def _update_agent_load(self, agent_id: str, task_duration: float):
        """Update agent's current load"""
        if agent_id in self.agent_profiles:
            self.agent_profiles[agent_id].current_load += task_duration
            self.agent_profiles[agent_id].last_updated = datetime.utcnow()

    def _record_task_assignment(
        self,
        task_id: str,
        agent_id: str,
        confidence: float
    ):
        """Record task assignment for learning"""
        self.task_history.append({
            'task_id': task_id,
            'agent_id': agent_id,
            'assigned_at': datetime.utcnow(),
            'confidence': confidence
        })

    async def record_task_completion(
        self,
        task_id: str,
        agent_id: str,
        success: bool,
        actual_duration: float,
        metrics: Dict[str, any]
    ):
        """Record task completion for learning"""
        # Update task history
        for record in self.task_history:
            if record['task_id'] == task_id:
                record['completed_at'] = datetime.utcnow()
                record['success'] = success
                record['actual_duration'] = actual_duration
                record['metrics'] = metrics
                break
        
        # Update agent performance history
        self.agent_performance_history[agent_id].append({
            'task_id': task_id,
            'timestamp': datetime.utcnow(),
            'success': success,
            'duration': actual_duration,
            'metrics': metrics
        })
        
        # Decrease agent load
        if agent_id in self.agent_profiles:
            self.agent_profiles[agent_id].current_load = max(
                0, 
                self.agent_profiles[agent_id].current_load - actual_duration
            )
        
        # Check if retraining needed
        await self._check_retrain_models()

    async def _check_retrain_models(self):
        """Check if models need retraining"""
        if self.last_training_time:
            time_since_training = (datetime.utcnow() - self.last_training_time).total_seconds()
            if time_since_training < self.retrain_interval:
                return
        
        # Check if enough samples
        completed_tasks = [t for t in self.task_history if 'completed_at' in t]
        if len(completed_tasks) < self.min_training_samples:
            return
        
        # Trigger retraining
        asyncio.create_task(self._retrain_models())

    async def _retrain_models(self):
        """Retrain ML models with new data"""
        try:
            logger.info("Starting model retraining...")
            
            # Prepare training data
            X_train, y_train = self._prepare_training_data()
            
            if len(X_train) < self.min_training_samples:
                logger.warning("Insufficient training samples")
                return
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X_train)
            
            # Train performance predictor
            self.performance_predictor.fit(X_scaled, y_train)
            self._save_model(self.performance_predictor, 'performance_predictor')
            
            # Train failure predictor
            y_failure = [1 if y < 0.5 else 0 for y in y_train]
            self.failure_predictor.fit(X_scaled, y_failure)
            
            self.last_training_time = datetime.utcnow()
            
            logger.info(f"Model retraining complete. Samples: {len(X_train)}")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}", exc_info=True)

    def _prepare_training_data(self) -> Tuple[List, List]:
        """Prepare training data from task history"""
        X = []
        y = []
        
        completed_tasks = [t for t in self.task_history if 'completed_at' in t and 'success' in t]
        
        for task_record in completed_tasks:
            try:
                agent_id = task_record['agent_id']
                if agent_id not in self.agent_profiles:
                    continue
                
                profile = self.agent_profiles[agent_id]
                
                # Reconstruct task (simplified)
                task = TaskRequirement(
                    task_id=task_record['task_id'],
                    required_capabilities=[],
                    priority=TaskPriority.NORMAL,
                    deadline=None,
                    estimated_duration=task_record.get('actual_duration', 0),
                    resource_requirements={}
                )
                
                features = self._create_task_agent_features(profile, task)
                X.append(features)
                
                # Target: success rate
                y.append(1.0 if task_record['success'] else 0.0)
                
            except Exception as e:
                logger.debug(f"Skipping task record due to error: {e}")
                continue
        
        return X, y

    async def intelligent_load_balancing(self) -> Dict[str, any]:
        """Perform intelligent load balancing across agents"""
        try:
            # Calculate load distribution
            load_stats = self._calculate_load_distribution()
            
            # Detect imbalances
            imbalances = self._detect_load_imbalances(load_stats)
            
            if not imbalances:
                return {"status": "balanced", "action": "none"}
            
            # Generate rebalancing plan
            plan = await self._create_rebalancing_plan(imbalances)
            
            # Execute rebalancing
            await self._execute_rebalancing(plan)
            
            return {
                "status": "rebalanced",
                "imbalances_detected": len(imbalances),
                "actions_taken": len(plan),
                "plan": plan
            }
            
        except Exception as e:
            logger.error(f"Load balancing failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _calculate_load_distribution(self) -> Dict[str, float]:
        """Calculate current load distribution"""
        load_stats = {}
        
        for agent_id, profile in self.agent_profiles.items():
            utilization = profile.current_load / max(profile.max_capacity, 1.0)
            load_stats[agent_id] = utilization
        
        return load_stats

    def _detect_load_imbalances(self, load_stats: Dict[str, float]) -> List[Dict]:
        """Detect agents with load imbalances"""
        if not load_stats:
            return []
        
        avg_load = np.mean(list(load_stats.values()))
        std_load = np.std(list(load_stats.values()))
        
        imbalances = []
        
        for agent_id, load in load_stats.items():
            deviation = abs(load - avg_load)
            
            if deviation > self.rebalance_threshold:
                imbalances.append({
                    'agent_id': agent_id,
                    'current_load': load,
                    'average_load': avg_load,
                    'deviation': deviation,
                    'type': 'overloaded' if load > avg_load else 'underutilized'
                })
        
        return imbalances

    async def _create_rebalancing_plan(self, imbalances: List[Dict]) -> List[Dict]:
        """Create load rebalancing plan"""
        plan = []
        
        overloaded = [i for i in imbalances if i['type'] == 'overloaded']
        underutilized = [i for i in imbalances if i['type'] == 'underutilized']
        
        for overloaded_agent in overloaded:
            for underutilized_agent in underutilized:
                # Calculate transfer amount
                transfer_amount = min(
                    overloaded_agent['deviation'] / 2,
                    (overloaded_agent['average_load'] - underutilized_agent['current_load']) / 2
                )
                
                if transfer_amount > 0.05:  # Minimum 5% transfer
                    plan.append({
                        'from_agent': overloaded_agent['agent_id'],
                        'to_agent': underutilized_agent['agent_id'],
                        'transfer_amount': transfer_amount,
                        'action': 'redistribute_tasks'
                    })
        
        return plan

    async def _execute_rebalancing(self, plan: List[Dict]):
        """Execute load rebalancing plan"""
        for action in plan:
            try:
                # This would integrate with task queue management
                logger.info(f"Rebalancing: {action['from_agent']} -> {action['to_agent']}")
                # Actual implementation would move queued tasks between agents
            except Exception as e:
                logger.error(f"Rebalancing action failed: {e}")

    async def predictive_maintenance(self) -> List[Dict]:
        """Predict which agents need maintenance"""
        maintenance_schedule = []
        
        for agent_id, profile in self.agent_profiles.items():
            # Calculate maintenance score
            score = self._calculate_maintenance_score(profile)
            
            if score > 0.7:  # High maintenance need
                maintenance_schedule.append({
                    'agent_id': agent_id,
                    'maintenance_score': score,
                    'recommended_time': datetime.utcnow() + timedelta(days=7),
                    'reasons': self._get_maintenance_reasons(profile),
                    'priority': 'high' if score > 0.85 else 'medium'
                })
        
        return maintenance_schedule

    def _calculate_maintenance_score(self, profile: AgentProfile) -> float:
        """Calculate maintenance need score"""
        score = 0.0
        
        # Error rate factor
        error_rate = profile.performance_metrics.get('error_rate', 0.0)
        score += min(error_rate * 2, 0.3)
        
        # Performance degradation
        if profile.performance_level in [AgentPerformanceLevel.POOR, AgentPerformanceLevel.FAILING]:
            score += 0.3
        
        # Uptime factor
        uptime = profile.performance_metrics.get('uptime_hours', 0)
        if uptime > 720:  # 30 days
            score += 0.2
        
        # Recent failures
        recent_history = list(self.agent_performance_history.get(profile.agent_id, []))[-20:]
        if recent_history:
            failure_rate = sum(1 for h in recent_history if not h.get('success', True)) / len(recent_history)
            score += min(failure_rate, 0.2)
        
        return min(score, 1.0)

    def _get_maintenance_reasons(self, profile: AgentProfile) -> List[str]:
        """Get reasons for maintenance recommendation"""
        reasons = []
        
        if profile.performance_metrics.get('error_rate', 0) > 0.1:
            reasons.append("High error rate")
        
        if profile.performance_level == AgentPerformanceLevel.POOR:
            reasons.append("Poor performance")
        
        if profile.performance_metrics.get('uptime_hours', 0) > 720:
            reasons.append("Extended uptime without maintenance")
        
        return reasons or ["Preventive maintenance"]

    async def capacity_planning(self, forecast_days: int = 30) -> Dict[str, any]:
        """Perform capacity planning and forecasting"""
        # Analyze historical demand
        demand_history = self._analyze_demand_history()
        
        # Forecast future demand
        forecasted_demand = self._forecast_demand(demand_history, forecast_days)
        
        # Calculate current capacity
        total_capacity = sum(p.max_capacity for p in self.agent_profiles.values())
        available_capacity = total_capacity - sum(p.current_load for p in self.agent_profiles.values())
        
        # Calculate capacity gap
        peak_demand = max(forecasted_demand.values())
        capacity_gap = max(0, peak_demand - available_capacity)
        
        # Generate recommendations
        recommendations = self._generate_capacity_recommendations(capacity_gap, forecasted_demand)
        
        return {
            'current_capacity': total_capacity,
            'available_capacity': available_capacity,
            'forecasted_peak_demand': peak_demand,
            'capacity_gap': capacity_gap,
            'forecast': forecasted_demand,
            'recommendations': recommendations
        }

    def _analyze_demand_history(self) -> Dict[str, float]:
        """Analyze historical task demand"""
        demand_by_day = defaultdict(int)
        
        for task in self.task_history:
            day = task['assigned_at'].date().isoformat()
            demand_by_day[day] += 1
        
        return dict(demand_by_day)

    def _forecast_demand(self, history: Dict[str, float], days: int) -> Dict[str, float]:
        """Forecast future demand (simplified linear projection)"""
        if not history:
            return {f"day_{i}": 100 for i in range(days)}
        
        values = list(history.values())
        avg_demand = np.mean(values)
        trend = (values[-1] - values[0]) / max(len(values), 1)
        
        forecast = {}
        for i in range(days):
            forecast[f"day_{i}"] = max(0, avg_demand + trend * i)
        
        return forecast

    def _generate_capacity_recommendations(
        self,
        gap: float,
        forecast: Dict[str, float]
    ) -> List[str]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        if gap > 0:
            agents_needed = int(np.ceil(gap / 100))  # Assuming 100 capacity units per agent
            recommendations.append(f"Add {agents_needed} new agents to meet forecasted demand")
            recommendations.append(f"Capacity gap: {gap:.0f} units")
        
        # Check for efficiency improvements
        avg_utilization = np.mean([p.current_load / p.max_capacity for p in self.agent_profiles.values()])
        if avg_utilization < 0.3:
            recommendations.append("Consider consolidating agents - current utilization is low")
        
        # Check for cost optimization
        expensive_agents = [
            p for p in self.agent_profiles.values() 
            if p.cost_per_hour > 5.0 and p.current_load / p.max_capacity < 0.5
        ]
        if expensive_agents:
            recommendations.append(f"Optimize {len(expensive_agents)} underutilized expensive agents")
        
        if not recommendations:
            recommendations.append("Current capacity is adequate for forecasted demand")
        
        return recommendations

    async def optimize_agent_assignments(self) -> Dict[str, any]:
        """Optimize existing agent-task assignments"""
        optimization_results = {
            'reassignments': 0,
            'improvements': [],
            'estimated_benefit': 0.0
        }
        
        # Analyze current assignments
        active_assignments = [t for t in self.task_history if 'completed_at' not in t]
        
        for assignment in active_assignments:
            task_id = assignment['task_id']
            current_agent = assignment['agent_id']
            
            # Find potentially better agent
            better_agent = await self._find_better_assignment(task_id, current_agent)
            
            if better_agent:
                optimization_results['reassignments'] += 1
                optimization_results['improvements'].append({
                    'task_id': task_id,
                    'from': current_agent,
                    'to': better_agent['agent_id'],
                    'improvement': better_agent['improvement']
                })
                optimization_results['estimated_benefit'] += better_agent['improvement']
        
        return optimization_results

    async def _find_better_assignment(
        self,
        task_id: str,
        current_agent_id: str
    ) -> Optional[Dict]:
        """Find if there's a better agent for a task"""
        # Simplified - would need actual task object
        current_profile = self.agent_profiles.get(current_agent_id)
        if not current_profile:
            return None
        
        # Check all other agents
        for agent_id, profile in self.agent_profiles.items():
            if agent_id == current_agent_id:
                continue
            
            # Compare performance potential
            current_score = current_profile.performance_metrics.get('success_rate', 0.5)
            candidate_score = profile.performance_metrics.get('success_rate', 0.5)
            
            # Consider load
            current_load_factor = 1.0 - (current_profile.current_load / current_profile.max_capacity)
            candidate_load_factor = 1.0 - (profile.current_load / profile.max_capacity)
            
            improvement = (candidate_score * candidate_load_factor) - (current_score * current_load_factor)
            
            if improvement > 0.2:  # Significant improvement threshold
                return {
                    'agent_id': agent_id,
                    'improvement': improvement
                }
        
        return None

    async def get_orchestration_analytics(self) -> Dict[str, any]:
        """Get comprehensive orchestration analytics"""
        total_tasks = len(self.task_history)
        completed_tasks = [t for t in self.task_history if 'completed_at' in t]
        successful_tasks = [t for t in completed_tasks if t.get('success', False)]
        
        # Calculate metrics
        success_rate = len(successful_tasks) / max(len(completed_tasks), 1)
        
        # Agent utilization
        utilization_by_agent = {
            agent_id: profile.current_load / profile.max_capacity
            for agent_id, profile in self.agent_profiles.items()
        }
        avg_utilization = np.mean(list(utilization_by_agent.values())) if utilization_by_agent else 0.0
        
        # Performance distribution
        perf_distribution = defaultdict(int)
        for profile in self.agent_profiles.values():
            perf_distribution[profile.performance_level.value] += 1
        
        # Task distribution by agent
        task_distribution = defaultdict(int)
        for task in self.task_history:
            task_distribution[task['agent_id']] += 1
        
        # Model performance
        model_accuracy = self._calculate_model_accuracy()
        
        return {
            'total_tasks_assigned': total_tasks,
            'completed_tasks': len(completed_tasks),
            'success_rate': success_rate,
            'active_agents': len(self.agent_profiles),
            'average_utilization': avg_utilization,
            'utilization_by_agent': utilization_by_agent,
            'performance_distribution': dict(perf_distribution),
            'task_distribution': dict(task_distribution),
            'model_accuracy': model_accuracy,
            'clusters': len(self.agent_clusters),
            'last_training': self.last_training_time.isoformat() if self.last_training_time else None
        }

    def _calculate_model_accuracy(self) -> float:
        """Calculate ML model prediction accuracy"""
        if not hasattr(self.performance_predictor, 'n_features_in_'):
            return 0.0
        
        # Compare predictions vs actual outcomes for recent tasks
        recent_completed = [
            t for t in self.task_history 
            if 'completed_at' in t and 'success' in t
        ][-100:]  # Last 100 tasks
        
        if not recent_completed:
            return 0.0
        
        correct_predictions = 0
        for task in recent_completed:
            predicted_success = task.get('confidence', 0.5) > 0.5
            actual_success = task.get('success', False)
            if predicted_success == actual_success:
                correct_predictions += 1
        
        return correct_predictions / len(recent_completed)

    async def start_performance_monitoring(self):
        """Start continuous performance monitoring loop"""
        logger.info("Starting orchestration performance monitoring")
        
        while True:
            try:
                # Update agent clusters
                self._update_agent_clusters()
                
                # Perform load balancing
                await self.intelligent_load_balancing()
                
                # Check for maintenance needs
                maintenance = await self.predictive_maintenance()
                if maintenance:
                    logger.info(f"{len(maintenance)} agents need maintenance")
                
                # Capacity planning check
                if len(self.task_history) % 1000 == 0:  # Periodic capacity planning
                    capacity = await self.capacity_planning()
                    if capacity['capacity_gap'] > 0:
                        logger.warning(f"Capacity gap detected: {capacity['capacity_gap']}")
                
                await asyncio.sleep(settings.ai.agent_orchestration.performance_monitoring_interval)
                
            except asyncio.CancelledError:
                logger.info("Performance monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def health_check(self) -> str:
        """Health check for orchestrator"""
        try:
            if not self.agent_profiles:
                return "unhealthy: No agents registered"
            
            # Check model status
            if not hasattr(self.performance_predictor, 'n_features_in_'):
                return "degraded: Models not trained"
            
            return "healthy"
        except Exception as e:
            logger.error(f"Orchestrator health check failed: {e}")
            return "unhealthy"
