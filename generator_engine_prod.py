"""
Production-Ready Generator Engine v3.0
Enterprise-grade code generation with templates, validation,
and quality assurance
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
import traceback

try:
    from jinja2 import Environment, Template, TemplateError, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available - template rendering limited")


class CodeStyle(Enum):
    """Code style preferences"""
    CLEAN = "clean"
    FUNCTIONAL = "functional"
    OBJECT_ORIENTED = "object_oriented"
    MINIMAL = "minimal"
    ENTERPRISE = "enterprise"
    PYTHONIC = "pythonic"


class GenerationType(Enum):
    """Types of code generation"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    API = "api"
    MODEL = "model"
    COMPONENT = "component"
    TEST = "test"
    DOCUMENTATION = "documentation"
    SCRIPT = "script"
    INTERFACE = "interface"


@dataclass
class GenerationSpec:
    """Specification for code generation"""
    type: GenerationType
    name: str
    description: str
    language: str
    framework: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    async_mode: bool = False
    visibility: str = "public"
    properties: List[Dict[str, Any]] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    error_handling: bool = True
    logging: bool = True
    documentation: bool = True
    type_hints: bool = True
    validations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['type'] = self.type.value
        return result


@dataclass
class GeneratedArtifact:
    """Complete generated code artifact"""
    code: str
    language: str
    tests: str = ""
    documentation: str = ""
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    structure: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    complexity_estimate: int = 0
    best_practices_applied: List[str] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    generation_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GeneratorEngine:
    """
    Production-grade code generation engine
    
    Features:
    - Multi-language template-based generation
    - Quality validation and scoring
    - Best practices enforcement
    - Design pattern application
    - Comprehensive error handling
    - Performance optimization
    """
    
    # Language configurations
    LANGUAGE_CONFIG = {
        'python': {
            'indent': 4,
            'quote_style': 'double',
            'max_line_length': 88,
            'naming': 'snake_case',
            'class_naming': 'PascalCase',
            'extensions': ['.py']
        },
        'javascript': {
            'indent': 2,
            'quote_style': 'single',
            'max_line_length': 100,
            'naming': 'camelCase',
            'class_naming': 'PascalCase',
            'extensions': ['.js']
        },
        'typescript': {
            'indent': 2,
            'quote_style': 'single',
            'max_line_length': 100,
            'naming': 'camelCase',
            'class_naming': 'PascalCase',
            'extensions': ['.ts']
        }
    }
    
    # Design patterns registry
    DESIGN_PATTERNS = {
        'singleton': {
            'description': 'Single instance pattern',
            'languages': ['python', 'javascript', 'typescript'],
            'complexity': 'low'
        },
        'factory': {
            'description': 'Object creation pattern',
            'languages': ['python', 'javascript', 'typescript'],
            'complexity': 'medium'
        },
        'builder': {
            'description': 'Step-by-step construction',
            'languages': ['python', 'javascript', 'typescript'],
            'complexity': 'medium'
        },
        'observer': {
            'description': 'Event notification pattern',
            'languages': ['python', 'javascript', 'typescript'],
            'complexity': 'medium'
        },
        'strategy': {
            'description': 'Interchangeable algorithms',
            'languages': ['python', 'javascript', 'typescript'],
            'complexity': 'low'
        }
    }
    
    def __init__(
        self,
        template_dir: Optional[str] = None,
        enable_validation: bool = True,
        enable_metrics: bool = True,
        quality_threshold: float = 70.0
    ):
        """
        Initialize Generator Engine
        
        Args:
            template_dir: Custom template directory
            enable_validation: Enable code validation
            enable_metrics: Enable metrics collection
            quality_threshold: Minimum quality score
        """
        self.logger = logging.getLogger(__name__)
        self.template_dir = template_dir
        self.enable_validation = enable_validation
        self.enable_metrics = enable_metrics
        self.quality_threshold = quality_threshold
        
        # Initialize Jinja2 environment
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                autoescape=select_autoescape(),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None
        
        # Load templates
        self.templates = self._load_builtin_templates()
        
        # Metrics
        self.metrics = {
            'total_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'total_generation_time_ms': 0.0,
            'avg_generation_time_ms': 0.0,
            'languages_generated': {},
            'patterns_applied': {}
        }
        
        self.logger.info(
            "GeneratorEngine initialized",
            validation=enable_validation,
            metrics=enable_metrics,
            templates=len(self.templates)
        )
    
    def _load_builtin_templates(self) -> Dict[str, Dict[str, str]]:
        """Load built-in code templates"""
        return {
            'python': {
                'function': self._get_python_function_template(),
                'class': self._get_python_class_template(),
                'test': self._get_python_test_template(),
                'api': self._get_python_api_template()
            },
            'javascript': {
                'function': self._get_js_function_template(),
                'class': self._get_js_class_template()
            }
        }
    
    def _get_python_function_template(self) -> str:
        """Python function template"""
        return '''"""{{ description }}"""
{% if imports %}{% for imp in imports %}{{ imp }}
{% endfor %}
{% endif %}{% if logging %}import logging

logger = logging.getLogger(__name__)

{% endif %}{% for decorator in decorators %}@{{ decorator }}
{% endfor %}{% if async_mode %}async {% endif %}def {{ function_name }}(
    {% for param in params %}{{ param.name }}: {{ param.type }}{% if param.default %} = {{ param.default }}{% endif %}{% if not loop.last %},
    {% endif %}{% endfor %}
) -> {{ return_type }}:
    """
    {{ description }}
    
    Args:
        {% for param in params %}{{ param.name }}: {{ param.description }}
        {% endfor %}
    
    Returns:
        {{ return_type }}: {{ return_description }}
    {% if exceptions %}
    Raises:
        {% for exc in exceptions %}{{ exc.type }}: {{ exc.description }}
        {% endfor %}{% endif %}
    
    Example:
        >>> {{ function_name }}({% for param in params %}{{ param.example }}{% if not loop.last %}, {% endif %}{% endfor %})
        {{ example_output }}
    """
    {% if logging %}logger.debug(f"Executing {{ function_name }}")
    {% endif %}{% if validations %}# Input validation
    {% for validation in validations %}if {{ validation.condition }}:
        raise {{ validation.exception }}("{{ validation.message }}")
    {% endfor %}
    {% endif %}{% if error_handling %}try:
        {{ body | indent(8) }}
    except Exception as e:
        {% if logging %}logger.error(f"Error in {{ function_name }}: {e}")
        {% endif %}raise
    {% else %}{{ body | indent(4) }}{% endif %}'''
    
    def _get_python_class_template(self) -> str:
        """Python class template"""
        return '''"""{{ description }}"""
from typing import Any, Optional, List, Dict
{% if async_mode %}import asyncio
{% endif %}{% if logging %}import logging
{% endif %}{% for dep in dependencies %}{{ dep }}
{% endfor %}

{% if logging %}logger = logging.getLogger(__name__)

{% endif %}{% for decorator in decorators %}@{{ decorator }}
{% endfor %}class {{ class_name }}{% if extends %}({{ extends }}){% endif %}:
    """
    {{ description }}
    
    Attributes:
        {% for prop in properties %}{{ prop.name }}: {{ prop.description }}
        {% endfor %}
    """
    
    def __init__(self{% for param in init_params %}, {{ param.name }}: {{ param.type }}{% if param.default %} = {{ param.default }}{% endif %}{% endfor %}) -> None:
        """
        Initialize {{ class_name }}.
        
        Args:
            {% for param in init_params %}{{ param.name }}: {{ param.description }}
            {% endfor %}
        """
        {% if validations %}{% for validation in validations %}if {{ validation.condition }}:
            raise {{ validation.exception }}("{{ validation.message }}")
        {% endfor %}{% endif %}{% if extends %}super().__init__()
        {% endif %}{% for param in init_params %}self._{{ param.name }} = {{ param.name }}
        {% endfor %}{% for prop in properties %}self._{{ prop.name }}: {{ prop.type }} = {{ prop.default if prop.default else 'None' }}
        {% endfor %}
    {% for prop in properties %}
    @property
    def {{ prop.name }}(self) -> {{ prop.type }}:
        """Get {{ prop.name }}."""
        return self._{{ prop.name }}
    
    @{{ prop.name }}.setter
    def {{ prop.name }}(self, value: {{ prop.type }}) -> None:
        """Set {{ prop.name }}."""
        self._{{ prop.name }} = value
    {% endfor %}
    {% for method in methods %}
    {% if method.async %}async {% endif %}def {{ method.name }}(self{% for param in method.params %}, {{ param.name }}: {{ param.type }}{% if param.default %} = {{ param.default }}{% endif %}{% endfor %}) -> {{ method.return_type }}:
        """{{ method.description }}"""
        {% if error_handling %}try:
            {{ method.body | indent(12) }}
        except Exception as e:
            {% if logging %}logger.error(f"Error in {{ method.name }}: {e}")
            {% endif %}raise
        {% else %}{{ method.body | indent(8) }}{% endif %}
    {% endfor %}
    def __repr__(self) -> str:
        """String representation."""
        return f"{{ class_name }}({% for param in init_params %}{{ param.name }}={self._{{ param.name }}!r}{% if not loop.last %}, {% endif %}{% endfor %})"'''
    
    def _get_python_test_template(self) -> str:
        """Python test template"""
        return '''"""Tests for {{ module_name }}"""
import pytest
from unittest.mock import Mock, patch
{% for imp in imports %}{{ imp }}
{% endfor %}

class Test{{ class_name }}:
    """Test suite for {{ class_name }}."""
    
    def setup_method(self):
        """Setup test fixtures."""
        pass
    
    def teardown_method(self):
        """Cleanup after tests."""
        pass
    {% for test in tests %}
    def test_{{ test.name }}(self):
        """{{ test.description }}"""
        # Arrange
        {{ test.arrange | indent(8) }}
        
        # Act
        {{ test.act | indent(8) }}
        
        # Assert
        {{ test.assertions | indent(8) }}
    {% endfor %}'''
    
    def _get_python_api_template(self) -> str:
        """Python FastAPI endpoint template"""
        return '''"""{{ description }}"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
{% if logging %}import logging
{% endif %}{% for dep in dependencies %}{{ dep }}
{% endfor %}

{% if logging %}logger = logging.getLogger(__name__)
{% endif %}router = APIRouter(prefix="{{ prefix }}", tags=["{{ tag }}"])


class {{ request_model }}(BaseModel):
    """Request model."""
    {% for field in request_fields %}{{ field.name }}: {{ field.type }} = Field(description="{{ field.description }}")
    {% endfor %}


class {{ response_model }}(BaseModel):
    """Response model."""
    {% for field in response_fields %}{{ field.name }}: {{ field.type }} = Field(description="{{ field.description }}")
    {% endfor %}


@router.{{ method.lower() }}("{{ path }}", response_model={{ response_model }})
async def {{ endpoint_name }}({% if request_model %}request: {{ request_model }}{% endif %}) -> {{ response_model }}:
    """
    {{ description }}
    """
    {% if logging %}logger.info("{{ endpoint_name }} called")
    {% endif %}try:
        {{ body | indent(8) }}
        return {{ response_model }}({% for field in response_fields %}{{ field.name }}={{ field.value }}{% if not loop.last %}, {% endif %}{% endfor %})
    except Exception as e:
        {% if logging %}logger.error(f"Error: {e}")
        {% endif %}raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )'''
    
    def _get_js_function_template(self) -> str:
        """JavaScript function template"""
        return '''/**
 * {{ description }}
 * {% for param in params %}@param {{ '{' }}{{ param.type }}{{ '}' }} {{ param.name }} - {{ param.description }}
 * {% endfor %}@returns {{ '{' }}{{ return_type }}{{ '}' }} {{ return_description }}
 */
{% if async_mode %}async {% endif %}function {{ function_name }}({% for param in params %}{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
    try {
        {{ body | indent(8) }}
    } catch (error) {
        console.error(`Error in {{ function_name }}:`, error);
        throw error;
    }
}

export default {{ function_name }};'''
    
    def _get_js_class_template(self) -> str:
        """JavaScript class template"""
        return '''/**
 * {{ description }}
 * @class {{ class_name }}
 */
class {{ class_name }}{% if extends %} extends {{ extends }}{% endif %} {
    /**
     * Creates instance of {{ class_name }}.
     * {% for param in constructor_params %}@param {{ '{' }}{{ param.type }}{{ '}' }} {{ param.name }} - {{ param.description }}
     * {% endfor %}
     */
    constructor({% for param in constructor_params %}{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {% if extends %}super();
        {% endif %}{% for param in constructor_params %}this.{{ param.name }} = {{ param.name }};
        {% endfor %}
    }
    {% for method in methods %}
    /**
     * {{ method.description }}
     * {% for param in method.params %}@param {{ '{' }}{{ param.type }}{{ '}' }} {{ param.name }} - {{ param.description }}
     * {% endfor %}@returns {{ '{' }}{{ method.return_type }}{{ '}' }}
     */
    {% if method.async %}async {% endif %}{{ method.name }}({% for param in method.params %}{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        try {
            {{ method.body | indent(12) }}
        } catch (error) {
            console.error(`Error in {{ method.name }}:`, error);
            throw error;
        }
    }
    {% endfor %}
}

export default {{ class_name }};'''
    
    async def generate(
        self,
        specification: Union[str, GenerationSpec, Dict[str, Any]],
        language: str,
        style: CodeStyle = CodeStyle.CLEAN,
        include_tests: bool = False,
        include_docs: bool = True,
        patterns: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> GeneratedArtifact:
        """
        Generate code from specification
        
        Args:
            specification: Generation specification
            language: Target language
            style: Code style preference
            include_tests: Generate tests
            include_docs: Generate documentation
            patterns: Design patterns to apply
            options: Additional options
            
        Returns:
            GeneratedArtifact with code and metadata
        """
        start_time = time.time()
        options = options or {}
        patterns = patterns or []
        
        try:
            # Parse specification
            if isinstance(specification, str):
                spec = await self._parse_text_specification(specification, language)
            elif isinstance(specification, dict):
                spec = GenerationSpec(**specification)
            elif isinstance(specification, GenerationSpec):
                spec = specification
            else:
                raise ValueError(f"Invalid specification type: {type(specification)}")
            
            # Validate language support
            if language not in self.LANGUAGE_CONFIG:
                raise ValueError(f"Unsupported language: {language}")
            
            # Apply design patterns
            for pattern in patterns:
                if pattern in self.DESIGN_PATTERNS:
                    spec = await self._apply_design_pattern(spec, pattern, language)
            
            # Generate main code
            code = await self._generate_code(spec, language, style, options)
            
            # Apply formatting and best practices
            code = await self._apply_formatting(code, language, style)
            
            # Generate tests
            tests = ""
            if include_tests:
                tests = await self._generate_tests(spec, code, language)
            
            # Generate documentation
            docs = ""
            if include_docs:
                docs = await self._generate_documentation(spec, code, language)
            
            # Extract metadata
            dependencies = self._extract_dependencies(code, language)
            imports = self._extract_imports(code, language)
            
            # Calculate quality metrics
            quality_score = await self._calculate_quality_score(code, spec, language)
            complexity = self._estimate_complexity(code)
            best_practices = await self._identify_best_practices(code, language)
            
            # Generate examples
            examples = await self._generate_examples(spec, code, language) if options.get('generate_examples') else []
            
            # Create artifact
            artifact = GeneratedArtifact(
                code=code,
                language=language,
                tests=tests,
                documentation=docs,
                dependencies=dependencies,
                imports=imports,
                structure=spec.to_dict(),
                metadata={
                    'language': language,
                    'style': style.value,
                    'patterns': patterns,
                    'lines': code.count('\n') + 1,
                    'framework': spec.framework
                },
                examples=examples,
                quality_score=quality_score,
                complexity_estimate=complexity,
                best_practices_applied=best_practices,
                design_patterns=patterns,
                generation_time_ms=(time.time() - start_time) * 1000
            )
            
            # Validate if enabled
            if self.enable_validation:
                validation_result = await self._validate_generated_code(artifact)
                if not validation_result['valid']:
                    artifact.warnings.extend(validation_result.get('warnings', []))
            
            # Update metrics
            self._update_metrics(artifact, success=True)
            
            self.logger.info(
                "Code generation successful",
                language=language,
                type=spec.type.value,
                quality_score=quality_score,
                generation_time_ms=artifact.generation_time_ms
            )
            
            return artifact
            
        except Exception as e:
            self.logger.error(
                "Code generation failed",
                error=str(e),
                traceback=traceback.format_exc()
            )
            self._update_metrics(None, success=False)
            raise
    
    async def _parse_text_specification(
        self,
        text: str,
        language: str
    ) -> GenerationSpec:
        """Parse natural language specification"""
        text_lower = text.lower()
        
        # Determine generation type
        gen_type = GenerationType.FUNCTION
        if any(word in text_lower for word in ['class', 'object', 'entity']):
            gen_type = GenerationType.CLASS
        elif any(word in text_lower for word in ['api', 'endpoint', 'route']):
            gen_type = GenerationType.API
        elif any(word in text_lower for word in ['test', 'unit test']):
            gen_type = GenerationType.TEST
        
        # Extract name
        name = 'generated'
        name_patterns = [
            r'(?:called|named|for)\s+(\w+)',
            r'(?:function|class|api)\s+(\w+)',
            r'^(\w+)\s+(?:function|class)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_lower)
            if match:
                name = match.group(1)
                break
        
        # Format name according to language conventions
        name = self._format_name(name, gen_type.value, language)
        
        return GenerationSpec(
            type=gen_type,
            name=name,
            description=text,
            language=language,
            error_handling=True,
            logging='production' in text_lower or 'logging' in text_lower,
            documentation=True,
            type_hints=language in ['python', 'typescript']
        )
    
    async def _apply_design_pattern(
        self,
        spec: GenerationSpec,
        pattern: str,
        language: str
    ) -> GenerationSpec:
        """Apply design pattern to specification"""
        if pattern not in self.DESIGN_PATTERNS:
            return spec
        
        pattern_info = self.DESIGN_PATTERNS[pattern]
        
        if language not in pattern_info['languages']:
            self.logger.warning(
                f"Pattern {pattern} not supported for {language}"
            )
            return spec
        
        # Apply pattern-specific modifications
        if pattern == 'singleton' and spec.type == GenerationType.CLASS:
            if language == 'python':
                spec.methods.insert(0, {
                    'name': '__new__',
                    'description': 'Singleton implementation',
                    'params': [{'name': 'cls', 'type': 'Type', 'description': 'Class type'}],
                    'return_type': 'Self',
                    'body': """if not hasattr(cls, '_instance'):
    cls._instance = super().__new__(cls)
return cls._instance""",
                    'async': False
                })
        
        elif pattern == 'factory' and spec.type == GenerationType.CLASS:
            spec.methods.insert(0, {
                'name': 'create',
                'description': 'Factory method',
                'params': [
                    {'name': 'cls', 'type': 'Type', 'description': 'Class type'},
                    {'name': 'type_name', 'type': 'str', 'description': 'Object type'}
                ],
                'return_type': 'Self',
                'body': """# Factory implementation
return cls()""",
                'async': False
            })
            spec.decorators.insert(0, 'classmethod')
        
        self.logger.debug(f"Applied {pattern} pattern to {spec.name}")
        return spec
    
    async def _generate_code(
        self,
        spec: GenerationSpec,
        language: str,
        style: CodeStyle,
        options: Dict[str, Any]
    ) -> str:
        """Generate main code from specification"""
        gen_type = spec.type.value
        
        # Get template
        template_str = self.templates.get(language, {}).get(gen_type)
        if not template_str:
            raise ValueError(f"No template for {language}/{gen_type}")
        
        if not JINJA2_AVAILABLE:
            raise RuntimeError("Jinja2 required for code generation")
        
        # Prepare context
        context = self._prepare_template_context(spec, language, style)
        
        # Render template
        try:
            template = Template(template_str)
            code = template.render(**context)
            return code
        except TemplateError as e:
            self.logger.error(f"Template rendering failed: {e}")
            raise
    
    def _prepare_template_context(
        self,
        spec: GenerationSpec,
        language: str,
        style: CodeStyle
    ) -> Dict[str, Any]:
        """Prepare template rendering context"""
        lang_config = self.LANGUAGE_CONFIG[language]
        
        context = {
            'function_name': self._format_name(spec.name, 'function', language),
            'class_name': self._format_name(spec.name, 'class', language),
            'description': spec.description,
            'async_mode': spec.async_mode,
            'logging': spec.logging,
            'error_handling': spec.error_handling,
            'decorators': spec.decorators,
            'imports': spec.dependencies,
            'params': spec.parameters,
            'init_params': spec.parameters,
            'return_type': spec.return_type or 'None',
            'return_description': 'Operation result',
            'properties': spec.properties,
            'methods': spec.methods,
            'validations': spec.validations,
            'body': 'pass' if language == 'python' else 'return;',
            'exceptions': [],
            'example_output': '# Result',
            'extends': None,
            'dependencies': spec.dependencies
        }
        
        # Add type-specific context
        if spec.type == GenerationType.API:
            context.update({
                'prefix': spec.metadata.get('prefix', '/api'),
                'tag': spec.metadata.get('tag', 'default'),
                'method': spec.metadata.get('method', 'GET'),
                'path': spec.metadata.get('path', '/resource'),
                'endpoint_name': self._format_name(spec.name, 'function', language),
                'request_model': f"{spec.name}Request",
                'response_model': f"{spec.name}Response",
                'request_fields': spec.metadata.get('request_fields', []),
                'response_fields': spec.metadata.get('response_fields', [])
            })
        
        return context
    
    def _format_name(
        self,
        name: str,
        name_type: str,
        language: str
    ) -> str:
        """Format name according to language conventions"""
        lang_config = self.LANGUAGE_CONFIG.get(language, {})
        
        # Remove special characters
        name = re.sub(r'[^\w\s]', '', name)
        
        if name_type == 'class':
            # PascalCase
            words = name.replace('_', ' ').replace('-', ' ').split()
            return ''.join(word.capitalize() for word in words)
        
        elif name_type == 'function':
            if language == 'python':
                # snake_case
                name = name.replace(' ', '_').replace('-', '_')
                return name.lower()
            else:
                # camelCase
                words = name.replace('_', ' ').replace('-', ' ').split()
                if not words:
                    return 'generated'
                return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
        
        return name.lower()
    
    async def _apply_formatting(
        self,
        code: str,
        language: str,
        style: CodeStyle
    ) -> str:
        """Apply code formatting and style guidelines"""
        lang_config = self.LANGUAGE_CONFIG.get(language, {})
        
        # Line length enforcement
        max_length = lang_config.get('max_line_length', 100)
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            if len(line) <= max_length:
                formatted_lines.append(line)
            else:
                # Simple line wrapping (production would use language-specific formatter)
                formatted_lines.append(line[:max_length])
        
        # Remove trailing whitespace
        formatted_lines = [line.rstrip() for line in formatted_lines]
        
        # Ensure single empty line at end
        while formatted_lines and not formatted_lines[-1]:
            formatted_lines.pop()
        formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    async def _generate_tests(
        self,
        spec: GenerationSpec,
        code: str,
        language: str
    ) -> str:
        """Generate test code"""
        if language != 'python':
            return f"// Tests for {spec.name}\n// TODO: Implement tests"
        
        template_str = self.templates['python']['test']
        
        # Generate basic test cases
        tests = []
        if spec.type == GenerationType.FUNCTION:
            tests.append({
                'name': 'basic_functionality',
                'description': 'Test basic functionality',
                'arrange': 'pass',
                'act': f"result = {spec.name}()",
                'assertions': 'assert result is not None'
            })
        elif spec.type == GenerationType.CLASS:
            tests.append({
                'name': 'initialization',
                'description': 'Test initialization',
                'arrange': 'pass',
                'act': f"instance = {spec.name}()",
                'assertions': 'assert instance is not None'
            })
            
            for method in spec.methods[:3]:  # Limit to first 3 methods
                tests.append({
                    'name': method['name'],
                    'description': f"Test {method['name']}",
                    'arrange': f"instance = {spec.name}()",
                    'act': f"result = instance.{method['name']}()",
                    'assertions': 'assert True  # Add assertions'
                })
        
        context = {
            'module_name': spec.name,
            'class_name': self._format_name(spec.name, 'class', language),
            'imports': [f"from {spec.name} import {self._format_name(spec.name, 'class', language)}"],
            'tests': tests
        }
        
        template = Template(template_str)
        return template.render(**context)
    
    async def _generate_documentation(
        self,
        spec: GenerationSpec,
        code: str,
        language: str
    ) -> str:
        """Generate documentation"""
        return f"""# {spec.name}

## Overview
{spec.description}

## Usage

```{language}
{code[:500]}
...
```

## API Reference

### {self._format_name(spec.name, 'class', language)}
{spec.description}

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Examples

See code for usage examples.

## License

MIT License
"""
    
    def _extract_dependencies(self, code: str, language: str) -> List[str]:
        """Extract dependencies from code"""
        dependencies = []
        
        if language == 'python':
            import_pattern = r'^(?:from|import)\s+([\w.]+)'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                dep = match.group(1).split('.')[0]
                if dep not in ['typing', 'asyncio', 'logging'] and dep not in dependencies:
                    dependencies.append(dep)
        
        elif language in ['javascript', 'typescript']:
            import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
            for match in re.finditer(import_pattern, code):
                dep = match.group(1)
                if not dep.startswith('.') and dep not in dependencies:
                    dependencies.append(dep)
        
        return dependencies
    
    def _extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements"""
        imports = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            if language == 'python':
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
            elif language in ['javascript', 'typescript']:
                if 'import' in line and 'from' in line:
                    imports.append(line)
        
        return imports
    
    async def _calculate_quality_score(
        self,
        code: str,
        spec: GenerationSpec,
        language: str
    ) -> float:
        """Calculate code quality score"""
        score = 100.0
        
        # Documentation check
        if spec.documentation:
            if '"""' not in code and '/*' not in code:
                score -= 15
        
        # Type hints check (Python)
        if language == 'python' and spec.type_hints:
            if '->' not in code:
                score -= 10
        
        # Error handling check
        if spec.error_handling:
            if 'try' not in code.lower():
                score -= 15
        
        # Logging check
        if spec.logging:
            if 'log' not in code.lower():
                score -= 10
        
        # Length check (too short might be incomplete)
        if len(code) < 100:
            score -= 20
        
        # Complexity penalty
        complexity = self._estimate_complexity(code)
        if complexity > 20:
            score -= min(20, (complexity - 20) * 2)
        
        return max(0.0, min(100.0, score))
    
    def _estimate_complexity(self, code: str) -> int:
        """Estimate cyclomatic complexity"""
        complexity = 1
        
        # Count decision points
        complexity += code.count('if ')
        complexity += code.count('for ')
        complexity += code.count('while ')
        complexity += code.count('except ')
        complexity += code.count('elif ')
        complexity += code.count(' and ')
        complexity += code.count(' or ')
        complexity += code.count('case ')
        
        return complexity
    
    async def _identify_best_practices(
        self,
        code: str,
        language: str
    ) -> List[str]:
        """Identify applied best practices"""
        practices = []
        
        if language == 'python':
            if '"""' in code:
                practices.append('Docstrings')
            if '->' in code:
                practices.append('Type hints')
            if 'try:' in code:
                practices.append('Error handling')
            if 'logger.' in code:
                practices.append('Logging')
            if 'raise ' in code:
                practices.append('Input validation')
            if '__repr__' in code:
                practices.append('String representation')
        
        elif language in ['javascript', 'typescript']:
            if '/**' in code:
                practices.append('JSDoc comments')
            if 'try {' in code:
                practices.append('Error handling')
            if 'console.error' in code:
                practices.append('Error logging')
            if 'export ' in code:
                practices.append('Module exports')
        
        return practices
    
    async def _generate_examples(
        self,
        spec: GenerationSpec,
        code: str,
        language: str
    ) -> List[str]:
        """Generate usage examples"""
        examples = []
        
        if spec.type == GenerationType.FUNCTION:
            example = f"# Basic usage\nresult = {spec.name}()"
            examples.append(example)
        
        elif spec.type == GenerationType.CLASS:
            example = f"# Create instance\ninstance = {spec.name}()\ninstance.process()"
            examples.append(example)
        
        return examples
    
    async def _validate_generated_code(
        self,
        artifact: GeneratedArtifact
    ) -> Dict[str, Any]:
        """Validate generated code"""
        warnings = []
        
        # Quality threshold check
        if artifact.quality_score < self.quality_threshold:
            warnings.append(
                f"Quality score {artifact.quality_score:.1f} below threshold {self.quality_threshold}"
            )
        
        # Complexity check
        if artifact.complexity_estimate > 30:
            warnings.append(
                f"High complexity: {artifact.complexity_estimate}"
            )
        
        # Length check
        if len(artifact.code) < 50:
            warnings.append("Generated code seems too short")
        
        # Syntax check for Python
        if artifact.language == 'python':
            try:
                compile(artifact.code, '<string>', 'exec')
            except SyntaxError as e:
                warnings.append(f"Syntax error: {e.msg}")
        
        return {
            'valid': len(warnings) == 0,
            'warnings': warnings
        }
    
    def _update_metrics(self, artifact: Optional[GeneratedArtifact], success: bool):
        """Update generation metrics"""
        if not self.enable_metrics:
            return
        
        self.metrics['total_generations'] += 1
        
        if success:
            self.metrics['successful_generations'] += 1
            if artifact:
                self.metrics['total_generation_time_ms'] += artifact.generation_time_ms
                self.metrics['avg_generation_time_ms'] = (
                    self.metrics['total_generation_time_ms'] / 
                    self.metrics['successful_generations']
                )
                
                lang = artifact.language
                self.metrics['languages_generated'][lang] = \
                    self.metrics['languages_generated'].get(lang, 0) + 1
                
                for pattern in artifact.design_patterns:
                    self.metrics['patterns_applied'][pattern] = \
                        self.metrics['patterns_applied'].get(pattern, 0) + 1
        else:
            self.metrics['failed_generations'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get generation metrics"""
        return self.metrics.copy()
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.LANGUAGE_CONFIG.keys())
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported design patterns"""
        return list(self.DESIGN_PATTERNS.keys())
    
    def get_pattern_info(self, pattern: str) -> Dict[str, Any]:
        """Get design pattern information"""
        return self.DESIGN_PATTERNS.get(pattern, {})


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def test_generator():
        generator = GeneratorEngine()
        
        # Test function generation
        spec = GenerationSpec(
            type=GenerationType.FUNCTION,
            name="calculate_sum",
            description="Calculate sum of two numbers",
            language="python",
            parameters=[
                {'name': 'a', 'type': 'int', 'description': 'First number', 'example': '5'},
                {'name': 'b', 'type': 'int', 'description': 'Second number', 'example': '3'}
            ],
            return_type="int",
            error_handling=True,
            logging=True
        )
        
        artifact = await generator.generate(
            spec,
            language="python",
            include_tests=True,
            include_docs=True
        )
        
        logger.info("Generated Code:")
        logger.info(artifact.code)
        logger.info(f"\nQuality Score: {artifact.quality_score}")
        logger.info(f"Complexity: {artifact.complexity_estimate}")
        logger.info(f"Best Practices: {', '.join(artifact.best_practices_applied)}")
        logger.info(f"\nMetrics: {generator.get_metrics()}")
    
    asyncio.run(test_generator())