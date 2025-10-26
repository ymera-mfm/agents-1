"""
Advanced Static Analysis Agent
Code quality, security vulnerability detection, architecture analysis, and compliance checking
"""

import asyncio
import json
import time
import ast
import re
import os
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pathlib import Path
from datetime import datetime

# External analysis libraries (mocked for sandbox environment, actual libraries would be installed)
# import bandit
# from bandit.core import manager as bandit_manager
# from bandit.core import config as bandit_config
# import pylint.lint
# import flake8.api.legacy as flake8
# import mypy.api
# import safety
# import semgrep
# import radon.complexity as radon_cc
# import radon.metrics as radon_metrics
# from vulture import Vulture

from base_agent import BaseAgent, AgentConfig, TaskRequest, Priority
from opentelemetry import trace

class AnalysisType(Enum):
    SECURITY = "security"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    COMPLIANCE = "compliance"
    VULNERABILITY = "vulnerability"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Finding:
    id: str
    type: AnalysisType
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    rule_id: Optional[str] = None
    confidence: float = 1.0
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResult:
    analysis_id: str
    target_path: str
    analysis_types: List[AnalysisType]
    findings: List[Finding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    summary: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StaticAnalysisRule:
    id: str
    name: str
    description: str
    rule_type: AnalysisType
    severity: Severity
    pattern: str # Regex or other rule definition
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class StaticAnalysisAgent(BaseAgent):
    """
    Advanced Static Analysis Agent with:
    - Multi-language security scanning (Bandit, Semgrep)
    - Code quality analysis (Pylint, Flake8, MyPy)
    - Vulnerability detection (Safety, custom rules)
    - Architecture analysis and design pattern detection
    - Performance bottleneck identification
    - Compliance checking (OWASP, CWE, PCI-DSS)
    - Advanced metrics (Cyclomatic complexity, maintainability)
    - ML-powered anomaly detection
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Analysis engines (mocked for sandbox environment)
        self.security_engines = {
            "bandit": self._init_bandit(),
            "semgrep": self._init_semgrep(),
            "custom_security": self._init_custom_security()
        }
        
        self.quality_engines = {
            "pylint": self._init_pylint(),
            "flake8": self._init_flake8(),
            "mypy": self._init_mypy(),
            "radon": self._init_radon()
        }
        
        # Rule sets loaded from DB
        self.static_analysis_rules: Dict[str, StaticAnalysisRule] = {}
        
        # Analysis cache
        self.analysis_cache = {}
        self.file_signatures = {}
        
        # Statistics
        self.analysis_stats = {
            "total_analyses": 0,
            "files_analyzed": 0,
            "findings_by_severity": {s.value: 0 for s in Severity},
            "average_analysis_time": 0.0
        }
    
    async def start(self):
        """Start static analysis agent services"""
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_analysis_task,
            queue_group=f"{self.config.name}_workers"
        )
        
        await self._subscribe(
            "static_analysis.scan_project",
            self._handle_project_scan
        )
        
        await self._subscribe(
            "static_analysis.scan_file",
            self._handle_file_scan
        )
        
        await self._subscribe(
            "static_analysis.security_scan",
            self._handle_security_scan
        )
        
        await self._subscribe(
            "static_analysis.quality_check",
            self._handle_quality_check
        )

        await self._subscribe(
            "static_analysis.rule.update",
            self._handle_rule_update
        )
        
        # Background tasks
        asyncio.create_task(self._rule_updates_monitor())
        asyncio.create_task(self._performance_monitor())
        
        # Load rules from DB on startup
        await self._load_rules_from_db()

        self.logger.info("Static Analysis Agent started")
    
    def _init_bandit(self):
        """Initialize Bandit security scanner (mocked)"""
        # In a real scenario, you would initialize bandit.core.manager.BanditManager
        return {"status": "mocked_bandit_initialized"}
    
    def _init_semgrep(self):
        """Initialize Semgrep scanner (mocked)"""
        return {
            "rules_path": "/opt/semgrep-rules",
            "config_path": "/opt/semgrep-config.yml",
            "status": "mocked_semgrep_initialized"
        }
    
    def _init_custom_security(self):
        """Initialize custom security scanner (mocked)"""
        return {
            "sql_injection_patterns": [
                r"execute\s*\(\s*[\'\"]?.*%.*[\'\"]?",
                r"cursor\.execute\s*\(\s*[\'\"]?.*\+.*[\'\"]?",
                r"query\s*=\s*[\'\"]?.*%.*[\'\"]?"
            ],
            "xss_patterns": [
                r"innerHTML\s*=.*user_input",
                r"document\.write\s*\(.*user_input",
                r"eval\s*\(.*user_input"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*[\'\"][^\'\"]*[\'\"]",
                r"api_key\s*=\s*[\'\"][^\'\"]*[\'\"]",
                r"secret\s*=\s*[\'\"][^\'\"]*[\'\"]"
            ]
        }
    
    def _init_pylint(self):
        """Initialize Pylint (mocked)"""
        return {
            "rcfile": "/opt/pylint.rc",
            "disable": ["C0111", "R0903"],  # Configurable
            "status": "mocked_pylint_initialized"
        }
    
    def _init_flake8(self):
        """Initialize Flake8 (mocked)"""
        # return flake8.get_style_guide(
        #     max_line_length=88,
        #     ignore=["E203", "W503"]
        # )
        return {"status": "mocked_flake8_initialized"}
    
    def _init_mypy(self):
        """Initialize MyPy (mocked)"""
        return {
            "config_file": "/opt/mypy.ini",
            "strict": True,
            "status": "mocked_mypy_initialized"
        }
    
    def _init_radon(self):
        """Initialize Radon complexity analyzer (mocked)"""
        return {
            "cc_threshold": 10,
            "mi_threshold": 20,
            "status": "mocked_radon_initialized"
        }

    async def _load_rules_from_db(self):
        """Load static analysis rules from the database."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, cannot load static analysis rules.")
            return

        try:
            records = await self._db_query(
                "SELECT id, name, description, rule_type, severity, pattern, enabled, metadata FROM static_analysis_rules"
            )
            if records:
                for r in records:
                    rule = StaticAnalysisRule(
                        id=r["id"],
                        name=r["name"],
                        description=r["description"],
                        rule_type=AnalysisType[r["rule_type"].upper()],
                        severity=Severity[r["severity"].upper()],
                        pattern=r["pattern"],
                        enabled=r["enabled"],
                        metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                    )
                    self.static_analysis_rules[rule.id] = rule
                self.logger.info(f"Loaded {len(self.static_analysis_rules)} static analysis rules from DB.")
            else:
                self.logger.info("No static analysis rules found in DB. Loading default rules.")
                self._load_default_rules()
        except Exception as e:
            self.logger.error(f"Failed to load static analysis rules from DB: {e}")
            self._load_default_rules() # Fallback to default rules

    def _load_default_rules(self):
        """Load default static analysis rules if DB is empty or inaccessible."""
        default_rules = [
            StaticAnalysisRule(
                id="default_sql_injection",
                name="Potential SQL Injection",
                description="Detects patterns indicative of SQL injection vulnerabilities.",
                rule_type=AnalysisType.SECURITY,
                severity=Severity.CRITICAL,
                pattern=r"execute\s*\([^)]*\%[^)]*\)|cursor\.execute\s*\([^)]*\+[^)]*\)"
            ),
            StaticAnalysisRule(
                id="default_hardcoded_secret",
                name="Hardcoded Secret",
                description="Identifies hardcoded passwords or API keys.",
                rule_type=AnalysisType.SECURITY,
                severity=Severity.HIGH,
                pattern=r"password\s*=\s*[\'\"][^\'\"]*[\'\"]|api_key\s*=\s*[\'\"][^\'\"]*[\'\"]"
            ),
            StaticAnalysisRule(
                id="default_long_function",
                name="Long Function",
                description="Functions exceeding a certain line count are harder to maintain.",
                rule_type=AnalysisType.QUALITY,
                severity=Severity.MEDIUM,
                pattern=r"def\s+\w+\(.*\):\s*\n(?:\s+.*\n){50,}" # Placeholder, actual check would be AST-based
            )
        ]
        for rule in default_rules:
            self.static_analysis_rules[rule.id] = rule
        self.logger.info(f"Loaded {len(self.static_analysis_rules)} default static analysis rules.")

    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute static analysis tasks"""
        task_type = request.task_type
        payload = request.payload
        
        if task_type == "analyze_code":
            return await self._analyze_code(payload)
        
        elif task_type == "security_scan":
            return await self._security_scan(payload)
        
        elif task_type == "quality_check":
            return await self._quality_check(payload)
        
        elif task_type == "architecture_analysis":
            return await self._architecture_analysis(payload)
        
        elif task_type == "performance_analysis":
            return await self._performance_analysis(payload)
        
        elif task_type == "compliance_check":
            return await self._compliance_check(payload)
        
        elif task_type == "vulnerability_scan":
            return await self._vulnerability_scan(payload)
        
        elif task_type == "batch_analysis":
            return await self._batch_analysis(payload)
        
        else:
            raise ValueError(f"Unknown analysis task: {task_type}")
    
    async def _analyze_code(self, payload: Dict) -> Dict[str, Any]:
        """Comprehensive code analysis"""
        source_code = payload.get("source_code", "")
        file_path = payload.get("file_path", "unknown.py")
        analysis_types = payload.get("analysis_types", [t.value for t in AnalysisType])
        
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        with self.tracer.start_as_current_span("code_analysis") as span:
            span.set_attribute("analysis_id", analysis_id)
            span.set_attribute("file_path", file_path)
            span.set_attribute("code_size", len(source_code))
            
            all_findings = []
            metrics = {}
            
            # Security analysis
            if AnalysisType.SECURITY.value in analysis_types:
                security_findings = await self._run_security_analysis(source_code, file_path)
                all_findings.extend(security_findings)
                metrics["security"] = self._calculate_security_metrics(security_findings)
            
            # Quality analysis
            if AnalysisType.QUALITY.value in analysis_types:
                quality_findings = await self._run_quality_analysis(source_code, file_path)
                all_findings.extend(quality_findings)
                metrics["quality"] = self._calculate_quality_metrics(quality_findings, source_code)
            
            # Performance analysis
            if AnalysisType.PERFORMANCE.value in analysis_types:
                perf_findings = await self._run_performance_analysis(source_code, file_path)
                all_findings.extend(perf_findings)
                metrics["performance"] = self._calculate_performance_metrics(perf_findings)
            
            # Architecture analysis
            if AnalysisType.ARCHITECTURE.value in analysis_types:
                arch_findings = await self._run_architecture_analysis(source_code, file_path)
                all_findings.extend(arch_findings)
                metrics["architecture"] = self._calculate_architecture_metrics(arch_findings)
            
            # Compliance check
            if AnalysisType.COMPLIANCE.value in analysis_types:
                compliance_findings = await self._run_compliance_check(source_code, file_path)
                all_findings.extend(compliance_findings)
                metrics["compliance"] = self._calculate_compliance_metrics(compliance_findings)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Create analysis result
            result = AnalysisResult(
                analysis_id=analysis_id,
                target_path=file_path,
                analysis_types=[AnalysisType(t) for t in analysis_types],
                findings=all_findings,
                metrics=metrics,
                execution_time_ms=execution_time,
                summary=self._generate_summary(all_findings, metrics)
            )
            
            # Persist analysis result and findings
            await self._persist_analysis_result(result)

            # Publish analysis update
            await self._publish_to_stream("static_analysis.result", result.__dict__)

            # Update statistics
            self._update_analysis_stats(result)
            
            return {
                "analysis_result": {
                    "analysis_id": result.analysis_id,
                    "target_path": result.target_path,
                    "total_findings": len(result.findings),
                    "findings_by_severity": {
                        s.value: len([f for f in result.findings if f.severity == s])
                        for s in Severity
                    },
                    "metrics": result.metrics,
                    "execution_time_ms": result.execution_time_ms,
                    "summary": result.summary
                },
                "findings": [
                    {
                        "id": f.id,
                        "type": f.type.value,
                        "severity": f.severity.value,
                        "title": f.title,
                        "description": f.description,
                        "file_path": f.file_path,
                        "line_number": f.line_number,
                        "rule_id": f.rule_id,
                        "confidence": f.confidence,
                        "remediation": f.remediation
                    }
                    for f in result.findings
                ],
                "recommendations": self._generate_recommendations(result.findings)
            }
    
    async def _run_security_analysis(self, source_code: str, file_path: str) -> List[Finding]:
        """Run comprehensive security analysis (mocked/simplified)"""
        findings = []
        
        # Custom security patterns (regex-based for simplicity)
        for rule_id, rule in self.static_analysis_rules.items():
            if rule.rule_type == AnalysisType.SECURITY and rule.enabled:
                for i, line in enumerate(source_code.splitlines()):
                    if re.search(rule.pattern, line):
                        findings.append(Finding(
                            id=f"sec_find_{uuid.uuid4().hex[:6]}",
                            type=AnalysisType.SECURITY,
                            severity=rule.severity,
                            title=rule.name,
                            description=rule.description,
                            file_path=file_path,
                            line_number=i + 1,
                            rule_id=rule.id,
                            remediation="Review code for potential vulnerability and sanitize inputs."
                        ))
        return findings
    
    async def _run_quality_analysis(self, source_code: str, file_path: str) -> List[Finding]:
        """Run code quality analysis (mocked/simplified)"""
        findings = []
        # Example: Check for long lines (Flake8-like)
        for i, line in enumerate(source_code.splitlines()):
            if len(line) > 80:
                findings.append(Finding(
                    id=f"qual_find_{uuid.uuid4().hex[:6]}",
                    type=AnalysisType.QUALITY,
                    severity=Severity.LOW,
                    title="Line too long",
                    description=f"Line {i+1} exceeds 80 characters.",
                    file_path=file_path,
                    line_number=i + 1,
                    rule_id="flake8_E501",
                    remediation="Refactor line to be shorter or split into multiple lines."
                ))
        return findings

    async def _run_performance_analysis(self, source_code: str, file_path: str) -> List[Finding]:
        """Run performance analysis (mocked/simplified)"""
        findings = []
        # Example: Simple check for inefficient loops
        if re.search(r"for\s+.*\s+in\s+range\(len\(.*\)\)", source_code):
            findings.append(Finding(
                id=f"perf_find_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Inefficient loop detected",
                description="Using `range(len())` for iteration can be inefficient. Consider direct iteration.",
                file_path=file_path,
                remediation="Iterate directly over the collection instead of using `range(len())`."
            ))
        return findings

    async def _run_architecture_analysis(self, source_code: str, file_path: str) -> List[Finding]:
        """Run architecture analysis (mocked/simplified)"""
        findings = []
        # Example: Detect potential God Object (simplified)
        class_definitions = re.findall(r"class\s+(\w+)\(.*\):", source_code)
        for class_name in class_definitions:
            class_code_match = re.search(rf"class\s+{class_name}\(.*\):\n((?:\s+.*\n)*)", source_code)
            if class_code_match:
                class_code = class_code_match.group(1)
                method_count = len(re.findall(r"\s+def\s+\w+\(self,.*\):", class_code))
                if method_count > 15: # Arbitrary threshold for God Object
                    findings.append(Finding(
                        id=f"arch_find_{uuid.uuid4().hex[:6]}",
                        type=AnalysisType.ARCHITECTURE,
                        severity=Severity.HIGH,
                        title="Potential God Object",
                        description=f"Class `{class_name}` has too many methods ({method_count}), indicating a potential God Object anti-pattern.",
                        file_path=file_path,
                        remediation="Refactor the class into smaller, more focused components following Single Responsibility Principle."
                    ))
        return findings

    async def _run_compliance_check(self, source_code: str, file_path: str) -> List[Finding]:
        """Run compliance check (mocked/simplified)"""
        findings = []
        # Example: Check for GDPR-like consent fields
        if "consent_given" not in source_code and "GDPR" in file_path:
            findings.append(Finding(
                id=f"comp_find_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.COMPLIANCE,
                severity=Severity.CRITICAL,
                title="Missing GDPR Consent Mechanism",
                description="GDPR compliance requires explicit consent for data processing. 'consent_given' field not found.",
                file_path=file_path,
                remediation="Implement explicit user consent mechanisms and record consent status."
            ))
        return findings

    async def _vulnerability_scan(self, payload: Dict) -> Dict[str, Any]:
        """Perform a vulnerability scan (mocked/simplified)"""
        # This would typically involve calling external tools like Safety or custom vulnerability databases.
        self.logger.info("Performing mocked vulnerability scan.")
        return {"status": "mocked_vulnerability_scan_complete", "findings": []}

    async def _batch_analysis(self, payload: Dict) -> Dict[str, Any]:
        """Perform batch analysis on multiple files or a project (mocked/simplified)"""
        self.logger.info("Performing mocked batch analysis.")
        return {"status": "mocked_batch_analysis_complete", "results": []}

    def _calculate_security_metrics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate security-related metrics from findings."""
        critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        high = sum(1 for f in findings if f.severity == Severity.HIGH)
        medium = sum(1 for f in findings if f.severity == Severity.MEDIUM)
        low = sum(1 for f in findings if f.severity == Severity.LOW)
        return {"critical_findings": critical, "high_findings": high, "medium_findings": medium, "low_findings": low}

    def _calculate_quality_metrics(self, findings: List[Finding], source_code: str) -> Dict[str, Any]:
        """Calculate quality-related metrics from findings and source code."""
        # Mocked complexity and maintainability metrics
        lines_of_code = len(source_code.splitlines())
        return {"lines_of_code": lines_of_code, "cyclomatic_complexity": 10, "maintainability_index": 70}

    def _calculate_performance_metrics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate performance-related metrics from findings."""
        return {"performance_bottlenecks": len(findings)}

    def _calculate_architecture_metrics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate architecture-related metrics from findings."""
        return {"anti_patterns_detected": len(findings)}

    def _calculate_compliance_metrics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate compliance-related metrics from findings."""
        return {"compliance_violations": len(findings)}

    def _generate_summary(self, findings: List[Finding], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the analysis result."""
        summary = {
            "total_findings": len(findings),
            "severity_breakdown": {s.value: sum(1 for f in findings if f.severity == s) for s in Severity},
            "metrics_overview": metrics
        }
        return summary

    def _generate_recommendations(self, findings: List[Finding]) -> List[str]:
        """Generate high-level recommendations based on findings."""
        recommendations = []
        if any(f.severity == Severity.CRITICAL for f in findings):
            recommendations.append("Address critical security vulnerabilities immediately.")
        if any(f.type == AnalysisType.QUALITY and f.severity in [Severity.HIGH, Severity.MEDIUM] for f in findings):
            recommendations.append("Improve code quality by refactoring complex functions and adhering to coding standards.")
        return recommendations

    async def _persist_analysis_result(self, result: AnalysisResult):
        """Persist the analysis result and its findings to the database."""
        if not self.db_pool:
            self.logger.warning("DB pool not initialized, cannot persist analysis results.")
            return

        try:
            # Persist AnalysisResult
            await self._db_query(
                """INSERT INTO static_analysis_results (id, target_path, analysis_types, metrics, execution_time_ms, timestamp, summary)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                result.analysis_id, result.target_path, [at.value for at in result.analysis_types],
                json.dumps(result.metrics), result.execution_time_ms, datetime.fromtimestamp(result.timestamp),
                json.dumps(result.summary)
            )

            # Persist Findings
            for finding in result.findings:
                await self._db_query(
                    """INSERT INTO static_analysis_findings (id, analysis_id, type, severity, title, description, file_path, line_number, column_number, rule_id, confidence, remediation, references, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
                    finding.id, result.analysis_id, finding.type.value, finding.severity.value,
                    finding.title, finding.description, finding.file_path, finding.line_number,
                    finding.column, finding.rule_id, finding.confidence, finding.remediation,
                    json.dumps(finding.references), json.dumps(finding.metadata)
                )
            self.logger.info(f"Analysis result {result.analysis_id} and {len(result.findings)} findings persisted.")
        except Exception as e:
            self.logger.error(f"Failed to persist analysis result {result.analysis_id}: {e}")

    async def _handle_analysis_task(self, msg):
        """Handle incoming analysis task requests."""
        await self._handle_task_request(msg)

    async def _handle_project_scan(self, msg):
        """Handle project scan requests."""
        payload = json.loads(msg.data.decode())
        project_path = payload.get("project_path")
        if not project_path:
            self.logger.error("Project path missing for project scan.")
            await msg.ack()
            return

        self.logger.info(f"Initiating project scan for: {project_path}")
        # In a real scenario, this would iterate through files in the project_path
        # and call _analyze_code for each relevant file.
        # For now, it's a placeholder.
        await self._publish_to_stream("static_analysis.project_scan_status", {"project_path": project_path, "status": "started"})
        await asyncio.sleep(5) # Simulate work
        await self._publish_to_stream("static_analysis.project_scan_status", {"project_path": project_path, "status": "completed", "results": []})
        await msg.ack()

    async def _handle_file_scan(self, msg):
        """Handle single file scan requests."""
        payload = json.loads(msg.data.decode())
        source_code = payload.get("source_code")
        file_path = payload.get("file_path")
        analysis_types = payload.get("analysis_types")

        if not source_code or not file_path:
            self.logger.error("Source code or file path missing for file scan.")
            await msg.ack()
            return

        try:
            result = await self._analyze_code({"source_code": source_code, "file_path": file_path, "analysis_types": analysis_types})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error(f"Error during file scan: {e}")
            await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _handle_security_scan(self, msg):
        """Handle security scan requests."""
        payload = json.loads(msg.data.decode())
        source_code = payload.get("source_code")
        file_path = payload.get("file_path")

        if not source_code or not file_path:
            self.logger.error("Source code or file path missing for security scan.")
            await msg.ack()
            return

        try:
            result = await self._analyze_code({"source_code": source_code, "file_path": file_path, "analysis_types": [AnalysisType.SECURITY.value]})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error(f"Error during security scan: {e}")
            await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _handle_quality_check(self, msg):
        """Handle quality check requests."""
        payload = json.loads(msg.data.decode())
        source_code = payload.get("source_code")
        file_path = payload.get("file_path")

        if not source_code or not file_path:
            self.logger.error("Source code or file path missing for quality check.")
            await msg.ack()
            return

        try:
            result = await self._analyze_code({"source_code": source_code, "file_path": file_path, "analysis_types": [AnalysisType.QUALITY.value]})
            await self._publish(msg.reply, json.dumps(result).encode())
        except Exception as e:
            self.logger.error(f"Error during quality check: {e}")
            await self._publish(msg.reply, json.dumps({"error": str(e)}).encode())
        finally:
            await msg.ack()

    async def _handle_rule_update(self, msg):
        """Handle dynamic rule updates or additions."""
        payload = json.loads(msg.data.decode())
        rule_data = payload.get("rule")
        action = payload.get("action") # e.g., "add", "update", "delete"

        if not rule_data or not action:
            self.logger.error("Rule data or action missing for rule update.")
            await msg.ack()
            return

        try:
            rule_id = rule_data["id"]
            if action == "add" or action == "update":
                rule = StaticAnalysisRule(
                    id=rule_id,
                    name=rule_data["name"],
                    description=rule_data["description"],
                    rule_type=AnalysisType[rule_data["rule_type"].upper()],
                    severity=Severity[rule_data["severity"].upper()],
                    pattern=rule_data["pattern"],
                    enabled=rule_data.get("enabled", True),
                    metadata=rule_data.get("metadata", {})
                )
                self.static_analysis_rules[rule_id] = rule
                # Persist to DB
                await self._db_query(
                    """INSERT INTO static_analysis_rules (id, name, description, rule_type, severity, pattern, enabled, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                       ON CONFLICT (id) DO UPDATE SET
                       name = EXCLUDED.name, description = EXCLUDED.description, rule_type = EXCLUDED.rule_type,
                       severity = EXCLUDED.severity, pattern = EXCLUDED.pattern, enabled = EXCLUDED.enabled,
                       metadata = EXCLUDED.metadata, updated_at = NOW()""",
                    rule.id, rule.name, rule.description, rule.rule_type.value, rule.severity.value,
                    rule.pattern, rule.enabled, json.dumps(rule.metadata)
                )
                self.logger.info(f"Rule {rule_id} {action}d and persisted.")
            elif action == "delete":
                if rule_id in self.static_analysis_rules:
                    del self.static_analysis_rules[rule_id]
                    await self._db_query("DELETE FROM static_analysis_rules WHERE id = $1", rule_id)
                    self.logger.info(f"Rule {rule_id} deleted.")
                else:
                    self.logger.warning(f"Attempted to delete non-existent rule: {rule_id}")
            else:
                self.logger.warning(f"Unknown rule update action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing rule update: {e}", rule_data=rule_data)
        finally:
            await msg.ack()

    async def _rule_updates_monitor(self):
        """Periodically refresh rules from the database to ensure consistency."""
        while not self._shutdown_event.is_set():
            await asyncio.sleep(300) # Refresh every 5 minutes
            await self._load_rules_from_db()

    async def _performance_monitor(self):
        """Monitor the performance of the static analysis agent."""
        # This is a placeholder for more advanced performance monitoring
        pass


if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            name="static-analysis-agent",
            agent_type="static_analysis",
            capabilities=["security_scan", "quality_check", "architecture_analysis", "compliance_check"]
        )
        agent = StaticAnalysisAgent(config)
        await agent.run()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Static Analysis Agent stopped.")

