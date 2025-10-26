# notification_manager.py - Advanced notification system

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
from redis import asyncio as aioredis
from fastapi import WebSocket
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class NotificationPriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel:
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"

class NotificationManager:
    """Multi-channel notification system with priority routing"""
    
    def __init__(self, redis_client: aioredis.Redis, config: Dict):
        self.redis = redis_client
        self.config = config
        self.channels = self._initialize_channels(config)
    
    def _initialize_channels(self, config: Dict) -> Dict:
        """Initialize notification channels"""
        channels = {}
        
        # Setup email channel if configured
        if config.get("email", {}).get("enabled", False):
            channels[NotificationChannel.EMAIL] = {
                "handler": self._send_email_notification,
                "config": config.get("email", {})
            }
        
        # Setup SMS channel if configured
        if config.get("sms", {}).get("enabled", False):
            channels[NotificationChannel.SMS] = {
                "handler": self._send_sms_notification,
                "config": config.get("sms", {})
            }
        
        # Setup webhook channel if configured
        if config.get("webhook", {}).get("enabled", False):
            channels[NotificationChannel.WEBHOOK] = {
                "handler": self._send_webhook_notification,
                "config": config.get("webhook", {})
            }
        
        # WebSocket channel is always enabled
        channels[NotificationChannel.WEBSOCKET] = {
            "handler": self._send_websocket_notification,
            "config": {}
        }
        
        return channels
    
    async def send_notification(self, recipient_id: str, notification: Dict) -> Dict:
        """
        Send notification through appropriate channels based on priority
        """
        # Ensure notification has required fields
        notification = {
            "id": notification.get("id", str(uuid.uuid4())),
            "type": notification.get("type", "info"),
            "title": notification.get("title", "Notification"),
            "message": notification.get("message", ""),
            "timestamp": notification.get("timestamp", datetime.utcnow().isoformat()),
            "priority": notification.get("priority", NotificationPriority.NORMAL),
            "source": notification.get("source", "system"),
            "data": notification.get("data", {}),
            "actions": notification.get("actions", []),
            "read": False
        }
        
        # Store notification for retrieval
        await self._store_notification(recipient_id, notification)
        
        # Determine channels based on priority
        channels = self._get_channels_for_priority(notification["priority"])
        
        # Send through appropriate channels
        results = {}
        for channel in channels:
            if channel in self.channels:
                handler = self.channels[channel]["handler"]
                try:
                    success = await handler(recipient_id, notification)
                    results[channel] = success
                except Exception as e:
                    logger.error(f"Error sending {channel} notification: {e}")
                    results[channel] = False
        
        return {
            "notification_id": notification["id"],
            "recipient_id": recipient_id,
            "results": results
        }
    
    def _get_channels_for_priority(self, priority: str) -> List[str]:
        """Determine notification channels based on priority"""
        if priority == NotificationPriority.CRITICAL:
            return [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL, 
                    NotificationChannel.SMS, NotificationChannel.WEBHOOK]
        elif priority == NotificationPriority.HIGH:
            return [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL, 
                    NotificationChannel.WEBHOOK]
        elif priority == NotificationPriority.NORMAL:
            return [NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL]
        else:  # LOW
            return [NotificationChannel.WEBSOCKET]
    
    async def _store_notification(self, recipient_id: str, notification: Dict):
        """Store notification for retrieval"""
        try:
            # Add to user's notification list
            await self.redis.lpush(
                f"notifications:{recipient_id}",
                json.dumps(notification)
            )
            
            # Set expiry (30 days default)
            await self.redis.expire(
                f"notifications:{recipient_id}",
                86400 * 30
            )
            
            # Add to real-time notification stream
            await self.redis.xadd(
                "notification_stream",
                {
                    "recipient": recipient_id,
                    "notification": json.dumps(notification)
                }
            )
            
        except Exception as e:
            logger.error(f"Error storing notification: {e}")
    
    async def get_user_notifications(self, user_id: str, limit: int = 50,
                                  include_read: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        try:
            # Get notifications from Redis
            notifications = await self.redis.lrange(
                f"notifications:{user_id}",
                0,
                limit - 1
            )
            
            if not notifications:
                return []
            
            # Parse JSON
            result = []
            for notification_json in notifications:
                try:
                    notification = json.loads(notification_json)
                    if include_read or not notification.get("read", False):
                        result.append(notification)
                except Exception:
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving notifications: {e}")
            return []
    
    async def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            # Get all notifications
            notifications = await self.redis.lrange(
                f"notifications:{user_id}",
                0,
                -1
            )
            
            # Find and update the notification
            for i, notification_json in enumerate(notifications):
                try:
                    notification = json.loads(notification_json)
                    if notification.get("id") == notification_id:
                        # Mark as read
                        notification["read"] = True
                        notification["read_at"] = datetime.utcnow().isoformat()
                        
                        # Update in Redis
                        await self.redis.lset(
                            f"notifications:{user_id}",
                            i,
                            json.dumps(notification)
                        )
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            return False
    
    # Channel-specific notification methods
    async def _send_websocket_notification(self, recipient_id: str, notification: Dict) -> bool:
        """Send notification via WebSocket"""
        try:
            # In production, this would use the connection manager
            await self.redis.publish(
                f"ws:notifications:{recipient_id}",
                json.dumps({
                    "type": "notification",
                    "data": notification
                })
            )
            return True
        except Exception as e:
            logger.error(f"WebSocket notification failed: {e}")
            return False
    
    async def _send_email_notification(self, recipient_id: str, notification: Dict) -> bool:
        """Send notification via email"""
        try:
            # Get user email (would retrieve from database in production)
            recipient_email = await self._get_user_email(recipient_id)
            if not recipient_email:
                return False
                
            # Queue email for sending
            await self.redis.lpush(
                "email_queue",
                json.dumps({
                    "to": recipient_email,
                    "subject": notification["title"],
                    "body": notification["message"],
                    "priority": notification["priority"],
                    "metadata": {
                        "notification_id": notification["id"],
                        "recipient_id": recipient_id
                    }
                })
            )
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False
    
    async def _send_sms_notification(self, recipient_id: str, notification: Dict) -> bool:
        """Send notification via SMS"""
        try:
            # Get user phone number (would retrieve from database in production)
            recipient_phone = await self._get_user_phone(recipient_id)
            if not recipient_phone:
                return False
                
            # Queue SMS for sending
            await self.redis.lpush(
                "sms_queue",
                json.dumps({
                    "to": recipient_phone,
                    "body": f"{notification['title']}: {notification['message']}",
                    "priority": notification["priority"],
                    "metadata": {
                        "notification_id": notification["id"],
                        "recipient_id": recipient_id
                    }
                })
            )
            return True
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return False
    
    async def _send_webhook_notification(self, recipient_id: str, notification: Dict) -> bool:
        """Send notification via webhook"""
        try:
            # Get webhook URL (would retrieve from database in production)
            webhook_url = await self._get_user_webhook(recipient_id)
            if not webhook_url:
                return False
                
            # Queue webhook for sending
            await self.redis.lpush(
                "webhook_queue",
                json.dumps({
                    "url": webhook_url,
                    "payload": {
                        "notification": notification,
                        "recipient_id": recipient_id
                    },
                    "priority": notification["priority"],
                    "metadata": {
                        "notification_id": notification["id"],
                        "recipient_id": recipient_id
                    }
                })
            )
            return True
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False
    
    # Helper methods for retrieving user contact information
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email address"""
        # This would query database in production
        return f"{user_id}@example.com"
    
    async def _get_user_phone(self, user_id: str) -> Optional[str]:
        """Get user phone number"""
        # This would query database in production
        return "+1234567890"
    
    async def _get_user_webhook(self, user_id: str) -> Optional[str]:
        """Get user webhook URL"""
        # This would query database in production
        return "https://example.com/webhook"