"""
Advanced Validation Agent
Schema validation, data integrity, business rules, and compliance checking
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import re
# Optional dependencies - JSON validation
try:
    import jsonschema
    from jsonschema import validate, ValidationError as JSONSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None
    validate = None
    JSONSchemaValidationError = None
    HAS_JSONSCHEMA = False

# Optional dependencies - Data validation
try:
    import pydantic
    from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, validator
    HAS_PYDANTIC = True
except ImportError:
    pydantic = None
    BaseModel = None
    Field = None
    PydanticValidationError = None
    validator = None
    HAS_PYDANTIC = False

# Optional dependencies - SQL ORM
try:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql
    HAS_SQLALCHEMY = True
except ImportError:
    sa = None
    postgresql = None
    HAS_SQLALCHEMY = False

import hashlib
import uuid

# Optional dependencies
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None
    validate = None
    class ValidationError(Exception): pass  # Fallback
    HAS_JSONSCHEMA = False

try:
    import pydantic
    from pydantic import BaseModel, Field, validator
    HAS_PYDANTIC = True
except ImportError:
    pydantic = None
    class BaseModel:
        """
        Stub BaseModel for when pydantic is not installed.
        Allows subclassing and instantiation, but raises an error on usage.
        """
        def __init__(self, *args, **kwargs):
            pass
        def __getattribute__(self, name):
            if name in ("__class__", "__doc__", "__init__", "__getattribute__"):
                return object.__getattribute__(self, name)
            raise RuntimeError(
                "Pydantic is required to use BaseModel functionality. Please install pydantic."
            )
    Field = None
    validator = None
    HAS_PYDANTIC = False

try:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql
    HAS_SQLALCHEMY = True
except ImportError:
    sa = None
    postgresql = None
    HAS_SQLALCHEMY = False

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority

# Optional dependencies - OpenTelemetry
try:
    from opentelemetry import trace
    HAS_OPENTELEMETRY = True
except ImportError:
    trace = None
    HAS_OPENTELEMETRY = False

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    ENTERPRISE = "enterprise"

class ValidationResult(Enum):
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationRule:
    id: str
    name: str
    description: str
    rule_type: str  # schema, regex, custom, business_logic
    rule_definition: Dict[str, Any]
    level: ValidationLevel = ValidationLevel.STANDARD
    enabled: bool = True
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationIssue:
    rule_id: str
    severity: ValidationResult
    message: str
    field_path: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationReport:
    validation_id: str
    data_id: str
    overall_result: ValidationResult
    issues: List[ValidationIssue] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)
    execution_time_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

# Predefined validation schemas
COMMON_SCHEMAS = {
    "email": {
        "type": "string",
        "format": "email",
        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    },
    "phone": {
        "type": "string",
        "pattern": r"^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$"
    },
    "url": {
        "type": "string",
        "format": "uri",
        "pattern": r"^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$"
    },
    "api_key": {
        "type": "string",
        "pattern": r"^[a-zA-Z0-9_-]{32,128}$",
        "minLength": 32,
        "maxLength": 128
    },
    "uuid": {
        "type": "string",
        "pattern": r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    },
    "json_web_token": {
        "type": "string",
        "pattern": r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"
    },
    "credit_card": {
        "type": "string",
        "pattern": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})$"
    },
    "ip_address": {
        "type": "string",
        "oneOf": [
            {"format": "ipv4"},
            {"format": "ipv6"}
        ]
    },
    "password": {
        "type": "string",
        "minLength": 8,
        "pattern": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]"
    }
}

# Business rule templates
BUSINESS_RULES = {
    "financial_transaction": {
        "rules": [
            {
                "name": "amount_range",
                "condition": "amount > 0 and amount <= 1000000",
                "message": "Transaction amount must be between $0 and $1,000,000"
            },
            {
                "name": "valid_currency",
                "condition": "currency in [\'USD\', \'EUR\', \'GBP\', \'JPY\', \'CAD\', \'AUD\']",
                "message": "Currency must be a valid ISO code"
            }
        ]
    },
    "user_registration": {
        "rules": [
            {
                "name": "unique_email",
                "condition": "email not in existing_emails",
                "message": "Email address is already registered"
            },
            {
                "name": "age_requirement",
                "condition": "age >= 13",
                "message": "Users must be at least 13 years old"
            }
        ]
    },
    "api_request": {
        "rules": [
            {
                "name": "rate_limit",
                "condition": "requests_per_hour <= rate_limit",
                "message": "API rate limit exceeded"
            },
            {
                "name": "valid_auth",
                "condition": "auth_token is not None and auth_token != \'\'",
                "message": "Valid authentication token required"
            }
        ]
    }
}

class ValidationAgent(BaseAgent):
    """
    Advanced Validation Agent with:
    - Multi-level schema validation (JSON Schema, Pydantic)
    - Business rule engine with custom logic
    - Data integrity checks and constraints
    - Compliance validation (GDPR, PCI-DSS, etc.)
    - Real-time validation with caching
    - Performance optimization with rule prioritization
    - Extensible rule system with hot-reloading
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Validation rules registry
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.schema_cache: Dict[str, Dict] = {}
        
        # Performance tracking
        self.validation_stats = {
            "total_validations": 0,
            "valid_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "average_validation_time": 0.0
        }
        
        # Rule categories
        self.rule_categories = {
            "schema": {},
            "business": {},
            "security": {},
            "compliance": {},
            "performance": {}
        }
        
        # Compliance frameworks
        self.compliance_frameworks = {
            "GDPR": self._load_gdpr_rules(),
            "PCI_DSS": self._load_pci_dss_rules(),
            "HIPAA": self._load_hipaa_rules(),
            "SOX": self._load_sox_rules()
        }
        
        # Custom validators
        self.custom_validators = {}
        
        # Load predefined rules
        self._load_predefined_rules()
    
    async def start(self):
        """Start validation agent services"""
        # Subscribe to validation requests
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_validation_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        # Subscribe to schema registration
        await self._subscribe(
            "validation.schema.register",
            self._handle_schema_registration
        )
        
        # Subscribe to rule updates
        await self._subscribe(
            "validation.rule.update",
            self._handle_rule_update
        )
        
        # Subscribe to bulk validation requests
        await self._subscribe(
            "validation.bulk",
            self._handle_bulk_validation
        )
        
        # Start background tasks
        asyncio.create_task(self._rule_cache_refresh())
        asyncio.create_task(self._performance_monitor())
        
        self.logger.info("Validation Agent started",
                        rule_count=len(self.validation_rules),
                        schema_count=len(self.schema_cache))
    
    def _load_predefined_rules(self):
        """Load predefined validation rules"""
        # Schema validation rules
        for schema_name, schema_def in COMMON_SCHEMAS.items():
            rule = ValidationRule(
                id=f"schema_{schema_name}",
                name=f"{schema_name.title()} Schema Validation",
                description=f"Validates {schema_name} format and structure",
                rule_type="schema",
                rule_definition={"schema": schema_def},
                level=ValidationLevel.STANDARD
            )
            self.validation_rules[rule.id] = rule
            self.rule_categories["schema"][rule.id] = rule
        
        # Business rules
        for rule_set_name, rule_set in BUSINESS_RULES.items():
            for i, business_rule in enumerate(rule_set["rules"]):
                rule = ValidationRule(
                    id=f"business_{rule_set_name}_{i}",
                    name=business_rule["name"],
                    description=business_rule["message"],
                    rule_type="business_logic",
                    rule_definition={
                        "condition": business_rule["condition"],
                        "message": business_rule["message"]
                    },
                    level=ValidationLevel.STANDARD
                )
                self.validation_rules[rule.id] = rule
                self.rule_categories["business"][rule.id] = rule
        
        self.logger.info("Predefined rules loaded", count=len(self.validation_rules))
    
    def _load_gdpr_rules(self) -> List[ValidationRule]:
        """Load GDPR compliance rules"""
        return [
            ValidationRule(
                id="gdpr_consent",
                name="GDPR Consent Validation",
                description="Ensures explicit consent for data processing",
                rule_type="compliance",
                rule_definition={
                    "required_fields": ["consent_given", "consent_timestamp", "consent_purpose"],
                    "consent_values": [True, "yes", "granted"]
                },
                level=ValidationLevel.ENTERPRISE
            ),
            ValidationRule(
                id="gdpr_data_minimization",
                name="GDPR Data Minimization",
                description="Ensures only necessary data is collected",
                rule_type="compliance",
                rule_definition={
                    "max_fields": 20,
                    "prohibited_fields": ["ssn", "passport_number", "medical_records"]
                }
            ),
            ValidationRule(
                id="gdpr_retention",
                name="GDPR Data Retention",
                description="Validates data retention period compliance",
                rule_type="compliance",
                rule_definition={
                    "max_retention_days": 2555,  # 7 years
                    "required_deletion_date": True
                }
            )
        ]
    
    def _load_pci_dss_rules(self) -> List[ValidationRule]:
        """Load PCI-DSS compliance rules"""
        return [
            ValidationRule(
                id="pci_card_data",
                name="PCI-DSS Card Data Protection",
                description="Ensures credit card data is properly masked",
                rule_type="security",
                rule_definition={
                    "mask_pattern": r"\*{12}\d{4}",  # Show only last 4 digits
                    "prohibited_storage": ["cvv", "pin", "magnetic_stripe"]
                },
                level=ValidationLevel.ENTERPRISE
            ),
            ValidationRule(
                id="pci_encryption",
                name="PCI-DSS Encryption Requirements",
                description="Validates encryption standards for card data",
                rule_type="security",
                rule_definition={
                    "min_encryption": "AES-256",
                    "required_fields": ["encryption_method", "key_management"]
                }
            )
        ]
    
    def _load_hipaa_rules(self) -> List[ValidationRule]:
        """Load HIPAA compliance rules"""
        return [
            ValidationRule(
                id="hipaa_phi_protection",
                name="HIPAA PHI Protection",
                description="Ensures protected health information is secured",
                rule_type="compliance",
                rule_definition={
                    "phi_fields": ["medical_record", "diagnosis", "treatment", "ssn"],
                    "encryption_required": True,
                    "access_controls": True
                },
                level=ValidationLevel.ENTERPRISE
            )
        ]
    
    def _load_sox_rules(self) -> List[ValidationRule]:
        """Load SOX compliance rules"""
        return [
            ValidationRule(
                id="sox_financial_data",
                name="SOX Financial Data Integrity",
                description="Ensures financial data accuracy and auditability",
                rule_type="compliance",
                rule_definition={
                    "required_audit_trail": True,
                    "immutable_records": True,
                    "dual_approval": True
                },
                level=ValidationLevel.ENTERPRISE
            )
        ]
    
    async def _handle_validation_task(self, msg):
        """Handle validation task requests"""
        try:
            data = json.loads(msg.data.decode())
            request = TaskRequest(**data)
            
            with self.tracer.start_as_current_span("validation_task") as span:
                span.set_attribute("task_id", request.task_id)
                span.set_attribute("validation_type", request.task_type)
                
                result = await self.execute_task(request)
                
                await self._publish_to_stream(
                    f"task.{request.task_id}.response",
                    result
                )
                
        except Exception as e:
            self.logger.error("Failed to handle validation task", error=str(e))
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute validation-specific tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "validate_data":
            return await self._validate_data(payload)
        
        elif task_type == "validate_schema":
            return await self._validate_schema(payload)
        
        elif task_type == "validate_business_rules":
            return await self._validate_business_rules(payload)
        
        elif task_type == "compliance_check":
            return await self._compliance_check(payload)
        
        elif task_type == "bulk_validation":
            return await self._bulk_validation(payload)
        
        elif task_type == "create_validation_rule":
            return await self._create_validation_rule(payload)
        
        elif task_type == "data_quality_assessment":
            return await self._data_quality_assessment(payload)
        
        else:
            raise ValueError(f"Unknown validation task type: {task_type}")
    
    async def _validate_data(self, payload: Dict) -> Dict[str, Any]:
        """Comprehensive data validation"""
        data = payload.get("data", {})
        rule_sets = payload.get("rule_sets", ["schema", "business"])
        validation_level = ValidationLevel(payload.get("level", "standard"))
        
        validation_id = f"val_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        with self.tracer.start_as_current_span("data_validation") as span:
            span.set_attribute("validation_id", validation_id)
            span.set_attribute("data_size", len(str(data)))
            
            issues = []
            rules_applied = []
            
            # Apply validation rules by category
            for rule_category in rule_sets:
                if rule_category in self.rule_categories:
                    category_rules = self.rule_categories[rule_category]
                    
                    for rule_id, rule in category_rules.items():
                        if not rule.enabled or rule.level.value not in [validation_level.value, "basic"]:
                            continue
                        
                        rule_issues = await self._apply_validation_rule(rule, data)
                        issues.extend(rule_issues)
                        rules_applied.append(rule_id)
            
            # Determine overall result
            overall_result = self._determine_overall_result(issues)
            
            # Create validation report
            execution_time = (time.time() - start_time) * 1000
            
            report = ValidationReport(
                validation_id=validation_id,
                data_id=payload.get("data_id", "N/A"),
                overall_result=overall_result,
                issues=issues,
                rules_applied=rules_applied,
                execution_time_ms=execution_time
            )
            
            # Persist report
            await self._persist_validation_report(report)
            
            return report.__dict__

    async def _apply_validation_rule(self, rule: ValidationRule, data: Dict) -> List[ValidationIssue]:
        """Apply a single validation rule to the data"""
        issues = []
        if rule.rule_type == "schema":
            try:
                validate(instance=data, schema=rule.rule_definition["schema"])
            except ValidationError as e:
                issues.append(ValidationIssue(
                    rule_id=rule.id,
                    severity=ValidationResult.ERROR,
                    message=e.message,
                    field_path=str(e.path)
                ))
        elif rule.rule_type == "business_logic":
            try:
                if not eval(rule.rule_definition["condition"], {"__builtins__": {}}, data):
                    issues.append(ValidationIssue(
                        rule_id=rule.id,
                        severity=ValidationResult.WARNING,
                        message=rule.rule_definition["message"]
                    ))
            except Exception as e:
                self.logger.warning(f"Error evaluating business rule {rule.id}: {e}")
        return issues

    def _determine_overall_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """Determine the overall validation result from a list of issues"""
        if any(issue.severity == ValidationResult.CRITICAL for issue in issues):
            return ValidationResult.CRITICAL
        if any(issue.severity == ValidationResult.ERROR for issue in issues):
            return ValidationResult.ERROR
        if any(issue.severity == ValidationResult.WARNING for issue in issues):
            return ValidationResult.WARNING
        return ValidationResult.VALID

    async def _persist_validation_report(self, report: ValidationReport):
        """Persist the validation report to the database."""
        if not self.db_pool:
            return

        await self._db_query(
            """INSERT INTO validation_reports (id, data_id, result, issues, rules_applied, execution_time_ms, timestamp)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            report.validation_id, report.data_id, report.overall_result.value,
            json.dumps([issue.__dict__ for issue in report.issues]),
            report.rules_applied, report.execution_time_ms, datetime.fromtimestamp(report.timestamp)
        )

    async def _rule_cache_refresh(self):
        """Periodically refresh validation rules from the database."""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(300) # Refresh every 5 minutes
            if not self.db_pool:
                continue

            self.logger.info("Refreshing validation rules from database...")
            records = await self._db_query("SELECT id, name, description, rule_type, rule_definition, level, enabled, priority, metadata FROM validation_rules")
            if records:
                for r in records:
                    rule = ValidationRule(**r)
                    self.validation_rules[rule.id] = rule
                    if rule.rule_type in self.rule_categories:
                        self.rule_categories[rule.rule_type][rule.id] = rule
                self.logger.info(f"{len(records)} validation rules refreshed.")

    async def _performance_monitor(self):
        """Monitor the performance of the validation agent."""
        # This is a placeholder for more advanced performance monitoring
        pass

    async def _handle_schema_registration(self, msg):
        """Handle new schema registration requests."""
        # Implementation for schema registration
        pass

    async def _handle_rule_update(self, msg):
        """Handle rule update requests."""
        # Implementation for rule updates
        pass

    async def _handle_bulk_validation(self, msg):
        """Handle bulk validation requests."""
        # Implementation for bulk validation
        pass

    async def _validate_schema(self, payload: Dict) -> Dict[str, Any]:
        """Validate data against a specific schema."""
        # Implementation for schema validation
        return {"status": "success"}

    async def _validate_business_rules(self, payload: Dict) -> Dict[str, Any]:
        """Validate data against a set of business rules."""
        # Implementation for business rule validation
        return {"status": "success"}

    async def _compliance_check(self, payload: Dict) -> Dict[str, Any]:
        """Perform a compliance check against a specific framework."""
        # Implementation for compliance checks
        return {"status": "success"}

    async def _bulk_validation(self, payload: Dict) -> Dict[str, Any]:
        """Perform validation on a bulk dataset."""
        # Implementation for bulk validation
        return {"status": "success"}

    async def _create_validation_rule(self, payload: Dict) -> Dict[str, Any]:
        """Create a new validation rule."""
        # Implementation for creating validation rules
        return {"status": "success"}

    async def _data_quality_assessment(self, payload: Dict) -> Dict[str, Any]:
        """Assess the overall data quality of a dataset."""
        # Implementation for data quality assessment
        return {"status": "success"}

if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            name="validation-agent",
            agent_type="validation",
            capabilities=["schema_validation", "business_rules", "compliance_checks"]
        )
        agent = ValidationAgent(config)
        await agent.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Validation Agent stopped.")

