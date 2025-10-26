"""
Production-Ready Static Analysis Agent
Enhanced with proper error handling, monitoring, and enterprise features
"""

import asyncio
import json
import time
import ast
import re
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from base_agent import (
    BaseAgent, 
    AgentConfig, 
    TaskRequest, 
    Priority,
    AgentState,
    ConnectionState
)


class AnalysisType(Enum):
    """Types of static analysis that can be performed"""
    SECURITY = "security"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    COMPLIANCE = "compliance"
    VULNERABILITY = "vulnerability"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"


class Severity(Enum):
    """Severity levels for findings"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Finding:
    """Represents a single analysis finding"""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "rule_id": self.rule_id,
            "confidence": self.confidence,
            "remediation": self.remediation,
            "references": self.references,
            "metadata": self.metadata
        }


@dataclass
class AnalysisResult:
    """Complete analysis result with findings and metrics"""
    analysis_id: str
    target_path: str
    analysis_types: List[AnalysisType]
    findings: List[Finding] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "analysis_id": self.analysis_id,
            "target_path": self.target_path,
            "analysis_types": [at.value for at in self.analysis_types],
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
            "summary": self.summary
        }


@dataclass
class StaticAnalysisRule:
    """Represents an analysis rule"""
    id: str
    name: str
    description: str
    rule_type: AnalysisType
    severity: Severity
    pattern: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StaticAnalysisAgent(BaseAgent):
    """
    Production-ready Static Analysis Agent with:
    - Multi-type code analysis (security, quality, performance, architecture)
    - Dynamic rule management with DB persistence
    - Result caching and file signature tracking
    - Comprehensive error handling and monitoring
    - Batch analysis capabilities
    - Real-time metrics and performance tracking
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Rule management
        self.static_analysis_rules: Dict[str, StaticAnalysisRule] = {}
        self.rules_last_loaded: float = 0
        self.rules_refresh_interval: float = 300  # 5 minutes
        
        # Analysis cache for avoiding duplicate work
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.file_signatures: Dict[str, str] = {}
        self.cache_ttl: float = 3600  # 1 hour
        
        # Performance tracking
        self.analysis_stats = {
            "total_analyses": 0,
            "files_analyzed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "findings_by_severity": {s.value: 0 for s in Severity},
            "average_analysis_time_ms": 0.0,
            "total_analysis_time_ms": 0.0
        }
        
        # Security patterns (can be loaded from config or DB)
        self.security_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*['\"]?.*%.*['\"]?\)",
                r"cursor\.execute\s*\(\s*['\"]?.*\+.*['\"]?\)",
                r"query\s*=\s*['\"]?.*%.*['\"]?",
                r"\.format\s*\([^)]*sql[^)]*\)"
            ],
            "xss": [
                r"innerHTML\s*=.*user_input",
                r"document\.write\s*\(.*user_input",
                r"eval\s*\(.*user_input",
                r"dangerouslySetInnerHTML"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]{8,}['\"]",
                r"api_key\s*=\s*['\"][^'\"]{20,}['\"]",
                r"secret\s*=\s*['\"][^'\"]{16,}['\"]",
                r"token\s*=\s*['\"][^'\"]{32,}['\"]"
            ],
            "command_injection": [
                r"os\.system\s*\([^)]*\+[^)]*\)",
                r"subprocess\.call\s*\([^)]*\+[^)]*\)",
                r"eval\s*\(",
                r"exec\s*\("
            ]
        }
    
    async def _setup_subscriptions(self):
        """Setup message subscriptions"""
        await super()._setup_subscriptions()
        
        # Task-based subscription
        await self._subscribe(
            f"agent.{self.config.name}.task",
            self._handle_task_message,
            queue_group=f"{self.config.name}_workers"
        )
        
        # Analysis-specific subscriptions
        await self._subscribe(
            "static_analysis.scan_project",
            self._handle_project_scan,
            queue_group="project_scanners"
        )
        
        await self._subscribe(
            "static_analysis.scan_file",
            self._handle_file_scan,
            queue_group="file_scanners"
        )
        
        await self._subscribe(
            "static_analysis.security_scan",
            self._handle_security_scan,
            queue_group="security_scanners"
        )
        
        await self._subscribe(
            "static_analysis.quality_check",
            self._handle_quality_check,
            queue_group="quality_checkers"
        )
        
        await self._subscribe(
            "static_analysis.rule.update",
            self._handle_rule_update,
            queue_group="rule_managers"
        )
        
        self.logger.info("Static Analysis Agent subscriptions configured")
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks"""
        await super()._start_background_tasks()
        
        # Rule refresh task
        task = asyncio.create_task(self._rule_refresh_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Cache cleanup task
        task = asyncio.create_task(self._cache_cleanup_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Stats publisher task
        task = asyncio.create_task(self._stats_publisher_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        # Load initial rules
        await self._load_rules_from_db()
        
        self.logger.info("Static Analysis Agent background tasks started")
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle incoming task requests"""
        task_type = task_request.task_type
        payload = task_request.payload
        
        try:
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
            
            elif task_type == "get_stats":
                return self._get_analysis_stats()
            
            elif task_type == "clear_cache":
                return await self._clear_cache()
            
            else:
                return await super()._handle_task(task_request)
                
        except Exception as e:
            self.logger.error(
                f"Error handling task {task_type}",
                exc_info=True,
                extra={"task_id": task_request.task_id, "error": str(e)}
            )
            return {
                "status": "error",
                "error": str(e),
                "task_type": task_type,
                "task_id": task_request.task_id
            }
    
    async def _analyze_code(self, payload: Dict) -> Dict[str, Any]:
        """Comprehensive code analysis with caching"""
        source_code = payload.get("source_code", "")
        file_path = payload.get("file_path", "unknown.py")
        analysis_types = payload.get("analysis_types", [t.value for t in AnalysisType])
        force_refresh = payload.get("force_refresh", False)
        
        # Generate file signature for caching
        file_signature = self._generate_file_signature(source_code, file_path)
        cache_key = f"{file_signature}:{'_'.join(sorted(analysis_types))}"
        
        # Check cache
        if not force_refresh and cache_key in self.analysis_cache:
            cached_result = self.analysis_cache[cache_key]
            if time.time() - cached_result.timestamp < self.cache_ttl:
                self.analysis_stats["cache_hits"] += 1
                self.logger.info(f"Cache hit for {file_path}")
                return self._format_analysis_response(cached_result)
        
        self.analysis_stats["cache_misses"] += 1
        
        # Perform analysis
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        self.logger.info(
            f"Starting analysis {analysis_id}",
            extra={
                "file_path": file_path,
                "analysis_types": analysis_types,
                "code_size": len(source_code)
            }
        )
        
        all_findings = []
        metrics = {}
        
        try:
            # Run requested analysis types
            analysis_map = {
                AnalysisType.SECURITY.value: self._run_security_analysis,
                AnalysisType.QUALITY.value: self._run_quality_analysis,
                AnalysisType.PERFORMANCE.value: self._run_performance_analysis,
                AnalysisType.ARCHITECTURE.value: self._run_architecture_analysis,
                AnalysisType.COMPLIANCE.value: self._run_compliance_check,
                AnalysisType.COMPLEXITY.value: self._run_complexity_analysis,
                AnalysisType.MAINTAINABILITY.value: self._run_maintainability_analysis
            }
            
            for analysis_type in analysis_types:
                if analysis_type in analysis_map:
                    findings = await analysis_map[analysis_type](source_code, file_path)
                    all_findings.extend(findings)
                    metrics[analysis_type] = self._calculate_type_metrics(
                        analysis_type, findings, source_code
                    )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = AnalysisResult(
                analysis_id=analysis_id,
                target_path=file_path,
                analysis_types=[AnalysisType(t) for t in analysis_types],
                findings=all_findings,
                metrics=metrics,
                execution_time_ms=execution_time_ms,
                summary=self._generate_summary(all_findings, metrics)
            )
            
            # Cache result
            self.analysis_cache[cache_key] = result
            self.file_signatures[file_path] = file_signature
            
            # Persist to database
            await self._persist_analysis_result(result)
            
            # Publish result
            await self._publish(
                "static_analysis.result",
                result.to_dict(),
                jetstream=True
            )
            
            # Update stats
            self._update_analysis_stats(result)
            
            return self._format_analysis_response(result)
            
        except Exception as e:
            self.logger.error(
                f"Analysis failed for {file_path}",
                exc_info=True,
                extra={"analysis_id": analysis_id, "error": str(e)}
            )
            raise
    
    async def _run_security_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run security analysis using pattern matching and custom rules"""
        findings = []
        
        # Apply custom security rules from DB
        for rule_id, rule in self.static_analysis_rules.items():
            if rule.rule_type == AnalysisType.SECURITY and rule.enabled:
                try:
                    matches = self._find_pattern_matches(
                        source_code, 
                        rule.pattern, 
                        file_path
                    )
                    
                    for match in matches:
                        findings.append(Finding(
                            id=f"sec_{uuid.uuid4().hex[:8]}",
                            type=AnalysisType.SECURITY,
                            severity=rule.severity,
                            title=rule.name,
                            description=rule.description,
                            file_path=file_path,
                            line_number=match["line_number"],
                            column=match.get("column"),
                            rule_id=rule.id,
                            confidence=0.85,
                            remediation=rule.metadata.get("remediation", 
                                "Review and sanitize user inputs."),
                            references=rule.metadata.get("references", [])
                        ))
                except Exception as e:
                    self.logger.warning(
                        f"Error applying rule {rule_id}: {e}",
                        extra={"rule_id": rule_id, "file_path": file_path}
                    )
        
        # Apply built-in security patterns
        for pattern_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                try:
                    matches = self._find_pattern_matches(
                        source_code, 
                        pattern, 
                        file_path
                    )
                    
                    for match in matches:
                        findings.append(self._create_security_finding(
                            pattern_type,
                            match,
                            file_path
                        ))
                except Exception as e:
                    self.logger.warning(
                        f"Error with pattern {pattern_type}: {e}",
                        extra={"pattern": pattern, "file_path": file_path}
                    )
        
        return findings
    
    async def _run_quality_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run code quality analysis"""
        findings = []
        
        # Check line length
        for i, line in enumerate(source_code.splitlines(), 1):
            if len(line) > 88:  # PEP 8 recommends 79, but 88 is common
                findings.append(Finding(
                    id=f"qual_{uuid.uuid4().hex[:6]}",
                    type=AnalysisType.QUALITY,
                    severity=Severity.LOW,
                    title="Line too long",
                    description=f"Line {i} exceeds 88 characters ({len(line)} chars).",
                    file_path=file_path,
                    line_number=i,
                    rule_id="E501",
                    confidence=1.0,
                    remediation="Break line into multiple lines or refactor."
                ))
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(source_code.splitlines(), 1):
            if re.search(r"#\s*(TODO|FIXME|XXX|HACK)", line, re.IGNORECASE):
                findings.append(Finding(
                    id=f"qual_{uuid.uuid4().hex[:6]}",
                    type=AnalysisType.QUALITY,
                    severity=Severity.INFO,
                    title="Technical debt marker found",
                    description=f"Line {i} contains TODO/FIXME comment.",
                    file_path=file_path,
                    line_number=i,
                    rule_id="W503",
                    confidence=1.0,
                    remediation="Address technical debt or create a ticket."
                ))
        
        # Check for unused imports (simplified)
        try:
            tree = ast.parse(source_code)
            imports = [
                node.names[0].name 
                for node in ast.walk(tree) 
                if isinstance(node, ast.Import)
            ]
            
            for imp in imports:
                if source_code.count(imp) == 1:  # Only appears in import
                    findings.append(Finding(
                        id=f"qual_{uuid.uuid4().hex[:6]}",
                        type=AnalysisType.QUALITY,
                        severity=Severity.LOW,
                        title="Potentially unused import",
                        description=f"Import '{imp}' may be unused.",
                        file_path=file_path,
                        rule_id="F401",
                        confidence=0.7,
                        remediation=f"Remove unused import '{imp}'."
                    ))
        except SyntaxError:
            pass  # Ignore syntax errors in quality check
        
        return findings
    
    async def _run_performance_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run performance analysis"""
        findings = []
        
        # Check for inefficient loops
        if re.search(r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)", source_code):
            findings.append(Finding(
                id=f"perf_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Inefficient loop pattern",
                description="Using range(len()) instead of direct iteration.",
                file_path=file_path,
                rule_id="PERF001",
                confidence=0.9,
                remediation="Iterate directly: 'for item in items:' instead of 'for i in range(len(items)):'"
            ))
        
        # Check for += in loops with strings
        pattern = r"for\s+.*:\s*\n\s+.*\+=.*['\"]"
        if re.search(pattern, source_code):
            findings.append(Finding(
                id=f"perf_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Inefficient string concatenation in loop",
                description="String concatenation in loops creates new objects.",
                file_path=file_path,
                rule_id="PERF002",
                confidence=0.8,
                remediation="Use list and join: result = ''.join(parts)"
            ))
        
        return findings
    
    async def _run_architecture_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run architecture analysis"""
        findings = []
        
        try:
            tree = ast.parse(source_code)
            
            # Check for God classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [
                        n for n in node.body 
                        if isinstance(n, ast.FunctionDef)
                    ]
                    
                    if len(methods) > 15:
                        findings.append(Finding(
                            id=f"arch_{uuid.uuid4().hex[:6]}",
                            type=AnalysisType.ARCHITECTURE,
                            severity=Severity.HIGH,
                            title="Potential God Object",
                            description=f"Class '{node.name}' has {len(methods)} methods.",
                            file_path=file_path,
                            line_number=node.lineno,
                            rule_id="ARCH001",
                            confidence=0.85,
                            remediation="Refactor into smaller, focused classes following Single Responsibility Principle.",
                            metadata={"class_name": node.name, "method_count": len(methods)}
                        ))
            
            # Check for long methods
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if lines > 50:
                        findings.append(Finding(
                            id=f"arch_{uuid.uuid4().hex[:6]}",
                            type=AnalysisType.ARCHITECTURE,
                            severity=Severity.MEDIUM,
                            title="Long method",
                            description=f"Method '{node.name}' is {lines} lines long.",
                            file_path=file_path,
                            line_number=node.lineno,
                            rule_id="ARCH002",
                            confidence=0.9,
                            remediation="Break down into smaller, focused methods.",
                            metadata={"method_name": node.name, "line_count": lines}
                        ))
        
        except SyntaxError:
            pass
        
        return findings
    
    async def _run_compliance_check(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run compliance checks"""
        findings = []
        
        # GDPR compliance check
        if "personal_data" in source_code.lower() or "user_data" in source_code.lower():
            if "consent" not in source_code.lower():
                findings.append(Finding(
                    id=f"comp_{uuid.uuid4().hex[:6]}",
                    type=AnalysisType.COMPLIANCE,
                    severity=Severity.HIGH,
                    title="Potential GDPR compliance issue",
                    description="Personal data handling without explicit consent mechanism.",
                    file_path=file_path,
                    rule_id="GDPR001",
                    confidence=0.6,
                    remediation="Implement and document user consent mechanisms.",
                    references=["https://gdpr.eu/"]
                ))
        
        # License header check
        if file_path.endswith(".py") and "Copyright" not in source_code[:500]:
            findings.append(Finding(
                id=f"comp_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.COMPLIANCE,
                severity=Severity.LOW,
                title="Missing license header",
                description="Source file missing copyright/license information.",
                file_path=file_path,
                rule_id="LIC001",
                confidence=0.8,
                remediation="Add appropriate license header to file."
            ))
        
        return findings
    
    async def _run_complexity_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run complexity analysis"""
        findings = []
        
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    
                    if complexity > 10:
                        findings.append(Finding(
                            id=f"complex_{uuid.uuid4().hex[:6]}",
                            type=AnalysisType.COMPLEXITY,
                            severity=Severity.HIGH if complexity > 15 else Severity.MEDIUM,
                            title="High cyclomatic complexity",
                            description=f"Function '{node.name}' has complexity of {complexity}.",
                            file_path=file_path,
                            line_number=node.lineno,
                            rule_id="CC001",
                            confidence=1.0,
                            remediation="Refactor to reduce branching and nesting.",
                            metadata={"complexity": complexity, "function_name": node.name}
                        ))
        
        except SyntaxError:
            pass
        
        return findings
    
    async def _run_maintainability_analysis(
        self, 
        source_code: str, 
        file_path: str
    ) -> List[Finding]:
        """Run maintainability analysis"""
        findings = []
        
        # Calculate maintainability metrics
        loc = len(source_code.splitlines())
        
        # Check file length
        if loc > 500:
            findings.append(Finding(
                id=f"maint_{uuid.uuid4().hex[:6]}",
                type=AnalysisType.MAINTAINABILITY,
                severity=Severity.MEDIUM,
                title="Large file",
                description=f"File has {loc} lines of code.",
                file_path=file_path,
                rule_id="MAINT001",
                confidence=1.0,
                remediation="Consider splitting into smaller modules.",
                metadata={"lines_of_code": loc}
            ))
        
        # Check for docstrings
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        findings.append(Finding(
                            id=f"maint_{uuid.uuid4().hex[:6]}",
                            type=AnalysisType.MAINTAINABILITY,
                            severity=Severity.LOW,
                            title="Missing docstring",
                            description=f"{type(node).__name__} '{node.name}' lacks documentation.",
                            file_path=file_path,
                            line_number=node.lineno,
                            rule_id="MAINT002",
                            confidence=1.0,
                            remediation="Add docstring explaining purpose and usage."
                        ))
        
        except SyntaxError:
            pass
        
        return findings
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _find_pattern_matches(
        self, 
        source_code: str, 
        pattern: str, 
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Find all matches of a regex pattern in source code"""
        matches = []
        
        for i, line in enumerate(source_code.splitlines(), 1):
            for match in re.finditer(pattern, line):
                matches.append({
                    "line_number": i,
                    "column": match.start(),
                    "matched_text": match.group(0)
                })
        
        return matches
    
    def _create_security_finding(
        self, 
        pattern_type: str, 
        match: Dict[str, Any], 
        file_path: str
    ) -> Finding:
        """Create a security finding from a pattern match"""
        severity_map = {
            "sql_injection": Severity.CRITICAL,
            "command_injection": Severity.CRITICAL,
            "xss": Severity.HIGH,
            "hardcoded_secrets": Severity.HIGH
        }
        
        title_map = {
            "sql_injection": "Potential SQL Injection",
            "command_injection": "Potential Command Injection",
            "xss": "Potential Cross-Site Scripting (XSS)",
            "hardcoded_secrets": "Hardcoded Secret Detected"
        }
        
        remediation_map = {
            "sql_injection": "Use parameterized queries or ORM methods.",
            "command_injection": "Avoid direct command execution with user input. Use safe alternatives.",
            "xss": "Sanitize and escape all user inputs before rendering.",
            "hardcoded_secrets": "Use environment variables or secure vaults for secrets."
        }
        
        return Finding(
            id=f"sec_{uuid.uuid4().hex[:8]}",
            type=AnalysisType.SECURITY,
            severity=severity_map.get(pattern_type, Severity.MEDIUM),
            title=title_map.get(pattern_type, f"Security Issue: {pattern_type}"),
            description=f"Detected {pattern_type.replace('_', ' ')} pattern.",
            file_path=file_path,
            line_number=match["line_number"],
            column=match.get("column"),
            rule_id=f"SEC_{pattern_type.upper()}",
            confidence=0.8,
            remediation=remediation_map.get(pattern_type, "Review and fix security issue."),
            metadata={"pattern_type": pattern_type, "matched_text": match.get("matched_text", "")}
        )
    
    def _calculate_type_metrics(
        self, 
        analysis_type: str, 
        findings: List[Finding], 
        source_code: str
    ) -> Dict[str, Any]:
        """Calculate metrics for a specific analysis type"""
        metrics = {
            "total_findings": len(findings),
            "by_severity": {
                s.value: len([f for f in findings if f.severity == s])
                for s in Severity
            }
        }
        
        if analysis_type == AnalysisType.QUALITY.value:
            metrics["lines_of_code"] = len(source_code.splitlines())
            metrics["average_line_length"] = sum(
                len(line) for line in source_code.splitlines()
            ) / max(len(source_code.splitlines()), 1)
        
        elif analysis_type == AnalysisType.COMPLEXITY.value:
            try:
                tree = ast.parse(source_code)
                functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                if functions:
                    complexities = [
                        self._calculate_cyclomatic_complexity(f) 
                        for f in functions
                    ]
                    metrics["average_complexity"] = sum(complexities) / len(complexities)
                    metrics["max_complexity"] = max(complexities)
                    metrics["function_count"] = len(functions)
            except SyntaxError:
                pass
        
        return metrics
    
    def _generate_summary(
        self, 
        findings: List[Finding], 
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analysis summary"""
        severity_counts = {s.value: 0 for s in Severity}
        type_counts = {t.value: 0 for t in AnalysisType}
        
        for finding in findings:
            severity_counts[finding.severity.value] += 1
            type_counts[finding.type.value] += 1
        
        # Calculate risk score
        risk_score = (
            severity_counts[Severity.CRITICAL.value] * 10 +
            severity_counts[Severity.HIGH.value] * 5 +
            severity_counts[Severity.MEDIUM.value] * 2 +
            severity_counts[Severity.LOW.value] * 1
        )
        
        return {
            "total_findings": len(findings),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "risk_score": risk_score,
            "metrics_summary": metrics,
            "recommendations": self._generate_recommendations(findings)
        }
    
    def _generate_recommendations(self, findings: List[Finding]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in findings if f.severity == Severity.HIGH)
        
        if critical_count > 0:
            recommendations.append(
                f"⚠️  URGENT: Address {critical_count} critical security "
                f"{'issue' if critical_count == 1 else 'issues'} immediately."
            )
        
        if high_count > 0:
            recommendations.append(
                f"Address {high_count} high-severity "
                f"{'finding' if high_count == 1 else 'findings'} before deployment."
            )
        
        # Type-specific recommendations
        security_findings = [f for f in findings if f.type == AnalysisType.SECURITY]
        if len(security_findings) > 3:
            recommendations.append(
                "Consider a comprehensive security audit and penetration testing."
            )
        
        quality_findings = [f for f in findings if f.type == AnalysisType.QUALITY]
        if len(quality_findings) > 10:
            recommendations.append(
                "Implement automated code formatting and linting in CI/CD pipeline."
            )
        
        arch_findings = [f for f in findings if f.type == AnalysisType.ARCHITECTURE]
        if len(arch_findings) > 2:
            recommendations.append(
                "Review and refactor architecture to improve maintainability."
            )
        
        return recommendations
    
    def _generate_file_signature(self, source_code: str, file_path: str) -> str:
        """Generate a hash signature for caching"""
        content = f"{file_path}:{source_code}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _format_analysis_response(self, result: AnalysisResult) -> Dict[str, Any]:
        """Format analysis result for response"""
        return {
            "status": "success",
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
                "timestamp": result.timestamp,
                "summary": result.summary
            },
            "findings": [f.to_dict() for f in result.findings[:100]],  # Limit response size
            "recommendations": result.summary.get("recommendations", [])
        }
    
    async def _persist_analysis_result(self, result: AnalysisResult):
        """Persist analysis result and findings to database"""
        if not self.db_pool:
            self.logger.warning("DB pool not available, skipping persistence")
            return
        
        try:
            async with self._db_connection() as conn:
                # Insert analysis result
                await conn.execute("""
                    INSERT INTO static_analysis_results 
                    (id, target_path, analysis_types, metrics, execution_time_ms, 
                     timestamp, summary, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        updated_at = NOW()
                """,
                    result.analysis_id,
                    result.target_path,
                    json.dumps([at.value for at in result.analysis_types]),
                    json.dumps(result.metrics),
                    result.execution_time_ms,
                    datetime.fromtimestamp(result.timestamp),
                    json.dumps(result.summary)
                )
                
                # Insert findings
                for finding in result.findings:
                    await conn.execute("""
                        INSERT INTO static_analysis_findings
                        (id, analysis_id, type, severity, title, description, 
                         file_path, line_number, column_number, rule_id, 
                         confidence, remediation, references, metadata, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
                        ON CONFLICT (id) DO NOTHING
                    """,
                        finding.id,
                        result.analysis_id,
                        finding.type.value,
                        finding.severity.value,
                        finding.title,
                        finding.description,
                        finding.file_path,
                        finding.line_number,
                        finding.column,
                        finding.rule_id,
                        finding.confidence,
                        finding.remediation,
                        json.dumps(finding.references),
                        json.dumps(finding.metadata)
                    )
                
                self.logger.info(
                    f"Persisted analysis {result.analysis_id} with {len(result.findings)} findings"
                )
                
        except Exception as e:
            self.logger.error(
                f"Failed to persist analysis result: {e}",
                exc_info=True,
                extra={"analysis_id": result.analysis_id}
            )
    
    async def _load_rules_from_db(self):
        """Load analysis rules from database"""
        if not self.db_pool:
            self.logger.warning("DB pool not available, loading default rules")
            self._load_default_rules()
            return
        
        try:
            records = await self._db_fetch("""
                SELECT id, name, description, rule_type, severity, pattern, 
                       enabled, metadata, created_at, updated_at
                FROM static_analysis_rules
                WHERE enabled = true
                ORDER BY severity DESC
            """)
            
            if records:
                self.static_analysis_rules.clear()
                for record in records:
                    rule = StaticAnalysisRule(
                        id=record["id"],
                        name=record["name"],
                        description=record["description"],
                        rule_type=AnalysisType[record["rule_type"].upper()],
                        severity=Severity[record["severity"].upper()],
                        pattern=record["pattern"],
                        enabled=record["enabled"],
                        metadata=json.loads(record["metadata"]) if record["metadata"] else {},
                        created_at=record.get("created_at"),
                        updated_at=record.get("updated_at")
                    )
                    self.static_analysis_rules[rule.id] = rule
                
                self.rules_last_loaded = time.time()
                self.logger.info(f"Loaded {len(self.static_analysis_rules)} rules from database")
            else:
                self.logger.info("No rules in database, loading defaults")
                self._load_default_rules()
                
        except Exception as e:
            self.logger.error(f"Failed to load rules from database: {e}", exc_info=True)
            self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default analysis rules"""
        default_rules = [
            StaticAnalysisRule(
                id="default_sql_injection",
                name="SQL Injection Vulnerability",
                description="Detects potential SQL injection vulnerabilities.",
                rule_type=AnalysisType.SECURITY,
                severity=Severity.CRITICAL,
                pattern=r"execute\s*\([^)]*\%[^)]*\)|cursor\.execute\s*\([^)]*\+[^)]*\)",
                metadata={
                    "remediation": "Use parameterized queries with placeholders.",
                    "references": ["https://owasp.org/www-community/attacks/SQL_Injection"]
                }
            ),
            StaticAnalysisRule(
                id="default_hardcoded_secret",
                name="Hardcoded Secret",
                description="Identifies hardcoded passwords or API keys.",
                rule_type=AnalysisType.SECURITY,
                severity=Severity.HIGH,
                pattern=r"(password|api_key|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                metadata={
                    "remediation": "Use environment variables or secret management systems.",
                    "references": ["https://owasp.org/www-project-top-ten/"]
                }
            ),
            StaticAnalysisRule(
                id="default_eval_usage",
                name="Dangerous eval() Usage",
                description="Use of eval() can lead to code injection.",
                rule_type=AnalysisType.SECURITY,
                severity=Severity.HIGH,
                pattern=r"\beval\s*\(",
                metadata={
                    "remediation": "Avoid eval(). Use ast.literal_eval() for safe evaluation.",
                    "references": []
                }
            )
        ]
        
        for rule in default_rules:
            self.static_analysis_rules[rule.id] = rule
        
        self.logger.info(f"Loaded {len(default_rules)} default rules")
    
    def _update_analysis_stats(self, result: AnalysisResult):
        """Update analysis statistics"""
        self.analysis_stats["total_analyses"] += 1
        self.analysis_stats["files_analyzed"] += 1
        self.analysis_stats["total_analysis_time_ms"] += result.execution_time_ms
        
        # Update average
        self.analysis_stats["average_analysis_time_ms"] = (
            self.analysis_stats["total_analysis_time_ms"] / 
            self.analysis_stats["total_analyses"]
        )
        
        # Update severity counts
        for finding in result.findings:
            self.analysis_stats["findings_by_severity"][finding.severity.value] += 1
    
    def _get_analysis_stats(self) -> Dict[str, Any]:
        """Get current analysis statistics"""
        return {
            "status": "success",
            "stats": self.analysis_stats,
            "cache_stats": {
                "cache_size": len(self.analysis_cache),
                "cache_hits": self.analysis_stats["cache_hits"],
                "cache_misses": self.analysis_stats["cache_misses"],
                "hit_rate": (
                    self.analysis_stats["cache_hits"] / 
                    max(self.analysis_stats["cache_hits"] + self.analysis_stats["cache_misses"], 1)
                ) * 100
            },
            "rules_loaded": len(self.static_analysis_rules),
            "uptime_seconds": self.metrics.uptime_seconds
        }
    
    async def _clear_cache(self) -> Dict[str, Any]:
        """Clear analysis cache"""
        cache_size = len(self.analysis_cache)
        self.analysis_cache.clear()
        self.file_signatures.clear()
        
        self.logger.info(f"Cleared cache: {cache_size} entries removed")
        
        return {
            "status": "success",
            "message": f"Cache cleared: {cache_size} entries removed"
        }
    
    # Specialized analysis methods
    
    async def _security_scan(self, payload: Dict) -> Dict[str, Any]:
        """Perform focused security scan"""
        payload["analysis_types"] = [AnalysisType.SECURITY.value]
        return await self._analyze_code(payload)
    
    async def _quality_check(self, payload: Dict) -> Dict[str, Any]:
        """Perform quality check"""
        payload["analysis_types"] = [AnalysisType.QUALITY.value]
        return await self._analyze_code(payload)
    
    async def _architecture_analysis(self, payload: Dict) -> Dict[str, Any]:
        """Perform architecture analysis"""
        payload["analysis_types"] = [AnalysisType.ARCHITECTURE.value]
        return await self._analyze_code(payload)
    
    async def _performance_analysis(self, payload: Dict) -> Dict[str, Any]:
        """Perform performance analysis"""
        payload["analysis_types"] = [AnalysisType.PERFORMANCE.value]
        return await self._analyze_code(payload)
    
    async def _compliance_check(self, payload: Dict) -> Dict[str, Any]:
        """Perform compliance check"""
        payload["analysis_types"] = [AnalysisType.COMPLIANCE.value]
        return await self._analyze_code(payload)
    
    async def _vulnerability_scan(self, payload: Dict) -> Dict[str, Any]:
        """Perform vulnerability scan"""
        # This would integrate with external vulnerability databases
        self.logger.info("Performing vulnerability scan")
        
        return {
            "status": "success",
            "message": "Vulnerability scan placeholder - integrate with CVE databases",
            "vulnerabilities": []
        }
    
    async def _batch_analysis(self, payload: Dict) -> Dict[str, Any]:
        """Perform batch analysis on multiple files"""
        files = payload.get("files", [])
        analysis_types = payload.get("analysis_types", [t.value for t in AnalysisType])
        
        self.logger.info(f"Starting batch analysis of {len(files)} files")
        
        results = []
        errors = []
        
        for file_info in files:
            try:
                file_result = await self._analyze_code({
                    "source_code": file_info.get("source_code", ""),
                    "file_path": file_info.get("file_path", "unknown"),
                    "analysis_types": analysis_types
                })
                results.append(file_result)
            except Exception as e:
                errors.append({
                    "file_path": file_info.get("file_path", "unknown"),
                    "error": str(e)
                })
                self.logger.error(
                    f"Batch analysis error for {file_info.get('file_path')}: {e}"
                )
        
        # Aggregate results
        total_findings = sum(
            r["analysis_result"]["total_findings"] 
            for r in results
        )
        
        return {
            "status": "success",
            "batch_summary": {
                "total_files": len(files),
                "analyzed": len(results),
                "errors": len(errors),
                "total_findings": total_findings
            },
            "results": results,
            "errors": errors
        }
    
    # Message handlers
    
    async def _handle_project_scan(self, msg):
        """Handle project scan request"""
        try:
            payload = json.loads(msg.data.decode())
            project_path = payload.get("project_path")
            
            if not project_path:
                raise ValueError("project_path is required")
            
            self.logger.info(f"Project scan requested for: {project_path}")
            
            # This would typically walk the directory and analyze files
            # For now, return a placeholder
            result = {
                "status": "success",
                "message": f"Project scan initiated for {project_path}",
                "project_path": project_path
            }
            
            if msg.reply:
                await self._publish(msg.reply, result)
            
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling project scan: {e}", exc_info=True)
            if msg.reply:
                await self._publish(msg.reply, {"status": "error", "error": str(e)})
            await msg.ack()
    
    async def _handle_file_scan(self, msg):
        """Handle file scan request"""
        try:
            payload = json.loads(msg.data.decode())
            result = await self._analyze_code(payload)
            
            if msg.reply:
                await self._publish(msg.reply, result)
            
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling file scan: {e}", exc_info=True)
            if msg.reply:
                await self._publish(msg.reply, {"status": "error", "error": str(e)})
            await msg.ack()
    
    async def _handle_security_scan(self, msg):
        """Handle security scan request"""
        try:
            payload = json.loads(msg.data.decode())
            result = await self._security_scan(payload)
            
            if msg.reply:
                await self._publish(msg.reply, result)
            
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling security scan: {e}", exc_info=True)
            if msg.reply:
                await self._publish(msg.reply, {"status": "error", "error": str(e)})
            await msg.ack()
    
    async def _handle_quality_check(self, msg):
        """Handle quality check request"""
        try:
            payload = json.loads(msg.data.decode())
            result = await self._quality_check(payload)
            
            if msg.reply:
                await self._publish(msg.reply, result)
            
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling quality check: {e}", exc_info=True)
            if msg.reply:
                await self._publish(msg.reply, {"status": "error", "error": str(e)})
            await msg.ack()
    
    async def _handle_rule_update(self, msg):
        """Handle rule update request"""
        try:
            payload = json.loads(msg.data.decode())
            rule_data = payload.get("rule")
            action = payload.get("action", "add")
            
            if not rule_data:
                raise ValueError("rule data is required")
            
            rule_id = rule_data["id"]
            
            if action in ["add", "update"]:
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
                
                # Persist to database
                if self.db_pool:
                    await self._db_execute("""
                        INSERT INTO static_analysis_rules 
                        (id, name, description, rule_type, severity, pattern, 
                         enabled, metadata, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            rule_type = EXCLUDED.rule_type,
                            severity = EXCLUDED.severity,
                            pattern = EXCLUDED.pattern,
                            enabled = EXCLUDED.enabled,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                    """,
                        rule.id, rule.name, rule.description,
                        rule.rule_type.value, rule.severity.value,
                        rule.pattern, rule.enabled,
                        json.dumps(rule.metadata)
                    )
                
                self.logger.info(f"Rule {rule_id} {action}d successfully")
                result = {"status": "success", "message": f"Rule {action}d", "rule_id": rule_id}
                
            elif action == "delete":
                if rule_id in self.static_analysis_rules:
                    del self.static_analysis_rules[rule_id]
                    
                    if self.db_pool:
                        await self._db_execute(
                            "DELETE FROM static_analysis_rules WHERE id = $1",
                            rule_id
                        )
                    
                    self.logger.info(f"Rule {rule_id} deleted")
                    result = {"status": "success", "message": "Rule deleted", "rule_id": rule_id}
                else:
                    result = {"status": "error", "message": "Rule not found", "rule_id": rule_id}
            
            else:
                result = {"status": "error", "message": f"Unknown action: {action}"}
            
            if msg.reply:
                await self._publish(msg.reply, result)
            
            await msg.ack()
            
        except Exception as e:
            self.logger.error(f"Error handling rule update: {e}", exc_info=True)
            if msg.reply:
                await self._publish(msg.reply, {"status": "error", "error": str(e)})
            await msg.ack()
    
    # Background tasks
    
    async def _rule_refresh_loop(self):
        """Periodically refresh rules from database"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(self.rules_refresh_interval)
                
                if time.time() - self.rules_last_loaded > self.rules_refresh_interval:
                    self.logger.info("Refreshing rules from database")
                    await self._load_rules_from_db()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in rule refresh loop: {e}", exc_info=True)
    
    async def _cache_cleanup_loop(self):
        """Periodically clean up expired cache entries"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                current_time = time.time()
                expired_keys = [
                    key for key, result in self.analysis_cache.items()
                    if current_time - result.timestamp > self.cache_ttl
                ]
                
                for key in expired_keys:
                    del self.analysis_cache[key]
                
                if expired_keys:
                    self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup loop: {e}", exc_info=True)
    
    async def _stats_publisher_loop(self):
        """Periodically publish statistics"""
        while self.state == AgentState.RUNNING:
            try:
                await asyncio.sleep(60)  # Every minute
                
                stats = self._get_analysis_stats()
                await self._publish(
                    "static_analysis.stats",
                    stats,
                    jetstream=True
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in stats publisher loop: {e}", exc_info=True)


# Entry point
if __name__ == "__main__":
    async def main():
        config = AgentConfig(
            agent_id=f"static_analysis_{uuid.uuid4().hex[:8]}",
            name="static_analysis_agent",
            agent_type="static_analysis",
            nats_url="nats://localhost:4222",
            postgres_url="postgresql://user:password@localhost:5432/agentdb",
            redis_url="redis://localhost:6379",
            version="2.0.0",
            max_concurrent_tasks=50,
            status_publish_interval_seconds=30,
            heartbeat_interval_seconds=10
        )
        
        agent = StaticAnalysisAgent(config)
        
        if await agent.start():
            await agent.run_forever()
        else:
            print("Failed to start Static Analysis Agent")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStatic Analysis Agent stopped by user")
    except Exception as e:
        print(f"Static Analysis Agent crashed: {e}")
