#!/usr/bin/env python3
"""
Test suite for audit system validation
"""

import json
import pytest
from pathlib import Path


def test_inventory_json_exists():
    """Test that inventory JSON file exists"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.json')
    assert inventory_path.exists(), "Inventory JSON file should exist"


def test_inventory_md_exists():
    """Test that inventory Markdown file exists"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.md')
    assert inventory_path.exists(), "Inventory Markdown file should exist"


def test_architecture_md_exists():
    """Test that architecture documentation exists"""
    arch_path = Path('audit_reports/architecture/ARCHITECTURE.md')
    assert arch_path.exists(), "Architecture documentation should exist"


def test_inventory_json_valid():
    """Test that inventory JSON is valid and has expected structure"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.json')
    
    with open(inventory_path) as f:
        data = json.load(f)
    
    # Check for required top-level keys
    assert 'summary' in data, "Should have summary section"
    assert 'components' in data, "Should have components section"
    assert 'dependency_graph' in data, "Should have dependency_graph section"
    assert 'orphaned_files' in data, "Should have orphaned_files section"
    assert 'missing_tests' in data, "Should have missing_tests section"


def test_inventory_summary_structure():
    """Test that inventory summary has correct structure"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.json')
    
    with open(inventory_path) as f:
        data = json.load(f)
    
    summary = data['summary']
    
    # Check summary fields
    assert 'total_files' in summary
    assert 'total_lines' in summary
    assert 'categories' in summary
    assert 'scan_date' in summary
    
    # Validate data types
    assert isinstance(summary['total_files'], int)
    assert isinstance(summary['total_lines'], int)
    assert isinstance(summary['categories'], dict)
    
    # Check that we found files
    assert summary['total_files'] > 0, "Should have found Python files"
    assert summary['total_lines'] > 0, "Should have counted lines of code"


def test_inventory_components_structure():
    """Test that components have correct structure"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.json')
    
    with open(inventory_path) as f:
        data = json.load(f)
    
    components = data['components']
    
    # Check that we have components
    assert len(components) > 0, "Should have categorized components"
    
    # Check first component in each category
    for category, component_list in components.items():
        if component_list:
            comp = component_list[0]
            
            # Check required fields
            required_fields = [
                'name', 'path', 'purpose', 'dependencies', 
                'public_api', 'state', 'loc', 'has_tests'
            ]
            for field in required_fields:
                assert field in comp, f"Component should have {field} field"
            
            # Validate field types
            assert isinstance(comp['name'], str)
            assert isinstance(comp['path'], str)
            assert isinstance(comp['dependencies'], list)
            assert isinstance(comp['loc'], int)
            assert isinstance(comp['has_tests'], bool)


def test_architecture_has_mermaid_diagrams():
    """Test that architecture doc contains Mermaid diagrams"""
    arch_path = Path('audit_reports/architecture/ARCHITECTURE.md')
    
    with open(arch_path) as f:
        content = f.read()
    
    # Check for Mermaid code blocks
    assert '```mermaid' in content, "Should contain Mermaid diagrams"
    
    # Check for specific diagram types
    assert 'graph TB' in content or 'graph LR' in content, "Should have graph diagrams"
    assert 'sequenceDiagram' in content, "Should have sequence diagram"
    assert 'erDiagram' in content or 'USERS' in content, "Should have ER diagram"


def test_architecture_has_required_sections():
    """Test that architecture doc has all required sections"""
    arch_path = Path('audit_reports/architecture/ARCHITECTURE.md')
    
    with open(arch_path) as f:
        content = f.read()
    
    required_sections = [
        'High-Level Overview',
        'System Architecture',
        'Database Schema',
        'API Routes',
        'Agent Interactions',
        'Deployment Architecture',
        'Component Responsibilities',
        'Technology Stack',
        'Design Patterns'
    ]
    
    for section in required_sections:
        assert section in content, f"Should have {section} section"


def test_readme_exists():
    """Test that README exists in audit_reports"""
    readme_path = Path('audit_reports/README.md')
    assert readme_path.exists(), "README should exist in audit_reports"


def test_component_count_consistency():
    """Test that component counts are consistent"""
    inventory_path = Path('audit_reports/inventory/platform_inventory.json')
    
    with open(inventory_path) as f:
        data = json.load(f)
    
    # Count components in categories
    total_in_categories = sum(len(v) for v in data['components'].values())
    
    # Should match total_files in summary
    assert total_in_categories == data['summary']['total_files'], \
        "Total components should match file count"


def test_audit_reports_directory_structure():
    """Test that audit reports directory has correct structure"""
    audit_dir = Path('audit_reports')
    
    assert audit_dir.exists(), "audit_reports directory should exist"
    assert (audit_dir / 'inventory').exists(), "inventory subdirectory should exist"
    assert (audit_dir / 'architecture').exists(), "architecture subdirectory should exist"
    assert (audit_dir / 'README.md').exists(), "README.md should exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
