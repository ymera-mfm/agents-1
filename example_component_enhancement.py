#!/usr/bin/env python3
"""
Example usage of Component Enhancement Workflow

This script demonstrates how to use the ComponentEnhancer to:
1. Load component inventory
2. Execute enhancement workflow
3. Generate reports
"""
import os
import sys
from pathlib import Path
from component_enhancement_workflow import ComponentEnhancer


def main():
    """Run example enhancement workflow"""
    print("=" * 80)
    print("COMPONENT ENHANCEMENT WORKFLOW - EXAMPLE")
    print("=" * 80)
    
    # Use the repository inventory or create a simple test one
    inventory_path = 'repository_analysis/component_inventory.json'
    
    if not os.path.exists(inventory_path):
        print(f"\n⚠️  Inventory file not found: {inventory_path}")
        print("Creating minimal example inventory...")
        
        os.makedirs('repository_analysis', exist_ok=True)
        
        # Create minimal inventory for demonstration
        import json
        test_inventory = {
            'example_category': [
                {
                    'file_name': 'component_enhancement_workflow.py',
                    'file_path': str(Path(__file__).parent / 'component_enhancement_workflow.py'),
                    'versions': [
                        {'branch': 'main', 'features': ['enhancement', 'analysis']}
                    ]
                }
            ]
        }
        
        with open(inventory_path, 'w') as f:
            json.dump(test_inventory, f, indent=2)
        
        print(f"✅ Created example inventory: {inventory_path}")
    
    # Initialize enhancer
    print(f"\n📥 Loading inventory from: {inventory_path}")
    enhancer = ComponentEnhancer(inventory_path)
    
    print(f"\n📊 Inventory Summary:")
    for category, components in enhancer.inventory.items():
        print(f"   - {category}: {len(components)} component(s)")
    
    # Execute workflow
    print("\n" + "=" * 80)
    enhancer.execute_enhancement_workflow()
    print("=" * 80)
    
    print("\n✅ Enhancement workflow completed successfully!")
    print("\n📂 Check the 'enhanced_workspace' directory for results:")
    print("   - enhanced_workspace/reports/enhancement_report.json")
    print("   - enhanced_workspace/reports/enhancement_report.md")
    print("   - enhanced_workspace/<category>/integrated/<category>_enhanced.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
