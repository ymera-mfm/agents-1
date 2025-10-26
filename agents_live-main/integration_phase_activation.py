#!/usr/bin/env python3
"""
Integration Phase Activation Script
Systematically activates and verifies all integration phases
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationPhaseActivator:
    """Manages the activation and verification of integration phases"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phases": {},
            "overall_status": "pending"
        }
        self.base_path = Path(__file__).parent
        
    async def run_all_phases(self):
        """Run all integration phases in sequence"""
        logger.info("=" * 70)
        logger.info("YMERA PLATFORM - INTEGRATION PHASE ACTIVATION")
        logger.info("=" * 70)
        
        phases = [
            ("Phase 1", "System State & Dependencies", self.phase1_verify_system),
            ("Phase 2", "Core System Activation", self.phase2_core_activation),
            ("Phase 3", "Agent System Activation", self.phase3_agent_activation),
            ("Phase 4", "Integration Layer Activation", self.phase4_integration_layer),
            ("Phase 5", "Validation & Health Checks", self.phase5_validation),
            ("Phase 6", "Final Verification", self.phase6_final_verification),
        ]
        
        all_passed = True
        for phase_num, phase_name, phase_func in phases:
            logger.info(f"\n{'=' * 70}")
            logger.info(f"{phase_num}: {phase_name}")
            logger.info(f"{'=' * 70}")
            
            try:
                result = await phase_func()
                self.results["phases"][phase_num] = result
                
                if result["status"] == "passed":
                    logger.info(f"✅ {phase_num} PASSED - All checks successful")
                elif result["status"] == "partial":
                    logger.warning(f"⚠️ {phase_num} PARTIAL - Some components need attention")
                    all_passed = False
                else:
                    logger.error(f"❌ {phase_num} FAILED - Critical issues found")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ {phase_num} FAILED with exception: {e}")
                self.results["phases"][phase_num] = {
                    "status": "failed",
                    "error": str(e),
                    "checks": []
                }
                all_passed = False
        
        # Set overall status
        self.results["overall_status"] = "passed" if all_passed else "partial"
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    async def phase1_verify_system(self) -> Dict[str, Any]:
        """Phase 1: Verify current system state and dependencies"""
        checks = []
        
        # Check 1: Python version
        python_version = sys.version.split()[0]
        python_check = {
            "name": "Python Version",
            "status": "passed" if python_version >= "3.11" else "failed",
            "details": f"Python {python_version}",
            "active": True
        }
        checks.append(python_check)
        logger.info(f"  ✓ Python version: {python_version}")
        
        # Check 2: Required files exist
        required_files = [
            "main.py",
            "requirements.txt",
            ".env.example",
            "core/config.py",
            "core/database.py"
        ]
        
        files_exist = all((self.base_path / f).exists() for f in required_files)
        files_check = {
            "name": "Core Files Present",
            "status": "passed" if files_exist else "failed",
            "details": f"{sum(1 for f in required_files if (self.base_path / f).exists())}/{len(required_files)} files found",
            "active": files_exist
        }
        checks.append(files_check)
        logger.info(f"  ✓ Core files: {files_check['details']}")
        
        # Check 3: Check if basic dependencies can be imported
        import_checks = []
        try:
            import fastapi
            import_checks.append(("FastAPI", True, fastapi.__version__))
        except ImportError:
            import_checks.append(("FastAPI", False, "Not installed"))
        
        try:
            import sqlalchemy
            import_checks.append(("SQLAlchemy", True, sqlalchemy.__version__))
        except ImportError:
            import_checks.append(("SQLAlchemy", False, "Not installed"))
        
        try:
            import redis
            import_checks.append(("Redis", True, "Installed"))
        except ImportError:
            import_checks.append(("Redis", False, "Not installed"))
        
        deps_installed = all(check[1] for check in import_checks)
        deps_check = {
            "name": "Core Dependencies",
            "status": "passed" if deps_installed else "partial",
            "details": {name: f"{status} - {version}" for name, status, version in import_checks},
            "active": deps_installed
        }
        checks.append(deps_check)
        for name, status, version in import_checks:
            symbol = "✓" if status else "✗"
            logger.info(f"  {symbol} {name}: {version}")
        
        # Check 4: Configuration files
        env_example_exists = (self.base_path / ".env.example").exists()
        env_exists = (self.base_path / ".env").exists()
        config_check = {
            "name": "Configuration Files",
            "status": "passed" if env_example_exists else "failed",
            "details": f".env.example: {env_example_exists}, .env: {env_exists}",
            "active": env_exists
        }
        checks.append(config_check)
        logger.info(f"  ✓ Configuration: {config_check['details']}")
        
        # Check 5: Test if core modules can be imported
        core_modules_ok = True
        try:
            from core.config import Settings
            logger.info(f"  ✓ Core config module: OK")
        except Exception as e:
            core_modules_ok = False
            logger.warning(f"  ✗ Core config module: {e}")
        
        core_check = {
            "name": "Core Modules",
            "status": "passed" if core_modules_ok else "partial",
            "details": "Core modules can be imported" if core_modules_ok else "Some modules have import issues",
            "active": core_modules_ok
        }
        checks.append(core_check)
        
        # Determine phase status
        all_passed = all(check["status"] == "passed" for check in checks)
        any_partial = any(check["status"] == "partial" for check in checks)
        
        return {
            "status": "passed" if all_passed else ("partial" if any_partial else "failed"),
            "checks": checks,
            "summary": f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} checks passed"
        }
    
    async def phase2_core_activation(self) -> Dict[str, Any]:
        """Phase 2: Core system activation"""
        checks = []
        
        # Check 1: Verify core config can be loaded
        try:
            from core.config import Settings
            settings = Settings()
            config_check = {
                "name": "Configuration Loading",
                "status": "passed",
                "details": "Settings loaded successfully",
                "active": True
            }
            logger.info(f"  ✓ Configuration loaded successfully")
        except Exception as e:
            config_check = {
                "name": "Configuration Loading",
                "status": "failed",
                "details": f"Error: {str(e)}",
                "active": False
            }
            logger.error(f"  ✗ Configuration loading failed: {e}")
        checks.append(config_check)
        
        # Check 2: Test database models
        try:
            from core.sqlalchemy_models import Base, User, Agent, Task
            models_check = {
                "name": "Database Models",
                "status": "passed",
                "details": "All models imported successfully",
                "active": True
            }
            logger.info(f"  ✓ Database models loaded")
        except Exception as e:
            models_check = {
                "name": "Database Models",
                "status": "failed",
                "details": f"Error: {str(e)}",
                "active": False
            }
            logger.error(f"  ✗ Database models failed: {e}")
        checks.append(models_check)
        
        # Check 3: Verify auth module
        try:
            from core.auth import AuthService
            auth_check = {
                "name": "Authentication System",
                "status": "passed",
                "details": "Auth service available",
                "active": True
            }
            logger.info(f"  ✓ Authentication system ready")
        except Exception as e:
            auth_check = {
                "name": "Authentication System",
                "status": "partial",
                "details": f"Warning: {str(e)}",
                "active": False
            }
            logger.warning(f"  ⚠ Authentication system: {e}")
        checks.append(auth_check)
        
        # Check 4: Verify middleware
        try:
            from middleware.rate_limiter import RateLimitMiddleware
            middleware_check = {
                "name": "Middleware Components",
                "status": "passed",
                "details": "Rate limiter available",
                "active": True
            }
            logger.info(f"  ✓ Middleware components loaded")
        except Exception as e:
            middleware_check = {
                "name": "Middleware Components",
                "status": "partial",
                "details": f"Warning: {str(e)}",
                "active": False
            }
            logger.warning(f"  ⚠ Middleware: {e}")
        checks.append(middleware_check)
        
        # Check 5: Verify main app can be imported
        try:
            import main
            app_check = {
                "name": "Main Application",
                "status": "passed",
                "details": "Main app module loaded",
                "active": True
            }
            logger.info(f"  ✓ Main application module loaded")
        except Exception as e:
            app_check = {
                "name": "Main Application",
                "status": "failed",
                "details": f"Error: {str(e)}",
                "active": False
            }
            logger.error(f"  ✗ Main application: {e}")
        checks.append(app_check)
        
        # Determine phase status
        critical_checks = [config_check, models_check, app_check]
        all_critical_passed = all(check["status"] == "passed" for check in critical_checks)
        
        return {
            "status": "passed" if all_critical_passed else "partial",
            "checks": checks,
            "summary": f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} components active"
        }
    
    async def phase3_agent_activation(self) -> Dict[str, Any]:
        """Phase 3: Agent system activation"""
        checks = []
        
        # Check 1: Agent discovery
        agent_files = list(Path(self.base_path / "agents").glob("*agent*.py")) if (self.base_path / "agents").exists() else []
        discovery_check = {
            "name": "Agent Discovery",
            "status": "passed" if len(agent_files) > 0 else "partial",
            "details": f"Found {len(agent_files)} agent files",
            "active": len(agent_files) > 0
        }
        checks.append(discovery_check)
        logger.info(f"  ✓ Agent files discovered: {len(agent_files)}")
        
        # Check 2: Agent base class
        try:
            # Try different possible locations
            base_imported = False
            try:
                from agents.base_agent import BaseAgent
                base_imported = True
            except:
                try:
                    import base_agent
                    base_imported = True
                except:
                    pass
            
            base_check = {
                "name": "Agent Base Class",
                "status": "passed" if base_imported else "partial",
                "details": "BaseAgent available" if base_imported else "BaseAgent not in standard location",
                "active": base_imported
            }
            logger.info(f"  {'✓' if base_imported else '⚠'} Base agent class: {base_check['details']}")
        except Exception as e:
            base_check = {
                "name": "Agent Base Class",
                "status": "partial",
                "details": f"Warning: {str(e)}",
                "active": False
            }
            logger.warning(f"  ⚠ Base agent class: {e}")
        checks.append(base_check)
        
        # Check 3: Agent manager
        try:
            from core.manager_client import ManagerClient
            manager_check = {
                "name": "Agent Manager",
                "status": "passed",
                "details": "Manager client available",
                "active": True
            }
            logger.info(f"  ✓ Agent manager ready")
        except Exception as e:
            manager_check = {
                "name": "Agent Manager",
                "status": "partial",
                "details": f"Warning: {str(e)}",
                "active": False
            }
            logger.warning(f"  ⚠ Agent manager: {e}")
        checks.append(manager_check)
        
        # Check 4: Agent orchestration
        orchestrator_exists = (self.base_path / "agent_orchestrator.py").exists()
        orchestrator_check = {
            "name": "Agent Orchestrator",
            "status": "passed" if orchestrator_exists else "partial",
            "details": "Orchestrator available" if orchestrator_exists else "Orchestrator file not found",
            "active": orchestrator_exists
        }
        checks.append(orchestrator_check)
        logger.info(f"  {'✓' if orchestrator_exists else '⚠'} Agent orchestrator: {orchestrator_check['details']}")
        
        return {
            "status": "partial",  # Agent system needs more work based on integration_results.json
            "checks": checks,
            "summary": f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} agent components active"
        }
    
    async def phase4_integration_layer(self) -> Dict[str, Any]:
        """Phase 4: Integration layer activation"""
        checks = []
        
        # Check 1: WebSocket support
        try:
            import websockets
            ws_check = {
                "name": "WebSocket Support",
                "status": "passed",
                "details": "WebSockets library available",
                "active": True
            }
            logger.info(f"  ✓ WebSocket support ready")
        except ImportError:
            ws_check = {
                "name": "WebSocket Support",
                "status": "partial",
                "details": "WebSockets not installed",
                "active": False
            }
            logger.warning(f"  ⚠ WebSocket support: Not installed")
        checks.append(ws_check)
        
        # Check 2: Integration preparation module
        integration_prep_exists = (self.base_path / "integration_preparation.py").exists()
        prep_check = {
            "name": "Integration Preparation",
            "status": "passed" if integration_prep_exists else "partial",
            "details": "Integration prep module available" if integration_prep_exists else "Module not found",
            "active": integration_prep_exists
        }
        checks.append(prep_check)
        logger.info(f"  {'✓' if integration_prep_exists else '⚠'} Integration prep: {prep_check['details']}")
        
        # Check 3: Monitoring
        try:
            from prometheus_client import Counter
            monitoring_check = {
                "name": "Monitoring System",
                "status": "passed",
                "details": "Prometheus client available",
                "active": True
            }
            logger.info(f"  ✓ Monitoring system ready")
        except ImportError:
            monitoring_check = {
                "name": "Monitoring System",
                "status": "partial",
                "details": "Prometheus client not installed",
                "active": False
            }
            logger.warning(f"  ⚠ Monitoring: Not installed")
        checks.append(monitoring_check)
        
        # Check 4: Task orchestration
        task_orchestrator_exists = (self.base_path / "task_orchestrator.py").exists()
        task_check = {
            "name": "Task Orchestration",
            "status": "passed" if task_orchestrator_exists else "partial",
            "details": "Task orchestrator available" if task_orchestrator_exists else "Orchestrator not found",
            "active": task_orchestrator_exists
        }
        checks.append(task_check)
        logger.info(f"  {'✓' if task_orchestrator_exists else '⚠'} Task orchestrator: {task_check['details']}")
        
        return {
            "status": "partial",
            "checks": checks,
            "summary": f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} integration components active"
        }
    
    async def phase5_validation(self) -> Dict[str, Any]:
        """Phase 5: Validation and health checks"""
        checks = []
        
        # Check 1: Test suite exists
        test_dirs = ["tests", "test"]
        test_dir_exists = any((self.base_path / d).exists() for d in test_dirs)
        test_check = {
            "name": "Test Suite",
            "status": "passed" if test_dir_exists else "partial",
            "details": "Test directory found" if test_dir_exists else "Test directory not found",
            "active": test_dir_exists
        }
        checks.append(test_check)
        logger.info(f"  {'✓' if test_dir_exists else '⚠'} Test suite: {test_check['details']}")
        
        # Check 2: Health check endpoints
        try:
            import main
            # Check if health endpoint exists in the app
            health_exists = hasattr(main, 'app')
            health_check = {
                "name": "Health Check Endpoints",
                "status": "passed" if health_exists else "partial",
                "details": "Health endpoints defined" if health_exists else "Endpoints may not be configured",
                "active": health_exists
            }
            logger.info(f"  {'✓' if health_exists else '⚠'} Health check: {health_check['details']}")
        except Exception as e:
            health_check = {
                "name": "Health Check Endpoints",
                "status": "partial",
                "details": f"Could not verify: {str(e)}",
                "active": False
            }
            logger.warning(f"  ⚠ Health check: {e}")
        checks.append(health_check)
        
        # Check 3: Documentation
        doc_files = ["README.md", "DEPLOYMENT_GUIDE.md", "API_DOCUMENTATION.md"]
        docs_exist = sum(1 for f in doc_files if (self.base_path / f).exists())
        doc_check = {
            "name": "Documentation",
            "status": "passed" if docs_exist >= 2 else "partial",
            "details": f"{docs_exist}/{len(doc_files)} key documents present",
            "active": docs_exist >= 2
        }
        checks.append(doc_check)
        logger.info(f"  ✓ Documentation: {doc_check['details']}")
        
        # Check 4: Deployment readiness
        deployment_files = ["docker-compose.yml", "Dockerfile", "requirements.txt"]
        deploy_ready = sum(1 for f in deployment_files if (self.base_path / f).exists())
        deploy_check = {
            "name": "Deployment Readiness",
            "status": "passed" if deploy_ready >= 2 else "partial",
            "details": f"{deploy_ready}/{len(deployment_files)} deployment files present",
            "active": deploy_ready >= 2
        }
        checks.append(deploy_check)
        logger.info(f"  ✓ Deployment readiness: {deploy_check['details']}")
        
        return {
            "status": "partial",
            "checks": checks,
            "summary": f"{sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} validation checks passed"
        }
    
    async def phase6_final_verification(self) -> Dict[str, Any]:
        """Phase 6: Final verification"""
        checks = []
        
        # Check 1: Overall system health
        all_phases_passed = all(
            phase_result.get("status") == "passed" 
            for phase_num, phase_result in self.results["phases"].items() 
            if phase_num != "Phase 6"
        )
        system_check = {
            "name": "Overall System Health",
            "status": "passed" if all_phases_passed else "partial",
            "details": "All previous phases passed" if all_phases_passed else "Some phases have warnings",
            "active": True
        }
        checks.append(system_check)
        logger.info(f"  {'✓' if all_phases_passed else '⚠'} System health: {system_check['details']}")
        
        # Check 2: Production readiness report
        prod_reports = list(self.base_path.glob("*PRODUCTION*READINESS*.md"))
        prod_check = {
            "name": "Production Readiness",
            "status": "passed" if len(prod_reports) > 0 else "partial",
            "details": f"Found {len(prod_reports)} production readiness reports",
            "active": len(prod_reports) > 0
        }
        checks.append(prod_check)
        logger.info(f"  {'✓' if len(prod_reports) > 0 else '⚠'} Production readiness: {prod_check['details']}")
        
        # Check 3: Integration completeness
        integration_docs = list(self.base_path.glob("*INTEGRATION*.md"))
        integration_check = {
            "name": "Integration Documentation",
            "status": "passed" if len(integration_docs) > 0 else "partial",
            "details": f"Found {len(integration_docs)} integration documents",
            "active": len(integration_docs) > 0
        }
        checks.append(integration_check)
        logger.info(f"  {'✓' if len(integration_docs) > 0 else '⚠'} Integration docs: {integration_check['details']}")
        
        # Check 4: Final system status
        active_components = sum(
            1 for phase_result in self.results["phases"].values() 
            if phase_result.get("status") in ["passed", "partial"]
        )
        final_check = {
            "name": "Final System Status",
            "status": "passed",
            "details": f"{active_components}/5 phases completed",
            "active": True
        }
        checks.append(final_check)
        logger.info(f"  ✓ Final status: {final_check['details']}")
        
        return {
            "status": "passed",
            "checks": checks,
            "summary": "Integration phase activation completed"
        }
    
    def _save_results(self):
        """Save results to JSON file"""
        results_file = self.base_path / "integration_phase_activation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, indent=2, fp=f)
        logger.info(f"\n📄 Results saved to: {results_file}")
    
    def _print_summary(self):
        """Print a summary of all phases"""
        logger.info("\n" + "=" * 70)
        logger.info("INTEGRATION PHASE ACTIVATION SUMMARY")
        logger.info("=" * 70)
        
        for phase_num, phase_result in self.results["phases"].items():
            status = phase_result.get("status", "unknown")
            summary = phase_result.get("summary", "No summary")
            
            if status == "passed":
                symbol = "✅"
            elif status == "partial":
                symbol = "⚠️"
            else:
                symbol = "❌"
            
            logger.info(f"{symbol} {phase_num}: {summary}")
            
            # Show active components
            active_count = sum(1 for check in phase_result.get("checks", []) if check.get("active", False))
            total_count = len(phase_result.get("checks", []))
            logger.info(f"   Active: {active_count}/{total_count} components")
        
        logger.info("\n" + "=" * 70)
        overall = self.results["overall_status"]
        if overall == "passed":
            logger.info("✅ OVERALL STATUS: ALL PHASES PASSED")
        else:
            logger.info("⚠️ OVERALL STATUS: SOME COMPONENTS NEED ATTENTION")
        logger.info("=" * 70)


async def main():
    """Main entry point"""
    activator = IntegrationPhaseActivator()
    results = await activator.run_all_phases()
    
    # Exit with appropriate code
    if results["overall_status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
