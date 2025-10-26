"""
Production-Ready Parser Engine v3.0
Enterprise-grade code parsing with comprehensive error handling,
performance optimization, and scalability features
"""

import ast
import asyncio
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import time

# Third-party imports with fallback handling
try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False
    logging.warning("esprima not available - JavaScript parsing limited")

try:
    from tree_sitter_languages import get_language, get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree-sitter not available - multi-language parsing limited")


class NodeType(Enum):
    """Enhanced node type classification"""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"
    EXPRESSION = "expression"
    STATEMENT = "statement"
    COMMENT = "comment"
    DECORATOR = "decorator"
    ANNOTATION = "annotation"
    MODULE = "module"
    INTERFACE = "interface"
    ENUM = "enum"


@dataclass
class Location:
    """Precise code location tracking"""
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    start_byte: int = 0
    end_byte: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class Symbol:
    """Symbol table entry with full context"""
    name: str
    type: NodeType
    location: Location
    scope: str
    visibility: str = "public"
    is_async: bool = False
    is_static: bool = False
    is_abstract: bool = False
    decorators: List[str] = field(default_factory=list)
    annotations: Dict[str, str] = field(default_factory=dict)
    docstring: Optional[str] = None
    complexity: int = 0
    references: List[Location] = field(default_factory=list)
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['type'] = self.type.value
        result['location'] = self.location.to_dict()
        return result


@dataclass
class Dependency:
    """Dependency tracking with metadata"""
    name: str
    type: str
    source: str
    is_external: bool
    version: Optional[str] = None
    usage_count: int = 0
    locations: List[Location] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['locations'] = [loc.to_dict() for loc in self.locations]
        return result


@dataclass
class ParseResult:
    """Comprehensive parse result"""
    success: bool
    language: str
    ast: Optional[Dict[str, Any]] = None
    tokens: List[Dict[str, Any]] = field(default_factory=list)
    symbols: List[Symbol] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    scopes: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_map: Dict[int, str] = field(default_factory=dict)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    language_features: Set[str] = field(default_factory=set)
    code_hash: str = ""
    parse_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'success': self.success,
            'language': self.language,
            'ast': self.ast,
            'tokens': self.tokens,
            'symbols': [s.to_dict() for s in self.symbols],
            'dependencies': [d.to_dict() for d in self.dependencies],
            'scopes': self.scopes,
            'metadata': self.metadata,
            'source_map': self.source_map,
            'comments': self.comments,
            'errors': self.errors,
            'warnings': self.warnings,
            'language_features': list(self.language_features),
            'code_hash': self.code_hash,
            'parse_time_ms': self.parse_time_ms
        }


class ParserEngine:
    """
    Production-grade universal code parser
    
    Features:
    - Multi-language support with graceful fallbacks
    - Comprehensive error handling and recovery
    - Performance optimization with caching
    - Thread-safe concurrent parsing
    - Detailed logging and metrics
    - Memory-efficient processing
    """
    
    # Language registry with parser availability
    LANGUAGE_REGISTRY = {
        'python': {'parser': 'ast', 'extensions': ['.py', '.pyw', '.pyi']},
        'javascript': {'parser': 'esprima', 'extensions': ['.js', '.mjs']},
        'typescript': {'parser': 'esprima', 'extensions': ['.ts']},
        'jsx': {'parser': 'esprima', 'extensions': ['.jsx']},
        'tsx': {'parser': 'esprima', 'extensions': ['.tsx']},
        'java': {'parser': 'tree_sitter', 'extensions': ['.java']},
        'cpp': {'parser': 'tree_sitter', 'extensions': ['.cpp', '.cc', '.cxx', '.hpp']},
        'c': {'parser': 'tree_sitter', 'extensions': ['.c', '.h']},
        'rust': {'parser': 'tree_sitter', 'extensions': ['.rs']},
        'go': {'parser': 'tree_sitter', 'extensions': ['.go']},
        'ruby': {'parser': 'tree_sitter', 'extensions': ['.rb']},
        'php': {'parser': 'tree_sitter', 'extensions': ['.php']},
        'swift': {'parser': 'tree_sitter', 'extensions': ['.swift']},
        'kotlin': {'parser': 'tree_sitter', 'extensions': ['.kt', '.kts']},
    }
    
    def __init__(
        self,
        max_workers: int = 4,
        cache_size: int = 100,
        max_file_size_mb: int = 10,
        enable_metrics: bool = True
    ):
        """
        Initialize Parser Engine
        
        Args:
            max_workers: Max thread pool workers
            cache_size: Parse result cache size
            max_file_size_mb: Max file size to parse
            enable_metrics: Enable performance metrics
        """
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.cache_size = cache_size
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.enable_metrics = enable_metrics
        
        # Thread pool for concurrent parsing
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="parser_"
        )
        
        # Initialize parsers
        self.parsers = {}
        self._initialize_parsers()
        
        # Parse cache (LRU-style with size limit)
        self.parse_cache: Dict[str, Tuple[ParseResult, float]] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Metrics
        self.metrics = {
            'total_parses': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'total_parse_time_ms': 0.0,
            'avg_parse_time_ms': 0.0,
            'languages_parsed': defaultdict(int)
        }
        
        self.logger.info(
            "ParserEngine initialized",
            max_workers=max_workers,
            cache_size=cache_size,
            parsers_available=list(self.parsers.keys())
        )
    
    def _initialize_parsers(self):
        """Initialize available parsers with error handling"""
        # Python AST is always available
        self.parsers['python'] = ('ast', None)
        
        # JavaScript/TypeScript
        if ESPRIMA_AVAILABLE:
            for lang in ['javascript', 'typescript', 'jsx', 'tsx']:
                self.parsers[lang] = ('esprima', None)
        
        # Tree-sitter languages
        if TREE_SITTER_AVAILABLE:
            ts_langs = {
                'java': 'java',
                'cpp': 'cpp',
                'c': 'c',
                'rust': 'rust',
                'go': 'go',
                'ruby': 'ruby',
                'php': 'php',
                'swift': 'swift',
                'kotlin': 'kotlin',
            }
            
            for lang_name, ts_name in ts_langs.items():
                try:
                    language = get_language(ts_name)
                    parser = get_parser(ts_name)
                    self.parsers[lang_name] = (parser, language)
                except Exception as e:
                    self.logger.debug(f"Tree-sitter parser unavailable for {lang_name}: {e}")
    
    async def parse(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> ParseResult:
        """
        Parse code with comprehensive error handling
        
        Args:
            code: Source code to parse
            language: Programming language
            filename: Optional filename for context
            options: Parsing options
            
        Returns:
            ParseResult with all extracted information
        """
        start_time = time.time()
        options = options or {}
        language = language.lower()
        
        # Validate inputs
        if not code or not code.strip():
            return self._create_error_result(
                "Empty or whitespace-only code",
                language,
                filename=filename
            )
        
        if len(code.encode('utf-8')) > self.max_file_size_bytes:
            return self._create_error_result(
                f"File size exceeds limit ({self.max_file_size_bytes} bytes)",
                language,
                filename=filename
            )
        
        if language not in self.LANGUAGE_REGISTRY:
            return self._create_error_result(
                f"Unsupported language: {language}",
                language,
                filename=filename
            )
        
        # Generate cache key
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        cache_key = f"{language}:{code_hash}"
        
        # Check cache
        if cache_key in self.parse_cache and not options.get('skip_cache'):
            cached_result, cache_time = self.parse_cache[cache_key]
            # Cache valid for 1 hour
            if time.time() - cache_time < 3600:
                self.cache_hits += 1
                self.logger.debug("Cache hit", cache_key=cache_key)
                return cached_result
            else:
                del self.parse_cache[cache_key]
        
        self.cache_misses += 1
        
        try:
            # Route to appropriate parser
            if language == 'python':
                result = await self._parse_python(code, options)
            elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
                result = await self._parse_javascript(code, language, options)
            elif language in self.parsers:
                result = await self._parse_tree_sitter(code, language, options)
            else:
                result = self._create_error_result(
                    f"Parser not implemented for {language}",
                    language,
                    filename=filename
                )
            
            # Set metadata
            result.code_hash = code_hash
            result.parse_time_ms = (time.time() - start_time) * 1000
            result.metadata['filename'] = filename
            
            # Update metrics
            self._update_metrics(result, language)
            
            # Cache successful results
            if result.success and len(self.parse_cache) < self.cache_size:
                self.parse_cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Parse failed with exception",
                language=language,
                error=str(e),
                traceback=traceback.format_exc()
            )
            return self._create_error_result(
                f"Unexpected error: {str(e)}",
                language,
                code_hash=code_hash,
                filename=filename
            )
    
    async def _parse_python(
        self,
        code: str,
        options: Dict[str, Any]
    ) -> ParseResult:
        """Parse Python code with AST"""
        errors = []
        warnings = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return self._create_error_result(
                f"Syntax Error: {e.msg}",
                'python',
                line=e.lineno,
                column=e.offset
            )
        except Exception as e:
            return self._create_error_result(
                f"Parse Error: {str(e)}",
                'python'
            )
        
        # Extract symbols
        symbols = []
        scopes = defaultdict(list)
        
        class SymbolExtractor(ast.NodeVisitor):
            def __init__(self):
                self.symbols = []
                self.scope_stack = ['<module>']
                self.class_stack = []
            
            def visit_FunctionDef(self, node):
                self._process_function(node, False)
            
            def visit_AsyncFunctionDef(self, node):
                self._process_function(node, True)
            
            def _process_function(self, node, is_async):
                scope_name = '.'.join(self.scope_stack)
                parent_class = self.class_stack[-1] if self.class_stack else None
                
                symbol = Symbol(
                    name=node.name,
                    type=NodeType.METHOD if parent_class else NodeType.FUNCTION,
                    location=Location(
                        node.lineno,
                        node.col_offset,
                        getattr(node, 'end_lineno', node.lineno),
                        getattr(node, 'end_col_offset', node.col_offset)
                    ),
                    scope=scope_name,
                    visibility=self._get_visibility(node.name),
                    is_async=is_async,
                    decorators=[
                        self._extract_decorator_name(d) 
                        for d in node.decorator_list
                    ],
                    docstring=ast.get_docstring(node),
                    annotations={
                        arg.arg: ast.unparse(arg.annotation)
                        for arg in node.args.args
                        if arg.annotation
                    },
                    parent=parent_class,
                    complexity=self._calculate_complexity(node)
                )
                
                if node.returns:
                    symbol.annotations['return'] = ast.unparse(node.returns)
                
                self.symbols.append(symbol)
                scopes[scope_name].append(node.name)
                
                self.scope_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()
            
            def visit_ClassDef(self, node):
                scope_name = '.'.join(self.scope_stack)
                
                bases = [ast.unparse(base) for base in node.bases]
                
                symbol = Symbol(
                    name=node.name,
                    type=NodeType.CLASS,
                    location=Location(
                        node.lineno,
                        node.col_offset,
                        getattr(node, 'end_lineno', node.lineno),
                        getattr(node, 'end_col_offset', node.col_offset)
                    ),
                    scope=scope_name,
                    visibility='public',
                    decorators=[
                        self._extract_decorator_name(d)
                        for d in node.decorator_list
                    ],
                    docstring=ast.get_docstring(node)
                )
                
                if bases:
                    symbol.annotations['bases'] = ', '.join(bases)
                
                self.symbols.append(symbol)
                scopes[scope_name].append(node.name)
                
                self.scope_stack.append(node.name)
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()
                self.scope_stack.pop()
            
            def visit_Assign(self, node):
                # Extract global/class variables
                if len(self.scope_stack) <= 2:  # Module or class level
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            scope_name = '.'.join(self.scope_stack)
                            symbol = Symbol(
                                name=target.id,
                                type=NodeType.VARIABLE,
                                location=Location(
                                    node.lineno,
                                    node.col_offset,
                                    getattr(node, 'end_lineno', node.lineno),
                                    getattr(node, 'end_col_offset', node.col_offset)
                                ),
                                scope=scope_name,
                                visibility=self._get_visibility(target.id)
                            )
                            self.symbols.append(symbol)
                
                self.generic_visit(node)
            
            def _extract_decorator_name(self, decorator):
                """Extract decorator name safely"""
                try:
                    if isinstance(decorator, ast.Name):
                        return decorator.id
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            return decorator.func.id
                    return ast.unparse(decorator)
                except:
                    return "unknown"
            
            def _get_visibility(self, name: str) -> str:
                """Determine visibility from name"""
                if name.startswith('__') and not name.endswith('__'):
                    return 'private'
                elif name.startswith('_'):
                    return 'protected'
                return 'public'
            
            def _calculate_complexity(self, node) -> int:
                """Calculate cyclomatic complexity"""
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                return complexity
        
        extractor = SymbolExtractor()
        extractor.visit(tree)
        symbols = extractor.symbols
        
        # Extract dependencies
        dependencies = self._extract_python_dependencies(tree)
        
        # Extract tokens
        tokens = self._extract_python_tokens(code)
        
        # Extract comments
        comments = self._extract_python_comments(code)
        
        # Detect features
        features = self._detect_python_features(tree, code)
        
        # Build AST dict (limited depth for performance)
        ast_dict = self._python_ast_to_dict(tree, max_depth=10)
        
        # Source map
        source_map = {i+1: line for i, line in enumerate(code.split('\n'))}
        
        # Metadata
        lines = code.split('\n')
        blank_lines = sum(1 for line in lines if not line.strip())
        
        metadata = {
            'language': 'python',
            'lines': len(lines),
            'characters': len(code),
            'blank_lines': blank_lines,
            'comment_lines': len(comments),
            'code_lines': len(lines) - blank_lines - len(comments),
            'functions': sum(1 for s in symbols if s.type == NodeType.FUNCTION),
            'methods': sum(1 for s in symbols if s.type == NodeType.METHOD),
            'classes': sum(1 for s in symbols if s.type == NodeType.CLASS),
            'variables': sum(1 for s in symbols if s.type == NodeType.VARIABLE),
            'async_functions': sum(1 for s in symbols if s.is_async),
            'decorators': sum(len(s.decorators) for s in symbols),
            'imports': len(dependencies),
            'external_deps': sum(1 for d in dependencies if d.is_external),
            'python_version': self._detect_python_version(features),
            'has_type_hints': any(s.annotations for s in symbols),
            'has_docstrings': any(s.docstring for s in symbols),
            'avg_complexity': np.mean([s.complexity for s in symbols]) if symbols else 0
        }
        
        return ParseResult(
            success=True,
            language='python',
            ast=ast_dict,
            tokens=tokens,
            symbols=symbols,
            dependencies=dependencies,
            scopes=dict(scopes),
            metadata=metadata,
            source_map=source_map,
            comments=comments,
            errors=errors,
            warnings=warnings,
            language_features=features
        )
    
    def _extract_python_dependencies(self, tree: ast.AST) -> List[Dependency]:
        """Extract Python dependencies"""
        dependencies = []
        seen = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    key = f"import:{alias.name}"
                    if key not in seen:
                        seen.add(key)
                        dependencies.append(Dependency(
                            name=alias.asname or alias.name,
                            type='import',
                            source=alias.name,
                            is_external=not alias.name.startswith('.'),
                            locations=[Location(
                                node.lineno,
                                node.col_offset,
                                getattr(node, 'end_lineno', node.lineno),
                                getattr(node, 'end_col_offset', node.col_offset)
                            )]
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    key = f"from:{module}:{alias.name}"
                    if key not in seen:
                        seen.add(key)
                        dependencies.append(Dependency(
                            name=alias.asname or alias.name,
                            type='from_import',
                            source=f"{module}.{alias.name}" if module else alias.name,
                            is_external=not module.startswith('.'),
                            locations=[Location(
                                node.lineno,
                                node.col_offset,
                                getattr(node, 'end_lineno', node.lineno),
                                getattr(node, 'end_col_offset', node.col_offset)
                            )]
                        ))
        
        return dependencies
    
    def _detect_python_features(self, tree: ast.AST, code: str) -> Set[str]:
        """Detect Python language features"""
        features = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)):
                features.add('async_await')
            
            if isinstance(node, ast.AnnAssign):
                features.add('type_hints')
            
            if isinstance(node, ast.FunctionDef) and node.returns:
                features.add('type_hints')
            
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.decorator_list:
                features.add('decorators')
            
            if isinstance(node, (ast.With, ast.AsyncWith)):
                features.add('context_managers')
            
            if isinstance(node, (ast.Yield, ast.YieldFrom)):
                features.add('generators')
            
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                features.add('comprehensions')
            
            if isinstance(node, ast.JoinedStr):
                features.add('f_strings')
            
            if isinstance(node, ast.NamedExpr):
                features.add('walrus_operator')
            
            if isinstance(node, ast.Match):
                features.add('pattern_matching')
            
            if isinstance(node, ast.ClassDef) and any(
                isinstance(base, ast.Name) and base.id in ('Protocol', 'TypedDict')
                for base in node.bases
            ):
                features.add('typing_extensions')
        
        return features
    
    def _detect_python_version(self, features: Set[str]) -> str:
        """Detect minimum Python version"""
        if 'pattern_matching' in features:
            return '3.10+'
        if 'walrus_operator' in features:
            return '3.8+'
        if 'f_strings' in features:
            return '3.6+'
        if 'async_await' in features or 'type_hints' in features:
            return '3.5+'
        return '3.0+'
    
    def _extract_python_comments(self, code: str) -> List[Dict[str, Any]]:
        """Extract Python comments"""
        comments = []
        for i, line in enumerate(code.split('\n'), 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                comments.append({
                    'line': i,
                    'text': stripped[1:].strip(),
                    'type': 'line_comment'
                })
        return comments
    
    def _extract_python_tokens(self, code: str) -> List[Dict[str, Any]]:
        """Extract Python tokens"""
        import tokenize
        import io
        
        tokens = []
        try:
            readline = io.BytesIO(code.encode('utf-8')).readline
            for tok in tokenize.tokenize(readline):
                if tok.type not in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL):
                    tokens.append({
                        "type": tokenize.tok_name[tok.type],
                        "value": tok.string,
                        "line": tok.start[0],
                        "column": tok.start[1],
                        "end_line": tok.end[0],
                        "end_column": tok.end[1]
                    })
        except Exception as e:
            self.logger.debug(f"Token extraction failed: {e}")
        
        return tokens[:1000]  # Limit for performance
    
    def _python_ast_to_dict(
        self,
        node: Any,
        max_depth: int = 10,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """Convert Python AST to dict with depth limit"""
        if current_depth >= max_depth:
            return {"type": "MaxDepthReached"}
        
        if not isinstance(node, ast.AST):
            return {"type": "Constant", "value": str(node)[:100]}
        
        result = {
            "type": node.__class__.__name__,
            "fields": {}
        }
        
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                result["fields"][field] = [
                    self._python_ast_to_dict(item, max_depth, current_depth + 1)
                    for item in value[:10]  # Limit list items
                ]
            else:
                result["fields"][field] = self._python_ast_to_dict(
                    value, max_depth, current_depth + 1
                )
        
        if hasattr(node, 'lineno'):
            result["location"] = {
                "line": node.lineno,
                "column": node.col_offset,
                "end_line": getattr(node, 'end_lineno', node.lineno),
                "end_column": getattr(node, 'end_col_offset', node.col_offset)
            }
        
        return result
    
    async def _parse_javascript(
        self,
        code: str,
        language: str,
        options: Dict[str, Any]
    ) -> ParseResult:
        """Parse JavaScript/TypeScript code"""
        if not ESPRIMA_AVAILABLE:
            return self._create_error_result(
                "JavaScript parser not available",
                language
            )
        
        try:
            parse_options = {
                'loc': True,
                'range': True,
                'tokens': True,
                'comment': True,
                'tolerant': True,
                'jsx': language in ['jsx', 'tsx']
            }
            
            tree = esprima.parseScript(code, parse_options)
            
            # Extract data
            tokens = [self._esprima_token_to_dict(t) for t in getattr(tree, 'tokens', [])]
            comments = [self._esprima_comment_to_dict(c) for c in getattr(tree, 'comments', [])]
            
            # Build AST
            ast_dict = self._esprima_to_dict(tree, max_depth=10)
            
            # Extract dependencies
            dependencies = self._extract_js_dependencies(code)
            
            # Detect features
            features = self._detect_js_features(code)
            
            # Source map
            source_map = {i+1: line for i, line in enumerate(code.split('\n'))}
            
            lines = code.split('\n')
            metadata = {
                'language': language,
                'lines': len(lines),
                'characters': len(code),
                'imports': len(dependencies),
                'arrow_functions': code.count('=>'),
                'jsx_elements': code.count('<') if language in ['jsx', 'tsx'] else 0
            }
            
            return ParseResult(
                success=True,
                language=language,
                ast=ast_dict,
                tokens=tokens[:1000],
                symbols=[],
                dependencies=dependencies,
                scopes={},
                metadata=metadata,
                source_map=source_map,
                comments=comments,
                language_features=features
            )
            
        except Exception as e:
            return self._create_error_result(
                f"JavaScript parse error: {str(e)}",
                language
            )
    
    def _esprima_token_to_dict(self, token) -> Dict[str, Any]:
        """Convert esprima token to dict"""
        return {
            'type': getattr(token, 'type', 'unknown'),
            'value': getattr(token, 'value', ''),
            'range': getattr(token, 'range', [0, 0])
        }
    
    def _esprima_comment_to_dict(self, comment) -> Dict[str, Any]:
        """Convert esprima comment to dict"""
        return {
            'type': getattr(comment, 'type', 'unknown'),
            'value': getattr(comment, 'value', ''),
            'range': getattr(comment, 'range', [0, 0])
        }
    
    def _esprima_to_dict(self, node, max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
        """Convert esprima AST to dict"""
        if current_depth >= max_depth:
            return {"type": "MaxDepthReached"}
        
        if not hasattr(node, '__dict__'):
            return str(node)[:100]
        
        result = {"type": getattr(node, 'type', 'Unknown')}
        
        if hasattr(node, 'loc') and node.loc:
            result['location'] = {
                'start': {'line': node.loc.start.line, 'column': node.loc.start.column},
                'end': {'line': node.loc.end.line, 'column': node.loc.end.column}
            }
        
        if hasattr(node, 'body'):
            if isinstance(node.body, list):
                result['children'] = [
                    self._esprima_to_dict(child, max_depth, current_depth + 1)
                    for child in node.body[:10]
                ]
            else:
                result['children'] = [self._esprima_to_dict(node.body, max_depth, current_depth + 1)]
        
        return result
    
    def _extract_js_dependencies(self, code: str) -> List[Dependency]:
        """Extract JavaScript dependencies"""
        import re
        dependencies = []
        seen = set()
        
        # ES6 imports
        import_pattern = r'import\s+(?:.*?\s+from\s+)?[\'"](.+?)[\'"]'
        for match in re.finditer(import_pattern, code):
            module = match.group(1)
            if module not in seen:
                seen.add(module)
                dependencies.append(Dependency(
                    name=module,
                    type='import',
                    source=module,
                    is_external=not module.startswith('.')
                ))
        
        # CommonJS require
        require_pattern = r'require\([\'"](.+?)[\'"]\)'
        for match in re.finditer(require_pattern, code):
            module = match.group(1)
            if module not in seen:
                seen.add(module)
                dependencies.append(Dependency(
                    name=module,
                    type='require',
                    source=module,
                    is_external=not module.startswith('.')
                ))
        
        return dependencies
    
    def _detect_js_features(self, code: str) -> Set[str]:
        """Detect JavaScript features"""
        features = set()
        
        if '=>' in code:
            features.add('arrow_functions')
        if 'async' in code and 'await' in code:
            features.add('async_await')
        if 'class ' in code:
            features.add('es6_classes')
        if '...' in code:
            features.add('spread_operator')
        if 'const ' in code or 'let ' in code:
            features.add('es6_variables')
        if '`' in code:
            features.add('template_literals')
        if 'Promise' in code:
            features.add('promises')
        
        return features
    
    async def _parse_tree_sitter(
        self,
        code: str,
        language: str,
        options: Dict[str, Any]
    ) -> ParseResult:
        """Parse code using tree-sitter"""
        if language not in self.parsers:
            return self._create_error_result(
                f"Tree-sitter parser not available for {language}",
                language
            )
        
        try:
            parser, lang = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))
            root = tree.root_node
            
            # Check for errors
            if root.has_error:
                errors = [{"message": "Parse tree contains errors", "severity": "error"}]
            else:
                errors = []
            
            ast_dict = self._tree_sitter_to_dict(root, code, max_depth=10)
            tokens = self._extract_tree_sitter_tokens(root, code)
            
            source_map = {i+1: line for i, line in enumerate(code.split('\n'))}
            
            lines = code.split('\n')
            metadata = {
                'language': language,
                'lines': len(lines),
                'characters': len(code),
                'nodes': self._count_nodes(root, max_count=1000)
            }
            
            return ParseResult(
                success=not root.has_error,
                language=language,
                ast=ast_dict,
                tokens=tokens,
                symbols=[],
                dependencies=[],
                scopes={},
                metadata=metadata,
                source_map=source_map,
                errors=errors
            )
            
        except Exception as e:
            return self._create_error_result(
                f"Tree-sitter parse error: {str(e)}",
                language
            )
    
    def _tree_sitter_to_dict(
        self,
        node,
        code: str,
        max_depth: int = 10,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """Convert tree-sitter node to dict"""
        if current_depth >= max_depth:
            return {"type": "MaxDepthReached"}
        
        result = {
            "type": node.type,
            "location": {
                "start_line": node.start_point[0],
                "start_column": node.start_point[1],
                "end_line": node.end_point[0],
                "end_column": node.end_point[1]
            }
        }
        
        # Add text for leaf nodes
        if len(node.children) == 0:
            text = code[node.start_byte:node.end_byte]
            result["text"] = text[:100] if len(text) <= 100 else text[:97] + "..."
        
        # Add children
        if node.children and current_depth < max_depth:
            result["children"] = [
                self._tree_sitter_to_dict(child, code, max_depth, current_depth + 1)
                for child in node.children[:10]
            ]
        
        return result
    
    def _extract_tree_sitter_tokens(self, node, code: str, max_tokens: int = 1000) -> List[Dict[str, Any]]:
        """Extract tokens from tree-sitter"""
        tokens = []
        
        def traverse(n, depth=0):
            if len(tokens) >= max_tokens or depth > 5:
                return
            
            if len(n.children) == 0:
                tokens.append({
                    "type": n.type,
                    "value": code[n.start_byte:n.end_byte][:100],
                    "line": n.start_point[0],
                    "column": n.start_point[1]
                })
            
            for child in n.children:
                traverse(child, depth + 1)
        
        traverse(node)
        return tokens
    
    def _count_nodes(self, node, max_count: int = 1000) -> int:
        """Count AST nodes with limit"""
        count = 1
        if count >= max_count:
            return count
        
        for child in node.children:
            count += self._count_nodes(child, max_count - count)
            if count >= max_count:
                break
        
        return count
    
    def _create_error_result(
        self,
        error: str,
        language: str,
        code_hash: str = "",
        line: Optional[int] = None,
        column: Optional[int] = None,
        filename: Optional[str] = None
    ) -> ParseResult:
        """Create error result"""
        self.logger.error(
            "Parse error",
            error=error,
            language=language,
            filename=filename
        )
        
        return ParseResult(
            success=False,
            language=language,
            metadata={"language": language, "filename": filename},
            errors=[{
                "message": error,
                "line": line,
                "column": column,
                "severity": "error"
            }],
            code_hash=code_hash
        )
    
    def _update_metrics(self, result: ParseResult, language: str):
        """Update parsing metrics"""
        if not self.enable_metrics:
            return
        
        self.metrics['total_parses'] += 1
        if result.success:
            self.metrics['successful_parses'] += 1
        else:
            self.metrics['failed_parses'] += 1
        
        self.metrics['total_parse_time_ms'] += result.parse_time_ms
        self.metrics['avg_parse_time_ms'] = (
            self.metrics['total_parse_time_ms'] / self.metrics['total_parses']
        )
        self.metrics['languages_parsed'][language] += 1
    
    async def batch_parse(
        self,
        files: List[Tuple[str, str, Optional[str]]],
        options: Optional[Dict[str, Any]] = None
    ) -> List[ParseResult]:
        """
        Parse multiple files concurrently
        
        Args:
            files: List of (code, language, filename) tuples
            options: Parsing options
            
        Returns:
            List of ParseResult objects
        """
        tasks = [
            self.parse(code, lang, filename, options)
            for code, lang, filename in files
        ]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get parsing metrics"""
        return {
            **self.metrics,
            'cache_stats': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
                'size': len(self.parse_cache)
            }
        }
    
    def clear_cache(self):
        """Clear parse cache"""
        self.parse_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("Parse cache cleared")
    
    def supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return sorted(list(self.parsers.keys()))
    
    def get_language_info(self, language: str) -> Dict[str, Any]:
        """Get language information"""
        if language not in self.LANGUAGE_REGISTRY:
            return {"error": f"Unknown language: {language}"}
        
        info = self.LANGUAGE_REGISTRY[language].copy()
        info['available'] = language in self.parsers
        return info
    
    def shutdown(self):
        """Shutdown parser engine"""
        self.logger.info("Shutting down ParserEngine")
        self.executor.shutdown(wait=True)
        self.parse_cache.clear()


# Utility to prevent import errors
try:
    import numpy as np
except ImportError:
    class np:
        @staticmethod
        def mean(values):
            return sum(values) / len(values) if values else 0


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def test_parser():
        parser = ParserEngine(max_workers=4)
        
        # Test Python parsing
        python_code = """
import asyncio
from typing import List

class Calculator:
    '''A simple calculator'''
    
    def __init__(self, name: str):
        self.name = name
    
    async def add(self, a: int, b: int) -> int:
        '''Add two numbers'''
        return a + b
"""
        
        result = await parser.parse(python_code, "python")
        print(f"Parse success: {result.success}")
        print(f"Symbols found: {len(result.symbols)}")
        print(f"Dependencies: {len(result.dependencies)}")
        print(f"Metrics: {parser.get_metrics()}")
        
        parser.shutdown()
    
    asyncio.run(test_parser())