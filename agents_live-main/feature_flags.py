"""
Feature Flags System
Allows features to be toggled without code changes and supports gradual rollouts
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Dict, Optional
from enum import Enum


class RolloutStrategy(str, Enum):
    """Rollout strategy for feature flags"""
    ALL = "all"  # Enable for all users
    NONE = "none"  # Disable for all users
    PERCENTAGE = "percentage"  # Enable for a percentage of users
    WHITELIST = "whitelist"  # Enable for specific users/groups


class FeatureFlags(BaseSettings):
    """
    Feature Flags Configuration
    Control features at runtime without code deployment
    """
    
    # ============================================================================
    # CORE FEATURES
    # ============================================================================
    enable_chat_interface: bool = Field(
        default=True,
        env="FEATURE_CHAT_INTERFACE",
        description="Enable/disable chat interface"
    )
    enable_file_versioning: bool = Field(
        default=True,
        env="FEATURE_FILE_VERSIONING",
        description="Enable/disable file versioning"
    )
    enable_auto_integration: bool = Field(
        default=True,
        env="FEATURE_AUTO_INTEGRATION",
        description="Enable/disable automatic integration"
    )
    enable_rollback: bool = Field(
        default=True,
        env="FEATURE_ROLLBACK",
        description="Enable/disable rollback functionality"
    )
    
    # ============================================================================
    # MONITORING & OBSERVABILITY
    # ============================================================================
    enable_distributed_tracing: bool = Field(
        default=True,
        env="FEATURE_DISTRIBUTED_TRACING",
        description="Enable/disable distributed tracing"
    )
    enable_metrics_export: bool = Field(
        default=True,
        env="FEATURE_METRICS_EXPORT",
        description="Enable/disable metrics export"
    )
    enable_structured_logging: bool = Field(
        default=True,
        env="FEATURE_STRUCTURED_LOGGING",
        description="Enable/disable structured logging"
    )
    enable_performance_profiling: bool = Field(
        default=False,
        env="FEATURE_PERFORMANCE_PROFILING",
        description="Enable/disable performance profiling"
    )
    
    # ============================================================================
    # SECURITY FEATURES
    # ============================================================================
    enable_two_factor_auth: bool = Field(
        default=False,
        env="FEATURE_TWO_FACTOR_AUTH",
        description="Enable/disable two-factor authentication"
    )
    enable_api_key_rotation: bool = Field(
        default=True,
        env="FEATURE_API_KEY_ROTATION",
        description="Enable/disable automatic API key rotation"
    )
    enable_rate_limiting: bool = Field(
        default=True,
        env="FEATURE_RATE_LIMITING",
        description="Enable/disable rate limiting"
    )
    enable_ip_whitelist: bool = Field(
        default=False,
        env="FEATURE_IP_WHITELIST",
        description="Enable/disable IP whitelisting"
    )
    
    # ============================================================================
    # EXPERIMENTAL FEATURES
    # ============================================================================
    enable_ai_suggestions: bool = Field(
        default=False,
        env="FEATURE_AI_SUGGESTIONS",
        description="Enable/disable AI-powered suggestions"
    )
    enable_auto_scaling: bool = Field(
        default=False,
        env="FEATURE_AUTO_SCALING",
        description="Enable/disable automatic scaling"
    )
    enable_predictive_caching: bool = Field(
        default=False,
        env="FEATURE_PREDICTIVE_CACHING",
        description="Enable/disable predictive caching"
    )
    enable_collaborative_editing: bool = Field(
        default=False,
        env="FEATURE_COLLABORATIVE_EDITING",
        description="Enable/disable collaborative editing"
    )
    
    # ============================================================================
    # INTEGRATION FEATURES
    # ============================================================================
    enable_webhook_notifications: bool = Field(
        default=False,
        env="FEATURE_WEBHOOK_NOTIFICATIONS",
        description="Enable/disable webhook notifications"
    )
    enable_email_notifications: bool = Field(
        default=False,
        env="FEATURE_EMAIL_NOTIFICATIONS",
        description="Enable/disable email notifications"
    )
    enable_slack_integration: bool = Field(
        default=False,
        env="FEATURE_SLACK_INTEGRATION",
        description="Enable/disable Slack integration"
    )
    enable_third_party_auth: bool = Field(
        default=False,
        env="FEATURE_THIRD_PARTY_AUTH",
        description="Enable/disable third-party authentication (OAuth)"
    )
    
    # ============================================================================
    # DATA & STORAGE
    # ============================================================================
    enable_data_encryption: bool = Field(
        default=True,
        env="FEATURE_DATA_ENCRYPTION",
        description="Enable/disable data encryption at rest"
    )
    enable_backup_automation: bool = Field(
        default=True,
        env="FEATURE_BACKUP_AUTOMATION",
        description="Enable/disable automated backups"
    )
    enable_data_archival: bool = Field(
        default=True,
        env="FEATURE_DATA_ARCHIVAL",
        description="Enable/disable automatic data archival"
    )
    enable_multi_region_replication: bool = Field(
        default=False,
        env="FEATURE_MULTI_REGION_REPLICATION",
        description="Enable/disable multi-region data replication"
    )
    
    # ============================================================================
    # ROLLOUT CONFIGURATION
    # ============================================================================
    rollout_percentage: int = Field(
        default=100,
        env="ROLLOUT_PERCENTAGE",
        description="Percentage of users to enable new features for (0-100)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def is_feature_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for a given user
        
        Args:
            feature_name: Name of the feature to check
            user_id: Optional user ID for percentage-based rollouts
            
        Returns:
            True if feature is enabled, False otherwise
        """
        # Get the feature flag value
        feature_value = getattr(self, feature_name, None)
        
        if feature_value is None:
            return False
        
        # If it's a boolean, return it directly
        if isinstance(feature_value, bool):
            return feature_value
        
        return False
    
    def get_enabled_features(self) -> Dict[str, bool]:
        """Get dictionary of all feature flags and their states"""
        features = {}
        for field_name, field_info in self.__fields__.items():
            if field_name != "rollout_percentage":
                value = getattr(self, field_name)
                if isinstance(value, bool):
                    features[field_name] = value
        return features
    
    def get_experimental_features(self) -> Dict[str, bool]:
        """Get only experimental features"""
        return {
            "enable_ai_suggestions": self.enable_ai_suggestions,
            "enable_auto_scaling": self.enable_auto_scaling,
            "enable_predictive_caching": self.enable_predictive_caching,
            "enable_collaborative_editing": self.enable_collaborative_editing,
        }


# Global feature flags instance
feature_flags = FeatureFlags()


def is_enabled(feature_name: str, user_id: Optional[str] = None) -> bool:
    """
    Convenience function to check if a feature is enabled
    
    Args:
        feature_name: Name of the feature to check
        user_id: Optional user ID for percentage-based rollouts
        
    Returns:
        True if feature is enabled, False otherwise
    """
    return feature_flags.is_feature_enabled(feature_name, user_id)
