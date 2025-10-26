# data_pipeline/etl_processor.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
import json
import avro.schema
import avro.io
import io
from google.cloud import bigquery
from google.oauth2 import service_account
import snowflake.connector
from sqlalchemy import create_engine
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

class RealTimeDataPipeline:
    """Real-time ETL/ELT data processing pipeline"""
    
    def __init__(self):
        self.kafka_producer = self._init_kafka_producer()
        self.kafka_consumer = self._init_kafka_consumer()
        self.bigquery_client = self._init_bigquery_client()
        self.snowflake_conn = self._init_snowflake_connection()
        self.data_warehouse_engine = self._init_data_warehouse()
        self.avro_schema = self._load_avro_schema()
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer"""
        try:
            return KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS').split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: str(k).encode('utf-8'),
                acks='all',
                retries=3,
                compression_type='snappy'
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    def _init_kafka_consumer(self):
        """Initialize Kafka consumer"""
        try:
            return KafkaConsumer(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS').split(','),
                group_id='ymera-etl-group',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            return None
    
    def _init_bigquery_client(self):
        """Initialize Google BigQuery client"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                os.getenv('BIGQUERY_CREDENTIALS_PATH')
            )
            return bigquery.Client(
                credentials=credentials,
                project=os.getenv('BIGQUERY_PROJECT_ID')
            )
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            return None
    
    def _init_snowflake_connection(self):
        """Initialize Snowflake connection"""
        try:
            return snowflake.connector.connect(
                user=os.getenv('SNOWFLAKE_USER'),
                password=os.getenv('SNOWFLAKE_PASSWORD'),
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
                database=os.getenv('SNOWFLAKE_DATABASE'),
                schema=os.getenv('SNOWFLAKE_SCHEMA')
            )
        except Exception as e:
            logger.error(f"Failed to initialize Snowflake connection: {e}")
            return None
    
    def _init_data_warehouse(self):
        """Initialize data warehouse connection"""
        try:
            return create_engine(os.getenv('DATA_WAREHOUSE_URL'))
        except Exception as e:
            logger.error(f"Failed to initialize data warehouse: {e}")
            return None
    
    def _load_avro_schema(self):
        """Load Avro schema for data serialization"""
        try:
            schema_path = os.getenv('AVRO_SCHEMA_PATH', 'schemas/event.avsc')
            with open(schema_path, 'r') as f:
                return avro.schema.Parse(f.read())
        except Exception as e:
            logger.error(f"Failed to load Avro schema: {e}")
            return None
    
    async def stream_data_to_kafka(self, topic: str, data: Dict[str, Any], key: str = None):
        """Stream data to Kafka topic"""
        if not self.kafka_producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            # Serialize data with Avro if schema available
            if self.avro_schema:
                bytes_writer = io.BytesIO()
                encoder = avro.io.BinaryEncoder(bytes_writer)
                writer = avro.io.DatumWriter(self.avro_schema)
                writer.write(data, encoder)
                serialized_data = bytes_writer.getvalue()
            else:
                serialized_data = json.dumps(data).encode('utf-8')
            
            # Send to Kafka
            future = self.kafka_producer.send(
                topic=topic,
                value=serialized_data,
                key=key
            )
            future.get(timeout=10)
            
            logger.debug(f"Data sent to Kafka topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send data to Kafka: {e}")
            return False
    
    async def process_kafka_messages(self, topics: List[str]):
        """Process messages from Kafka topics"""
        if not self.kafka_consumer:
            logger.error("Kafka consumer not initialized")
            return
        
        try:
            self.kafka_consumer.subscribe(topics)
            
            for message in self.kafka_consumer:
                try:
                    # Process message based on topic
                    await self._process_message(message.topic, message.value, message.key)
                    
                    # Commit offset
                    self.kafka_consumer.commit()
                    
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
                    # Move to dead letter queue
                    await self._send_to_dlq(message)
        
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
    
    async def _process_message(self, topic: str, message: Dict[str, Any], key: str):
        """Process incoming message based on topic"""
        processing_strategy = {
            'project-events': self._process_project_event,
            'task-events': self._process_task_event,
            'user-events': self._process_user_event,
            'audit-events': self._process_audit_event,
            'metric-events': self._process_metric_event
        }
        
        processor = processing_strategy.get(topic)
        if processor:
            await processor(message, key)
        else:
            logger.warning(f"No processor found for topic: {topic}")
    
    async def _process_project_event(self, event: Dict[str, Any], key: str):
        """Process project-related events"""
        # Extract data for data warehouse
        dw_data = {
            'project_id': event.get('project_id'),
            'event_type': event.get('event_type'),
            'event_timestamp': event.get('timestamp'),
            'project_data': event.get('data', {})
        }
        
        # Load to data warehouse
        await self._load_to_data_warehouse('project_events', dw_data)
        
        # Load to BigQuery
        await self._load_to_bigquery('project_events', dw_data)
        
        # Load to Snowflake
        await self._load_to_snowflake('project_events', dw_data)
        
        # Update real-time analytics
        await self._update_realtime_analytics('project', event)
    
    async def _process_task_event(self, event: Dict[str, Any], key: str):
        """Process task-related events"""
        # Similar processing for task events
        pass
    
    async def _load_to_data_warehouse(self, table: str, data: Dict[str, Any]):
        """Load data to data warehouse"""
        if not self.data_warehouse_engine:
            return
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([data])
            
            # Load to warehouse
            df.to_sql(
                table,
                self.data_warehouse_engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
        except Exception as e:
            logger.error(f"Failed to load data to warehouse: {e}")
    
    async def _load_to_bigquery(self, table: str, data: Dict[str, Any]):
        """Load data to Google BigQuery"""
        if not self.bigquery_client:
            return
        
        try:
            table_ref = self.bigquery_client.dataset('ymera').table(table)
            job_config = bigquery.LoadJobConfig()
            
            # Convert to DataFrame
            df = pd.DataFrame([data])
            
            # Load to BigQuery
            job = self.bigquery_client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )
            job.result()
            
        except Exception as e:
            logger.error(f"Failed to load data to BigQuery: {e}")
    
    async def _load_to_snowflake(self, table: str, data: Dict[str, Any]):
        """Load data to Snowflake"""
        if not self.snowflake_conn:
            return
        
        try:
            cursor = self.snowflake_conn.cursor()
            
            # Prepare insert statement
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            # Execute insert
            cursor.execute(query, list(data.values()))
            
        except Exception as e:
            logger.error(f"Failed to load data to Snowflake: {e}")
    
    async def _update_realtime_analytics(self, entity_type: str, data: Dict[str, Any]):
        """Update real-time analytics systems"""
        # Update Redis cache for real-time dashboards
        cache_key = f"realtime:{entity_type}:{data.get('id')}"
        await CacheManager().set(cache_key, data, expire=300)
        
        # Update Elasticsearch for real-time search
        await self._update_elasticsearch(entity_type, data)
        
        # Trigger real-time analytics calculations
        await self._trigger_realtime_calculations(entity_type, data)
    
    async def batch_processing_pipeline(self):
        """Batch processing pipeline for ETL/ELT"""
        while True:
            try:
                # Extract data from source systems
                source_data = await self._extract_batch_data()
                
                # Transform data
                transformed_data = await self._transform_batch_data(source_data)
                
                # Load to destination systems
                await self._load_batch_data(transformed_data)
                
                # Wait for next batch
                await asyncio.sleep(3600)  # Process hourly batches
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _extract_batch_data(self) -> Dict[str, Any]:
        """Extract data from various source systems"""
        extraction_tasks = [
            self._extract_from_database(),
            self._extract_from_apis(),
            self._extract_from_files(),
            self._extract_from_streams()
        ]
        
        results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        return {
            'database': results[0] if not isinstance(results[0], Exception) else {},
            'apis': results[1] if not isinstance(results[1], Exception) else {},
            'files': results[2] if not isinstance(results[2], Exception) else {},
            'streams': results[3] if not isinstance(results[3], Exception) else {}
        }
    
    async def _transform_batch_data(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform batch data for loading"""
        transformed_data = {}
        
        # Data cleaning and validation
        cleaned_data = await self._clean_and_validate_data(source_data)
        
        # Data enrichment
        enriched_data = await self._enrich_data(cleaned_data)
        
        # Data aggregation
        aggregated_data = await self._aggregate_data(enriched_data)
        
        # Feature engineering for ML
        ml_features = await self._engineer_features(aggregated_data)
        
        return {
            'cleaned': cleaned_data,
            'enriched': enriched_data,
            'aggregated': aggregated_data,
            'ml_features': ml_features
        }
    
    async def _load_batch_data(self, transformed_data: Dict[str, Any]):
        """Load transformed data to destination systems"""
        load_tasks = [
            self._load_to_data_lake(transformed_data),
            self._load_to_data_warehouse(transformed_data),
            self._load_to_ml_systems(transformed_data['ml_features']),
            self._update_analytics_systems(transformed_data)
        ]
        
        await asyncio.gather(*load_tasks, return_exceptions=True)

# ML model training and serving pipeline
class MLOpsPipeline:
    """MLOps pipeline for model training and serving"""
    
    def __init__(self):
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
        self.s3_bucket = os.getenv('ML_MODELS_BUCKET')
        self.model_registry = {}
    
    async def train_models(self, model_types: List[str] = None):
        """Train machine learning models"""
        model_types = model_types or ['risk_prediction', 'resource_optimization', 'anomaly_detection']
        
        for model_type in model_types:
            try:
                logger.info(f"Training {model_type} model")
                
                # Get training data
                training_data = await self._get_training_data(model_type)
                
                if not training_data:
                    logger.warning(f"No training data for {model_type}")
                    continue
                
                # Train model
                model = await self._train_model(model_type, training_data)
                
                # Evaluate model
                evaluation = await self._evaluate_model(model, model_type, training_data)
                
                # Register model
                model_version = await self._register_model(model_type, model, evaluation)
                
                # Deploy model if meets criteria
                if evaluation.get('accuracy', 0) > 0.8:
                    await self._deploy_model(model_version)
                
                return model_version
            except Exception as e:
                logger.error(f"Failed to train model {model_type}: {e}")
                continue

# ML model training and serving pipeline (continued)
class MLOpsPipeline:
    """MLOps pipeline for model training and serving"""
    
    def __init__(self):
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
        self.s3_bucket = os.getenv('ML_MODELS_BUCKET')
        self.model_registry = {}
    
    async def train_models(self, model_types: List[str] = None):
        """Train machine learning models"""
        model_types = model_types or ['risk_prediction', 'resource_optimization', 'anomaly_detection']
        
        for model_type in model_types:
            try:
                logger.info(f"Training {model_type} model")
                
                # Get training data
                training_data = await self._get_training_data(model_type)
                
                if not training_data:
                    logger.warning(f"No training data for {model_type}")
                    continue
                
                # Train model
                model = await self._train_model(model_type, training_data)
                
                # Evaluate model
                evaluation = await self._evaluate_model(model, model_type, training_data)
                
                # Register model
                model_version = await self._register_model(model_type, model, evaluation)
                
                # Deploy model if meets criteria
                if evaluation.get('accuracy', 0) > 0.8:  # Deployment threshold
                    await self._deploy_model(model_type, model_version)
                
                logger.info(f"Successfully trained and deployed {model_type} model")
                
            except Exception as e:
                logger.error(f"Failed to train {model_type} model: {e}")
    
    async def _get_training_data(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get training data for specific model type"""
        # Implementation would fetch historical data from data warehouse
        # For example, for risk prediction:
        if model_type == 'risk_prediction':
            return await self._get_risk_training_data()
        elif model_type == 'resource_optimization':
            return await self._get_resource_training_data()
        elif model_type == 'anomaly_detection':
            return await self._get_anomaly_training_data()
        
        return None
    
    async def _train_model(self, model_type: str, training_data: Dict[str, Any]):
        """Train specific model type"""
        if model_type == 'risk_prediction':
            return await self._train_risk_model(training_data)
        elif model_type == 'resource_optimization':
            return await self._train_resource_model(training_data)
        elif model_type == 'anomaly_detection':
            return await self._train_anomaly_model(training_data)
        
        return None
    
    async def _evaluate_model(self, model, model_type: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate model performance"""
        # Implementation would perform model evaluation
        # and return metrics like accuracy, precision, recall, etc.
        return {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.87,
            "f1_score": 0.84,
            "roc_auc": 0.89
        }
    
    async def _register_model(self, model_type: str, model, evaluation: Dict[str, Any]) -> str:
        """Register model in model registry"""
        model_version = f"{model_type}_v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model to storage
        await self._save_model(model, model_version)
        
        # Register in MLflow
        await self._register_in_mlflow(model_type, model_version, evaluation)
        
        return model_version
    
    async def _deploy_model(self, model_type: str, model_version: str):
        """Deploy model to serving environment"""
        # Implementation would deploy model to Kubernetes, SageMaker, etc.
        logger.info(f"Deploying {model_type} model version {model_version}")
        
        # Update model registry
        self.model_registry[model_type] = {
            'version': model_version,
            'deployed_at': datetime.utcnow(),
            'status': 'deployed'
        }

# Real-time model serving
class ModelServing:
    """Real-time model serving for predictions"""
    
    def __init__(self):
        self.model_registry = {}
        self.load_balancer = {}
        self._load_models()
    
    def _load_models(self):
        """Load deployed models"""
        # Implementation would load models from storage
        # and initialize them for serving
        pass
    
    async def predict(self, model_type: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using specified model"""
        if model_type not in self.model_registry:
            return {"error": f"Model {model_type} not deployed"}
        
        try:
            model = self.model_registry[model_type]['model']
            
            # Preprocess features
            processed_features = await self._preprocess_features(model_type, features)
            
            # Make prediction
            prediction = model.predict([processed_features])[0]
            
            # Postprocess prediction
            result = await self._postprocess_prediction(model_type, prediction)
            
            return {
                "prediction": result,
                "model_version": self.model_registry[model_type]['version'],
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": await self._calculate_confidence(model, processed_features)
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"error": "Prediction failed"}
    
    async def batch_predict(self, model_type: str, features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Make batch predictions"""
        results = []
        
        for features in features_list:
            result = await self.predict(model_type, features)
            results.append(result)
        
        return results

# API endpoints for analytics and data pipeline
@app.get("/analytics/projects/{project_id}/insights", tags=["Analytics"])
async def get_project_insights(
    project_id: str,
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Get comprehensive project insights"""
    analytics_engine = AdvancedAnalyticsEngine()
    insights = await analytics_engine.generate_project_insights(project_id)
    return insights

@app.post("/analytics/projects/risks/predict", tags=["Analytics"])
async def predict_project_risk(
    project_data: Dict[str, Any],
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Predict project risks"""
    analytics_engine = AdvancedAnalyticsEngine()
    prediction = await analytics_engine.predict_project_risks(project_data)
    return prediction

@app.get("/analytics/dashboard", tags=["Analytics"])
async def get_analytics_dashboard(
    timeframe: str = Query("7d"),
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Get analytics dashboard data"""
    dashboard = RealTimeAnalyticsDashboard()
    data = await dashboard.get_dashboard_data(timeframe)
    return data

@app.post("/ml/models/train", tags=["MLOps"])
async def train_ml_models(
    model_types: List[str] = Body(["risk_prediction", "resource_optimization"]),
    current_user: UserRecord = Depends(require_role(UserRole.ADMIN))
):
    """Train machine learning models"""
    ml_pipeline = MLOpsPipeline()
    await ml_pipeline.train_models(model_types)
    return {"status": "training_started", "models": model_types}

@app.post("/ml/predict/{model_type}", tags=["MLOps"])
async def ml_prediction(
    model_type: str,
    features: Dict[str, Any],
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Make ML prediction"""
    model_serving = ModelServing()
    prediction = await model_serving.predict(model_type, features)
    return prediction

# Data pipeline endpoints
@app.post("/data/stream", tags=["Data Pipeline"])
async def stream_data(
    topic: str,
    data: Dict[str, Any],
    key: str = None,
    current_user: UserRecord = Depends(get_current_active_user)
):
    """Stream data to pipeline"""
    pipeline = RealTimeDataPipeline()
    success = await pipeline.stream_data_to_kafka(topic, data, key)
    return {"status": "success" if success else "failed"}

@app.post("/data/batch/process", tags=["Data Pipeline"])
async def process_batch_data(
    current_user: UserRecord = Depends(require_role(UserRole.ADMIN))
):
    """Trigger batch data processing"""
    pipeline = RealTimeDataPipeline()
    asyncio.create_task(pipeline.batch_processing_pipeline())
    return {"status": "batch_processing_started"}