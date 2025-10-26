# security/data_flow_validator.py
"""
Advanced data flow validation with secure routing, schema enforcement,
content inspection, and data loss prevention.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from enum import Enum
import re
import json
import hashlib
import base64
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class DataValidationLevel(str, Enum):
    """Validation levels for data flows"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    PARANOID = "paranoid"

class DataClassification(str, Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class ValidationRule:
    """Data validation rule definition"""
    name: str
    pattern: str
    description: str
    validation_type: str  # regex, format, schema, semantic
    severity: str  # low, medium, high, critical
    enabled: bool = True

class DataFlowValidator:
    """Advanced data flow validation and security"""
    
    def __init__(self, manager):
        self.manager = manager
        self.validation_rules = self._load_validation_rules()
        self.sensitive_data_patterns = self._load_sensitive_patterns()
        self.schema_validators = {}
        self.validation_callbacks = {}
        
        # Initialize metrics
        self.validation_count = 0
        self.validation_failures = 0
        self.validation_time_total = 0
    
    def _load_validation_rules(self) -> Dict[str, List[ValidationRule]]:
        """Load validation rules for different flow types"""
        rules = {}
        
        # Agent report validation rules
        rules["agent.report"] = [
            ValidationRule(
                name="required_fields",
                pattern=r'(status|health)',
                description="Report must contain status and health fields",
                validation_type="regex",
                severity="high"
            ),
            ValidationRule(
                name="valid_status",
                pattern=r'^(active|inactive|busy|error|suspended|isolated)$',
                description="Status must be a valid status value",
                validation_type="regex",
                severity="medium"
            )
        ]
        
        # Task result validation rules
        rules["task.result"] = [
            ValidationRule(
                name="max_result_size",
                pattern=r'^.{1,1048576}$',  # Max 1MB result
                description="Task result exceeds maximum size",
                validation_type="regex",
                severity="medium"
            )
        ]
        
        # Task creation validation rules
        rules["task.create"] = [
            ValidationRule(
                name="task_type_whitelist",
                pattern=r'^[a-zA-Z0-9_\-\.]+$',
                description="Task type contains invalid characters",
                validation_type="regex",
                severity="high"
            )
        ]
        
        return rules
    
    def _load_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Load patterns for sensitive data detection"""
        return {
            "credit_card": re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "api_key": re.compile(r'\b[A-Za-z0-9_\-]{20,}\b'),
            "password": re.compile(r'password["\s:=]+[^"\s]+'),
            "jwt": re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+')
        }
    
    async def validate_data_flow(self, flow_type: str, data: Dict[str, Any], 
                               context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Validate data flow with comprehensive security checks
        Returns: (valid, message)
        """
        start_time = datetime.utcnow()
        context = context or {}
        validation_level = context.get("validation_level", DataValidationLevel.STANDARD)
        
        try:
            # Validation result (valid, message)
            result = (True, "Data validated successfully")
            
            # 1. Apply basic validation
            basic_validation = self._perform_basic_validation(flow_type, data, context)
            if not basic_validation[0]:
                return basic_validation
            
            # 2. Apply schema validation
            schema_validation = await self._perform_schema_validation(flow_type, data, context)
            if not schema_validation[0]:
                return schema_validation
            
            # 3. Perform sensitive data check
            if validation_level in [DataValidationLevel.STRICT, DataValidationLevel.PARANOID]:
                sensitive_check = self._check_sensitive_data(data)
                if sensitive_check[0]:  # Contains sensitive data
                    result = (False, f"Sensitive data detected: {sensitive_check[1]}")
                    return result
            
            # 4. Perform custom validation rules
            rule_validation = self._validate_against_rules(flow_type, data)
            if not rule_validation[0]:
                return rule_validation
            
            # 5. Apply custom validation callbacks if registered
            if flow_type in self.validation_callbacks:
                for callback in self.validation_callbacks[flow_type]:
                    callback_result = await callback(data, context)
                    if not callback_result[0]:
                        return callback_result
            
            # Update metrics
            self.validation_count += 1
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.validation_time_total += duration
            
            # 6. Log data access for auditing
            await self._log_data_access(flow_type, data, context, True)
            
            return result
            
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            self.validation_failures += 1
            
            # Log failed validation
            await self._log_data_access(flow_type, data, context, False, str(e))
            
            return (False, f"Validation error: {str(e)}")
    
    def _perform_basic_validation(self, flow_type: str, data: Dict[str, Any], 
                                context: Dict[str, Any]) -> Tuple[bool, str]:
        """Perform basic data validation"""
        # Check for null/empty data
        if not data:
            return (False, "Data cannot be empty")
        
        # Check for payload size limits
        data_size = len(json.dumps(data))
        if data_size > 10 * 1024 * 1024:  # 10MB limit
            return (False, f"Data exceeds maximum size: {data_size} bytes")
        
        # Check for malicious input patterns
        if self._contains_malicious_patterns(data):
            return (False, "Potential security threat detected in data")
        
        return (True, "Basic validation passed")
    
    async def _perform_schema_validation(self, flow_type: str, data: Dict[str, Any],
                                      context: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate data against defined schemas"""
        if flow_type in self.schema_validators:
            validator = self.schema_validators[flow_type]
            try:
                result = validator(data)
                if not result:
                    return (False, f"Schema validation failed for {flow_type}")
            except Exception as e:
                return (False, f"Schema validation error: {str(e)}")
        
        return (True, "Schema validation passed")
    
    def _validate_against_rules(self, flow_type: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate data against defined rules for flow type"""
        if flow_type not in self.validation_rules:
            return (True, "No specific rules for this flow type")
        
        rules = self.validation_rules[flow_type]
        data_str = json.dumps(data)
        
        for rule in rules:
            if not rule.enabled:
                continue
                
            if rule.validation_type == "regex":
                pattern = re.compile(rule.pattern)
                
                # For required fields, check if fields exist
                if rule.name == "required_fields":
                    missing_fields = []
                    for field in pattern.findall(rule.pattern):
                        if field not in data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        return (False, f"Required fields missing: {', '.join(missing_fields)}")
                
                # For value validation, check if values match pattern
                elif "valid_" in rule.name:
                    field_name = rule.name.replace("valid_", "")
                    if field_name in data:
                        value = str(data[field_name])
                        if not pattern.match(value):
                            return (False, rule.description)
        
        return (True, "Rule validation passed")
    
    def _check_sensitive_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for sensitive data patterns"""
        data_str = json.dumps(data)
        
        for pattern_name, pattern in self.sensitive_data_patterns.items():
            if pattern.search(data_str):
                return (True, pattern_name)
        
        return (False, "")
    
    def _contains_malicious_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for potentially malicious patterns"""
        data_str = json.dumps(data)
        
        # Check for common attack patterns
        malicious_patterns = [
            # SQL injection
            r"(?i)'\s*OR\s*'1'='1",
            r"(?i);\s*DROP\s+TABLE",
            r"(?i);\s*DELETE\s+FROM",
            
            # Command injection
            r"(?i)`.*`",
            r"(?i)\|\s*.*",
            r"(?i);\s*.*",
            
            # XSS
            r"(?i)<script.*>",
            r"(?i)javascript:",
            r"(?i)onerror=",
            
            # Path traversal
            r"(?i)\.\./"
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, data_str):
                return True
        
        return False
    
    async def _log_data_access(self, flow_type: str, data: Dict[str, Any], 
                             context: Dict[str, Any], success: bool, 
                             error: str = None) -> None:
        """Log data access for auditing"""
        try:
            # Create data access log entry
            log_entry = {
                "flow_type": flow_type,
                "timestamp": datetime.utcnow().isoformat(),
                "context": {
                    "user_id": context.get("user_id"),
                    "agent_id": context.get("agent_id"),
                    "ip_address": context.get("ip_address")
                },
                "success": success,
                "data_size": len(json.dumps(data)),
                "error": error
            }
            
            # Store in database
            async with self.manager.get_db_session() as session:
                from models import DataAccessLog
                log = DataAccessLog(
                    user_id=context.get("user_id"),
                    agent_id=context.get("agent_id"),
                    resource_type=flow_type,
                    resource_id=context.get("resource_id", str(hash(json.dumps(data)))),
                    operation="read",
                    success=success,
                    details=log_entry,
                    ip_address=context.get("ip_address"),
                    data_size=log_entry["data_size"]
                )
                session.add(log)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
    
    def register_schema_validator(self, flow_type: str, validator: Callable) -> None:
        """Register schema validator for flow type"""
        self.schema_validators[flow_type] = validator
    
    def register_validation_callback(self, flow_type: str, callback: Callable) -> None:
        """Register custom validation callback for flow type"""
        if flow_type not in self.validation_callbacks:
            self.validation_callbacks[flow_type] = []
        self.validation_callbacks[flow_type].append(callback)

    async def classify_data(self, data: Dict[str, Any]) -> DataClassification:
        """Classify data sensitivity level"""
        data_str = json.dumps(data)
        
        # Check for most restricted patterns first
        if any(pattern.search(data_str) for name, pattern in 
               self.sensitive_data_patterns.items() if name in ['ssn', 'credit_card']):
            return DataClassification.RESTRICTED
        
        # Check for confidential patterns
        if any(pattern.search(data_str) for name, pattern in 
               self.sensitive_data_patterns.items() if name in ['api_key', 'password', 'jwt']):
            return DataClassification.CONFIDENTIAL
        
        # Default to internal
        return DataClassification.INTERNAL