# security/vault_manager.py
import hvac
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VaultManager:
    def __init__(self, vault_url: str, token: str, namespace: str = ""):
        self.vault_url = vault_url
        self.token = token
        self.namespace = namespace
        self.client: Optional[hvac.Client] = None
        self._secrets_cache: Dict[str, tuple] = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize Vault client"""
        try:
            self.client = hvac.Client(
                url=self.vault_url,
                token=self.token,
                namespace=self.namespace
            )
            
            if not self.client.is_authenticated():
                raise Exception("Vault authentication failed")
                
            logger.info("Vault manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vault: {e}")
            raise
    
    async def get_secret(self, path: str, use_cache: bool = True) -> Dict[str, Any]:
        """Retrieve secret from Vault with caching"""
        if use_cache and path in self._secrets_cache:
            secret, timestamp = self._secrets_cache[path]
            if datetime.utcnow() - timestamp < timedelta(seconds=self._cache_ttl):
                return secret
        
        try:
            response = await asyncio.to_thread(
                self.client.secrets.kv.v2.read_secret_version,
                path=path
            )
            secret = response["data"]["data"]
            
            # Update cache
            self._secrets_cache[path] = (secret, datetime.utcnow())
            
            return secret
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret from {path}: {e}")
            raise
    
    async def store_secret(self, path: str, secret: Dict[str, Any]):
        """Store secret in Vault"""
        try:
            await asyncio.to_thread(
                self.client.secrets.kv.v2.create_or_update_secret,
                path=path,
                secret=secret
            )
            
            # Invalidate cache
            if path in self._secrets_cache:
                del self._secrets_cache[path]
                
        except Exception as e:
            logger.error(f"Failed to store secret at {path}: {e}")
            raise
    
    async def rotate_secret(self, path: str, new_secret: Dict[str, Any]):
        """Rotate secret with versioning"""
        try:
            # Store new version
            await self.store_secret(path, new_secret)
            
            # Keep last 3 versions
            await asyncio.to_thread(
                self.client.secrets.kv.v2.delete_secret_versions,
                path=path,
                versions=list(range(1, max(1, self._get_latest_version(path) - 2)))
            )
            
        except Exception as e:
            logger.error(f"Failed to rotate secret at {path}: {e}")
            raise
    
    def _get_latest_version(self, path: str) -> int:
        """Get latest version number for a secret"""
        try:
            metadata = self.client.secrets.kv.v2.read_secret_metadata(path=path)
            return metadata["data"]["current_version"]
        except:
            return 0

# security/encryption_service.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
import os
import secrets
from typing import Optional

class EnhancedEncryptionService:
    def __init__(self, vault_manager: VaultManager):
        self.vault_manager = vault_manager
        self.backend = default_backend()
        self._key_cache: Optional[bytes] = None
        
    async def initialize(self):
        """Initialize encryption service with key from Vault"""
        try:
            # Retrieve or generate encryption key
            try:
                key_data = await self.vault_manager.get_secret("encryption/master_key")
                self._key_cache = base64.b64decode(key_data["key"])
            except:
                # Generate new key if not exists
                new_key = secrets.token_bytes(32)
                await self.vault_manager.store_secret(
                    "encryption/master_key",
                    {"key": base64.b64encode(new_key).decode()}
                )
                self._key_cache = new_key
                
            logger.info("Encryption service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise
    
    async def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-GCM"""
        if not self._key_cache:
            raise Exception("Encryption service not initialized")
        
        # Generate IV
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._key_cache),
            modes.GCM(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Return IV + tag + ciphertext
        return iv + encryptor.tag + ciphertext
    
    async def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        if not self._key_cache:
            raise Exception("Encryption service not initialized")
        
        # Extract components
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._key_cache),
            modes.GCM(iv, tag),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        
        # Decrypt data
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    async def hash_password(self, password: str) -> str:
        """Hash password using PBKDF2"""
        salt = os.urandom(32)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(salt + key).decode()
    
    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        decoded = base64.b64decode(hashed)
        salt = decoded[:32]
        stored_key = decoded[32:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        try:
            new_key = kdf.derive(password.encode())
            return new_key == stored_key
        except:
            return False

# database/connection_pool.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
from sqlalchemy import event, text

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self, database_url: str, pool_size: int = 20, max_overflow: int = 10):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine: Optional[Any] = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Create engine with connection pooling
            self.engine = create_async_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "ymera-learning-agent",
                        "jit": "off"
                    },
                    "pool_reset_connection_state": True
                }
            )
            
            # Create session factory
            self.async_session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            # Set up event listeners
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                if "postgresql" in self.database_url:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("SET statement_timeout = '30s'")
                    cursor.close()
            
            logger.info(f"Database pool initialized: {self.pool_size} connections")
            
        except Exception as e:
            logger.error(f"Database pool initialization failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session from pool"""
        if not self.async_session_factory:
            raise Exception("Database pool not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, query: str, params: Optional[Dict] = None):
        """Execute a raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except:
            return False
    
    async def get_pool_stats(self) -> Dict:
        """Get connection pool statistics"""
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checked_in_connections,
            "checked_out": pool.checked_out_connections,
            "total": pool.total_connections,
            "overflow": pool.overflow
        }
    
    async def close(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# database/redis_manager.py
import redis.asyncio as redis
from typing import Optional, Any, Dict, List
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self, redis_url: str, max_connections: int = 50):
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.Redis] = None
        self._subscriptions: Dict[str, List] = {}
        
    async def connect(self):
        """Connect to Redis"""
        try:
            # Create connection pool
            pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 60, # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                }
            )
            
            # Create Redis clients
            self.redis_client = redis.Redis(connection_pool=pool)
            self.pubsub_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """Set value in Redis with optional expiration"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                await self.redis_client.setex(key, expire, value)
            else:
                await self.redis_client.set(key, value)
                
        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            raise
    
    async def delete(self, *keys: str):
        """Delete keys from Redis"""
        try:
            await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int):
        """Set expiration on key"""
        try:
            await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            raise
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR failed for key {key}: {e}")
            raise
    
    async def get_json(self, key: str) -> Optional[Dict]:
        """Get JSON value from Redis"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key {key}")
        return None
    
    async def set_json(self, key: str, value: Dict, expire: Optional[int] = None):
        """Set JSON value in Redis"""
        await self.set(key, json.dumps(value), expire)
    
    async def zadd(self, key: str, mapping: Dict[str, float]):
        """Add to sorted set"""
        try:
            await self.redis_client.zadd(key, mapping)
        except Exception as e:
            logger.error(f"Redis ZADD failed for key {key}: {e}")
            raise
    
    async def zrange(self, key: str, start: int, end: int, withscores: bool = False):
        """Get range from sorted set"""
        try:
            return await self.redis_client.zrange(key, start, end, withscores=withscores)
        except Exception as e:
            logger.error(f"Redis ZRANGE failed for key {key}: {e}")
            return []
    
    async def publish(self, channel: str, message: str):
        """Publish message to channel"""
        try:
            await self.redis_client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis PUBLISH failed for channel {channel}: {e}")
            raise
    
    async def subscribe(self, channel: str, callback):
        """Subscribe to channel"""
        try:
            pubsub = self.pubsub_client.pubsub()
            await pubsub.subscribe(channel)
            
            if channel not in self._subscriptions:
                self._subscriptions[channel] = []
            self._subscriptions[channel].append(callback)
            
            # Start listening in background
            asyncio.create_task(self._listen_channel(pubsub, channel))
            
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE failed for channel {channel}: {e}")
            raise
    
    async def _listen_channel(self, pubsub, channel: str):
        """Listen to channel messages"""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    for callback in self._subscriptions.get(channel, []):
                        try:
                            await callback(message["data"])
                        except Exception as e:
                            logger.error(f"Callback error for channel {channel}: {e}")
        except Exception as e:
            logger.error(f"Channel listener error for {channel}: {e}")
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        try:
            await self.redis_client.ping()
            return True
        except:
            return False
    
    async def get_info(self) -> Dict:
        """Get Redis server info"""
        try:
            info = await self.redis_client.info()
            return {
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    async def close(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.pubsub_client:
            await self.pubsub_client.close()
        logger.info("Redis connections closed")

# ml/model_factory.py
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class BaseModel:
    """Base class for all models"""
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    async def predict(self, input_data: Any) -> Any:
        raise NotImplementedError
    
    async def load(self, path: str):
        raise NotImplementedError
    
    async def save(self, path: str):
        raise NotImplementedError

class TransformerModel(BaseModel):
    """Transformer-based model for NLP tasks"""
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__()
        self.model_name = model_name
        self.tokenizer = None
        
    async def load(self, path: Optional[str] = None):
        """Load transformer model"""
        try:
            if path and os.path.exists(path):
                self.model = AutoModel.from_pretrained(path)
                self.tokenizer = AutoTokenizer.from_pretrained(path)
            else:
                self.model = AutoModel.from_pretrained(self.model_name)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Loaded transformer model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load transformer model: {e}")
            raise
    
    async def predict(self, text: str) -> torch.Tensor:
        """Generate embeddings for text"""
        with torch.no_grad():
            inputs = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            return embeddings.cpu().numpy()
    
    async def save(self, path: str):
        """Save model to disk"""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

class KnowledgeExtractionModel(nn.Module):
    """Custom model for knowledge extraction"""
    def __init__(self, input_dim: int = 768, hidden_dim: int = 256, num_classes: int = 10):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim // 2)
        self.fc3 = nn.Linear(hidden_dim // 2, num_classes)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.fc3(x)
        return self.softmax(x)

class ModelFactory:
    """Factory for creating different model types"""
    
    def __init__(self):
        self.model_types = {
            "transformer": TransformerModel,
            "knowledge_extraction": KnowledgeExtractionModel,
            "embedding": TransformerModel,
        }
    
    async def create_model(self, model_type: str, config: Dict[str, Any] = None) -> BaseModel:
        """Create a model instance"""
        if model_type not in self.model_types:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_class = self.model_types[model_type]
        
        if model_type == "transformer" or model_type == "embedding":
            model = model_class(config.get("model_name") if config else None)
        elif model_type == "knowledge_extraction":
            model = model_class(
                input_dim=config.get("input_dim", 768) if config else 768,
                hidden_dim=config.get("hidden_dim", 256) if config else 256,
                num_classes=config.get("num_classes", 10) if config else 10
            )
        else:
            model = model_class()
        
        # Load weights if path provided
        if config and "model_path" in config:
            await model.load(config["model_path"])
        
        return model
    
    def register_model_type(self, name: str, model_class):
        """Register a new model type"""
        self.model_types[name] = model_class

# utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client.exposition import push_to_gateway
from typing import Dict, Optional
import psutil
import asyncio
import logging

logger = logging.getLogger(__name__)

class AdvancedMetrics:
    def __init__(self, pushgateway_url: Optional[str] = None):
        self.pushgateway_url = pushgateway_url
        
        # Agent metrics
        self.agent_initialized = Counter(
            "agent_initialized_total",
            "Total number of agent initializations"
        )
        self.agent_shutdown = Counter(
            "agent_shutdown_total",
            "Total number of agent shutdowns"
        )
        
        # Experience processing metrics
        self.experiences_processed = Counter(
            "experiences_processed_total",
            "Total number of experiences processed"
        )
        self.experience_processing_time = Histogram(
            "experience_processing_seconds",
            "Time taken to process experiences"
        )
        self.experience_processing_errors = Counter(
            "experience_processing_errors_total",
            "Total number of experience processing errors"
        )
        
        # Knowledge metrics
        self.knowledge_items_stored = Counter(
            "knowledge_items_stored_total",
            "Total number of knowledge items stored"
        )
        self.knowledge_searches = Counter(
            "knowledge_searches_total",
            "Total number of knowledge searches"
        )
        self.knowledge_search_errors = Counter(
            "knowledge_search_errors_total",
            "Total number of knowledge search errors"
        )
        
        # Model metrics
        self.model_training_started = Counter(
            "model_training_started_total",
            "Total number of model trainings started"
        )
        self.model_training_completed = Counter(
            "model_training_completed_total",
            "Total number of model trainings completed"
        )
        self.model_training_errors = Counter(
            "model_training_errors_total",
            "Total number of model training errors"
        )
        self.model_retraining_completed = Counter(
            "model_retraining_completed_total",
            "Total number of model retrainings completed"
        )
        self.model_retraining_errors = Counter(
            "model_retraining_errors_total",
            "Total number of model retraining errors"
        )
        
        # Chat metrics
        self.chat_messages_processed = Counter(
            "chat_messages_processed_total",
            "Total number of chat messages processed"
        )
        self.chat_errors = Counter(
            "chat_errors_total",
            "Total number of chat handling errors"
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            "system_cpu_usage_percent",
            "Current CPU usage percentage"
        )
        self.memory_usage = Gauge(
            "system_memory_usage_percent",
            "Current memory usage percentage"
        )
        self.disk_usage = Gauge(
            "system_disk_usage_percent",
            "Current disk usage percentage"
        )
        
        # Database metrics
        self.database_pool_connections_used = Gauge(
            "database_pool_connections_used",
            "Number of database connections currently in use"
        )
        self.database_pool_max_connections = Gauge(
            "database_pool_max_connections",
            "Maximum number of database connections"
        )
        
        # Background task metrics
        self.background_task_errors = Counter(
            "background_task_errors_total",
            "Total number of background task errors",
            ["task"]
        )
        self.batch_processing_completed = Counter(
            "batch_processing_completed_total",
            "Total number of batch processing completions"
        )
        self.batch_processing_errors = Counter(
            "batch_processing_errors_total",
            "Total number of batch processing errors"
        )
        
        # Security metrics
        self.security_incidents = Counter(
            "security_incidents_total",
            "Total number of security incidents",
            ["type", "severity"]
        )
        
        # Knowledge sync metrics
        self.knowledge_last_sync_timestamp = Gauge(
            "knowledge_last_sync_timestamp",
            "Timestamp of last knowledge synchronization"
        )
        
        # Agent info
        self.agent_info = Info(
            "agent_info",
            "Agent information"
        )
    
    async def initialize(self):
        """Initialize metrics collection"""
        logger.info("Metrics collection initialized")
    
    async def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # CPU usage
            self.cpu_usage.set(psutil.cpu_percent(interval=1))
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage("/")
            self.disk_usage.set(disk.percent)
            
            # Push to gateway if configured
            if self.pushgateway_url:
                await self._push_metrics()
                
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    async def _push_metrics(self):
        """Push metrics to Prometheus Pushgateway"""
        try:
            await asyncio.to_thread(
                push_to_gateway,
                self.pushgateway_url,
                job="learning-agent",
                registry=None
            )
        except Exception as e:
            logger.error(f"Failed to push metrics: {e}")
    
    async def generate_metrics_response(self) -> bytes:
        """Generate metrics in Prometheus format"""
        return generate_latest()
