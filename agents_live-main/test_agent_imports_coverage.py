"""
Comprehensive Agent Import Coverage Test
Tests all 23 agents that were fixed and generates coverage report
"""
import sys
import os
sys.path.insert(0, os.getcwd())

def test_agent_imports():
    """Test that all fixed agents can be imported"""
    agents = [
        'base_agent',
        'enhanced_base_agent', 
        'production_base_agent',
        'coding_agent',
        'communication_agent',
        'drafting_agent',
        'editing_agent',
        'enhanced_learning_agent',
        'enhanced_llm_agent',
        'enhancement_agent',
        'examination_agent',
        'example_agent',
        'llm_agent',
        'metrics_agent',
        'orchestrator_agent',
        'performance_engine_agent',
        'prod_communication_agent',
        'prod_monitoring_agent',
        'production_monitoring_agent',
        'real_time_monitoring_agent',
        'security_agent',
        'static_analysis_agent',
        'validation_agent',
    ]
    
    results = {'passed': 0, 'failed': 0, 'modules': []}
    
    for agent_name in agents:
        try:
            module = __import__(agent_name)
            results['passed'] += 1
            results['modules'].append({
                'name': agent_name,
                'status': 'pass',
                'has_flags': [attr for attr in dir(module) if attr.startswith('HAS_')]
            })
        except Exception as e:
            results['failed'] += 1
            results['modules'].append({
                'name': agent_name,
                'status': 'fail',
                'error': str(e)
            })
    
    return results

if __name__ == '__main__':
    results = test_agent_imports()
    print(f"\nAgent Import Test Results:")
    print(f"Passed: {results['passed']}/{results['passed'] + results['failed']}")
    print(f"Failed: {results['failed']}/{results['passed'] + results['failed']}")
    
    if results['failed'] > 0:
        print("\nFailed imports:")
        for module in results['modules']:
            if module['status'] == 'fail':
                print(f"  - {module['name']}: {module['error']}")
    
    sys.exit(0 if results['failed'] == 0 else 1)
