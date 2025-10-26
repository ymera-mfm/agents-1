"""
Report Generator
Generate comprehensive reports for projects and quality metrics
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

try:
    from .database import ProjectDatabase
except ImportError:
    try:
        from database import ProjectDatabase
    except ImportError:
        # Stub for compatibility
        class ProjectDatabase:
            """Stub ProjectDatabase"""
            def __init__(self, *args, **kwargs):
                pass

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Report Generation System
    
    Features:
    - Project status reports
    - Quality trend analysis
    - Performance metrics
    - Export formats (JSON, PDF)
    """
    
    def __init__(self, settings, database: ProjectDatabase):
        self.settings = settings
        self.database = database
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize report generator"""
        self.is_initialized = True
        logger.info("✓ Report generator initialized")
    
    async def generate_project_report(
        self,
        project_id: str,
        report_type: str = "comprehensive",
        format: str = "json"
    ) -> Dict:
        """
        Generate project report
        
        Args:
            project_id: Project ID
            report_type: Type of report (comprehensive, summary, quality)
            format: Output format (json, pdf)
        
        Returns:
            Report data
        """
        logger.info(f"Generating {report_type} report for project {project_id}")
        
        # Get project data
        project = await self.database.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Build report based on type
        if report_type == "comprehensive":
            report = await self._generate_comprehensive_report(project)
        elif report_type == "summary":
            report = await self._generate_summary_report(project)
        elif report_type == "quality":
            report = await self._generate_quality_report(project)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Format report
        if format == "json":
            return report
        elif format == "pdf":
            return await self._export_to_pdf(report)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    async def _generate_comprehensive_report(self, project: Dict) -> Dict:
        """Generate comprehensive project report"""
        # Get submissions
        submissions = await self.database.execute_query(
            """
            SELECT status, COUNT(*) as count, AVG(quality_score) as avg_score
            FROM agent_submissions
            WHERE project_id = $1
            GROUP BY status
            """,
            project["id"]
        )
        
        # Get quality metrics
        quality_metrics = await self.database.execute_query(
            """
            SELECT 
                metric_type,
                AVG(metric_value) as avg_value,
                COUNT(*) as count
            FROM quality_metrics qm
            JOIN agent_submissions s ON qm.submission_id = s.id
            WHERE s.project_id = $1
            GROUP BY metric_type
            """,
            project["id"]
        )
        
        # Get timeline
        timeline = await self.database.execute_query(
            """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as submissions
            FROM agent_submissions
            WHERE project_id = $1
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 30
            """,
            project["id"]
        )
        
        return {
            "project": {
                "id": str(project["id"]),
                "name": project["name"],
                "description": project["description"],
                "status": project["status"],
                "progress": float(project.get("progress", 0)),
                "created_at": project["created_at"].isoformat(),
                "updated_at": project["updated_at"].isoformat()
            },
            "submissions": {
                "by_status": [dict(row) for row in submissions],
                "total": sum(row["count"] for row in submissions)
            },
            "quality_metrics": [dict(row) for row in quality_metrics],
            "timeline": [dict(row) for row in timeline],
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "comprehensive"
        }
    
    async def _generate_summary_report(self, project: Dict) -> Dict:
        """Generate summary report"""
        # Get basic stats
        stats = await self.database.execute_single(
            """
            SELECT 
                COUNT(*) as total_submissions,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                AVG(quality_score) as avg_quality_score
            FROM agent_submissions
            WHERE project_id = $1
            """,
            project["id"]
        )
        
        return {
            "project_id": str(project["id"]),
            "name": project["name"],
            "status": project["status"],
            "progress": float(project.get("progress", 0)),
            "statistics": dict(stats) if stats else {},
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "summary"
        }
    
    async def _generate_quality_report(self, project: Dict) -> Dict:
        """Generate quality-focused report"""
        # Get quality trends
        trends = await self.database.execute_query(
            """
            SELECT 
                DATE(s.created_at) as date,
                AVG(s.quality_score) as avg_quality_score,
                COUNT(*) as submission_count,
                COUNT(CASE WHEN s.status = 'approved' THEN 1 END) as approved_count
            FROM agent_submissions s
            WHERE s.project_id = $1 AND s.quality_score IS NOT NULL
            GROUP BY DATE(s.created_at)
            ORDER BY date DESC
            LIMIT 30
            """,
            project["id"]
        )
        
        # Get issue breakdown
        issues = await self.database.execute_query(
            """
            SELECT 
                s.issues::text,
                COUNT(*) as count
            FROM agent_submissions s
            WHERE s.project_id = $1 AND s.issues IS NOT NULL
            GROUP BY s.issues::text
            LIMIT 10
            """,
            project["id"]
        )
        
        return {
            "project_id": str(project["id"]),
            "name": project["name"],
            "quality_trends": [dict(row) for row in trends],
            "common_issues": [dict(row) for row in issues],
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "quality"
        }
    
    async def _export_to_pdf(self, report: Dict) -> bytes:
        """Export report to PDF"""
        # Simplified - would use reportlab or weasyprint in production
        logger.info("PDF export not yet implemented")
        
        import json
        # Return JSON as bytes for now
        return json.dumps(report, indent=2).encode()
    
    async def health_check(self) -> bool:
        """Check report generator health"""
        return self.is_initialized
    
    async def shutdown(self):
        """Shutdown report generator"""
        logger.info("Report generator shutdown complete")

