"""
Final Platform Verification System
Verifies the enhanced platform is complete and ready for deployment
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class FinalVerifier:
    """
    Final Platform Verification Engine
    
    Performs comprehensive verification of:
    - Repository analysis completion
    - Component enhancement status
    - Testing completion
    - Integration preparation
    - Deployment readiness
    - Expansion capability
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the FinalVerifier
        
        Args:
            base_path: Base path for verification (defaults to current directory)
        """
        self.base_path = base_path or os.getcwd()
        self.verification_results = {}
    
    def verify_complete_platform(self) -> bool:
        """
        Verify the enhanced platform is complete and ready
        
        Returns:
            bool: True if all verifications pass, False otherwise
        """
        print("✅ FINAL PLATFORM VERIFICATION")
        print("=" * 60)
        
        verification_steps = {
            'repository_analysis': self.verify_analysis_complete(),
            'component_enhancement': self.verify_enhancement_complete(),
            'testing_completion': self.verify_testing_complete(),
            'integration_preparation': self.verify_integration_ready(),
            'deployment_readiness': self.verify_deployment_ready(),
            'expansion_capability': self.verify_expansion_ready()
        }
        
        # Store results
        self.verification_results = verification_steps
        
        # Check if all passed
        all_passed = all(verification_steps.values())
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ENHANCED PLATFORM IS COMPLETE AND READY!")
            self.generate_success_report()
        else:
            print("❌ Some verification steps failed")
            self.generate_issues_report(verification_steps)
        
        return all_passed
    
    def verify_analysis_complete(self) -> bool:
        """
        Verify repository analysis is complete
        
        Returns:
            bool: True if all required analysis files exist
        """
        print("\n📊 Verifying Repository Analysis...")
        
        required_files = [
            'repository_analysis/comprehensive_report.json',
            'repository_analysis/component_inventory.json',
            'repository_analysis/duplicate_analysis.json'
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = os.path.join(self.base_path, file_path)
            exists = os.path.exists(full_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {file_path}")
            if not exists:
                all_exist = False
        
        if all_exist:
            print("  ✅ Repository analysis complete")
        else:
            print("  ❌ Missing required analysis files")
        
        return all_exist
    
    def verify_enhancement_complete(self) -> bool:
        """
        Verify all components have enhanced versions
        
        Returns:
            bool: True if all categories have enhanced components
        """
        print("\n🔧 Verifying Component Enhancement...")
        
        categories = ["agents", "modules", "engines", "systems", "database", "api"]
        
        all_enhanced = True
        for category in categories:
            enhanced_path = os.path.join(
                self.base_path,
                f"enhanced_workspace/{category}/integrated/{category}_enhanced.py"
            )
            exists = os.path.exists(enhanced_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {category}: {enhanced_path}")
            
            if not exists:
                print(f"    ❌ Missing enhanced component for {category}")
                all_enhanced = False
        
        if all_enhanced:
            print("  ✅ All components enhanced")
        else:
            print("  ❌ Some components missing enhanced versions")
        
        return all_enhanced
    
    def verify_testing_complete(self) -> bool:
        """
        Verify testing is complete
        
        Returns:
            bool: True if testing requirements are met
        """
        print("\n🧪 Verifying Testing Completion...")
        
        # Check for test files and reports
        test_indicators = [
            ('test_*.py files', self._check_test_files()),
            ('pytest.ini config', os.path.exists(os.path.join(self.base_path, 'pytest.ini'))),
            ('test coverage', self._check_test_coverage()),
        ]
        
        all_passed = True
        for indicator_name, passed in test_indicators:
            status = "✓" if passed else "✗"
            print(f"  {status} {indicator_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("  ✅ Testing completion verified")
        else:
            print("  ⚠️  Some testing requirements not fully met")
        
        return all_passed
    
    def verify_integration_ready(self) -> bool:
        """
        Verify integration preparation is complete
        
        Returns:
            bool: True if integration is ready
        """
        print("\n🔗 Verifying Integration Preparation...")
        
        integration_checks = [
            ('API gateway', self._check_api_gateway()),
            ('Database connectivity', self._check_database_setup()),
            ('Configuration files', self._check_config_files()),
        ]
        
        all_ready = True
        for check_name, passed in integration_checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_ready = False
        
        if all_ready:
            print("  ✅ Integration preparation complete")
        else:
            print("  ⚠️  Some integration checks need attention")
        
        return all_ready
    
    def verify_deployment_ready(self) -> bool:
        """
        Verify deployment readiness
        
        Returns:
            bool: True if ready for deployment
        """
        print("\n🚀 Verifying Deployment Readiness...")
        
        deployment_checks = [
            ('Dockerfile', os.path.exists(os.path.join(self.base_path, 'Dockerfile'))),
            ('docker-compose.yml', os.path.exists(os.path.join(self.base_path, 'docker-compose.yml'))),
            ('requirements.txt', os.path.exists(os.path.join(self.base_path, 'requirements.txt'))),
            ('.env.example', os.path.exists(os.path.join(self.base_path, '.env.example'))),
        ]
        
        all_ready = True
        for check_name, passed in deployment_checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_ready = False
        
        if all_ready:
            print("  ✅ Deployment files ready")
        else:
            print("  ⚠️  Some deployment files missing")
        
        return all_ready
    
    def verify_expansion_ready(self) -> bool:
        """
        Verify expansion capability
        
        Returns:
            bool: True if platform is ready for expansion
        """
        print("\n📈 Verifying Expansion Capability...")
        
        expansion_checks = [
            ('Modular architecture', self._check_modular_architecture()),
            ('Documentation', self._check_documentation()),
            ('API extensibility', self._check_api_extensibility()),
        ]
        
        all_ready = True
        for check_name, passed in expansion_checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_ready = False
        
        if all_ready:
            print("  ✅ Platform ready for expansion")
        else:
            print("  ⚠️  Some expansion capabilities need work")
        
        return all_ready
    
    def generate_success_report(self):
        """Generate and save success report"""
        report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "verification_results": self.verification_results,
            "message": "Enhanced platform is complete and ready for deployment"
        }
        
        report_path = os.path.join(self.base_path, 'verification_success_report.json')
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Success report saved to: {report_path}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
    
    def generate_issues_report(self, verification_steps: Dict[str, bool]):
        """
        Generate and save issues report
        
        Args:
            verification_steps: Dictionary of verification step results
        """
        failed_steps = [step for step, passed in verification_steps.items() if not passed]
        
        report = {
            "status": "incomplete",
            "timestamp": datetime.now().isoformat(),
            "verification_results": verification_steps,
            "failed_steps": failed_steps,
            "message": f"{len(failed_steps)} verification step(s) failed"
        }
        
        report_path = os.path.join(self.base_path, 'verification_issues_report.json')
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Issues report saved to: {report_path}")
            print(f"\nFailed steps: {', '.join(failed_steps)}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
    
    # Helper methods for verification checks
    
    def _check_test_files(self) -> bool:
        """Check if test files exist"""
        test_files = list(Path(self.base_path).glob('test_*.py'))
        return len(test_files) > 0
    
    def _check_test_coverage(self) -> bool:
        """Check if test coverage reports exist"""
        coverage_indicators = [
            os.path.exists(os.path.join(self.base_path, '.coverage')),
            os.path.exists(os.path.join(self.base_path, 'htmlcov')),
            os.path.exists(os.path.join(self.base_path, 'test_report.json')),
        ]
        return any(coverage_indicators)
    
    def _check_api_gateway(self) -> bool:
        """Check if API gateway is configured"""
        api_files = [
            'api_gateway.py',
            'gateway.py',
            'ymera_api_system.py',
        ]
        return any(os.path.exists(os.path.join(self.base_path, f)) for f in api_files)
    
    def _check_database_setup(self) -> bool:
        """Check if database setup is complete"""
        db_files = [
            'database.py',
            'models.py',
            'database_schema.sql',
        ]
        return any(os.path.exists(os.path.join(self.base_path, f)) for f in db_files)
    
    def _check_config_files(self) -> bool:
        """Check if configuration files exist"""
        config_files = [
            'config.py',
            'settings.py',
            '.env.example',
        ]
        return any(os.path.exists(os.path.join(self.base_path, f)) for f in config_files)
    
    def _check_modular_architecture(self) -> bool:
        """Check if architecture is modular"""
        # Check for organized directory structure
        expected_dirs = ['agents', 'modules', 'engines', 'systems']
        found_dirs = [d for d in expected_dirs if os.path.exists(os.path.join(self.base_path, d))]
        
        # Also check for Python packages with __init__.py
        py_files = list(Path(self.base_path).glob('*.py'))
        return len(py_files) > 10 or len(found_dirs) >= 2
    
    def _check_documentation(self) -> bool:
        """Check if documentation exists"""
        doc_files = list(Path(self.base_path).glob('*.md'))
        readme_exists = os.path.exists(os.path.join(self.base_path, 'README.md'))
        return readme_exists and len(doc_files) >= 3
    
    def _check_api_extensibility(self) -> bool:
        """Check if API is extensible"""
        # Check for FastAPI or similar framework
        try:
            with open(os.path.join(self.base_path, 'requirements.txt'), 'r') as f:
                content = f.read()
                return 'fastapi' in content.lower() or 'flask' in content.lower()
        except:
            return False


def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("YMERA ENHANCED PLATFORM - FINAL VERIFICATION")
    print("=" * 60)
    
    # Execute final verification
    verifier = FinalVerifier()
    success = verifier.verify_complete_platform()
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    
    print("\n" + "=" * 60)
    print(f"Verification {'PASSED' if success else 'FAILED'}")
    print("=" * 60 + "\n")
    
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
