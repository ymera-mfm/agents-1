"""
YMERA Production System - Quick Start Script
Initializes and demonstrates the system
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.system import YMERASystem
from core.config import Config


async def quick_start():
    """Quick start demonstration"""
    
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "YMERA PRODUCTION LEARNING SYSTEM" + " "*26 + "║")
    print("║" + " "*32 + "Version 2.0.0" + " "*33 + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n🚀 Initializing YMERA System...")
    
    # Create and initialize system
    system = YMERASystem()
    
    try:
        await system.initialize()
        print("✅ System initialized successfully!\n")
        
        # Get and display system status
        status = await system.get_system_status()
        
        print("📊 System Status:")
        print(f"   ├─ System ID: {status['system_id']}")
        print(f"   ├─ Status: {status['status']}")
        print(f"   ├─ Version: {status['version']}")
        print(f"   └─ Uptime: {status['uptime_seconds']:.2f}s\n")
        
        print("🔧 Active Components:")
        for component, state in status['components'].items():
            symbol = "✓" if state == "active" else "✗"
            print(f"   {symbol} {component}")
        
        print("\n📈 System Metrics:")
        print(f"   ├─ Total Tasks: {status['metrics']['total_tasks']}")
        print(f"   ├─ Active Tasks: {status['metrics']['active_tasks']}")
        print(f"   ├─ Patterns Detected: {status['metrics']['patterns_detected']}")
        print(f"   ├─ Knowledge Entries: {status['metrics']['knowledge_entries']}")
        print(f"   └─ Error Rate: {status['metrics']['error_rate']:.2%}\n")
        
        # Submit a sample task
        print("🎯 Submitting sample learning task...")
        task_id = await system.submit_learning_task(
            task_type="classification",
            data={"sample": "data"},
            config={"learning_rate": 0.001}
        )
        print(f"✅ Task submitted: {task_id}\n")
        
        # Enable advanced features
        print("🔄 Enabling advanced features...")
        await system.enable_continuous_learning()
        print("   ✓ Continuous learning enabled")
        
        await system.enable_external_learning()
        print("   ✓ External learning enabled\n")
        
        # Final status
        print("═"*80)
        print("✅ YMERA System is ready for production!")
        print("═"*80)
        print("\n📚 Next steps:")
        print("   1. Run comprehensive tests: python tests/test_comprehensive.py")
        print("   2. Start API server: python api/main.py")
        print("   3. View documentation: README.md")
        print("   4. Check system status: SYSTEM_STATUS_REPORT.md\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Shutdown
        print("🛑 Shutting down system...")
        await system.shutdown()
        print("✅ Shutdown complete\n")


if __name__ == "__main__":
    asyncio.run(quick_start())
