# analytics/engine.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
import json
import pickle
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AdvancedAnalyticsEngine:
    """Advanced analytics engine with ML capabilities for business intelligence"""
    
    def __init__(self):
        self.db = DatabaseUtils()
        self.cache = CacheManager()
        self.ml_models = {}
        self._init_ml_models()
    
    def _init_ml_models(self):
        """Initialize machine learning models"""
        # Project risk prediction model
        self.ml_models['project_risk'] = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        
        # Resource optimization model
        self.ml_models['resource_optimization'] = LinearRegression()
        
        # Anomaly detection model
        self.ml_models['anomaly_detection'] = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Team clustering model
        self.ml_models['team_clustering'] = KMeans(
            n_clusters=4,
            random_state=42
        )
        
        # Model training status
        self.model_training_status = {
            'project_risk': False,
            'resource_optimization': False,
            'anomaly_detection': False,
            'team_clustering': False
        }
    
    async def generate_project_insights(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive insights for a project"""
        cache_key = f"project_insights:{project_id}"
        cached_insights = await self.cache.get(cache_key)
        
        if cached_insights:
            return cached_insights
        
        # Get project data
        project_data = await self._get_project_data(project_id)
        if not project_data:
            return {"error": "Project not found"}
        
        # Calculate various insights
        insights = {
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat(),
            "performance_metrics": await self._calculate_performance_metrics(project_data),
            "risk_assessment": await self._assess_project_risks(project_data),
            "team_analysis": await self._analyze_team_performance(project_data),
            "timeline_analysis": await self._analyze_project_timeline(project_data),
            "resource_utilization": await self._analyze_resource_utilization(project_data),
            "financial_metrics": await self._calculate_financial_metrics(project_data),
            "recommendations": await self._generate_recommendations(project_data)
        }
        
        # Cache insights for 1 hour
        await self.cache.set(cache_key, insights, expire=3600)
        
        return insights
    
    async def predict_project_risks(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict project risks using ML model"""
        if not self.model_training_status['project_risk']:
            await self._train_risk_prediction_model()
        
        # Prepare features for prediction
        features = self._extract_risk_features(project_data)
        
        if not features:
            return {"error": "Insufficient data for prediction"}
        
        # Make prediction
        try:
            risk_probabilities = self.ml_models['project_risk'].predict_proba([features])[0]
            risk_level = self.ml_models['project_risk'].predict([features])[0]
            
            return {
                "risk_level": risk_level,
                "probabilities": {
                    "low": float(risk_probabilities[0]),
                    "medium": float(risk_probabilities[1]),
                    "high": float(risk_probabilities[2])
                },
                "key_risk_factors": self._identify_risk_factors(features),
                "confidence_score": float(max(risk_probabilities))
            }
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
            return {"error": "Prediction failed"}
    
    async def optimize_resource_allocation(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize resource allocation across projects"""
        if not self.model_training_status['resource_optimization']:
            await self._train_resource_optimization_model()
        
        # Analyze current resource allocation
        current_allocation = await self._analyze_current_allocation(projects)
        
        # Predict optimal allocation
        optimal_allocation = await self._predict_optimal_allocation(projects)
        
        # Calculate optimization recommendations
        recommendations = await self._generate_allocation_recommendations(
            current_allocation, optimal_allocation
        )
        
        return {
            "current_allocation": current_allocation,
            "optimal_allocation": optimal_allocation,
            "recommendations": recommendations,
            "expected_improvement": await self._calculate_expected_improvement(
                current_allocation, optimal_allocation
            )
        }
    
    async def calculate_team_productivity_metrics(self, team_id: str = None) -> Dict[str, Any]:
        """Calculate comprehensive team productivity metrics"""
        # Get team data
        team_data = await self._get_team_data(team_id)
        
        if not team_data:
            return {"error": "No team data available"}
        
        # Calculate various productivity metrics
        metrics = {
            "team_id": team_id or "all_teams",
            "timestamp": datetime.utcnow().isoformat(),
            "overall_productivity": await self._calculate_overall_productivity(team_data),
            "task_completion_rates": await self._calculate_completion_rates(team_data),
            "quality_metrics": await self._calculate_quality_metrics(team_data),
            "efficiency_metrics": await self._calculate_efficiency_metrics(team_data),
            "collaboration_metrics": await self._calculate_collaboration_metrics(team_data),
            "trend_analysis": await self._analyze_productivity_trends(team_data),
            "benchmark_comparison": await self._compare_to_benchmarks(team_data)
        }
        
        return metrics
    
    async def _train_risk_prediction_model(self):
        """Train the project risk prediction model"""
        try:
            # Get historical project data for training
            training_data = await self._get_training_data()
            
            if not training_data or len(training_data) < 100:
                logger.warning("Insufficient training data for risk prediction model")
                return
            
            # Prepare features and labels
            X = []
            y = []
            
            for project in training_data:
                features = self._extract_risk_features(project)
                if features and 'risk_level' in project:
                    X.append(features)
                    y.append(project['risk_level'])
            
            if len(X) > 50:  # Minimum samples for training
                # Train the model
                self.ml_models['project_risk'].fit(X, y)
                self.model_training_status['project_risk'] = True
                
                logger.info("Project risk prediction model trained successfully")
        
        except Exception as e:
            logger.error(f"Failed to train risk prediction model: {e}")
    
    async def _train_resource_optimization_model(self):
        """Train the resource optimization model"""
        try:
            # Get historical resource allocation data
            allocation_data = await self._get_allocation_training_data()
            
            if not allocation_data or len(allocation_data) < 50:
                logger.warning("Insufficient training data for resource optimization model")
                return
            
            # Prepare features and targets
            X = []
            y = []
            
            for allocation in allocation_data:
                features = self._extract_allocation_features(allocation)
                if features and 'efficiency_score' in allocation:
                    X.append(features)
                    y.append(allocation['efficiency_score'])
            
            if len(X) > 20:  # Minimum samples for regression
                # Train the model
                self.ml_models['resource_optimization'].fit(X, y)
                self.model_training_status['resource_optimization'] = True
                
                logger.info("Resource optimization model trained successfully")
        
        except Exception as e:
            logger.error(f"Failed to train resource optimization model: {e}")
    
    def _extract_risk_features(self, project_data: Dict[str, Any]) -> List[float]:
        """Extract features for risk prediction"""
        features = []
        
        # Project complexity features
        features.append(project_data.get('team_size', 0))
        features.append(project_data.get('task_count', 0))
        features.append(project_data.get('dependency_count', 0))
        
        # Timeline features
        if 'deadline' in project_data and 'start_date' in project_data:
            timeline_days = (project_data['deadline'] - project_data['start_date']).days
            features.append(timeline_days)
        else:
            features.append(0)
        
        # Budget features
        features.append(project_data.get('budget', 0))
        features.append(project_data.get('actual_spend', 0))
        
        # Historical performance features
        features.append(project_data.get('historical_success_rate', 0.5))
        features.append(project_data.get('avg_task_completion_time', 0))
        
        return features
    
    def _identify_risk_factors(self, features: List[float]) -> List[Dict[str, Any]]:
        """Identify key risk factors from features"""
        risk_factors = []
        feature_names = [
            'team_size', 'task_count', 'dependency_count', 'timeline_days',
            'budget', 'actual_spend', 'historical_success_rate', 'avg_completion_time'
        ]
        
        # Define risk thresholds (these would be tuned based on historical data)
        thresholds = {
            'team_size': 10,
            'task_count': 50,
            'dependency_count': 15,
            'timeline_days': 30,
            'budget': 100000,
            'actual_spend': 0.8,  # Percentage of budget spent
            'historical_success_rate': 0.7,
            'avg_completion_time': 14  # Days
        }
        
        for i, (feature_name, value) in enumerate(zip(feature_names, features)):
            threshold = thresholds.get(feature_name)
            
            if threshold is not None:
                if feature_name == 'historical_success_rate' and value < threshold:
                    risk_factors.append({
                        'factor': feature_name,
                        'value': value,
                        'risk': 'Low historical success rate'
                    })
                elif feature_name == 'actual_spend' and value > threshold:
                    risk_factors.append({
                        'factor': feature_name,
                        'value': value,
                        'risk': 'High budget utilization'
                    })
                elif value > threshold:
                    risk_factors.append({
                        'factor': feature_name,
                        'value': value,
                        'risk': f'High {feature_name.replace("_", " ")}'
                    })
        
        return risk_factors
    
    async def _get_project_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive project data for analysis"""
        async with self.db.get_session() as session:
            # Get project details
            project = await session.get(ProjectRecord, project_id)
            if not project:
                return None
            
            # Get related data
            tasks = await session.execute(
                select(TaskRecord).where(TaskRecord.project_id == project_id)
            )
            tasks = tasks.scalars().all()
            
            team_members = await session.execute(
                select(UserRecord).where(UserRecord.id.in_(project.team_members or []))
            )
            team_members = team_members.scalars().all()
            
            # Compile comprehensive data
            project_data = {
                **project.to_dict(),
                'tasks': [task.to_dict() for task in tasks],
                'team_members': [member.to_dict() for member in team_members],
                'task_count': len(tasks),
                'completed_tasks': len([t for t in tasks if t.status == 'completed']),
                'team_size': len(team_members)
            }
            
            return project_data
    
    async def _calculate_performance_metrics(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate project performance metrics"""
        tasks = project_data.get('tasks', [])
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        # Basic metrics
        completion_rate = len(completed_tasks) / len(tasks) if tasks else 0
        
        # Time metrics
        task_durations = [
            (t.get('updated_at') - t.get('created_at')).total_seconds() / 3600
            for t in completed_tasks if t.get('updated_at') and t.get('created_at')
        ]
        avg_duration = sum(task_durations) / len(task_durations) if task_durations else 0
        
        # Quality metrics
        quality_scores = [t.get('quality_score', 0) for t in completed_tasks]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "completion_rate": completion_rate,
            "avg_task_duration_hours": avg_duration,
            "avg_quality_score": avg_quality,
            "on_time_performance": await self._calculate_on_time_performance(project_data),
            "budget_adherence": await self._calculate_budget_adherence(project_data)
        }
    
    async def _assess_project_risks(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess project risks using multiple methods"""
        # ML-based risk prediction
        ml_prediction = await self.predict_project_risks(project_data)
        
        # Rule-based risk assessment
        rule_based_risks = await self._rule_based_risk_assessment(project_data)
        
        # Historical comparison
        historical_risks = await self._historical_risk_assessment(project_data)
        
        return {
            "ml_prediction": ml_prediction,
            "rule_based_assessment": rule_based_risks,
            "historical_comparison": historical_risks,
            "overall_risk_score": self._calculate_overall_risk_score(
                ml_prediction, rule_based_risks, historical_risks
            )
        }
    
    async def _analyze_team_performance(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team performance metrics"""
        team_members = project_data.get('team_members', [])
        tasks = project_data.get('tasks', [])
        
        performance_metrics = {}
        
        for member in team_members:
            member_id = member.get('id')
            member_tasks = [t for t in tasks if t.get('assigned_to') == member_id]
            completed_tasks = [t for t in member_tasks if t.get('status') == 'completed']
            
            if member_tasks:
                performance_metrics[member_id] = {
                    "completion_rate": len(completed_tasks) / len(member_tasks),
                    "avg_task_duration": await self._calculate_avg_duration(completed_tasks),
                    "quality_score": await self._calculate_avg_quality(completed_tasks),
                    "task_complexity": await self._calculate_avg_complexity(member_tasks),
                    "collaboration_score": await self._calculate_collaboration_score(member_id, tasks)
                }
        
        return {
            "individual_performance": performance_metrics,
            "team_metrics": await self._calculate_team_level_metrics(performance_metrics),
            "skill_gaps": await self._identify_skill_gaps(team_members, tasks),
            "recommendations": await self._generate_team_recommendations(performance_metrics)
        }

# Real-time analytics dashboard
class RealTimeAnalyticsDashboard:
    """Real-time analytics dashboard for business intelligence"""
    
    def __init__(self):
        self.analytics_engine = AdvancedAnalyticsEngine()
        self.data_visualization = DataVisualization()
        self.cache = CacheManager()
    
    async def get_dashboard_data(self, timeframe: str = "7d") -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        cache_key = f"dashboard:{timeframe}"
        cached_data = await self.cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Calculate various dashboard metrics
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "timeframe": timeframe,
            "overview_metrics": await self._get_overview_metrics(timeframe),
            "project_analytics": await self._get_project_analytics(timeframe),
            "team_analytics": await self._get_team_analytics(timeframe),
            "financial_analytics": await self._get_financial_analytics(timeframe),
            "risk_analytics": await self._get_risk_analytics(timeframe),
            "trend_analysis": await self._get_trend_analysis(timeframe),
            "top_performers": await self._get_top_performers(timeframe),
            "alerts_and_insights": await self._get_alerts_and_insights()
        }
        
        # Cache for 5 minutes for real-time dashboards
        await self.cache.set(cache_key, dashboard_data, expire=300)
        
        return dashboard_data
    
    async def _get_overview_metrics(self, timeframe: str) -> Dict[str, Any]:
        """Get overview metrics for dashboard"""
        return {
            "total_projects": await self._count_projects(timeframe),
            "active_projects": await self._count_active_projects(),
            "completed_projects": await self._count_completed_projects(timeframe),
            "total_tasks": await self._count_tasks(timeframe),
            "completed_tasks": await self._count_completed_tasks(timeframe),
            "active_users": await self._count_active_users(timeframe),
            "total_teams": await self._count_teams(),
            "overall_productivity": await self._calculate_overall_productivity(timeframe)
        }
    
    async def _get_project_analytics(self, timeframe: str) -> Dict[str, Any]:
        """Get project analytics"""
        return {
            "project_status_distribution": await self._get_project_status_distribution(),
            "project_completion_rates": await self._get_project_completion_rates(timeframe),
            "project_timeline_analysis": await self._analyze_project_timelines(timeframe),
            "project_budget_analysis": await self._analyze_project_budgets(timeframe),
            "project_risk_distribution": await self._get_project_risk_distribution()
        }
    
    async def _get_team_analytics(self, timeframe: str) -> Dict[str, Any]:
        """Get team analytics"""
        return {
            "team_performance_comparison": await self._compare_team_performance(timeframe),
            "team_capacity_utilization": await self._analyze_team_capacity(timeframe),
            "team_skill_distribution": await self._analyze_team_skills(),
            "team_collaboration_metrics": await self._analyze_team_collaboration(timeframe)
        }

# Predictive analytics for forecasting
class PredictiveAnalytics:
    """Predictive analytics for forecasting and trend prediction"""
    
    def __init__(self):
        self.analytics_engine = AdvancedAnalyticsEngine()
        self.time_series_models = {}
    
    async def forecast_project_completion(self, project_id: str) -> Dict[str, Any]:
        """Forecast project completion date and likelihood"""
        project_data = await self.analytics_engine._get_project_data(project_id)
        if not project_data:
            return {"error": "Project not found"}
        
        # Use multiple forecasting methods
        monte_carlo_forecast = await self._monte_carlo_simulation(project_data)
        regression_forecast = await self._regression_forecast(project_data)
        historical_forecast = await self._historical_comparison_forecast(project_data)
        
        # Combine forecasts
        combined_forecast = self._combine_forecasts(
            monte_carlo_forecast, regression_forecast, historical_forecast
        )
        
        return {
            "project_id": project_id,
            "forecasts": {
                "monte_carlo": monte_carlo_forecast,
                "regression": regression_forecast,
                "historical": historical_forecast,
                "combined": combined_forecast
            },
            "confidence_interval": await self._calculate_confidence_interval(combined_forecast),
            "risk_factors": await self._identify_forecast_risks(project_data)
        }
    
    async def predict_resource_demand(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Predict future resource demand"""
        historical_data = await self._get_historical_resource_data(timeframe)
        
        if not historical_data or len(historical_data) < 30:
            return {"error": "Insufficient historical data"}
        
        # Use time series forecasting
        demand_forecast = await self._time_series_forecast(historical_data)
        
        return {
            "timeframe": timeframe,
            "historical_demand": historical_data,
            "predicted_demand": demand_forecast,
            "confidence_level": await self._calculate_demand_confidence(demand_forecast),
            "recommendations": await self._generate_resource_recommendations(demand_forecast)
        }
    
    async def _monte_carlo_simulation(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform Monte Carlo simulation for project completion"""
        tasks = project_data.get('tasks', [])
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        pending_tasks = [t for t in tasks if t.get('status') != 'completed']
        
        if not pending_tasks:
            return {
                "expected_completion": project_data.get('deadline'),
                "confidence": 1.0,
                "simulation_runs": 0
            }
        
        # Get task duration distributions from historical data
        task_durations = await self._get_task_duration_distributions()
        
        # Run Monte Carlo simulation
        num_simulations = 1000
        completion_dates = []
        
        for _ in range(num_simulations):
            simulated_completion = await self._run_single_simulation(
                pending_tasks, task_durations, project_data
            )
            completion_dates.append(simulated_completion)
        
        # Calculate statistics
        expected_completion = np.percentile(completion_dates, 50)
        confidence_80 = np.percentile(completion_dates, 80)
        confidence_20 = np.percentile(completion_dates, 20)
        
        return {
            "expected_completion": expected_completion,
            "confidence_80": confidence_80,
            "confidence_20": confidence_20,
            "simulation_runs": num_simulations,
            "completion_likelihood": await self._calculate_completion_likelihood(
                completion_dates, project_data.get('deadline')
            )
        }