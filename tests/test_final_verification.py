"""
Test Suite for Final Platform Verification
Tests the FinalVerifier class and all verification methods
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from final_verification import FinalVerifier


def test_verifier_initialization():
    """Test 1: Verifier Initialization"""
    print("\n" + "="*60)
    print("TEST 1: Verifier Initialization")
    print("="*60)
    
    try:
        verifier = FinalVerifier()
        assert verifier.verification_results == {}
        assert verifier.base_path is not None
        print("✓ Verifier initialized successfully")
        print("\n✅ TEST 1 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}\n")
        return False


def test_repository_analysis_verification():
    """Test 2: Repository Analysis Verification"""
    print("\n" + "="*60)
    print("TEST 2: Repository Analysis Verification")
    print("="*60)
    
    try:
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FinalVerifier(base_path=tmpdir)
            
            # Should fail without files
            result = verifier.verify_analysis_complete()
            assert result is False, "Should fail without analysis files"
            print("✓ Correctly identified missing analysis files")
            
            # Create required files
            os.makedirs(os.path.join(tmpdir, 'repository_analysis'), exist_ok=True)
            
            required_files = [
                'comprehensive_report.json',
                'component_inventory.json',
                'duplicate_analysis.json'
            ]
            
            for filename in required_files:
                filepath = os.path.join(tmpdir, 'repository_analysis', filename)
                with open(filepath, 'w') as f:
                    json.dump({"test": "data"}, f)
            
            # Should pass with files
            result = verifier.verify_analysis_complete()
            assert result is True, "Should pass with all analysis files"
            print("✓ Correctly verified analysis files exist")
        
        print("\n✅ TEST 2 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_component_enhancement_verification():
    """Test 3: Component Enhancement Verification"""
    print("\n" + "="*60)
    print("TEST 3: Component Enhancement Verification")
    print("="*60)
    
    try:
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FinalVerifier(base_path=tmpdir)
            
            # Should fail without enhanced components
            result = verifier.verify_enhancement_complete()
            assert result is False, "Should fail without enhanced components"
            print("✓ Correctly identified missing enhanced components")
            
            # Create enhanced workspace structure
            categories = ["agents", "modules", "engines", "systems", "database", "api"]
            
            for category in categories:
                enhanced_dir = os.path.join(
                    tmpdir, 
                    f"enhanced_workspace/{category}/integrated"
                )
                os.makedirs(enhanced_dir, exist_ok=True)
                
                enhanced_file = os.path.join(enhanced_dir, f"{category}_enhanced.py")
                with open(enhanced_file, 'w') as f:
                    f.write(f"# Enhanced {category}\n")
            
            # Should pass with all components
            result = verifier.verify_enhancement_complete()
            assert result is True, "Should pass with all enhanced components"
            print("✓ Correctly verified all enhanced components exist")
        
        print("\n✅ TEST 3 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_testing_verification():
    """Test 4: Testing Completion Verification"""
    print("\n" + "="*60)
    print("TEST 4: Testing Completion Verification")
    print("="*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FinalVerifier(base_path=tmpdir)
            
            # Create test files
            with open(os.path.join(tmpdir, 'test_example.py'), 'w') as f:
                f.write("# Test file\n")
            
            with open(os.path.join(tmpdir, 'pytest.ini'), 'w') as f:
                f.write("[pytest]\n")
            
            # Create coverage indicator
            with open(os.path.join(tmpdir, '.coverage'), 'w') as f:
                f.write("# Coverage data\n")
            
            result = verifier.verify_testing_complete()
            assert result is True, "Should pass with test infrastructure"
            print("✓ Correctly verified testing infrastructure")
        
        print("\n✅ TEST 4 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_deployment_readiness_verification():
    """Test 5: Deployment Readiness Verification"""
    print("\n" + "="*60)
    print("TEST 5: Deployment Readiness Verification")
    print("="*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FinalVerifier(base_path=tmpdir)
            
            # Create deployment files
            deployment_files = [
                'Dockerfile',
                'docker-compose.yml',
                'requirements.txt',
                '.env.example'
            ]
            
            for filename in deployment_files:
                with open(os.path.join(tmpdir, filename), 'w') as f:
                    f.write(f"# {filename}\n")
            
            result = verifier.verify_deployment_ready()
            assert result is True, "Should pass with deployment files"
            print("✓ Correctly verified deployment files")
        
        print("\n✅ TEST 5 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_complete_platform_verification():
    """Test 6: Complete Platform Verification"""
    print("\n" + "="*60)
    print("TEST 6: Complete Platform Verification")
    print("="*60)
    
    try:
        # Use actual repository path
        verifier = FinalVerifier()
        
        result = verifier.verify_complete_platform()
        
        # Should have results for all verification steps
        assert 'repository_analysis' in verifier.verification_results
        assert 'component_enhancement' in verifier.verification_results
        assert 'testing_completion' in verifier.verification_results
        assert 'integration_preparation' in verifier.verification_results
        assert 'deployment_readiness' in verifier.verification_results
        assert 'expansion_capability' in verifier.verification_results
        
        print(f"✓ All verification steps completed")
        print(f"✓ Overall result: {result}")
        
        # Check if report was generated
        if result:
            report_path = os.path.join(verifier.base_path, 'verification_success_report.json')
            assert os.path.exists(report_path), "Success report should be generated"
            print("✓ Success report generated")
        
        print("\n✅ TEST 6 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 6 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation():
    """Test 7: Report Generation"""
    print("\n" + "="*60)
    print("TEST 7: Report Generation")
    print("="*60)
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            verifier = FinalVerifier(base_path=tmpdir)
            
            # Test success report
            verifier.verification_results = {
                'step1': True,
                'step2': True
            }
            verifier.generate_success_report()
            
            report_path = os.path.join(tmpdir, 'verification_success_report.json')
            assert os.path.exists(report_path), "Success report should be created"
            
            with open(report_path, 'r') as f:
                report = json.load(f)
                assert report['status'] == 'success'
                assert 'timestamp' in report
            
            print("✓ Success report generated correctly")
            
            # Test issues report
            verification_steps = {
                'step1': True,
                'step2': False,
                'step3': True
            }
            verifier.generate_issues_report(verification_steps)
            
            issues_path = os.path.join(tmpdir, 'verification_issues_report.json')
            assert os.path.exists(issues_path), "Issues report should be created"
            
            with open(issues_path, 'r') as f:
                report = json.load(f)
                assert report['status'] == 'incomplete'
                assert 'step2' in report['failed_steps']
            
            print("✓ Issues report generated correctly")
        
        print("\n✅ TEST 7 PASSED\n")
        return True
    except Exception as e:
        print(f"\n❌ TEST 7 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("FINAL VERIFICATION TEST SUITE")
    print("="*60)
    
    tests = [
        test_verifier_initialization,
        test_repository_analysis_verification,
        test_component_enhancement_verification,
        test_testing_verification,
        test_deployment_readiness_verification,
        test_complete_platform_verification,
        test_report_generation,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
