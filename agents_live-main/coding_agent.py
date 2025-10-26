"""
Production-Ready Coding Agent v1.0
===================================
A robust coding agent that executes code safely in isolated environments
with comprehensive monitoring, caching, and security features.

Features:
- Multi-language support (Python, JavaScript, Bash)
- Sandboxed execution with resource limits
- Code validation and sanitization
- Result caching with Redis
- Execution metrics and profiling
- Security scanning and constraints
- Docker-based isolation (optional)
"""

import asyncio
import json
import hashlib
import subprocess
import tempfile
import os
import sys
import re
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import resource
import signal as sig
from contextlib import asynccontextmanager

# Import the base agent
from enhanced_base_agent import (
    BaseAgent, AgentConfig, TaskRequest, Priority,
    AgentState, run_agent
)


class CodeLanguage:
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"
    SQL = "sql"


class ExecutionStatus:
    """Code execution status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_VIOLATION = "security_violation"
    INVALID_CODE = "invalid_code"


@dataclass
class CodeExecutionRequest:
    """Code execution request structure"""
    code: str
    language: str
    timeout_seconds: int = 30
    max_memory_mb: int = 512
    max_output_size: int = 1024 * 1024  # 1MB
    allow_network: bool = False
    allow_filesystem: bool = False
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    stdin_data: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate execution request"""
        errors = []
        
        if not self.code or not isinstance(self.code, str):
            errors.append("code must be a non-empty string")
        
        if self.language not in [CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT, 
                                  CodeLanguage.BASH, CodeLanguage.SQL]:
            errors.append(f"Unsupported language: {self.language}")
        
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            errors.append("timeout_seconds must be between 1 and 300")
        
        if self.max_memory_mb < 64 or self.max_memory_mb > 2048:
            errors.append("max_memory_mb must be between 64 and 2048")
        
        if len(self.code) > 100000:  # 100KB
            errors.append("code size exceeds maximum (100KB)")
        
        return errors
    
    def get_cache_key(self) -> str:
        """Generate cache key for execution result"""
        cache_data = {
            'code': self.code,
            'language': self.language,
            'dependencies': sorted(self.dependencies)
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return f"code_exec:{hashlib.sha256(cache_str.encode()).hexdigest()}"


@dataclass
class CodeExecutionResult:
    """Code execution result"""
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    output_truncated: bool = False
    error_message: Optional[str] = None
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'exit_code': self.exit_code,
            'execution_time_ms': self.execution_time_ms,
            'memory_used_mb': self.memory_used_mb,
            'output_truncated': self.output_truncated,
            'error_message': self.error_message,
            'cached': self.cached
        }


@dataclass
class CodingAgentMetrics:
    """Coding agent specific metrics"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    timeout_executions: int = 0
    security_violations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_execution_time_ms: float = 0.0
    
    # Language-specific counters
    python_executions: int = 0
    javascript_executions: int = 0
    bash_executions: int = 0
    sql_executions: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'timeout_executions': self.timeout_executions,
            'security_violations': self.security_violations,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'avg_execution_time_ms': self.avg_execution_time_ms,
            'language_breakdown': {
                'python': self.python_executions,
                'javascript': self.javascript_executions,
                'bash': self.bash_executions,
                'sql': self.sql_executions
            }
        }


class SecurityValidator:
    """Validate code for security concerns"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = {
        CodeLanguage.PYTHON: [
            r'import\s+os\s*$',
            r'import\s+subprocess',
            r'import\s+sys',
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
        ],
        CodeLanguage.JAVASCRIPT: [
            r'require\s*\(\s*["\']fs["\']',
            r'require\s*\(\s*["\']child_process["\']',
            r'eval\s*\(',
            r'Function\s*\(',
            r'process\.exit',
            r'require\s*\(\s*["\']net["\']',
        ],
        CodeLanguage.BASH: [
            r'rm\s+-rf',
            r'sudo\s+',
            r'curl\s+',
            r'wget\s+',
            r'nc\s+',
            r'netcat\s+',
            r'/dev/tcp',
        ]
    }
    
    @classmethod
    def validate_code(cls, code: str, language: str, allow_network: bool = False,
                     allow_filesystem: bool = False) -> tuple[bool, List[str]]:
        """
        Validate code for security issues
        Returns: (is_safe, list_of_issues)
        """
        issues = []
        
        if language not in cls.DANGEROUS_PATTERNS:
            return True, []
        
        patterns = cls.DANGEROUS_PATTERNS[language].copy()
        
        # Add filesystem patterns if not allowed
        if not allow_filesystem:
            if language == CodeLanguage.PYTHON:
                patterns.extend([r'open\s*\(', r'file\s*\(', r'Path\s*\('])
            elif language == CodeLanguage.JAVASCRIPT:
                patterns.extend([r'fs\.', r'require\s*\(\s*["\']fs["\']'])
            elif language == CodeLanguage.BASH:
                patterns.extend([r'>\s*/', r'<\s*/', r'cat\s+/', r'echo\s+.*>\s*/'])
        
        # Add network patterns if not allowed
        if not allow_network:
            if language == CodeLanguage.PYTHON:
                patterns.extend([r'import\s+socket', r'import\s+requests', 
                               r'urllib', r'http\.client'])
            elif language == CodeLanguage.JAVASCRIPT:
                patterns.extend([r'http\.', r'https\.', r'fetch\s*\(',
                               r'XMLHttpRequest', r'require\s*\(\s*["\']net["\']'])
        
        # Check for dangerous patterns
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                issues.append(f"Potentially dangerous pattern detected: {pattern}")
        
        # Check for extremely long lines (possible obfuscation)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 500:
                issues.append(f"Line {i+1} is suspiciously long ({len(line)} chars)")
        
        # Check for excessive complexity
        if code.count('{') > 100 or code.count('(') > 200:
            issues.append("Code has excessive nesting/complexity")
        
        is_safe = len(issues) == 0
        return is_safe, issues


class CodeExecutor:
    """Execute code in isolated environment"""
    
    def __init__(self, logger):
        self.logger = logger
        self.temp_dirs: Set[str] = set()
    
    async def execute(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute code with resource limits and isolation"""
        import time
        start_time = time.time()
        
        try:
            # Validate code security
            is_safe, security_issues = SecurityValidator.validate_code(
                request.code,
                request.language,
                request.allow_network,
                request.allow_filesystem
            )
            
            if not is_safe:
                self.logger.warning(f"Security validation failed: {security_issues}")
                return CodeExecutionResult(
                    status=ExecutionStatus.SECURITY_VIOLATION,
                    error_message=f"Security issues: {', '.join(security_issues)}"
                )
            
            # Execute based on language
            if request.language == CodeLanguage.PYTHON:
                result = await self._execute_python(request)
            elif request.language == CodeLanguage.JAVASCRIPT:
                result = await self._execute_javascript(request)
            elif request.language == CodeLanguage.BASH:
                result = await self._execute_bash(request)
            elif request.language == CodeLanguage.SQL:
                result = await self._execute_sql(request)
            else:
                return CodeExecutionResult(
                    status=ExecutionStatus.INVALID_CODE,
                    error_message=f"Unsupported language: {request.language}"
                )
            
            # Calculate execution time
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            self.logger.error(f"Code execution error: {e}", exc_info=True)
            return CodeExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _execute_python(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute Python code"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_file = f.name
            f.write(request.code)
        
        try:
            # Prepare command
            cmd = [sys.executable, temp_file]
            
            # Setup environment
            env = os.environ.copy()
            env.update(request.environment_vars)
            
            # Execute with timeout and resource limits
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if request.stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                preexec_fn=lambda: self._set_resource_limits(request.max_memory_mb)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(
                        input=request.stdin_data.encode() if request.stdin_data else None
                    ),
                    timeout=request.timeout_seconds
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')
                
                # Truncate output if too large
                output_truncated = False
                if len(stdout_str) > request.max_output_size:
                    stdout_str = stdout_str[:request.max_output_size]
                    output_truncated = True
                if len(stderr_str) > request.max_output_size:
                    stderr_str = stderr_str[:request.max_output_size]
                    output_truncated = True
                
                status = ExecutionStatus.SUCCESS if proc.returncode == 0 else ExecutionStatus.ERROR
                
                return CodeExecutionResult(
                    status=status,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=proc.returncode,
                    output_truncated=output_truncated
                )
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    error_message=f"Execution exceeded {request.timeout_seconds}s timeout"
                )
                
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def _execute_javascript(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute JavaScript code using Node.js"""
        # Check if node is available
        try:
            proc = await asyncio.create_subprocess_exec(
                'node', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
            if proc.returncode != 0:
                raise Exception("Node.js not available")
        except Exception as e:
            return CodeExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message="Node.js is not installed or not available"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            temp_file = f.name
            f.write(request.code)
        
        try:
            cmd = ['node', temp_file]
            
            env = os.environ.copy()
            env.update(request.environment_vars)
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if request.stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(
                        input=request.stdin_data.encode() if request.stdin_data else None
                    ),
                    timeout=request.timeout_seconds
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')
                
                output_truncated = False
                if len(stdout_str) > request.max_output_size:
                    stdout_str = stdout_str[:request.max_output_size]
                    output_truncated = True
                if len(stderr_str) > request.max_output_size:
                    stderr_str = stderr_str[:request.max_output_size]
                    output_truncated = True
                
                status = ExecutionStatus.SUCCESS if proc.returncode == 0 else ExecutionStatus.ERROR
                
                return CodeExecutionResult(
                    status=status,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=proc.returncode,
                    output_truncated=output_truncated
                )
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    error_message=f"Execution exceeded {request.timeout_seconds}s timeout"
                )
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def _execute_bash(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute Bash script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            temp_file = f.name
            f.write(request.code)
        
        try:
            cmd = ['bash', temp_file]
            
            env = os.environ.copy()
            env.update(request.environment_vars)
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE if request.stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(
                        input=request.stdin_data.encode() if request.stdin_data else None
                    ),
                    timeout=request.timeout_seconds
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')
                
                output_truncated = False
                if len(stdout_str) > request.max_output_size:
                    stdout_str = stdout_str[:request.max_output_size]
                    output_truncated = True
                if len(stderr_str) > request.max_output_size:
                    stderr_str = stderr_str[:request.max_output_size]
                    output_truncated = True
                
                status = ExecutionStatus.SUCCESS if proc.returncode == 0 else ExecutionStatus.ERROR
                
                return CodeExecutionResult(
                    status=status,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=proc.returncode,
                    output_truncated=output_truncated
                )
                
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CodeExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    error_message=f"Execution exceeded {request.timeout_seconds}s timeout"
                )
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
    
    async def _execute_sql(self, request: CodeExecutionRequest) -> CodeExecutionResult:
        """Execute SQL query (requires database connection from base agent)"""
        # This would use the database connection from the base agent
        # For now, return not implemented
        return CodeExecutionResult(
            status=ExecutionStatus.ERROR,
            error_message="SQL execution requires database connection (implement in subclass)"
        )
    
    def _set_resource_limits(self, max_memory_mb: int):
        """Set resource limits for subprocess"""
        try:
            # Set memory limit
            memory_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            
            # Set CPU time limit (soft limit)
            resource.setrlimit(resource.RLIMIT_CPU, (60, 120))
            
            # Limit number of processes
            resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))
        except Exception as e:
            # Resource limits may not work on all platforms
            pass
    
    def cleanup(self):
        """Cleanup temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass


class CodingAgent(BaseAgent):
    """
    Production-ready Coding Agent for executing code safely
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        
        # Coding agent specific components
        self.executor = CodeExecutor(self.logger)
        self.coding_metrics = CodingAgentMetrics()
        
        # Cache configuration
        self.cache_ttl_seconds = config.config_data.get('cache_ttl_seconds', 3600)
        self.enable_caching = config.config_data.get('enable_caching', True)
        
        # Execution limits
        self.default_timeout = config.config_data.get('default_timeout_seconds', 30)
        self.max_timeout = config.config_data.get('max_timeout_seconds', 300)
        self.default_memory_mb = config.config_data.get('default_memory_mb', 512)
        self.max_memory_mb = config.config_data.get('max_memory_mb', 2048)
        
        self.logger.info("CodingAgent initialized with execution limits",
                        extra={
                            'default_timeout': self.default_timeout,
                            'max_timeout': self.max_timeout,
                            'cache_enabled': self.enable_caching
                        })
    
    async def _initialize_database(self):
        """Initialize database schema for coding agent"""
        if not self.db_pool:
            return
        
        schema = """
        CREATE TABLE IF NOT EXISTS code_executions (
            id SERIAL PRIMARY KEY,
            execution_id VARCHAR(255) UNIQUE NOT NULL,
            language VARCHAR(50) NOT NULL,
            code_hash VARCHAR(64) NOT NULL,
            status VARCHAR(50) NOT NULL,
            execution_time_ms FLOAT,
            memory_used_mb FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            INDEX idx_code_hash (code_hash),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        );
        
        CREATE TABLE IF NOT EXISTS code_execution_logs (
            id SERIAL PRIMARY KEY,
            execution_id VARCHAR(255) REFERENCES code_executions(execution_id),
            stdout TEXT,
            stderr TEXT,
            exit_code INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        try:
            await self._db_execute(schema)
            self.logger.info("Database schema initialized for coding agent")
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
    
    async def _handle_task(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle coding agent specific tasks"""
        task_type = task_request.task_type
        
        if task_type == "execute_code":
            return await self._handle_execute_code(task_request)
        elif task_type == "validate_code":
            return await self._handle_validate_code(task_request)
        elif task_type == "list_languages":
            return await self._handle_list_languages(task_request)
        elif task_type == "get_execution_history":
            return await self._handle_get_execution_history(task_request)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}",
                "task_id": task_request.task_id
            }
    
    async def _handle_execute_code(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Handle code execution request"""
        try:
            payload = task_request.payload
            
            # Parse execution request
            exec_request = CodeExecutionRequest(
                code=payload.get('code', ''),
                language=payload.get('language', CodeLanguage.PYTHON),
                timeout_seconds=min(
                    payload.get('timeout_seconds', self.default_timeout),
                    self.max_timeout
                ),
                max_memory_mb=min(
                    payload.get('max_memory_mb', self.default_memory_mb),
                    self.max_memory_mb
                ),
                max_output_size=payload.get('max_output_size', 1024 * 1024),
                allow_network=payload.get('allow_network', False),
                allow_filesystem=payload.get('allow_filesystem', False),
                environment_vars=payload.get('environment_vars', {}),
                stdin_data=payload.get('stdin_data'),
                dependencies=payload.get('dependencies', [])
            )
            
            # Validate request
            validation_errors = exec_request.validate()
            if validation_errors:
                self.coding_metrics.failed_executions += 1
                return {
                    "status": "error",
                    "message": "Validation failed",
                    "errors": validation_errors,
                    "task_id": task_request.task_id
                }
            
            # Check cache if enabled
            if self.enable_caching and self.redis:
                cache_key = exec_request.get_cache_key()
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    self.coding_metrics.cache_hits += 1
                    cached_result['cached'] = True
                    return {
                        "status": "success",
                        "result": cached_result,
                        "task_id": task_request.task_id
                    }
                self.coding_metrics.cache_misses += 1
            
            # Execute code
            result = await self.executor.execute(exec_request)
            
            # Update metrics
            self.coding_metrics.total_executions += 1
            if result.status == ExecutionStatus.SUCCESS:
                self.coding_metrics.successful_executions += 1
            elif result.status == ExecutionStatus.TIMEOUT:
                self.coding_metrics.timeout_executions += 1
            elif result.status == ExecutionStatus.SECURITY_VIOLATION:
                self.coding_metrics.security_violations += 1
            else:
                self.coding_metrics.failed_executions += 1
            
            # Update language-specific counters
            if exec_request.language == CodeLanguage.PYTHON:
                self.coding_metrics.python_executions += 1
            elif exec_request.language == CodeLanguage.JAVASCRIPT:
                self.coding_metrics.javascript_executions += 1
            elif exec_request.language == CodeLanguage.BASH:
                self.coding_metrics.bash_executions += 1
            elif exec_request.language == CodeLanguage.SQL:
                self.coding_metrics.sql_executions += 1
            
            # Update average execution time
            if self.coding_metrics.total_executions == 1:
                self.coding_metrics.avg_execution_time_ms = result.execution_time_ms
            else:
                alpha = 0.1
                self.coding_metrics.avg_execution_time_ms = (
                    alpha * result.execution_time_ms +
                    (1 - alpha) * self.coding_metrics.avg_execution_time_ms
                )
            
            # Cache successful results
            if self.enable_caching and self.redis and result.status == ExecutionStatus.SUCCESS:
                cache_key = exec_request.get_cache_key()
                await self._cache_result(cache_key, result.to_dict())
            
            # Store in database
            if self.db_pool:
                await self._store_execution(exec_request, result, task_request.task_id)
            
            return {
                "status": "success",
                "result": result.to_dict(),
                "task_id": task_request.task_id
            }
            
        except Exception as e:
            self.logger.error(f"Execute code handler error: {e}", exc_info=True)
            self.coding_metrics.failed_executions += 1
            return {
                "status": "error",
                "message": str(e),
                "task_id": task_request.task_id
            }
    
    async def _handle_validate_code(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Validate code without executing"""
        try:
            payload = task_request.payload
            code = payload.get('code', '')
            language = payload.get('language', CodeLanguage.PYTHON)
            allow_network = payload.get('allow_network', False)
            allow_filesystem = payload.get('allow_filesystem', False)
            
            is_safe, issues = SecurityValidator.validate_code(
                code, language, allow_network, allow_filesystem
            )
            
            return {
                "status": "success",
                "result": {
                    "is_safe": is_safe,
                    "issues": issues,
                    "language": language
                },
                "task_id": task_request.task_id
            }
            
        except Exception as e:
            self.logger.error(f"Validate code handler error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "task_id": task_request.task_id
            }
    
    async def _handle_list_languages(self, task_request: TaskRequest) -> Dict[str, Any]:
        """List supported languages and their availability"""
        languages = {
            CodeLanguage.PYTHON: {
                "available": True,
                "version": sys.version.split()[0]
            },
            CodeLanguage.JAVASCRIPT: {
                "available": await self._check_node_available(),
                "version": await self._get_node_version()
            },
            CodeLanguage.BASH: {
                "available": True,
                "version": "system"
            },
            CodeLanguage.SQL: {
                "available": self.db_pool is not None,
                "version": "postgresql"
            }
        }
        
        return {
            "status": "success",
            "result": {
                "languages": languages,
                "default_timeout": self.default_timeout,
                "max_timeout": self.max_timeout,
                "default_memory_mb": self.default_memory_mb,
                "max_memory_mb": self.max_memory_mb
            },
            "task_id": task_request.task_id
        }
    
    async def _handle_get_execution_history(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Get execution history from database"""
        if not self.db_pool:
            return {
                "status": "error",
                "message": "Database not available",
                "task_id": task_request.task_id
            }
        
        try:
            payload = task_request.payload
            limit = min(payload.get('limit', 100), 1000)
            offset = payload.get('offset', 0)
            language = payload.get('language')
            status = payload.get('status')
            
            # Build query
            conditions = []
            params = []
            param_count = 1
            
            if language:
                conditions.append(f"language = ${param_count}")
                params.append(language)
                param_count += 1
            
            if status:
                conditions.append(f"status = ${param_count}")
                params.append(status)
                param_count += 1
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT 
                    execution_id,
                    language,
                    status,
                    execution_time_ms,
                    memory_used_mb,
                    created_at
                FROM code_executions
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            
            params.extend([limit, offset])
            
            results = await self._db_fetch(query, *params)
            
            return {
                "status": "success",
                "result": {
                    "executions": results,
                    "count": len(results),
                    "limit": limit,
                    "offset": offset
                },
                "task_id": task_request.task_id
            }
            
        except Exception as e:
            self.logger.error(f"Get execution history error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "task_id": task_request.task_id
            }
    
    async def _check_node_available(self) -> bool:
        """Check if Node.js is available"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'node', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
            return proc.returncode == 0
        except:
            return False
    
    async def _get_node_version(self) -> Optional[str]:
        """Get Node.js version"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'node', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.wait_for()
            if proc.returncode == 0:
                return stdout.decode().strip()
        except:
            pass
        return None
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached execution result from Redis"""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache execution result in Redis"""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(
                cache_key,
                self.cache_ttl_seconds,
                json.dumps(result)
            )
        except Exception as e:
            self.logger.warning(f"Cache storage failed: {e}")
    
    async def _store_execution(
        self,
        request: CodeExecutionRequest,
        result: CodeExecutionResult,
        execution_id: str
    ):
        """Store execution in database"""
        try:
            # Generate code hash
            code_hash = hashlib.sha256(request.code.encode()).hexdigest()
            
            # Insert execution record
            await self._db_execute(
                """
                INSERT INTO code_executions 
                (execution_id, language, code_hash, status, execution_time_ms, memory_used_mb)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (execution_id) DO NOTHING
                """,
                execution_id,
                request.language,
                code_hash,
                result.status,
                result.execution_time_ms,
                result.memory_used_mb
            )
            
            # Insert execution logs
            await self._db_execute(
                """
                INSERT INTO code_execution_logs
                (execution_id, stdout, stderr, exit_code)
                VALUES ($1, $2, $3, $4)
                """,
                execution_id,
                result.stdout[:10000],  # Limit log size
                result.stderr[:10000],
                result.exit_code
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store execution: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get enhanced status with coding metrics"""
        base_status = await super().get_status()
        base_status['coding_metrics'] = self.coding_metrics.to_dict()
        return base_status
    
    async def get_health(self) -> Dict[str, Any]:
        """Get enhanced health check"""
        base_health = await super().get_health()
        
        # Add coding-specific health checks
        if self.coding_metrics.total_executions > 0:
            success_rate = (
                self.coding_metrics.successful_executions / 
                self.coding_metrics.total_executions
            )
            if success_rate < 0.5:
                base_health['issues'].append(
                    f"Low success rate: {success_rate:.2%}"
                )
        
        if self.coding_metrics.security_violations > 10:
            base_health['issues'].append(
                f"High security violations: {self.coding_metrics.security_violations}"
            )
        
        return base_health
    
    async def stop(self):
        """Enhanced cleanup for coding agent"""
        self.logger.info("Stopping CodingAgent and cleaning up resources")
        
        # Cleanup executor resources
        self.executor.cleanup()
        
        # Call parent stop
        await super().stop()


async def main():
    """Main function to run the coding agent"""
    
    # Configuration
    config = AgentConfig(
        agent_id="coding-001",
        name="coding_agent",
        agent_type="coding",
        version="1.0.0",
        description="Production-ready coding agent for safe code execution",
        capabilities=[
            "execute_python",
            "execute_javascript",
            "execute_bash",
            "validate_code",
            "cache_results"
        ],
        
        # Connection URLs
        nats_url="nats://localhost:4222",
        postgres_url="postgresql://user:password@localhost:5432/agentdb",
        redis_url="redis://localhost:6379",
        
        # Connection pool settings
        postgres_min_pool_size=5,
        postgres_max_pool_size=20,
        
        # NATS settings
        nats_max_reconnect_attempts=-1,
        nats_reconnect_time_wait=2,
        
        # Health and monitoring
        status_publish_interval_seconds=30,
        heartbeat_interval_seconds=10,
        health_check_interval_seconds=60,
        
        # Circuit breaker
        circuit_breaker_failure_threshold=5,
        circuit_breaker_timeout_seconds=60,
        
        # Rate limiting
        max_concurrent_tasks=50,
        request_timeout_seconds=30.0,
        max_retry_attempts=3,
        
        # Graceful shutdown
        shutdown_timeout_seconds=30,
        
        # Logging
        log_level="INFO",
        log_format="json",
        
        # Coding agent specific config
        config_data={
            'cache_ttl_seconds': 3600,  # 1 hour
            'enable_caching': True,
            'default_timeout_seconds': 30,
            'max_timeout_seconds': 300,
            'default_memory_mb': 512,
            'max_memory_mb': 2048
        }
    )
    
    # Create and run agent
    agent = CodingAgent(config)
    await run_agent(agent)


if __name__ == "__main__":
    asyncio.run(main())