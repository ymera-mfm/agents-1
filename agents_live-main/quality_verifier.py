"""
Quality Verification Engine
Multi-criteria quality assessment for agent outputs
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .database import ProjectDatabase

logger = logging.getLogger(__name__)


class QualityVerificationEngine:
    """
    Quality Verification Engine
    
    Assesses agent outputs using multiple criteria:
    - Code quality (syntax, style, complexity)
    - Security (vulnerabilities, secrets)
    - Performance (benchmarks, metrics)
    - Documentation (completeness, clarity)
    """
    
    def __init__(self, settings, database: ProjectDatabase):
        self.settings = settings
        self.database = database
        self.is_initialized = False
        self.background_task = None
    
    async def initialize(self):
        """Initialize quality verification engine"""
        self.is_initialized = True
        logger.info("✓ Quality verification engine initialized")
    
    async def verify_submission(self, submission_id: str, submission_data: Dict) -> Dict:
        """
        Verify submission quality
        
        Returns:
            quality_score: float (0-100)
            passed: bool
            issues: List[Dict]
        """
        logger.info(f"Verifying submission {submission_id}")
        
        try:
            # Run all quality checks
            code_quality = await self._check_code_quality(submission_data)
            security_score = await self._check_security(submission_data)
            performance_score = await self._check_performance(submission_data)
            documentation_score = await self._check_documentation(submission_data)
            
            # Calculate weighted score
            quality_score = (
                self.settings.quality_code_weight * code_quality["score"] +
                self.settings.quality_security_weight * security_score["score"] +
                self.settings.quality_performance_weight * performance_score["score"] +
                self.settings.quality_documentation_weight * documentation_score["score"]
            )
            
            # Determine pass/fail
            passed = quality_score >= self.settings.quality_threshold
            
            # Collect all issues
            issues = []
            issues.extend(code_quality.get("issues", []))
            issues.extend(security_score.get("issues", []))
            issues.extend(performance_score.get("issues", []))
            issues.extend(documentation_score.get("issues", []))
            
            # Update submission status
            status = "approved" if passed else "rejected"
            message = f"Quality score: {quality_score:.1f}/100"
            
            if not passed:
                message += f" (threshold: {self.settings.quality_threshold})"
            
            await self.database.update_submission_status(
                submission_id,
                status,
                quality_score,
                issues,
                message
            )
            
            # Store detailed metrics
            await self._store_quality_metrics(submission_id, {
                "code_quality": code_quality,
                "security": security_score,
                "performance": performance_score,
                "documentation": documentation_score
            })
            
            return {
                "submission_id": submission_id,
                "quality_score": quality_score,
                "passed": passed,
                "status": status,
                "issues": issues,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Quality verification failed: {e}")
            await self.database.update_submission_status(
                submission_id,
                "error",
                None,
                [{"severity": "critical", "description": str(e)}],
                "Verification failed"
            )
            raise
    
    async def _check_code_quality(self, submission: Dict) -> Dict:
        """Check code quality metrics"""
        # Simplified implementation
        # In production, integrate pylint, flake8, radon, etc.
        
        issues = []
        score = 85.0  # Base score
        
        files = submission.get("files", [])
        
        # Check file count (too many or too few might indicate issues)
        if len(files) > 50:
            issues.append({
                "severity": "medium",
                "category": "code_quality",
                "description": f"Large number of files ({len(files)}). Consider modularity.",
                "suggestion": "Break into smaller modules"
            })
            score -= 5
        
        # Check for common patterns
        for file_info in files:
            content = file_info.get("content", "")
            
            # Check for TODO/FIXME
            if "TODO" in content or "FIXME" in content:
                issues.append({
                    "severity": "low",
                    "category": "code_quality",
                    "file": file_info.get("path"),
                    "description": "Contains TODO/FIXME comments",
                    "suggestion": "Complete todos before submission"
                })
                score -= 2
        
        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "details": {"file_count": len(files)}
        }
    
    async def _check_security(self, submission: Dict) -> Dict:
        """Check security vulnerabilities"""
        # Simplified implementation
        # In production, integrate bandit, safety, trivy, etc.
        
        issues = []
        score = 90.0  # Base score
        
        files = submission.get("files", [])
        
        # Check for common security issues
        dangerous_patterns = [
            ("eval(", "Use of eval() is dangerous"),
            ("exec(", "Use of exec() is dangerous"),
            ("pickle.loads", "pickle.loads is unsafe with untrusted data"),
            ("password", "Possible hardcoded password"),
            ("secret", "Possible hardcoded secret"),
        ]
        
        for file_info in files:
            content = file_info.get("content", "").lower()
            
            for pattern, description in dangerous_patterns:
                if pattern.lower() in content:
                    issues.append({
                        "severity": "high",
                        "category": "security",
                        "file": file_info.get("path"),
                        "description": description,
                        "suggestion": "Review and use secure alternatives"
                    })
                    score -= 10
        
        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "details": {"patterns_checked": len(dangerous_patterns)}
        }
    
    async def _check_performance(self, submission: Dict) -> Dict:
        """Check performance metrics"""
        # Simplified implementation
        # In production, run actual benchmarks
        
        issues = []
        score = 80.0  # Base score
        
        # Placeholder for actual performance testing
        # Would run benchmarks, measure memory usage, etc.
        
        return {
            "score": score,
            "issues": issues,
            "details": {"benchmarks_run": 0}
        }
    
    async def _check_documentation(self, submission: Dict) -> Dict:
        """Check documentation completeness"""
        # Simplified implementation
        
        issues = []
        score = 75.0  # Base score
        
        files = submission.get("files", [])
        
        # Check for docstrings in Python files
        for file_info in files:
            if file_info.get("path", "").endswith(".py"):
                content = file_info.get("content", "")
                
                # Very basic check for docstrings
                if '"""' not in content and "'''" not in content:
                    issues.append({
                        "severity": "medium",
                        "category": "documentation",
                        "file": file_info.get("path"),
                        "description": "Missing docstrings",
                        "suggestion": "Add module/function docstrings"
                    })
                    score -= 5
        
        return {
            "score": max(0, min(100, score)),
            "issues": issues,
            "details": {"files_checked": len(files)}
        }
    
    async def _store_quality_metrics(self, submission_id: str, metrics: Dict):
        """Store detailed quality metrics"""
        for metric_type, metric_data in metrics.items():
            await self.database.execute_command(
                """
                INSERT INTO quality_metrics 
                (submission_id, metric_type, metric_name, metric_value, passed, details)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                submission_id,
                metric_type,
                f"{metric_type}_score",
                metric_data["score"],
                metric_data["score"] >= 70,  # Pass threshold for individual metrics
                json.dumps(metric_data.get("details", {}))
            )
    
    async def get_detailed_feedback(self, submission_id: str) -> Dict:
        """Get detailed quality feedback"""
        submission = await self.database.get_submission(submission_id)
        
        if not submission:
            return None
        
        metrics = await self.database.execute_query(
            "SELECT * FROM quality_metrics WHERE submission_id = $1",
            submission_id
        )
        
        return {
            "submission_id": submission_id,
            "quality_score": submission.get("quality_score"),
            "status": submission.get("status"),
            "issues": json.loads(submission.get("issues", "[]")),
            "metrics": metrics,
            "timestamp": submission.get("updated_at")
        }
    
    async def get_project_metrics(self, project_id: str) -> Dict:
        """Get quality metrics for a project"""
        query = """
            SELECT 
                AVG(quality_score) as avg_quality_score,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
                COUNT(*) as total_submissions
            FROM agent_submissions
            WHERE project_id = $1
        """
        
        result = await self.database.execute_single(query, project_id)
        
        return {
            "avg_quality_score": float(result["avg_quality_score"] or 0),
            "approved_count": result["approved_count"],
            "rejected_count": result["rejected_count"],
            "total_submissions": result["total_submissions"],
            "approval_rate": (result["approved_count"] / result["total_submissions"] * 100) 
                           if result["total_submissions"] > 0 else 0
        }
    
    async def get_quality_trends(self, project_id: Optional[str], days: int) -> List[Dict]:
        """Get quality trends over time"""
        query = """
            SELECT 
                DATE(created_at) as date,
                AVG(quality_score) as avg_score,
                COUNT(*) as submission_count,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count
            FROM agent_submissions
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """ % days
        
        if project_id:
            query += f" AND project_id = '{project_id}'"
        
        query += """
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        
        return await self.database.execute_query(query)
    
    async def start_background_processing(self):
        """Start background processing of submissions"""
        # Placeholder for background task
        logger.info("Quality verification background processing started")
    
    async def health_check(self) -> bool:
        """Check quality verifier health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown quality verifier"""
        if self.background_task:
            self.background_task.cancel()
        logger.info("Quality verifier shutdown complete")

