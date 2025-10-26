"""Fix tracker for agent repairs - Phase 3 Task 3.1"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class FixTracker:
    """Track agent fixes with timestamps and test results"""
    
    def __init__(self, output_file: str = "agent_fixes_applied.json"):
        self.fixes: List[Dict] = []
        self.output_file = output_file
        self._load_existing()
    
    def _load_existing(self):
        """Load existing fixes if file exists"""
        if Path(self.output_file).exists():
            try:
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
                    self.fixes = data.get('fixes', [])
            except Exception:
                self.fixes = []
    
    def add_fix(
        self,
        agent_file: str,
        issue: str,
        fix_description: str,
        test_results: Dict[str, int],
        root_cause: Optional[str] = None,
        priority: str = "MEDIUM"
    ):
        """Add a fix record"""
        self.fixes.append({
            "agent": agent_file,
            "issue": issue,
            "root_cause": root_cause or issue,
            "fix": fix_description,
            "tests": test_results,
            "priority": priority,
            "fixed_at": datetime.now().isoformat(),
            "status": "FIXED"
        })
    
    def save(self):
        """Save fixes to JSON file"""
        with open(self.output_file, 'w') as f:
            json.dump({
                "total_fixes": len(self.fixes),
                "last_updated": datetime.now().isoformat(),
                "fixes": self.fixes
            }, f, indent=2)
    
    def get_summary(self) -> Dict:
        """Get summary of fixes"""
        issues_by_type = {}
        for fix in self.fixes:
            issue_type = fix.get('issue', 'Unknown')
            issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        
        return {
            "total_fixes": len(self.fixes),
            "issues_by_type": issues_by_type,
            "fixed_count": len([f for f in self.fixes if f.get('status') == 'FIXED'])
        }


if __name__ == "__main__":
    # Example usage
    tracker = FixTracker()
    
    tracker.add_fix(
        agent_file="base_agent.py",
        issue="No module named 'nats'",
        fix_description="Added nats-py to requirements.txt",
        test_results={"passed": 5, "failed": 0},
        root_cause="Missing dependency in requirements.txt",
        priority="HIGH"
    )
    
    tracker.save()
    print(f"Fix tracker initialized: {tracker.get_summary()}")
