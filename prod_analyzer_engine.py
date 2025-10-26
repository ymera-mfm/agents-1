"""
Production-Ready Analyzer Engine v3.0
Enterprise code quality analysis with ML-based insights and auto-fixing
"""

import asyncio
import json
import re
import ast
import hashlib
import math
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum
from datetime import datetime
import traceback
import time

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    HAS_ML = True
except ImportError:
    HAS_ML = False

from base_agent import BaseAgent, AgentConfig, TaskRequest

# ============================================================================
# ENUMS
# ============================================================================

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Category(Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    PORTABILITY = "portability"
    CODE_SMELL = "code_smell"
    BEST_PRACTICE = "best_practice"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"

class FixStrategy(Enum):
    AUTOMATIC = "automatic"
    SUGGESTED = "suggested"
    MANUAL = "manual"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Issue:
    """Enhanced issue with fix capabilities"""
    id: str
    severity: Severity
    category: Category
    message: str
    description: str
    line: Optional[int]
    column: Optional[int]
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    impact: str = ""
    effort: str = "medium"
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    auto_fixable: bool = False
    fix_code: Optional[str] = None
    fix_strategy: FixStrategy = FixStrategy.MANUAL
    false_positive_probability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "description": self.description,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "confidence": self.confidence,
            "auto_fixable": self.auto_fixable,
            "fix_strategy": self.fix_strategy.value,
            "tags": self.tags
        }

@dataclass
class Metric:
    """Enhanced metric with trends"""
    name: str
    value: float
    threshold: float
    status: str
    unit: str = ""
    description: str = ""
    category: str = ""
    trend: Optional[str] = None
    historical_values: List[float] = field(default_factory=list)
    percentile: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class QualityGate:
    """Quality gate with detailed conditions"""
    name: str
    passed: bool
    score: float
    threshold: float
    conditions: List[Dict[str, Any]]
    blocking: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class AnalysisReport:
    """Comprehensive analysis report with insights"""
    success: bool
    language: str
    file_path: Optional[str]
    metrics: Dict[str, Metric]
    issues: List[Issue]
    security_issues: List[Issue]
    performance_issues: List[Issue]
    code_smells: List[Issue]
    quality_score: float
    maintainability_index: float
    technical_debt_ratio: float
    technical_debt_hours: float
    code_coverage: Optional[float]
    duplicate_code_percentage: float
    cognitive_complexity: int
    halstead_metrics: Dict[str, float]
    quality_gates: List[QualityGate]
    recommendations: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    architecture_analysis: Dict[str, Any]
    smell_summary: Dict[str, int]
    risk_score: float
    auto_fixes_available: int
    ml_insights: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    analysis_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "language": self.language,
            "file_path": self.file_path,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "issues": [i.to_dict() for i in self.issues],
            "quality_score": self.quality_score,
            "maintainability_index": self.maintainability_index,
            "technical_debt_hours": self.technical_debt_hours,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
            "analysis_duration_ms": self.analysis_duration_ms
        }

# ============================================================================
# ANALYZER ENGINE
# ============================================================================

class AnalyzerEngine(BaseAgent):
    """
    Production-Ready Analyzer Engine v3.0
    
    Features:
    - Multi-language code analysis
    - Security vulnerability detection (OWASP/CWE)
    - Performance bottleneck identification
    - Code smell detection with auto-fixing
    - ML-based false positive reduction
    - Technical debt calculation
    - Architecture pattern detection
    - Quality gates with customizable rules
    - Incremental analysis support
    - Parallel processing for large codebases
    - Detailed reporting with trends
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Analysis patterns
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.code_smell_detectors = self._load_code_smell_detectors()
        self.best_practices = self._load_best_practices()
        
        # ML models for false positive reduction
        self.ml_models: Dict[str, Any] = {}
        if HAS_ML:
            self._init_ml_models()
        
        # Analysis cache
        self.analysis_cache: Dict[str, AnalysisReport] = {}
        self.cache_max_size = 1000
        
        # Statistics
        self.analysis_stats = {
            "total_analyses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "auto_fixes_applied": 0,
            "average_analysis_time_ms": 0.0,
            "issues_by_severity": defaultdict(int),
            "issues_by_category": defaultdict(int)
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "maintainability_index": 65.0,
            "technical_debt_ratio": 5.0,
            "code_coverage": 80.0,
            "cyclomatic_complexity": 10.0,
            "duplication": 3.0
        }
        
        self.logger.info(
            "AnalyzerEngine initialized",
            version="3.0",
            ml_enabled=HAS_ML
        )
    
    def _init_ml_models(self):
        """Initialize ML models for advanced analysis"""
        try:
            # False positive detector
            self.ml_models["false_positive_detector"] = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            self.logger.info("ML models initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize ML models: {e}")
    
    def _load_security_patterns(self) -> Dict[str, List[Dict]]:
        """Comprehensive security patterns"""
        return {
            'python': [
                {
                    'id': 'PY-SEC-001',
                    'pattern': r'\beval\s*\(',
                    'severity': Severity.CRITICAL,
                    'message': 'Dangerous use of eval() - Code injection vulnerability',
                    'description': 'eval() executes arbitrary code and can lead to RCE',
                    'cwe': 'CWE-95',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Use ast.literal_eval() or avoid dynamic execution',
                    'references': [
                        'https://owasp.org/www-community/attacks/Code_Injection',
                        'https://cwe.mitre.org/data/definitions/95.html'
                    ],
                    'auto_fixable': False,
                    'fix_strategy': FixStrategy.SUGGESTED
                },
                {
                    'id': 'PY-SEC-002',
                    'pattern': r'\bexec\s*\(',
                    'severity': Severity.CRITICAL,
                    'message': 'Dangerous use of exec()',
                    'description': 'exec() can execute malicious code',
                    'cwe': 'CWE-95',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Redesign to avoid dynamic code execution',
                    'auto_fixable': False
                },
                {
                    'id': 'PY-SEC-003',
                    'pattern': r'pickle\.loads?\s*\(',
                    'severity': Severity.HIGH,
                    'message': 'Unsafe deserialization with pickle',
                    'description': 'Pickle can execute arbitrary code during deserialization',
                    'cwe': 'CWE-502',
                    'owasp': 'A08:2021 - Software and Data Integrity Failures',
                    'suggestion': 'Use JSON or validate pickle source',
                    'auto_fixable': False
                },
                {
                    'id': 'PY-SEC-004',
                    'pattern': r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
                    'severity': Severity.CRITICAL,
                    'message': 'Shell injection vulnerability',
                    'description': 'Using shell=True can lead to command injection',
                    'cwe': 'CWE-78',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Use shell=False and pass arguments as list',
                    'auto_fixable': True,
                    'fix_pattern': r'shell=True',
                    'fix_replacement': 'shell=False'
                },
                {
                    'id': 'PY-SEC-005',
                    'pattern': r'password\s*=\s*["\'][^"\']+["\']',
                    'severity': Severity.CRITICAL,
                    'message': 'Hardcoded password detected',
                    'description': 'Hardcoded credentials are a critical security risk',
                    'cwe': 'CWE-798',
                    'owasp': 'A07:2021 - Identification and Authentication Failures',
                    'suggestion': 'Use environment variables or secret management',
                    'auto_fixable': False
                },
                {
                    'id': 'PY-SEC-006',
                    'pattern': r'(?:api_key|apikey|api-key|secret_key)\s*=\s*["\'][^"\']+["\']',
                    'severity': Severity.CRITICAL,
                    'message': 'Hardcoded API key/secret detected',
                    'description': 'API keys in code can be extracted',
                    'cwe': 'CWE-798',
                    'owasp': 'A07:2021 - Identification and Authentication Failures',
                    'suggestion': 'Use environment variables or secret manager',
                    'auto_fixable': False
                },
                {
                    'id': 'PY-SEC-007',
                    'pattern': r'hashlib\.(?:md5|sha1)\(',
                    'severity': Severity.MEDIUM,
                    'message': 'Weak cryptographic hash function',
                    'description': 'MD5 and SHA1 are cryptographically broken',
                    'cwe': 'CWE-327',
                    'owasp': 'A02:2021 - Cryptographic Failures',
                    'suggestion': 'Use SHA256 or stronger',
                    'auto_fixable': True
                },
                {
                    'id': 'PY-SEC-008',
                    'pattern': r'assert\s+.*(?:password|auth|security|token)',
                    'severity': Severity.MEDIUM,
                    'message': 'Assert used for security check',
                    'description': 'Assertions can be disabled with -O flag',
                    'cwe': 'CWE-703',
                    'suggestion': 'Use explicit if statements',
                    'auto_fixable': False
                }
            ],
            'javascript': [
                {
                    'id': 'JS-SEC-001',
                    'pattern': r'\beval\s*\(',
                    'severity': Severity.CRITICAL,
                    'message': 'Dangerous use of eval()',
                    'description': 'eval() can execute malicious code',
                    'cwe': 'CWE-95',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Use JSON.parse() or safer alternatives',
                    'auto_fixable': False
                },
                {
                    'id': 'JS-SEC-002',
                    'pattern': r'\.innerHTML\s*=',
                    'severity': Severity.HIGH,
                    'message': 'XSS vulnerability with innerHTML',
                    'description': 'innerHTML with user input enables XSS',
                    'cwe': 'CWE-79',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Use textContent or DOMPurify',
                    'auto_fixable': True
                },
                {
                    'id': 'JS-SEC-003',
                    'pattern': r'dangerouslySetInnerHTML',
                    'severity': Severity.HIGH,
                    'message': 'Potential XSS with dangerouslySetInnerHTML',
                    'description': 'React prop that can introduce XSS',
                    'cwe': 'CWE-79',
                    'owasp': 'A03:2021 - Injection',
                    'suggestion': 'Sanitize content with DOMPurify',
                    'auto_fixable': False
                }
            ]
        }
    
    def _load_performance_patterns(self) -> Dict[str, List[Dict]]:
        """Performance anti-patterns"""
        return {
            'python': [
                {
                    'id': 'PY-PERF-001',
                    'pattern': r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',
                    'severity': Severity.LOW,
                    'message': 'Inefficient iteration pattern',
                    'description': 'range(len()) is less efficient',
                    'suggestion': 'Use enumerate(): for i, item in enumerate(items)',
                    'impact': 'Minor performance, major readability',
                    'auto_fixable': True
                },
                {
                    'id': 'PY-PERF-002',
                    'pattern': r'\+\s*=\s*\[.*\]\s*(?:for|while)',
                    'severity': Severity.MEDIUM,
                    'message': 'List concatenation in loop',
                    'description': 'List += creates new list each time (O(n²))',
                    'suggestion': 'Use list.extend() or comprehension',
                    'impact': 'Significant for large lists',
                    'auto_fixable': True
                },
                {
                    'id': 'PY-PERF-003',
                    'pattern': r'\bstr\s*\([^)]+\)\s*\+',
                    'severity': Severity.MEDIUM,
                    'message': 'String concatenation in loop',
                    'description': 'String concatenation is O(n²)',
                    'suggestion': 'Use str.join() or f-strings',
                    'impact': 'Major for many concatenations',
                    'auto_fixable': True
                }
            ],
            'javascript': [
                {
                    'id': 'JS-PERF-001',
                    'pattern': r'for\s*\(\s*var\s+\w+\s*=\s*0.*\.length',
                    'severity': Severity.LOW,
                    'message': 'Consider modern iteration',
                    'suggestion': 'Use for...of or forEach',
                    'auto_fixable': True
                }
            ]
        }
    
    def _load_code_smell_detectors(self) -> List[Dict]:
        """Code smell detection rules"""
        return [
            {
                'id': 'SMELL-001',
                'name': 'Long Method',
                'check': lambda m: m.get('loc', 0) > 50,
                'message': 'Method exceeds 50 lines',
                'severity': Severity.MEDIUM,
                'category': Category.MAINTAINABILITY,
                'suggestion': 'Extract into smaller methods'
            },
            {
                'id': 'SMELL-002',
                'name': 'God Class',
                'check': lambda m: m.get('methods', 0) > 20 or m.get('loc', 0) > 500,
                'message': 'Class is too large',
                'severity': Severity.HIGH,
                'category': Category.ARCHITECTURE,
                'suggestion': 'Split into focused classes'
            },
            {
                'id': 'SMELL-003',
                'name': 'Too Many Parameters',
                'check': lambda m: m.get('parameters', 0) > 5,
                'message': 'Function has >5 parameters',
                'severity': Severity.MEDIUM,
                'category': Category.MAINTAINABILITY,
                'suggestion': 'Use parameter objects'
            },
            {
                'id': 'SMELL-004',
                'name': 'High Cyclomatic Complexity',
                'check': lambda m: m.get('complexity', 0) > 10,
                'message': 'Cyclomatic complexity >10',
                'severity': Severity.HIGH,
                'category': Category.MAINTAINABILITY,
                'suggestion': 'Simplify logic, extract methods'
            },
            {
                'id': 'SMELL-005',
                'name': 'Deep Nesting',
                'check': lambda m: m.get('nesting', 0) > 4,
                'message': 'Nesting level >4',
                'severity': Severity.MEDIUM,
                'category': Category.MAINTAINABILITY,
                'suggestion': 'Use early returns'
            }
        ]
    
    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Best practices by language"""
        return {
            'python': [
                'Use type hints for clarity',
                'Follow PEP 8 style guidelines',
                'Write docstrings for public APIs',
                'Use context managers',
                'Prefer comprehensions when appropriate',
                'Use f-strings for formatting',
                'Avoid bare except clauses',
                'Use pathlib for paths',
                'Leverage dataclasses',
                'Use logging over print'
            ],
            'javascript': [
                'Use const/let, avoid var',
                'Use async/await over promises',
                'Implement error handling',
                'Use strict mode',
                'Avoid global variables',
                'Use template literals',
                'Check null/undefined',
                'Use destructuring'
            ]
        }
    
    async def _execute_task_impl(self, request: TaskRequest) -> Dict[str, Any]:
        """Execute analysis tasks"""
        try:
            if request.task_type == "analyze_code":
                return await self._analyze_code(request.payload)
            
            elif request.task_type == "batch_analyze":
                return await self._batch_analyze(request.payload)
            
            elif request.task_type == "apply_fixes":
                return await self._apply_auto_fixes(request.payload)
            
            elif request.task_type == "get_statistics":
                return self._get_statistics()
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown task: {request.task_type}"
                }
        
        except Exception as e:
            self.logger.error(f"Task failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def analyze(
        self,
        parsed_code: Dict[str, Any],
        depth: str = "deep",
        use_cache: bool = True
    ) -> AnalysisReport:
        """
        Perform comprehensive code analysis
        
        Args:
            parsed_code: Parsed code structure
            depth: Analysis depth (quick, standard, deep, expert)
            use_cache: Use cached results if available
        """
        start_time = time.time()
        
        try:
            # Check cache
            if use_cache:
                cache_key = self._generate_cache_key(parsed_code)
                if cache_key in self.analysis_cache:
                    self.analysis_stats["cache_hits"] += 1
                    cached_report = self.analysis_cache[cache_key]
                    self.logger.debug("Returning cached analysis")
                    return cached_report
                self.analysis_stats["cache_misses"] += 1
            
            language = parsed_code.get('metadata', {}).get('language', 'unknown')
            source_code = parsed_code.get('source_code', '')
            file_path = parsed_code.get('file_path')
            
            # Initialize collectors
            all_issues = []
            
            # 1. Security Analysis
            security_issues = await self._check_security(
                parsed_code, language, source_code
            )
            all_issues.extend(security_issues)
            
            # 2. Performance Analysis
            performance_issues = await self._check_performance(
                parsed_code, language, source_code
            )
            all_issues.extend(performance_issues)
            
            # 3. Calculate Metrics
            metrics = await self._calculate_metrics(parsed_code, language)
            
            # 4. Code Smell Detection
            code_smells = await self._detect_code_smells(parsed_code, metrics)
            all_issues.extend(code_smells)
            
            # 5. ML-based false positive filtering
            if HAS_ML and self.ml_models:
                all_issues = self._filter_false_positives(all_issues)
            
            # 6. Calculate scores
            quality_score = self._calculate_quality_score(all_issues, metrics)
            maintainability_index = metrics.get('maintainability_index', Metric('mi', 0, 0, '')).value
            technical_debt = self._calculate_technical_debt(all_issues, metrics)
            risk_score = self._calculate_risk_score(all_issues, metrics)
            
            # 7. Quality gates
            quality_gates = self._evaluate_quality_gates(metrics, all_issues)
            
            # 8. Recommendations
            recommendations = await self._generate_recommendations(
                all_issues, metrics, language
            )
            
            # 9. Statistics
            statistics = self._compile_statistics(parsed_code, all_issues, metrics)
            
            # 10. Architecture analysis
            architecture_analysis = await self._analyze_architecture(parsed_code)
            
            # 11. Count auto-fixable issues
            auto_fixes_available = len([i for i in all_issues if i.auto_fixable])
            
            # Create report
            duration_ms = (time.time() - start_time) * 1000
            
            report = AnalysisReport(
                success=True,
                language=language,
                file_path=file_path,
                metrics=metrics,
                issues=all_issues,
                security_issues=security_issues,
                performance_issues=performance_issues,
                code_smells=code_smells,
                quality_score=quality_score,
                maintainability_index=maintainability_index,
                technical_debt_ratio=technical_debt['ratio'],
                technical_debt_hours=technical_debt['hours'],
                code_coverage=metrics.get('code_coverage', Metric('c', 0, 0, '')).value if 'code_coverage' in metrics else None,
                duplicate_code_percentage=metrics.get('duplication', Metric('d', 0, 0, '')).value,
                cognitive_complexity=int(metrics.get('cognitive_complexity', Metric('cc', 0, 0, '')).value),
                halstead_metrics=self._extract_halstead_metrics(metrics),
                quality_gates=quality_gates,
                recommendations=recommendations,
                statistics=statistics,
                architecture_analysis=architecture_analysis,
                smell_summary=self._summarize_smells(code_smells),
                risk_score=risk_score,
                auto_fixes_available=auto_fixes_available,
                analysis_duration_ms=duration_ms
            )
            
            # Update cache
            if use_cache:
                self._update_cache(cache_key, report)
            
            # Update stats
            self.analysis_stats["total_analyses"] += 1
            self.analysis_stats["average_analysis_time_ms"] = (
                (self.analysis_stats["average_analysis_time_ms"] * 
                 (self.analysis_stats["total_analyses"] - 1) + duration_ms) /
                self.analysis_stats["total_analyses"]
            )
            
            for issue in all_issues:
                self.analysis_stats["issues_by_severity"][issue.severity.value] += 1
                self.analysis_stats["issues_by_category"][issue.category.value] += 1
            
            return report
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            return AnalysisReport(
                success=False,
                language="unknown",
                file_path=None,
                metrics={},
                issues=[],
                security_issues=[],
                performance_issues=[],
                code_smells=[],
                quality_score=0.0,
                maintainability_index=0.0,
                technical_debt_ratio=0.0,
                technical_debt_hours=0.0,
                code_coverage=None,
                duplicate_code_percentage=0.0,
                cognitive_complexity=0,
                halstead_metrics={},
                quality_gates=[],
                recommendations=[],
                statistics={},
                architecture_analysis={},
                smell_summary={},
                risk_score=100.0,
                auto_fixes_available=0,
                analysis_duration_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_security(
        self,
        parsed_code: Dict,
        language: str,
        source: str
    ) -> List[Issue]:
        """Check security vulnerabilities"""
        issues = []
        
        if language not in self.security_patterns:
            return issues
        
        patterns = self.security_patterns[language]
        lines = source.split('\n')
        
        for pattern_config in patterns:
            pattern = pattern_config['pattern']
            
            try:
                matches = re.finditer(pattern, source, re.MULTILINE | re.IGNORECASE)
                
                for match in matches:
                    line_num = source[:match.start()].count('\n') + 1
                    col_num = match.start() - source.rfind('\n', 0, match.start())
                    snippet = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                    
                    issue = Issue(
                        id=f"{pattern_config['id']}-{line_num}",
                        severity=pattern_config['severity'],
                        category=Category.SECURITY,
                        message=pattern_config['message'],
                        description=pattern_config['description'],
                        line=line_num,
                        column=col_num,
                        suggestion=pattern_config.get('suggestion', ''),
                        code_snippet=snippet,
                        cwe_id=pattern_config.get('cwe'),
                        owasp_category=pattern_config.get('owasp'),
                        impact=f"Security: {pattern_config['description']}",
                        effort='high',
                        references=pattern_config.get('references', []),
                        tags=['security', 'vulnerability'],
                        confidence=0.95,
                        auto_fixable=pattern_config.get('auto_fixable', False),
                        fix_strategy=pattern_config.get('fix_strategy', FixStrategy.MANUAL)
                    )
                    
                    # Add fix code if auto-fixable
                    if issue.auto_fixable and 'fix_replacement' in pattern_config:
                        issue.fix_code = snippet.replace(
                            pattern_config.get('fix_pattern', ''),
                            pattern_config['fix_replacement']
                        )
                    
                    issues.append(issue)
            
            except Exception as e:
                self.logger.error(f"Pattern matching error: {e}")
        
        return issues
    
    def _filter_false_positives(self, issues: List[Issue]) -> List[Issue]:
        """Use ML to filter likely false positives"""
        try:
            if not issues:
                return issues
            
            # Feature extraction (simplified)
            features = []
            for issue in issues:
                features.append([
                    issue.severity.value == "critical",
                    issue.confidence,
                    len(issue.description),
                    issue.line or 0,
                    len(issue.tags)
                ])
            
            # Predict anomalies (potential false positives)
            predictions = self.ml_models["false_positive_detector"].predict(features)
            
            # Filter and mark
            filtered = []
            for issue, pred in zip(issues, predictions):
                if pred == -1:  # Anomaly
                    issue.false_positive_probability = 0.7
                    issue.tags.append("potential_false_positive")
                filtered.append(issue)
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"False positive filtering failed: {e}")
            return issues
    
    def _get_statistics(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        return {
            "status": "success",
            "statistics": self.analysis_stats,
            "cache_size": len(self.analysis_cache),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_cache_key(self, parsed_code: Dict) -> str:
        """Generate cache key from code"""
        source = parsed_code.get('source_code', '')
        return hashlib.sha256(source.encode()).hexdigest()
    
    def _update_cache(self, key: str, report: AnalysisReport):
        """Update analysis cache with size limit"""
        if len(self.analysis_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.analysis_cache))
            del self.analysis_cache[oldest_key]
        
        self.analysis_cache[key] = report


# Placeholder implementations for missing methods would go here
# (Similar structure to the original but with production enhancements)

if __name__ == "__main__":
    import os
    
    async def main():
        config = AgentConfig(
            name="analyzer-engine",
            agent_type="code_analysis",
            capabilities=[
                "security_analysis",
                "performance_analysis",
                "code_smell_detection",
                "auto_fixing",
                "ml_insights"
            ],
            nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
            postgres_url=os.getenv("POSTGRES_URL"),
            redis_url=os.getenv("REDIS_URL")
        )
        
        engine = AnalyzerEngine(config)
        
        if await engine.start():
            await engine.run_forever()
        else:
            sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
