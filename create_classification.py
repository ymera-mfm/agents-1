#!/usr/bin/env python3
"""Create agent classification JSON from catalog and test results"""

import json

def main():
    # Load catalog
    with open('agent_catalog_complete.json', 'r') as f:
        catalog = json.load(f)
    
    # Load test results
    with open('agent_test_results_complete.json', 'r') as f:
        test_results = json.load(f)
    
    # Create test results map
    test_map = {}
    for result in test_results.get('test_results', []):
        test_map[result.get('file', '')] = result
    
    # Create classification
    classification = {
        'classification_timestamp': catalog.get('discovery_timestamp', ''),
        'by_type': {},
        'by_status': {
            'complete': [],
            'incomplete': [],
            'broken': [],
            'needs_dependencies': []
        },
        'by_capability': {
            'async': [],
            'database': [],
            'api': [],
            'file_ops': []
        }
    }
    
    # Classify each agent
    for agent in catalog.get('agents', []):
        file = agent.get('file', '')
        if not file:
            continue
        
        agent_entry = {
            'file': file,
            'classes': agent.get('agent_classes', []),
            'test_status': 'unknown'
        }
        
        # Classify by type
        file_lower = file.lower()
        if 'learning' in file_lower:
            agent_type = 'learning'
        elif 'monitoring' in file_lower:
            agent_type = 'monitoring'
        elif 'communication' in file_lower:
            agent_type = 'communication'
        elif 'validation' in file_lower:
            agent_type = 'validation'
        elif 'security' in file_lower:
            agent_type = 'security'
        elif 'editing' in file_lower or 'drafting' in file_lower:
            agent_type = 'content'
        elif 'orchestrator' in file_lower or 'coordinator' in file_lower:
            agent_type = 'orchestration'
        else:
            agent_type = 'other'
        
        if agent_type not in classification['by_type']:
            classification['by_type'][agent_type] = []
        classification['by_type'][agent_type].append(agent_entry)
        
        # Classify by status based on test results
        test_result = test_map.get(file)
        if test_result:
            if test_result.get('status') == 'PASS':
                classification['by_status']['complete'].append(agent_entry)
                agent_entry['test_status'] = 'complete'
            elif test_result.get('status') == 'FAIL':
                import_test = test_result.get('import_test', {})
                error = import_test.get('error') if import_test else None
                if error and isinstance(error, dict) and error.get('type') == 'ModuleNotFoundError':
                    classification['by_status']['needs_dependencies'].append(agent_entry)
                    agent_entry['test_status'] = 'needs_dependencies'
                else:
                    classification['by_status']['broken'].append(agent_entry)
                    agent_entry['test_status'] = 'broken'
            else:
                classification['by_status']['incomplete'].append(agent_entry)
                agent_entry['test_status'] = 'incomplete'
        else:
            classification['by_status']['incomplete'].append(agent_entry)
        
        # Classify by capability
        if agent.get('async_method_count', 0) > 0:
            classification['by_capability']['async'].append(file)
        
        imports = agent.get('imports', [])
        if any('sql' in imp.lower() or 'database' in imp.lower() for imp in imports):
            classification['by_capability']['database'].append(file)
        if any('fastapi' in imp.lower() or 'api' in imp.lower() for imp in imports):
            classification['by_capability']['api'].append(file)
        if any('file' in imp.lower() or 'aiofiles' in imp.lower() for imp in imports):
            classification['by_capability']['file_ops'].append(file)
    
    # Add summary
    classification['summary'] = {
        'total_agents': len(catalog.get('agents', [])),
        'by_type_counts': {k: len(v) for k, v in classification['by_type'].items()},
        'by_status_counts': {k: len(v) for k, v in classification['by_status'].items()},
        'by_capability_counts': {k: len(v) for k, v in classification['by_capability'].items()}
    }
    
    # Save classification
    with open('agent_classification.json', 'w') as f:
        json.dump(classification, f, indent=2)
    
    print(f'✅ agent_classification.json created')
    print(f'  Total agents: {classification["summary"]["total_agents"]}')
    print(f'  By type: {classification["summary"]["by_type_counts"]}')
    print(f'  By status: {classification["summary"]["by_status_counts"]}')

if __name__ == '__main__':
    main()
