# infrastructure/security/__init__.py
"""
Security Infrastructure for YMERA Enterprise System
"""
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
import time
import jwt
import bcrypt
from cryptography.fernet import Fernet
import secrets
import string
import re

logger = logging.getLogger("ymera.infrastructure.security")

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class User:
    user_id: str
    username: str
    email: str
    hashed_password: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    mfa_enabled: bool = False
    last_login: float = 0
    failed_attempts: int = 0

class AuthenticationManager:
    """Authentication and authorization management"""
    
    def __init__(self, secret_key: str, token_expiry: int = 3600):
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self.users: Dict[str, User] = {}
        self.blacklisted_tokens: set = set()
        self.login_attempts: Dict[str, int] = {}
    
    def register_user(self, username: str, email: str, password: str, 
                     roles: List[str] = None, permissions: List[str] = None) -> str:
        """Register a new user"""
        if username in self.users:
            raise ValueError("Username already exists")
        
        user_id = str(uuid.uuid4())
        hashed_password = self._hash_password(password)
        
        self.users[username] = User(
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            roles=roles or [],
            permissions=permissions or []
        )
        
        return user_id
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate a user"""
        if username not in self.users:
            return False, "Invalid credentials"
        
        user = self.users[username]
        
        # Check if account is locked
        if user.failed_attempts >= 5:
            return False, "Account locked due to too many failed attempts"
        
        # Verify password
        if not self._verify_password(password, user.hashed_password):
            user.failed_attempts += 1
            return False, "Invalid credentials"
        
        # Reset failed attempts on successful login
        user.failed_attempts = 0
        user.last_login = time.time()
        
        # Generate JWT token
        token = self._generate_token(user)
        return True, token
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[User]]:
        """Verify a JWT token"""
        if token in self.blacklisted_tokens:
            return False, None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            username = payload.get("sub")
            
            if username not in self.users:
                return False, None
            
            return True, self.users[username]
        except jwt.ExpiredSignatureError:
            return False, None
        except jwt.InvalidTokenError:
            return False, None
    
    def blacklist_token(self, token: str):
        """Blacklist a token (logout)"""
        self.blacklisted_tokens.add(token)
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission"""
        return permission in user.permissions
    
    def has_role(self, user: User, role: str) -> bool:
        """Check if user has a specific role"""
        return role in user.roles
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    
    def _generate_token(self, user: User) -> str:
        """Generate a JWT token for a user"""
        payload = {
            "sub": user.username,
            "user_id": user.user_id,
            "roles": user.roles,
            "permissions": user.permissions,
            "exp": time.time() + self.token_expiry,
            "iat": time.time()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

class EncryptionManager:
    """Encryption and decryption management"""
    
    def __init__(self):
        self.keys: Dict[str, bytes] = {}
        self.fernet_instances: Dict[str, Fernet] = {}
    
    def generate_key(self, key_id: str) -> str:
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        self.keys[key_id] = key
        self.fernet_instances[key_id] = Fernet(key)
        return key.decode()
    
    def encrypt_data(self, key_id: str, data: str) -> str:
        """Encrypt data using specified key"""
        if key_id not in self.fernet_instances:
            raise ValueError(f"Key {key_id} not found")
        
        encrypted_data = self.fernet_instances[key_id].encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_data(self, key_id: str, encrypted_data: str) -> str:
        """Decrypt data using specified key"""
        if key_id not in self.fernet_instances:
            raise ValueError(f"Key {key_id} not found")
        
        decrypted_data = self.fernet_instances[key_id].decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def rotate_key(self, old_key_id: str, new_key_id: str):
        """Rotate encryption keys"""
        if old_key_id not in self.fernet_instances:
            raise ValueError(f"Key {old_key_id} not found")
        
        self.generate_key(new_key_id)
        # In real implementation, you would re-encrypt data with new key

class DataMasker:
    """Data masking and anonymization utilities"""
    
    def __init__(self):
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text"""
        detected = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected[pii_type] = matches
        
        return detected
    
    def mask_pii(self, text: str, mask_char: str = '*') -> str:
        """Mask PII in text"""
        masked_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                original = match.group()
                masked = self._mask_string(original, mask_char)
                masked_text = masked_text.replace(original, masked)
        
        return masked_text
    
    def _mask_string(self, s: str, mask_char: str) -> str:
        """Mask a string, preserving format"""
        if '@' in s:  # Email
            parts = s.split('@')
            return f"{self._mask_partial(parts[0], mask_char)}@{parts[1]}"
        elif any(c in s for c in ['-', ' ', '.']):  # Phone, SSN, Credit Card
            return re.sub(r'\d', mask_char, s)
        else:
            return mask_char * len(s)
    
    def _mask_partial(self, s: str, mask_char: str, visible_chars: int = 2) -> str:
        """Mask part of a string, leaving some characters visible"""
        if len(s) <= visible_chars:
            return s
        return s[:visible_chars] + (mask_char * (len(s) - visible_chars))

class SecurityScanner:
    """Security scanning and vulnerability assessment"""
    
    def __init__(self):
        self.vulnerability_db: Dict[str, Any] = {}
        self.scan_results: Dict[str, List[Dict[str, Any]]] = {}
    
    async def scan_dependencies(self, dependencies: Dict[str, str]) -> List[Dict[str, Any]]:
        """Scan dependencies for known vulnerabilities"""
        vulnerabilities = []
        
        for package, version in dependencies.items():
            # Simulate vulnerability database lookup
            if await self._check_vulnerability(package, version):
                vulnerabilities.append({
                    'package': package,
                    'version': version,
                    'severity': 'high',  # Simulated
                    'cve': 'CVE-2023-XXXXX',  # Simulated
                    'description': 'Simulated vulnerability description'
                })
        
        return vulnerabilities
    
    async def scan_code(self, code_path: str) -> List[Dict[str, Any]]:
        """Scan code for security issues"""
        issues = []
        
        # Simulated code scanning
        issues.append({
            'type': 'security',
            'severity': 'medium',
            'file': 'example.py',
            'line': 42,
            'description': 'Potential SQL injection vulnerability',
            'recommendation': 'Use parameterized queries'
        })
        
        return issues
    
    async def _check_vulnerability(self, package: str, version: str) -> bool:
        """Check if a package version has known vulnerabilities"""
        # Simulated vulnerability check
        # In real implementation, this would query a vulnerability database
        return (package, version) in [
            ('requests', '2.25.0'),
            ('numpy', '1.19.0'),
            ('tensorflow', '2.3.0')
        ]

class AuditLogger:
    """Audit logging for compliance and security"""
    
    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []
    
    def log_event(self, event_type: str, user: str, resource: str, 
                 action: str, status: str, details: Dict[str, Any] = None):
        """Log an audit event"""
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'user': user,
            'resource': resource,
            'action': action,
            'status': status,
            'details': details or {}
        }
        
        self.audit_log.append(event)
        logger.info(f"AUDIT: {event_type} - {user} - {action} - {status}")
    
    def get_events(self, start_time: float = None, end_time: float = None, 
                  event_type: str = None, user: str = None) -> List[Dict[str, Any]]:
        """Retrieve audit events with filtering"""
        filtered_events = self.audit_log
        
        if start_time:
            filtered_events = [e for e in filtered_events if e['timestamp'] >= start_time]
        if end_time:
            filtered_events = [e for e in filtered_events if e['timestamp'] <= end_time]
        if event_type:
            filtered_events = [e for e in filtered_events if e['event_type'] == event_type]
        if user:
            filtered_events = [e for e in filtered_events if e['user'] == user]
        
        return filtered_events
    
    def generate_compliance_report(self, start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate a compliance report for the given time period"""
        events = self.get_events(start_time, end_time)
        
        report = {
            'period': {'start': start_time, 'end': end_time},
            'total_events': len(events),
            'events_by_type': {},
            'events_by_user': {},
            'events_by_status': {},
            'security_incidents': 0
        }
        
        for event in events:
            # Count by type
            report['events_by_type'][event['event_type']] = report['events_by_type'].get(event['event_type'], 0) + 1
            
            # Count by user
            report['events_by_user'][event['user']] = report['events_by_user'].get(event['user'], 0) + 1
            
            # Count by status
            report['events_by_status'][event['status']] = report['events_by_status'].get(event['status'], 0) + 1
            
            # Count security incidents
            if event['status'] == 'failure' and event['event_type'] in ['login', 'access']:
                report['security_incidents'] += 1
        
        return report
