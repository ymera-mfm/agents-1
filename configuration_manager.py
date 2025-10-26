# config/configuration_manager.py
"""
Centralized configuration management with environment-specific settings,
secure secret handling, and runtime updates.
"""

import os
import json
import yaml
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from redis import asyncio as aioredis
import hashlib
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Enterprise configuration management system"""
    
    def __init__(self, config_path: str, environment: str, redis_client: aioredis.Redis):
        self.config_path = config_path
        self.environment = environment
        self.redis = redis_client
        self.configs: Dict[str, Any] = {}
        self.secrets: Dict[str, str] = {}
        self.last_loaded: Dict[str, datetime] = {}
        self.watchers: Dict[str, asyncio.Task] = {}
        
        # Setup encryption for secrets
        self.fernet = self._initialize_fernet()
    
    def _initialize_fernet(self) -> Fernet:
        """Initialize encryption for secrets"""
        key = os.environ.get('CONFIG_ENCRYPTION_KEY')
        if not key:
            key_file = os.path.join(self.config_path, '.encryption_key')
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
        
        return Fernet(key)
    
    async def initialize(self) -> None:
        """Initialize all configuration components"""
        await self.load_all_configs()
        await self.load_secrets()
        
        # Start configuration watchers
        self._start_watchers()
        
        # Subscribe to Redis configuration updates
        await self._subscribe_to_config_updates()
        
        logger.info(f"Configuration manager initialized for environment: {self.environment}")
    
    async def load_all_configs(self) -> Dict[str, Any]:
        """Load all configuration files for the current environment"""
        config_files = [
            f for f in os.listdir(self.config_path) 
            if f.endswith('.yaml') or f.endswith('.json')
        ]
        
        for filename in config_files:
            name = os.path.splitext(filename)[0]
            file_path = os.path.join(self.config_path, filename)
            
            # Skip environment-specific configs that don't match current env
            if '_' in name:
                file_env = name.split('_', 1)[1]
                if file_env != self.environment:
                    continue
            
            # Load the config
            self.configs[name] = await self._load_config_file(file_path)
            self.last_loaded[name] = datetime.utcnow()
        
        # Load environment overrides
        env_dir = os.path.join(self.config_path, self.environment)
        if os.path.exists(env_dir):
            env_files = [
                f for f in os.listdir(env_dir) 
                if f.endswith('.yaml') or f.endswith('.json')
            ]
            
            for filename in env_files:
                name = os.path.splitext(filename)[0]
                file_path = os.path.join(env_dir, filename)
                
                # Override existing config
                env_config = await self._load_config_file(file_path)
                if name in self.configs:
                    self.configs[name] = self._deep_merge(self.configs[name], env_config)
                else:
                    self.configs[name] = env_config
                
                self.last_loaded[name] = datetime.utcnow()
        
        return self.configs
    
    async def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            return config
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
            return {}
    
    async def load_secrets(self) -> Dict[str, str]:
        """Load secrets from secure storage"""
        secrets_file = os.path.join(self.config_path, f"secrets_{self.environment}.enc")
        
        if os.path.exists(secrets_file):
            try:
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self.fernet.decrypt(encrypted_data)
                self.secrets = json.loads(decrypted_data)
                
                logger.info(f"Loaded {len(self.secrets)} secrets from {secrets_file}")
                
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
        
        # Also check for environment variable secrets
        for key, value in os.environ.items():
            if key.startswith('SECRET_'):
                secret_name = key[7:].lower()
                self.secrets[secret_name] = value
        
        return self.secrets
    
    def _start_watchers(self) -> None:
        """Start watchers for configuration files"""
        for filename in self.configs.keys():
            file_path = os.path.join(self.config_path, f"{filename}.yaml")
            if not os.path.exists(file_path):
                file_path = os.path.join(self.config_path, f"{filename}.json")
            
            if os.path.exists(file_path):
                task = asyncio.create_task(self._watch_config_file(file_path, filename))
                self.watchers[filename] = task
    
    async def _watch_config_file(self, file_path: str, config_name: str) -> None:
        """Watch configuration file for changes"""
        last_mtime = os.path.getmtime(file_path)
        
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                current_mtime = os.path.getmtime(file_path)
                if current_mtime > last_mtime:
                    # File changed, reload
                    config = await self._load_config_file(file_path)
                    self.configs[config_name] = config
                    self.last_loaded[config_name] = datetime.utcnow()
                    last_mtime = current_mtime
                    
                    # Notify subscribers
                    await self._notify_config_change(config_name)
                    
                    logger.info(f"Reloaded configuration: {config_name}")
            except Exception as e:
                logger.error(f"Error watching config file {file_path}: {e}")
                await asyncio.sleep(60)  # Retry after a minute
    
    async def _subscribe_to_config_updates(self) -> None:
        """Subscribe to Redis configuration updates"""
        # Start subscription in background task
        asyncio.create_task(self._config_subscription_listener())
    
    async def _config_subscription_listener(self) -> None:
        """Listen for configuration updates from Redis"""
        channel = self.redis.pubsub()
        await channel.subscribe("config_updates")
        
        try:
            while True:
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message:
                    data = json.loads(message["data"])
                    config_name = data.get("config_name")
                    config_value = data.get("config")
                    
                    if config_name and config_value:
                        # Update configuration
                        self.configs[config_name] = config_value
                        self.last_loaded[config_name] = datetime.utcnow()
                        
                        logger.info(f"Updated configuration from Redis: {config_name}")
                
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Config subscription error: {e}")
            # Restart subscription
            asyncio.create_task(self._config_subscription_listener())
    
    async def _notify_config_change(self, config_name: str) -> None:
        """Notify other instances of configuration changes"""
        message = {
            "config_name": config_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.redis.publish("config_updates", json.dumps(message))
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config_manager.get('database.connection.timeout', 30)
        """
        parts = path.split('.')
        config_name = parts[0]
        
        if config_name not in self.configs:
            return default
        
        current = self.configs[config_name]
        for part in parts[1:]:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        return current
    
    def get_secret(self, name: str, default: str = None) -> str:
        """Get secret value"""
        return self.secrets.get(name, default)
    
    async def set(self, path: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        parts = path.split('.')
        config_name = parts[0]
        
        if config_name not in self.configs:
            self.configs[config_name] = {}
        
        # Navigate to the right location
        current = self.configs[config_name]
        for part in parts[1:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
        
        # Notify other instances
        await self._notify_config_change(config_name)
        
        # Also persist to file if in development mode
        if self.environment == "development":
            await self._save_config_file(config_name)
        
        return True
    
    async def _save_config_file(self, config_name: str) -> bool:
        """Save configuration to file"""
        try:
            file_path = os.path.join(self.config_path, f"{config_name}.yaml")
            
            with open(file_path, 'w') as f:
                yaml.dump(self.configs[config_name], f)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save config file {config_name}: {e}")
            return False