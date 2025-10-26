"""
Code Generation Agent - Specialized agent for code generation and analysis tasks
"""
from typing import Any, Dict, Optional, List
import asyncio
import re
import json

from base_agent import BaseAgent, MessageType, AgentState
from logger import logger


class CodeGenerationAgent(BaseAgent):
    """
    Specialized agent for code generation, analysis, and refactoring tasks.
    
    Capabilities:
    - Generate code from specifications
    - Analyze code quality and suggest improvements
    - Refactor existing code
    - Generate test cases
    - Document code
    """
    
    def __init__(self, agent_id: str = "code_generation_agent", config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, config)
        self.supported_languages = config.get("supported_languages", [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#"
        ]) if config else ["python", "javascript", "typescript", "java", "go", "rust", "c++", "c#"]
        self.code_cache: Dict[str, str] = {}
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "languages_used": {}
        }
        
    async def initialize(self) -> bool:
        """Initialize code generation agent"""
        try:
            self.logger.info("Initializing Code Generation Agent")
            self.logger.info(f"Supported languages: {', '.join(self.supported_languages)}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}", exc_info=True)
            return False
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process code generation requests.
        
        Message format:
        {
            "type": "generate_code" | "analyze_code" | "refactor_code" | "generate_tests",
            "language": "python" | "javascript" | ...,
            "specification": "...",  # For generation
            "code": "...",  # For analysis/refactoring
            "options": {...}  # Additional options
        }
        """
        try:
            msg_type = message.get("type")
            language = message.get("language", "python")
            
            self.generation_stats["total_requests"] += 1
            
            if language not in self.supported_languages:
                return {
                    "status": "error",
                    "error": f"Unsupported language: {language}. Supported: {', '.join(self.supported_languages)}"
                }
            
            if msg_type == "generate_code":
                return await self.generate_code(
                    language=language,
                    specification=message.get("specification", ""),
                    options=message.get("options", {})
                )
            elif msg_type == "analyze_code":
                return await self.analyze_code(
                    language=language,
                    code=message.get("code", ""),
                    options=message.get("options", {})
                )
            elif msg_type == "refactor_code":
                return await self.refactor_code(
                    language=language,
                    code=message.get("code", ""),
                    options=message.get("options", {})
                )
            elif msg_type == "generate_tests":
                return await self.generate_tests(
                    language=language,
                    code=message.get("code", ""),
                    options=message.get("options", {})
                )
            else:
                return {
                    "status": "error",
                    "error": f"Unknown message type: {msg_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            self.generation_stats["failed_generations"] += 1
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def execute(self) -> Any:
        """Execute periodic maintenance tasks"""
        # Clean up old cache entries
        if len(self.code_cache) > 1000:
            # Keep only last 500 entries
            keys = list(self.code_cache.keys())
            for key in keys[:500]:
                del self.code_cache[key]
        
        await asyncio.sleep(60)  # Run maintenance every minute
    
    async def generate_code(
        self,
        language: str,
        specification: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate code from specification.
        
        Args:
            language: Programming language
            specification: Code specification/requirements
            options: Generation options (style, framework, etc.)
            
        Returns:
            Generated code and metadata
        """
        try:
            self.logger.info(f"Generating {language} code from specification")
            
            # Update stats
            self.generation_stats["languages_used"][language] = \
                self.generation_stats["languages_used"].get(language, 0) + 1
            
            # Generate code based on specification
            # In production, this would interface with an LLM or code generation model
            generated_code = await self._generate_code_impl(language, specification, options)
            
            # Cache the generated code
            cache_key = f"{language}:{hash(specification)}"
            self.code_cache[cache_key] = generated_code
            
            self.generation_stats["successful_generations"] += 1
            
            return {
                "status": "success",
                "language": language,
                "code": generated_code,
                "metadata": {
                    "lines_of_code": len(generated_code.split('\n')),
                    "cache_key": cache_key
                }
            }
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}", exc_info=True)
            self.generation_stats["failed_generations"] += 1
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_code(
        self,
        language: str,
        code: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze code quality and provide suggestions.
        
        Args:
            language: Programming language
            code: Code to analyze
            options: Analysis options
            
        Returns:
            Analysis results and suggestions
        """
        try:
            self.logger.info(f"Analyzing {language} code")
            
            analysis = {
                "language": language,
                "metrics": {
                    "lines_of_code": len(code.split('\n')),
                    "blank_lines": len([line for line in code.split('\n') if not line.strip()]),
                    "comment_lines": self._count_comments(code, language)
                },
                "issues": [],
                "suggestions": []
            }
            
            # Perform basic code analysis
            issues = self._detect_code_issues(code, language)
            analysis["issues"] = issues
            
            # Generate improvement suggestions
            suggestions = self._generate_suggestions(code, language, issues)
            analysis["suggestions"] = suggestions
            
            # Calculate code quality score
            analysis["quality_score"] = self._calculate_quality_score(analysis)
            
            return {
                "status": "success",
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"Code analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def refactor_code(
        self,
        language: str,
        code: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refactor code to improve quality and maintainability.
        
        Args:
            language: Programming language
            code: Code to refactor
            options: Refactoring options
            
        Returns:
            Refactored code and changes made
        """
        try:
            self.logger.info(f"Refactoring {language} code")
            
            # In production, this would use sophisticated refactoring tools
            refactored_code = await self._refactor_code_impl(code, language, options)
            
            changes = self._detect_changes(code, refactored_code)
            
            return {
                "status": "success",
                "language": language,
                "original_code": code,
                "refactored_code": refactored_code,
                "changes": changes,
                "improvements": {
                    "lines_reduced": len(code.split('\n')) - len(refactored_code.split('\n')),
                    "complexity_reduced": True  # Simplified for demo
                }
            }
            
        except Exception as e:
            self.logger.error(f"Code refactoring failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_tests(
        self,
        language: str,
        code: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate test cases for given code.
        
        Args:
            language: Programming language
            code: Code to generate tests for
            options: Test generation options
            
        Returns:
            Generated test code
        """
        try:
            self.logger.info(f"Generating tests for {language} code")
            
            test_framework = options.get("framework", self._get_default_test_framework(language))
            
            # Generate test code
            test_code = await self._generate_tests_impl(code, language, test_framework)
            
            return {
                "status": "success",
                "language": language,
                "test_framework": test_framework,
                "test_code": test_code,
                "metadata": {
                    "test_cases": self._count_test_cases(test_code, language),
                    "coverage_estimate": "85%"  # Simplified for demo
                }
            }
            
        except Exception as e:
            self.logger.error(f"Test generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Helper methods
    
    async def _generate_code_impl(
        self,
        language: str,
        specification: str,
        options: Dict[str, Any]
    ) -> str:
        """Implementation of code generation (would use LLM in production)"""
        # Simulate code generation
        await asyncio.sleep(0.1)  # Simulate processing time
        
        templates = {
            "python": f'''# Generated Python code
# Specification: {specification[:100]}...

def main():
    """Main function implementation"""
    pass

if __name__ == "__main__":
    main()
''',
            "javascript": f'''// Generated JavaScript code
// Specification: {specification[:100]}...

function main() {{
    // Implementation
}}

module.exports = {{ main }};
'''
        }
        
        return templates.get(language, f"// {language} code\n// {specification[:100]}...")
    
    async def _refactor_code_impl(
        self,
        code: str,
        language: str,
        options: Dict[str, Any]
    ) -> str:
        """Implementation of code refactoring"""
        # Simulate refactoring
        await asyncio.sleep(0.1)
        
        # Simple refactoring: remove excess blank lines
        lines = code.split('\n')
        refactored_lines = []
        prev_blank = False
        
        for line in lines:
            is_blank = not line.strip()
            if not (is_blank and prev_blank):
                refactored_lines.append(line)
            prev_blank = is_blank
        
        return '\n'.join(refactored_lines)
    
    async def _generate_tests_impl(
        self,
        code: str,
        language: str,
        framework: str
    ) -> str:
        """Implementation of test generation"""
        await asyncio.sleep(0.1)
        
        if language == "python":
            return f'''import pytest

def test_main():
    """Test main functionality"""
    # Test implementation
    assert True

def test_edge_cases():
    """Test edge cases"""
    # Test implementation
    assert True
'''
        else:
            return f"// {language} test code for {framework}"
    
    def _count_comments(self, code: str, language: str) -> int:
        """Count comment lines in code"""
        comment_patterns = {
            "python": r'^\s*#',
            "javascript": r'^\s*//',
            "java": r'^\s*//',
        }
        
        pattern = comment_patterns.get(language, r'^\s*//')
        return len([line for line in code.split('\n') if re.match(pattern, line)])
    
    def _detect_code_issues(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect potential issues in code"""
        issues = []
        
        lines = code.split('\n')
        
        # Check for long lines
        for i, line in enumerate(lines):
            if len(line) > 120:
                issues.append({
                    "type": "style",
                    "severity": "low",
                    "line": i + 1,
                    "message": "Line too long (>120 characters)"
                })
        
        return issues
    
    def _generate_suggestions(
        self,
        code: str,
        language: str,
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if issues:
            suggestions.append("Consider addressing the detected code issues")
        
        if len(code.split('\n')) > 200:
            suggestions.append("Consider breaking down into smaller, more manageable functions")
        
        return suggestions
    
    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate code quality score (0-100)"""
        base_score = 100.0
        
        # Deduct points for issues
        for issue in analysis.get("issues", []):
            if issue["severity"] == "high":
                base_score -= 10
            elif issue["severity"] == "medium":
                base_score -= 5
            else:
                base_score -= 2
        
        return max(0.0, min(100.0, base_score))
    
    def _detect_changes(self, original: str, refactored: str) -> List[Dict[str, Any]]:
        """Detect changes between original and refactored code"""
        return [
            {
                "type": "line_count",
                "original": len(original.split('\n')),
                "refactored": len(refactored.split('\n'))
            }
        ]
    
    def _get_default_test_framework(self, language: str) -> str:
        """Get default test framework for language"""
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "java": "junit",
            "go": "testing"
        }
        return frameworks.get(language, "generic")
    
    def _count_test_cases(self, test_code: str, language: str) -> int:
        """Count test cases in test code"""
        if language == "python":
            return len(re.findall(r'def test_\w+', test_code))
        return 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get code generation statistics"""
        return {
            "agent_id": self.agent_id,
            "stats": self.generation_stats,
            "cache_size": len(self.code_cache)
        }
    
    async def get_checkpoint_state(self) -> Dict[str, Any]:
        """Save custom state for checkpointing"""
        return {
            "generation_stats": self.generation_stats,
            "cache_size": len(self.code_cache)
        }
    
    async def restore_checkpoint_state(self, state: Dict[str, Any]) -> None:
        """Restore custom state from checkpoint"""
        self.generation_stats = state.get("generation_stats", self.generation_stats)
