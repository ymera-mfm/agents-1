"""
Advanced Security Agent
Handles authentication, authorization, threat detection, encryption, and security monitoring
"""

import asyncio
import json
import time
import hashlib
import hmac
import jwt
import bcrypt
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import uuid
from datetime import datetime, timedelta
import ipaddress
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# Optional dependencies - Redis
import base64
import os

# Optional dependencies
try:
    from redis import asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    aioredis = None
    HAS_REDIS = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# Optional dependencies - OpenTelemetry  
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    Fernet = None
    hashes = None
    serialization = None
    rsa = None
    padding = None
    PBKDF2HMAC = None
    HAS_CRYPTOGRAPHY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    RATE_LIMIT = "rate_limit"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    MALWARE = "malware"
    DATA_BREACH = "data_breach"
    PRIVILEGE_ESCALATION = "privilege_escalation"

class AuthMethod(Enum):
    PASSWORD = "password"
    MFA = "mfa"
    SSO = "sso"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH = "oauth"
    CERTIFICATE = "certificate"

@dataclass
class SecurityEvent:
    event_id: str
    event_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_id: Optional[str] = None
    resource: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False

@dataclass
class AuthToken:
    token_id: str
    user_id: str
    token_type: AuthMethod
    permissions: List[str]
    expires_at: float
    issued_at: float = field(default_factory=time.time)
    refresh_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityPolicy:
    policy_id: str
    name: str
    rules: List[Dict[str, Any]]
    enforcement_level: SecurityLevel
    enabled: bool = True
    created_at: float = field(default_factory=time.time)

class SecurityAgent(BaseAgent):
    """
    Advanced Security Agent with:
    - Multi-factor authentication and authorization
    - Real-time threat detection and response
    - Advanced encryption and key management
    - Security policy enforcement
    - Audit logging and compliance
    - Behavioral analysis and anomaly detection
    - Zero-trust security model
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Security state
        self.active_sessions: Dict[str, Dict] = {}
        self.security_events: List[SecurityEvent] = []
        self.blocked_ips: Set[str] = set()
        self.security_policies: Dict[str, SecurityPolicy] = {}
        
        # Threat detection
        self.failed_attempts: Dict[str, List[float]] = {}
        self.rate_limiters: Dict[str, Dict] = {}
        self.anomaly_patterns: Dict[str, Any] = {}
        
        # Encryption
        self.master_key = self._generate_master_key()
        self.session_keys: Dict[str, bytes] = {}
        
        # Security metrics
        self.security_metrics = {
            "total_auth_attempts": 0,
            "successful_auth": 0,
            "failed_auth": 0,
            "threats_detected": 0,
            "threats_blocked": 0,
            "active_sessions": 0
        }
        
        # Load security policies
        self._load_default_policies()
    
    async def start(self):
        """Start security agent services"""
        # Subscribe to authentication requests
        await self._subscribe(
            "security.auth.request",
            self._handle_auth_request
        )
        
        # Subscribe to authorization requests
        await self._subscribe(
            "security.authz.request",
            self._handle_authz_request
        )
        
        # Subscribe to encryption requests
        await self._subscribe(
            "security.encrypt.request",
            self._handle_encrypt_request
        )
        
        # Subscribe to security events
        await self._subscribe(
            "security.event",
            self._handle_security_event
        )
        
        # Subscribe to task requests
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_security_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        # Start background security tasks
        asyncio.create_task(self._threat_monitor())
        asyncio.create_task(self._session_cleaner())
        asyncio.create_task(self._security_metrics_publisher())
        asyncio.create_task(self._anomaly_detector())
        
        self.logger.info("Security Agent started")
    
    def _generate_master_key(self) -> bytes:
        """Generate or load master encryption key"""
        key_file = os.getenv("SECURITY_KEY_FILE", "/etc/security/master.key")
        
        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _load_default_policies(self):
        """Load default security policies"""
        # Rate limiting policy
        rate_limit_policy = SecurityPolicy(
            policy_id="rate_limit_default",
            name="Default Rate Limiting",
            rules=[
                {
                    "resource": "*",
                    "max_requests": 100,
                    "time_window": 60,
                    "action": "throttle"
                },
                {
                    "resource": "/api/auth/*",
                    "max_requests": 5,
                    "time_window": 300,
                    "action": "block"
                }
            ],
            enforcement_level=SecurityLevel.MEDIUM
        )
        
        # Authentication policy
        auth_policy = SecurityPolicy(
            policy_id="auth_default",
            name="Default Authentication",
            rules=[
                {
                    "min_password_length": 8,
                    "require_special_chars": True,
                    "require_numbers": True,
                    "max_failed_attempts": 5,
                    "lockout_duration": 900  # 15 minutes
                }
            ],
            enforcement_level=SecurityLevel.HIGH
        )
        
        # Data protection policy
        data_policy = SecurityPolicy(
            policy_id="data_protection",
            name="Data Protection Policy",
            rules=[
                {
                    "encrypt_pii": True,
                    "encrypt_at_rest": True,
                    "encrypt_in_transit": True,
                    "key_rotation_days": 90
                }
            ],
            enforcement_level=SecurityLevel.HIGH
        )
        
        self.security_policies.update({
            rate_limit_policy.policy_id: rate_limit_policy,
            auth_policy.policy_id: auth_policy,
            data_policy.policy_id: data_policy
        })
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute security-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "authenticate":
            return await self._authenticate_user(payload)
        
        elif task_type == "authorize":
            return await self._authorize_request(payload)
        
        elif task_type == "encrypt_data":
            return await self._encrypt_data(payload)
        
        elif task_type == "decrypt_data":
            return await self._decrypt_data(payload)
        
        elif task_type == "generate_token":
            return await self._generate_token(payload)
        
        elif task_type == "validate_token":
            return await self._validate_token(payload)
        
        elif task_type == "security_scan":
            return await self._security_scan(payload)
        
        elif task_type == "threat_analysis":
            return await self._threat_analysis(payload)
        
        elif task_type == "audit_log":
            return await self._create_audit_log(payload)
        
        else:
            raise ValueError(f"Unknown security task type: {task_type}")
    
    async def _authenticate_user(self, payload: Dict) -> Dict[str, Any]:
        """Authenticate user credentials"""
        username = payload.get("username")
        password = payload.get("password")
        auth_method = AuthMethod(payload.get("method", "password"))
        source_ip = payload.get("source_ip", "unknown")
        
        self.security_metrics["total_auth_attempts"] += 1
        
        # Check if IP is blocked
        if source_ip in self.blocked_ips:
            await self._create_security_event(
                ThreatType.BRUTE_FORCE,
                SecurityLevel.HIGH,
                source_ip,
                f"Authentication attempt from blocked IP: {source_ip}"
            )
            return {"authenticated": False, "reason": "blocked_ip"}
        
        # Check rate limiting
        if not await self._check_rate_limit(f"auth:{source_ip}", 5, 300):
            await self._create_security_event(
                ThreatType.RATE_LIMIT,
                SecurityLevel.MEDIUM,
                source_ip,
                f"Authentication rate limit exceeded: {source_ip}"
            )
            return {"authenticated": False, "reason": "rate_limit"}
        
        try:
            # Get user from database
            user_data = await self._get_user_data(username)
            if not user_data:
                await self._record_failed_attempt(source_ip, username)
                return {"authenticated": False, "reason": "invalid_credentials"}
            
            # Verify password
            if auth_method == AuthMethod.PASSWORD:
                if not await self._verify_password(password, user_data["password_hash"]):
                    await self._record_failed_attempt(source_ip, username)
                    return {"authenticated": False, "reason": "invalid_credentials"}
            
            # Multi-factor authentication
            if user_data.get("mfa_enabled") and auth_method != AuthMethod.MFA:
                return {
                    "authenticated": False,
                    "reason": "mfa_required",
                    "mfa_methods": user_data.get("mfa_methods", ["totp"])
                }
            
            # Successful authentication
            session_id = await self._create_session(user_data, source_ip)
            auth_token = await self._generate_auth_token(user_data, session_id)
            
            self.security_metrics["successful_auth"] += 1
            
            # Clear failed attempts
            if source_ip in self.failed_attempts:
                del self.failed_attempts[source_ip]
            
            await self._create_audit_log({
                "event": "user_authenticated",
                "user_id": user_data["id"],
                "source_ip": source_ip,
                "method": auth_method.value
            })
            
            return {
                "authenticated": True,
                "user_id": user_data["id"],
                "session_id": session_id,
                "token": auth_token,
                "permissions": user_data.get("permissions", []),
                "expires_at": time.time() + 3600  # 1 hour
            }
            
        except Exception as e:
            self.logger.error("Authentication error", error=str(e))
            return {"authenticated": False, "reason": "system_error"}
    
    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False
    
    async def _get_user_data(self, username: str) -> Optional[Dict]:
        """Get user data from database"""
        if not self.db_pool:
            # Mock user data for testing
            return {
                "id": "user_123",
                "username": username,
                "password_hash": bcrypt.hashpw("password123".encode(), bcrypt.gensalt()).decode(),
                "permissions": ["read", "write"],
                "mfa_enabled": False
            }
        
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, username, password_hash, permissions, mfa_enabled, mfa_methods
                    FROM users WHERE username = $1 AND active = true
                """, username)
                
                if row:
                    return dict(row)
        except Exception as e:
            self.logger.error("Database error getting user", error=str(e))
        
        return None
    
    async def _record_failed_attempt(self, source_ip: str, username: str):
        """Record failed authentication attempt"""
        current_time = time.time()
        
        if source_ip not in self.failed_attempts:
            self.failed_attempts[source_ip] = []
        
        self.failed_attempts[source_ip].append(current_time)
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[source_ip] = [
            t for t in self.failed_attempts[source_ip]
            if current_time - t < 3600
        ]
        
        # Check if we should block IP
        recent_attempts = [
            t for t in self.failed_attempts[source_ip]
            if current_time - t < 300  # 5 minutes
        ]
        
        if len(recent_attempts) >= 5:
            self.blocked_ips.add(source_ip)
            await self._create_security_event(
                ThreatType.BRUTE_FORCE,
                SecurityLevel.HIGH,
                source_ip,
                f"IP blocked due to {len(recent_attempts)} failed attempts"
            )
        
        self.security_metrics["failed_auth"] += 1
    
    async def _create_session(self, user_data: Dict, source_ip: str) -> str:
        """Create authenticated session"""
        session_id = f"sess_{uuid.uuid4().hex}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_data["id"],
            "username": user_data["username"],
            "permissions": user_data.get("permissions", []),
            "source_ip": source_ip,
            "created_at": time.time(),
            "last_activity": time.time(),
            "expires_at": time.time() + 3600  # 1 hour
        }
        
        self.active_sessions[session_id] = session_data
        self.security_metrics["active_sessions"] = len(self.active_sessions)
        
        # Store in Redis if available
        if hasattr(self, 'redis') and self.redis:
            await self.redis.setex(
                f"session:{session_id}",
                3600,
                json.dumps(session_data)
            )
        
        return session_id
    
    async def _generate_auth_token(self, user_data: Dict, session_id: str) -> str:
        """Generate JWT authentication token"""
        payload = {
            "user_id": user_data["id"],
            "username": user_data["username"],
            "session_id": session_id,
            "permissions": user_data.get("permissions", []),
            "iat": time.time(),
            "exp": time.time() + 3600  # 1 hour
        }
        
        secret = os.getenv("JWT_SECRET", "your-secret-key")
        return jwt.encode(payload, secret, algorithm="HS256")
    
    async def _authorize_request(self, payload: Dict) -> Dict[str, Any]:
        """Authorize request based on token and permissions"""
        token = payload.get("token")
        resource = payload.get("resource")
        action = payload.get("action", "read")
        
        try:
            # Validate token
            secret = os.getenv("JWT_SECRET", "your-secret-key")
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            
            user_id = decoded["user_id"]
            permissions = decoded.get("permissions", [])
            session_id = decoded.get("session_id")
            
            # Check session validity
            if session_id not in self.active_sessions:
                return {"authorized": False, "reason": "invalid_session"}
            
            session = self.active_sessions[session_id]
            if time.time() > session["expires_at"]:
                del self.active_sessions[session_id]
                return {"authorized": False, "reason": "session_expired"}
            
            # Update last activity
            session["last_activity"] = time.time()
            
            # Check permissions
            required_permission = f"{action}:{resource}"
            if required_permission in permissions or "admin" in permissions:
                return {
                    "authorized": True,
                    "user_id": user_id,
                    "permissions": permissions
                }
            else:
                await self._create_security_event(
                    ThreatType.PRIVILEGE_ESCALATION,
                    SecurityLevel.MEDIUM,
                    session.get("source_ip", "unknown"),
                    f"Unauthorized access attempt: {user_id} -> {required_permission}"
                )
                return {"authorized": False, "reason": "insufficient_permissions"}
        
        except jwt.ExpiredSignatureError:
            return {"authorized": False, "reason": "token_expired"}
        except jwt.InvalidTokenError:
            return {"authorized": False, "reason": "invalid_token"}
        except Exception as e:
            self.logger.error("Authorization error", error=str(e))
            return {"authorized": False, "reason": "system_error"}
    
    async def _encrypt_data(self, payload: Dict) -> Dict[str, Any]:
        """Encrypt sensitive data"""
        data = payload.get("data")
        encryption_method = payload.get("method", "fernet")
        
        try:
            if encryption_method == "fernet":
                fernet = Fernet(self.master_key)
                encrypted_data = fernet.encrypt(json.dumps(data).encode())
                
                return {
                    "encrypted": True,
                    "data": base64.b64encode(encrypted_data).decode(),
                    "method": encryption_method,
                    "key_id": "master"
                }
            
            elif encryption_method == "rsa":
                # Generate RSA key pair for this session
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                public_key = private_key.public_key()
                
                # Encrypt data with public key
                encrypted_data = public_key.encrypt(
                    json.dumps(data).encode(),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                # Store private key for decryption
                key_id = f"rsa_{uuid.uuid4().hex[:8]}"
                self.session_keys[key_id] = private_key
                
                return {
                    "encrypted": True,
                    "data": base64.b64encode(encrypted_data).decode(),
                    "method": encryption_method,
                    "key_id": key_id,
                    "public_key": base64.b64encode(
                        public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                        )
                    ).decode()
                }
            
            else:
                raise ValueError(f"Unsupported encryption method: {encryption_method}")
        
        except Exception as e:
            self.logger.error("Encryption error", error=str(e))
            return {"encrypted": False, "error": str(e)}
    
    async def _decrypt_data(self, payload: Dict) -> Dict[str, Any]:
        """Decrypt encrypted data"""
        encrypted_data = payload.get("data")
        encryption_method = payload.get("method", "fernet")
        key_id = payload.get("key_id", "master")
        
        try:
            if encryption_method == "fernet":
                fernet = Fernet(self.master_key)
                decrypted_bytes = fernet.decrypt(base64.b64decode(encrypted_data))
                decrypted_data = json.loads(decrypted_bytes.decode())
                
                return {
                    "decrypted": True,
                    "data": decrypted_data
                }
            
            elif encryption_method == "rsa":
                if key_id not in self.session_keys:
                    return {"decrypted": False, "error": "Private key not found"}
                
                private_key = self.session_keys[key_id]
                decrypted_bytes = private_key.decrypt(
                    base64.b64decode(encrypted_data),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                decrypted_data = json.loads(decrypted_bytes.decode())
                
                return {
                    "decrypted": True,
                    "data": decrypted_data
                }
            
            else:
                raise ValueError(f"Unsupported encryption method: {encryption_method}")
        
        except Exception as e:
            self.logger.error("Decryption error", error=str(e))
            return {"decrypted": False, "error": str(e)}
    
    async def _security_scan(self, payload: Dict) -> Dict[str, Any]:
        """Perform security vulnerability scan"""
        target = payload.get("target")
        scan_type = payload.get("type", "basic")
        
        vulnerabilities = []
        
        # SQL Injection detection
        if isinstance(target, str):
            sql_patterns = [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b)",
                r"(\bDROP\b.*\bTABLE\b)",
                r"(\bINSERT\b.*\bINTO\b)",
                r"(\bDELETE\b.*\bFROM\b)",
                r"(';.*--)",
                r"(\bOR\b.*\b1=1\b)"
            ]
            
            for pattern in sql_patterns:
                if re.search(pattern, target, re.IGNORECASE):
                    vulnerabilities.append({
                        "type": "sql_injection",
                        "severity": "high",
                        "description": "Potential SQL injection pattern detected",
                        "pattern": pattern
                    })
        
        # XSS detection
        if isinstance(target, str):
            xss_patterns = [
                r"<script[^>]*>.*</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>"
            ]
            
            for pattern in xss_patterns:
                if re.search(pattern, target, re.IGNORECASE):
                    vulnerabilities.append({
                        "type": "xss",
                        "severity": "medium",
                        "description": "Potential XSS pattern detected",
                        "pattern": pattern
                    })
        
        # Path traversal detection
        if isinstance(target, str):
            path_patterns = [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c"
            ]
            
            for pattern in path_patterns:
                if re.search(pattern, target, re.IGNORECASE):
                    vulnerabilities.append({
                        "type": "path_traversal",
                        "severity": "high",
                        "description": "Potential path traversal pattern detected",
                        "pattern": pattern
                    })
        
        return {
            "scan_completed": True,
            "target": target,
            "scan_type": scan_type,
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "risk_level": self._calculate_risk_level(vulnerabilities)
        }
    
    def _calculate_risk_level(self, vulnerabilities: List[Dict]) -> str:
        """Calculate overall risk level from vulnerabilities"""
        if not vulnerabilities:
            return "low"
        
        high_count = len([v for v in vulnerabilities if v["severity"] == "high"])
        medium_count = len([v for v in vulnerabilities if v["severity"] == "medium"])
        
        if high_count > 0:
            return "critical" if high_count > 2 else "high"
        elif medium_count > 2:
            return "medium"
        else:
            return "low"
    
    async def _threat_analysis(self, payload: Dict) -> Dict[str, Any]:
        """Analyze potential security threats"""
        events = payload.get("events", [])
        time_window = payload.get("time_window", 3600)  # 1 hour
        
        current_time = time.time()
        recent_events = [
            event for event in self.security_events
            if current_time - event.timestamp < time_window
        ]
        
        # Analyze threat patterns
        threat_patterns = {}
        for event in recent_events:
            threat_type = event.event_type.value
            if threat_type not in threat_patterns:
                threat_patterns[threat_type] = {
                    "count": 0,
                    "severity_levels": {},
                    "sources": set()
                }
            
            threat_patterns[threat_type]["count"] += 1
            severity = event.severity.value
            threat_patterns[threat_type]["severity_levels"][severity] = \
                threat_patterns[threat_type]["severity_levels"].get(severity, 0) + 1
            threat_patterns[threat_type]["sources"].add(event.source_ip)
        
        # Convert sets to lists for JSON serialization
        for pattern in threat_patterns.values():
            pattern["sources"] = list(pattern["sources"])
        
        # Detect anomalies
        anomalies = []
        for threat_type, pattern in threat_patterns.items():
            if pattern["count"] > 10:  # Threshold for anomaly
                anomalies.append({
                    "threat_type": threat_type,
                    "count": pattern["count"],
                    "severity": "high" if pattern["count"] > 50 else "medium",
                    "description": f"Unusually high number of {threat_type} events"
                })
        
        return {
            "analysis_completed": True,
            "time_window": time_window,
            "total_events": len(recent_events),
            "threat_patterns": threat_patterns,
            "anomalies": anomalies,
            "risk_score": self._calculate_threat_risk_score(threat_patterns, anomalies)
        }
    
    def _calculate_threat_risk_score(self, patterns: Dict, anomalies: List) -> int:
        """Calculate threat risk score (0-100)"""
        base_score = 0
        
        # Score based on threat patterns
        for threat_type, pattern in patterns.items():
            multiplier = 1.0
            if threat_type in ["brute_force", "sql_injection"]:
                multiplier = 2.0
            elif threat_type in ["malware", "data_breach"]:
                multiplier = 3.0
            
            base_score += min(pattern["count"] * multiplier, 30)
        
        # Add anomaly scores
        for anomaly in anomalies:
            if anomaly["severity"] == "high":
                base_score += 20
            else:
                base_score += 10
        
        return min(int(base_score), 100)
    
    async def _create_audit_log(self, payload: Dict) -> Dict[str, Any]:
        """Create security audit log entry"""
        event = payload.get("event")
        user_id = payload.get("user_id")
        resource = payload.get("resource")
        metadata = payload.get("metadata", {})
        
        audit_entry = {
            "id": f"audit_{uuid.uuid4().hex}",
            "event": event,
            "user_id": user_id,
            "resource": resource,
            "metadata": metadata,
            "timestamp": time.time(),
            "ip_address": metadata.get("source_ip"),
            "user_agent": metadata.get("user_agent")
        }
        
        # Store audit log
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO audit_logs 
                        (id, event, user_id, resource, metadata, timestamp, ip_address, user_agent)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, 
                    audit_entry["id"], audit_entry["event"], audit_entry["user_id"],
                    audit_entry["resource"], json.dumps(audit_entry["metadata"]),
                    audit_entry["timestamp"], audit_entry["ip_address"], 
                    audit_entry["user_agent"])
            except Exception as e:
                self.logger.error("Failed to store audit log", error=str(e))
        
        return {
            "audit_logged": True,
            "audit_id": audit_entry["id"],
            "timestamp": audit_entry["timestamp"]
        }
    
    async def _create_security_event(self, threat_type: ThreatType, severity: SecurityLevel, 
                                   source_ip: str, description: str, user_id: str = None):
        """Create and store security event"""
        event = SecurityEvent(
            event_id=f"event_{uuid.uuid4().hex[:8]}",
            event_type=threat_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            description=description
        )
        
        self.security_events.append(event)
        self.security_metrics["threats_detected"] += 1
        
        # Publish security event
        await self._publish("security.event.detected", {
            "event_id": event.event_id,
            "threat_type": threat_type.value,
            "severity": severity.value,
            "source_ip": source_ip,
            "description": description,
            "timestamp": event.timestamp
        })
        
        # Auto-response for critical threats
        if severity == SecurityLevel.CRITICAL:
            await self._handle_critical_threat(event)
        
        self.logger.warning("Security event created",
                          event_id=event.event_id,
                          threat_type=threat_type.value,
                          severity=severity.value,
                          source_ip=source_ip)
    
    async def _handle_critical_threat(self, event: SecurityEvent):
        """Handle critical security threats with immediate response"""
        # Block source IP for critical threats
        if event.source_ip and event.source_ip != "unknown":
            self.blocked_ips.add(event.source_ip)
            
            # Terminate all sessions from this IP
            sessions_to_remove = []
            for session_id, session in self.active_sessions.items():
                if session.get("source_ip") == event.source_ip:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            self.logger.critical("Critical threat response activated",
                               event_id=event.event_id,
                               blocked_ip=event.source_ip,
                               terminated_sessions=len(sessions_to_remove))
    
    async def _check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        current_time = time.time()
        
        if key not in self.rate_limiters:
            self.rate_limiters[key] = []
        
        # Remove old requests outside time window
        self.rate_limiters[key] = [
            timestamp for timestamp in self.rate_limiters[key]
            if current_time - timestamp < window
        ]
        
        # Check if limit exceeded
        if len(self.rate_limiters[key]) >= limit:
            return False
        
        # Add current request
        self.rate_limiters[key].append(current_time)
        return True
    
    async def _handle_auth_request(self, msg):
        """Handle authentication requests"""
        try:
            data = json.loads(msg.data.decode())
            result = await self._authenticate_user(data)
            
            if msg.reply:
                await self.nats.publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Failed to handle auth request", error=str(e))
    
    async def _handle_authz_request(self, msg):
        """Handle authorization requests"""
        try:
            data = json.loads(msg.data.decode())
            result = await self._authorize_request(data)
            
            if msg.reply:
                await self.nats.publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Failed to handle authz request", error=str(e))
    
    async def _handle_encrypt_request(self, msg):
        """Handle encryption requests"""
        try:
            data = json.loads(msg.data.decode())
            
            if data.get("action") == "encrypt":
                result = await self._encrypt_data(data)
            elif data.get("action") == "decrypt":
                result = await self._decrypt_data(data)
            else:
                result = {"error": "Invalid encryption action"}
            
            if msg.reply:
                await self.nats.publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error("Failed to handle encryption request", error=str(e))
    
    async def _handle_security_event(self, msg):
        """Handle incoming security events"""
        try:
            data = json.loads(msg.data.decode())
            
            threat_type = ThreatType(data.get("threat_type"))
            severity = SecurityLevel(data.get("severity"))
            source_ip = data.get("source_ip", "unknown")
            description = data.get("description", "")
            user_id = data.get("user_id")
            
            await self._create_security_event(threat_type, severity, source_ip, description, user_id)
            
        except Exception as e:
            self.logger.error("Failed to handle security event", error=str(e))
    
    async def _handle_security_task(self, msg):
        """Handle security task requests"""
        try:
            data = json.loads(msg.data.decode())
            request = TaskRequest(**data)
            
            with self.tracer.start_as_current_span("security_task") as span:
                span.set_attribute("task_id", request.task_id)
                span.set_attribute("task_type", request.task_type)
                
                result = await self.execute_task(request)
                
                await self._publish_to_stream(
                    f"task.{request.task_id}.response",
                    result
                )
                
        except Exception as e:
            self.logger.error("Failed to handle security task", error=str(e))
    
    async def _threat_monitor(self):
        """Background thread to monitor for threats"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Check for brute force attempts
                for ip, attempts in list(self.failed_attempts.items()):
                    recent_attempts = [t for t in attempts if current_time - t < 300]
                    
                    if len(recent_attempts) >= 3:
                        await self._create_security_event(
                            ThreatType.BRUTE_FORCE,
                            SecurityLevel.MEDIUM,
                            ip,
                            f"Multiple failed attempts detected: {len(recent_attempts)}"
                        )
                
                # Check session anomalies
                suspicious_sessions = []
                for session_id, session in self.active_sessions.items():
                    # Check for session hijacking indicators
                    if current_time - session["last_activity"] > 3600:  # Inactive for 1 hour
                        continue
                    
                    # Check for rapid location changes (if available)
                    # This would require GeoIP lookup implementation
                    
                    # Check for unusual activity patterns
                    # This would require behavioral analysis implementation
                
                # Clean up old events (keep last 24 hours)
                cutoff_time = current_time - 86400
                self.security_events = [
                    event for event in self.security_events
                    if event.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error("Threat monitoring error", error=str(e))
                await asyncio.sleep(30)
    
    async def _session_cleaner(self):
        """Clean up expired sessions"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                expired_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if current_time > session["expires_at"]:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    del self.active_sessions[session_id]
                    
                    # Remove from Redis if available
                    if hasattr(self, 'redis') and self.redis:
                        await self.redis.delete(f"session:{session_id}")
                
                self.security_metrics["active_sessions"] = len(self.active_sessions)
                
                if expired_sessions:
                    self.logger.info("Cleaned expired sessions", count=len(expired_sessions))
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                self.logger.error("Session cleanup error", error=str(e))
                await asyncio.sleep(60)
    
    async def _security_metrics_publisher(self):
        """Publish security metrics periodically"""
        while not self._shutdown_event.is_set():
            try:
                metrics = {
                    "timestamp": time.time(),
                    "security_metrics": self.security_metrics.copy(),
                    "active_threats": len([
                        event for event in self.security_events
                        if not event.resolved and 
                        time.time() - event.timestamp < 3600
                    ]),
                    "blocked_ips": len(self.blocked_ips),
                    "security_policies": len(self.security_policies),
                    "recent_events": len([
                        event for event in self.security_events
                        if time.time() - event.timestamp < 300
                    ])
                }
                
                await self._publish_to_stream("METRICS", {
                    "type": "security_agent_metrics",
                    "agent_id": self.id,
                    "metrics": metrics
                })
                
                await asyncio.sleep(60)  # Publish every minute
                
            except Exception as e:
                self.logger.error("Security metrics publishing failed", error=str(e))
                await asyncio.sleep(30)
    
    async def _anomaly_detector(self):
        """Detect behavioral anomalies"""
        while not self._shutdown_event.is_set():
            try:
                current_time = time.time()
                
                # Analyze authentication patterns
                auth_patterns = {}
                recent_auths = [
                    event for event in self.security_events
                    if event.event_type == ThreatType.BRUTE_FORCE and
                    current_time - event.timestamp < 3600
                ]
                
                for event in recent_auths:
                    hour = int(event.timestamp // 3600)
                    if hour not in auth_patterns:
                        auth_patterns[hour] = 0
                    auth_patterns[hour] += 1
                
                # Detect unusual spikes
                if auth_patterns:
                    avg_attempts = sum(auth_patterns.values()) / len(auth_patterns)
                    for hour, attempts in auth_patterns.items():
                        if attempts > avg_attempts * 3:  # 3x normal rate
                            await self._create_security_event(
                                ThreatType.SUSPICIOUS_BEHAVIOR,
                                SecurityLevel.MEDIUM,
                                "multiple",
                                f"Unusual authentication spike detected: {attempts} attempts"
                            )
                
                await asyncio.sleep(1800)  # Analyze every 30 minutes
                
            except Exception as e:
                self.logger.error("Anomaly detection error", error=str(e))
                await asyncio.sleep(300)


if __name__ == "__main__":
    import os
    
    config = AgentConfig(
        name="security",
        agent_type="security",
        capabilities=[
            "authentication",
            "authorization", 
            "encryption",
            "threat_detection",
            "security_scanning",
            "audit_logging"
        ],
        nats_url=os.getenv("NATS_URL", "nats://nats:4222"),
        postgres_url=os.getenv("POSTGRES_URL"),
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379"),
        consul_url=os.getenv("CONSUL_URL", "http://consul:8500")
    )
    
    agent = SecurityAgent(config)
    asyncio.run(agent.run())