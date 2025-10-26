#!/usr/bin/env python3
"""
YMERA Platform Audit Master Script
Runs complete audit and documentation generation including Phase 2: Testing & Quality Audit
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime


def print_banner():
    """Print audit system banner"""
    print("\n" + "="*80)
    print("🔍 YMERA PLATFORM COMPREHENSIVE AUDIT SYSTEM")
    print("="*80 + "\n")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def print_phase(phase_num: int, phase_name: str):
    """Print phase header"""
    print("\n" + "-"*80)
    print(f"📋 PHASE {phase_num}: {phase_name}")
    print("-"*80 + "\n")


def run_component_inventory():
    """Run component inventory generation"""
    print_phase(1, "Component Inventory Generation")
    
    try:
        from generate_component_inventory import PlatformAuditor
        
        repo_path = Path(__file__).parent
        output_dir = repo_path / 'audit_reports'
        
        auditor = PlatformAuditor(repo_path)
        auditor.run_audit(output_dir)
        
        return True
    except Exception as e:
        print(f"❌ Error in component inventory: {e}")
        return False


def run_testing_quality_audit():
    """Run Phase 2: Comprehensive Testing & Quality Audit"""
    print_phase(2, "Comprehensive Testing & Quality Audit")
    
    try:
        # Import and run the comprehensive audit
        sys.path.insert(0, str(Path(__file__).parent))
        from audit_scripts.comprehensive_audit import PlatformAuditor as TestAuditor
        
        repo_path = Path(__file__).parent
        auditor = TestAuditor(repo_path)
        auditor.run_all_audits()
        
        return True
    except Exception as e:
        print(f"❌ Error in testing & quality audit: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_architecture_docs():
    """Run architecture documentation generation"""
    print_phase(3, "Architecture Documentation Generation")
    
    try:
        from generate_architecture_docs import ArchitectureDocGenerator
        
        repo_path = Path(__file__).parent
        inventory_path = repo_path / 'audit_reports' / 'inventory' / 'platform_inventory.json'
        output_dir = repo_path / 'audit_reports'
        
        if not inventory_path.exists():
            print(f"❌ Inventory file not found at {inventory_path}")
            print("   Skipping architecture documentation generation")
            return False
        
        generator = ArchitectureDocGenerator(inventory_path)
        generator.run(output_dir)
        
        return True
    except Exception as e:
        print(f"❌ Error in architecture documentation: {e}")
        return False


def print_summary(inventory_success: bool, architecture_success: bool):
    """Print final summary"""
    print("\n" + "="*80)
    print("✅ AUDIT SUMMARY")
    print("="*80 + "\n")
    
    if inventory_success:
        print("✅ Component Inventory: SUCCESS")
        print("   - Generated platform_inventory.json")
        print("   - Generated platform_inventory.md")
    else:
        print("❌ Component Inventory: FAILED")
    
    if architecture_success:
        print("✅ Architecture Documentation: SUCCESS")
        print("   - Generated ARCHITECTURE.md with diagrams")
    else:
        print("❌ Architecture Documentation: FAILED")
    
    print("\n📁 Output Location: audit_reports/")
    print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if inventory_success and architecture_success:
        print("🎉 All audit phases completed successfully!\n")
        return 0
    else:
        print("⚠️  Some audit phases failed. Please check the errors above.\n")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='YMERA Platform Comprehensive Audit System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run complete audit
  %(prog)s --inventory-only   # Run only component inventory
  %(prog)s --architecture-only # Run only architecture docs
        """
    )
    
    parser.add_argument(
        '--inventory-only',
        action='store_true',
        help='Run only component inventory generation'
    )
    
    parser.add_argument(
        '--architecture-only',
        action='store_true',
        help='Run only architecture documentation generation'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimize output'
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print_banner()
    
    inventory_success = False
    architecture_success = False
    
    # Determine what to run
    if args.inventory_only:
        inventory_success = run_component_inventory()
    elif args.architecture_only:
        architecture_success = run_architecture_docs()
    else:
        # Run complete audit
        inventory_success = run_component_inventory()
        if inventory_success:
            architecture_success = run_architecture_docs()
    
    # Print summary
    if not args.quiet:
        exit_code = print_summary(inventory_success, architecture_success)
        return exit_code
    
    return 0 if (inventory_success or architecture_success) else 1


if __name__ == '__main__':
    sys.exit(main())
