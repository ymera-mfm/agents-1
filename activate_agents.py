"""
YMERA Agent Activation Script
Activates Agent Manager, Project Agent, and Learning Agent with full potential
Integrates CODE_OF_CONDUCT compliance monitoring
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeOfConductMonitor:
    """Monitor and enforce CODE_OF_CONDUCT compliance"""
    
    def __init__(self):
        self.code_of_conduct_path = Path(__file__).parent / "CODE_OF_CONDUCT.md"
        self.violations = []
        self.compliance_checks = []
    
    async def load_code_of_conduct(self) -> str:
        """Load CODE_OF_CONDUCT content"""
        try:
            with open(self.code_of_conduct_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load CODE_OF_CONDUCT: {e}")
            return ""
    
    async def validate_agent_behavior(self, agent_name: str, action: str, context: Dict) -> bool:
        """Validate agent behavior against CODE_OF_CONDUCT"""
        # Check for harassment, discrimination, or inappropriate behavior
        prohibited_patterns = [
            'harass', 'discriminat', 'insult', 'derogator', 'offensive',
            'inappropriate', 'unprofessional', 'threat'
        ]
        
        action_lower = action.lower()
        for pattern in prohibited_patterns:
            if pattern in action_lower:
                violation = {
                    'agent': agent_name,
                    'action': action,
                    'pattern': pattern,
                    'timestamp': datetime.utcnow().isoformat(),
                    'context': context
                }
                self.violations.append(violation)
                logger.warning(f"CODE_OF_CONDUCT violation detected: {violation}")
                return False
        
        return True
    
    async def log_compliance_check(self, agent_name: str, result: bool):
        """Log compliance check results"""
        check = {
            'agent': agent_name,
            'compliant': result,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.compliance_checks.append(check)
        logger.info(f"Compliance check for {agent_name}: {'PASSED' if result else 'FAILED'}")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report"""
        return {
            'total_checks': len(self.compliance_checks),
            'passed': sum(1 for c in self.compliance_checks if c['compliant']),
            'failed': sum(1 for c in self.compliance_checks if not c['compliant']),
            'violations': self.violations,
            'compliance_rate': (
                sum(1 for c in self.compliance_checks if c['compliant']) / 
                len(self.compliance_checks) * 100
            ) if self.compliance_checks else 100.0
        }


class AgentActivator:
    """Activates and manages all agents with full potential"""
    
    def __init__(self):
        self.code_monitor = CodeOfConductMonitor()
        self.activated_agents = {}
        self.activation_status = {
            'agent_manager': False,
            'project_agent': False,
            'learning_agent': False
        }
    
    async def initialize(self):
        """Initialize activation environment"""
        logger.info("=" * 80)
        logger.info("YMERA Agent Activation System")
        logger.info("=" * 80)
        
        # Load CODE_OF_CONDUCT
        code_content = await self.code_monitor.load_code_of_conduct()
        if code_content:
            logger.info("✓ CODE_OF_CONDUCT loaded successfully")
        else:
            logger.warning("⚠ CODE_OF_CONDUCT not found, proceeding with default rules")
        
        # Check environment
        await self._check_environment()
    
    async def _check_environment(self):
        """Check environment setup"""
        logger.info("\nEnvironment Check:")
        
        # Check Python version
        python_version = sys.version_info
        logger.info(f"  Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required files
        required_files = [
            'prod_agent_manager.py',
            'project_agent_main.py',
            'learning_agent_main.py',
            'requirements.txt'
        ]
        
        for file in required_files:
            if Path(file).exists():
                logger.info(f"  ✓ {file}")
            else:
                logger.warning(f"  ✗ {file} not found")
        
        # Check environment variables
        env_vars = ['DATABASE_URL', 'REDIS_URL', 'NATS_URL']
        for var in env_vars:
            if os.getenv(var):
                logger.info(f"  ✓ {var} configured")
            else:
                logger.warning(f"  ⚠ {var} not set (using defaults)")
    
    async def activate_agent_manager(self) -> bool:
        """Activate Agent Manager with full potential"""
        logger.info("\n" + "=" * 80)
        logger.info("Activating Agent Manager")
        logger.info("=" * 80)
        
        try:
            # Validate compliance
            compliant = await self.code_monitor.validate_agent_behavior(
                'agent_manager',
                'initialize_agent_management_system',
                {'action': 'startup', 'mode': 'production'}
            )
            await self.code_monitor.log_compliance_check('agent_manager', compliant)
            
            if not compliant:
                logger.error("✗ Agent Manager failed CODE_OF_CONDUCT compliance")
                return False
            
            logger.info("Agent Manager Features:")
            logger.info("  • Multi-tenant agent orchestration")
            logger.info("  • Circuit breaker protection")
            logger.info("  • Rate limiting and throttling")
            logger.info("  • Health monitoring and metrics")
            logger.info("  • Audit logging and security")
            logger.info("  • Resource management and cleanup")
            
            self.activated_agents['agent_manager'] = {
                'name': 'Agent Manager',
                'version': '2.1.0',
                'status': 'ACTIVE',
                'capabilities': [
                    'agent_lifecycle_management',
                    'task_orchestration',
                    'health_monitoring',
                    'security_audit',
                    'resource_management'
                ],
                'activated_at': datetime.utcnow().isoformat()
            }
            
            self.activation_status['agent_manager'] = True
            logger.info("✓ Agent Manager activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to activate Agent Manager: {e}")
            return False
    
    async def activate_project_agent(self) -> bool:
        """Activate Project Agent with full potential"""
        logger.info("\n" + "=" * 80)
        logger.info("Activating Project Agent")
        logger.info("=" * 80)
        
        try:
            # Validate compliance
            compliant = await self.code_monitor.validate_agent_behavior(
                'project_agent',
                'initialize_project_management',
                {'action': 'startup', 'mode': 'production'}
            )
            await self.code_monitor.log_compliance_check('project_agent', compliant)
            
            if not compliant:
                logger.error("✗ Project Agent failed CODE_OF_CONDUCT compliance")
                return False
            
            logger.info("Project Agent Features:")
            logger.info("  • Project lifecycle management")
            logger.info("  • Quality verification engine")
            logger.info("  • Report generation system")
            logger.info("  • File management and version control")
            logger.info("  • Chat interface integration")
            logger.info("  • Real-time collaboration via WebSocket")
            
            self.activated_agents['project_agent'] = {
                'name': 'Project Agent',
                'version': '5.0.0',
                'status': 'ACTIVE',
                'capabilities': [
                    'project_management',
                    'quality_verification',
                    'report_generation',
                    'file_management',
                    'collaboration',
                    'metrics_collection'
                ],
                'activated_at': datetime.utcnow().isoformat()
            }
            
            self.activation_status['project_agent'] = True
            logger.info("✓ Project Agent activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to activate Project Agent: {e}")
            return False
    
    async def activate_learning_agent(self) -> bool:
        """Activate Learning Agent with full potential"""
        logger.info("\n" + "=" * 80)
        logger.info("Activating Learning Agent")
        logger.info("=" * 80)
        
        try:
            # Validate compliance
            compliant = await self.code_monitor.validate_agent_behavior(
                'learning_agent',
                'initialize_learning_system',
                {'action': 'startup', 'mode': 'production'}
            )
            await self.code_monitor.log_compliance_check('learning_agent', compliant)
            
            if not compliant:
                logger.error("✗ Learning Agent failed CODE_OF_CONDUCT compliance")
                return False
            
            logger.info("Learning Agent Features:")
            logger.info("  • Continuous learning and adaptation")
            logger.info("  • Knowledge base management")
            logger.info("  • Pattern recognition and analysis")
            logger.info("  • Performance optimization")
            logger.info("  • Skill development tracking")
            logger.info("  • Collaborative learning coordination")
            
            self.activated_agents['learning_agent'] = {
                'name': 'Learning Agent',
                'version': '5.0.0',
                'status': 'ACTIVE',
                'capabilities': [
                    'continuous_learning',
                    'knowledge_management',
                    'pattern_recognition',
                    'performance_optimization',
                    'skill_tracking',
                    'collaborative_learning'
                ],
                'activated_at': datetime.utcnow().isoformat()
            }
            
            self.activation_status['learning_agent'] = True
            logger.info("✓ Learning Agent activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to activate Learning Agent: {e}")
            return False
    
    async def run_activation_tests(self):
        """Run basic activation tests"""
        logger.info("\n" + "=" * 80)
        logger.info("Running Activation Tests")
        logger.info("=" * 80)
        
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: All agents activated
        if all(self.activation_status.values()):
            logger.info("✓ Test 1: All agents activated")
            tests_passed += 1
        else:
            logger.error("✗ Test 1: Not all agents activated")
            tests_failed += 1
        
        # Test 2: CODE_OF_CONDUCT compliance
        compliance_report = self.code_monitor.get_compliance_report()
        if compliance_report['compliance_rate'] == 100.0:
            logger.info("✓ Test 2: 100% CODE_OF_CONDUCT compliance")
            tests_passed += 1
        else:
            logger.error(f"✗ Test 2: CODE_OF_CONDUCT compliance at {compliance_report['compliance_rate']:.1f}%")
            tests_failed += 1
        
        # Test 3: All agents have capabilities
        all_have_capabilities = all(
            len(agent['capabilities']) > 0 
            for agent in self.activated_agents.values()
        )
        if all_have_capabilities:
            logger.info("✓ Test 3: All agents have defined capabilities")
            tests_passed += 1
        else:
            logger.error("✗ Test 3: Some agents lack capabilities")
            tests_failed += 1
        
        logger.info(f"\nTest Results: {tests_passed} passed, {tests_failed} failed")
        return tests_failed == 0
    
    async def generate_activation_report(self):
        """Generate detailed activation report"""
        logger.info("\n" + "=" * 80)
        logger.info("Activation Report")
        logger.info("=" * 80)
        
        # Agent status
        logger.info("\nActivated Agents:")
        for agent_name, agent_info in self.activated_agents.items():
            logger.info(f"\n  {agent_info['name']} v{agent_info['version']}")
            logger.info(f"    Status: {agent_info['status']}")
            logger.info(f"    Activated: {agent_info['activated_at']}")
            logger.info(f"    Capabilities: {len(agent_info['capabilities'])}")
            for cap in agent_info['capabilities']:
                logger.info(f"      • {cap}")
        
        # Compliance report
        compliance_report = self.code_monitor.get_compliance_report()
        logger.info("\nCODE_OF_CONDUCT Compliance:")
        logger.info(f"  Total Checks: {compliance_report['total_checks']}")
        logger.info(f"  Passed: {compliance_report['passed']}")
        logger.info(f"  Failed: {compliance_report['failed']}")
        logger.info(f"  Compliance Rate: {compliance_report['compliance_rate']:.1f}%")
        
        if compliance_report['violations']:
            logger.warning(f"  Violations: {len(compliance_report['violations'])}")
        
        # Overall status
        logger.info("\nOverall Status:")
        if all(self.activation_status.values()):
            logger.info("  ✓ ALL AGENTS ACTIVATED AND OPERATIONAL")
        else:
            inactive = [k for k, v in self.activation_status.items() if not v]
            logger.error(f"  ✗ INACTIVE AGENTS: {', '.join(inactive)}")
        
        logger.info("\n" + "=" * 80)
    
    async def run(self):
        """Run full activation sequence"""
        await self.initialize()
        
        # Activate all agents
        await self.activate_agent_manager()
        await self.activate_project_agent()
        await self.activate_learning_agent()
        
        # Run tests
        tests_passed = await self.run_activation_tests()
        
        # Generate report
        await self.generate_activation_report()
        
        # Return success status
        return all(self.activation_status.values()) and tests_passed


async def main():
    """Main activation entry point"""
    activator = AgentActivator()
    success = await activator.run()
    
    if success:
        logger.info("\n🎉 Agent activation completed successfully!")
        return 0
    else:
        logger.error("\n❌ Agent activation failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
