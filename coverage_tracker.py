"""Coverage tracker for test coverage improvements - Phase 3 Task 3.2"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class CoverageTracker:
    """Track test coverage improvements over time"""
    
    def __init__(self, output_file: str = "coverage_progress.json"):
        self.output_file = output_file
        self.progress = self._load_progress()
    
    def _load_progress(self) -> Dict:
        """Load existing progress if available"""
        if Path(self.output_file).exists():
            try:
                with open(self.output_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"measurements": []}
    
    def measure_coverage(self, target_dir: str = "agents") -> Dict:
        """Measure current coverage"""
        try:
            # Run pytest with coverage
            result = subprocess.run(
                ['pytest', f'--cov={target_dir}', '--cov-report=json:coverage.json', '--cov-report=term'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Read coverage data
            if Path('coverage.json').exists():
                with open('coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0.0)
                
                files_coverage = {}
                for file_path, file_data in coverage_data.get('files', {}).items():
                    if target_dir in file_path.lower():
                        files_coverage[file_path] = file_data.get('summary', {}).get('percent_covered', 0.0)
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "total_coverage": total_coverage,
                    "files": files_coverage
                }
            else:
                # No coverage data available
                return {
                    "timestamp": datetime.now().isoformat(),
                    "total_coverage": 0.0,
                    "files": {},
                    "error": "No coverage data generated"
                }
        
        except subprocess.TimeoutExpired:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_coverage": 0.0,
                "files": {},
                "error": "Coverage measurement timed out"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_coverage": 0.0,
                "files": {},
                "error": str(e)
            }
    
    def track_progress(self) -> Dict:
        """Track coverage improvement over time"""
        current = self.measure_coverage()
        self.progress["measurements"].append(current)
        
        # Calculate improvement
        if len(self.progress["measurements"]) > 1:
            previous = self.progress["measurements"][-2]["total_coverage"]
            current_pct = current["total_coverage"]
            improvement = current_pct - previous
            first_measurement = self.progress["measurements"][0]["total_coverage"]
            self.progress["improvement_from_start"] = current_pct - first_measurement
            self.progress["last_improvement"] = improvement
        
        self._save_progress()
        return self.progress
    
    def _save_progress(self):
        """Save progress to file"""
        with open(self.output_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def get_summary(self) -> Dict:
        """Get coverage summary"""
        if not self.progress["measurements"]:
            return {
                "status": "No measurements yet",
                "current_coverage": 0.0
            }
        
        latest = self.progress["measurements"][-1]
        
        return {
            "current_coverage": latest.get("total_coverage", 0.0),
            "total_measurements": len(self.progress["measurements"]),
            "improvement_from_start": self.progress.get("improvement_from_start", 0.0),
            "last_improvement": self.progress.get("last_improvement", 0.0),
            "timestamp": latest.get("timestamp", "unknown")
        }


if __name__ == "__main__":
    # Example usage
    tracker = CoverageTracker()
    progress = tracker.track_progress()
    summary = tracker.get_summary()
    
    print(f"Current Coverage: {summary['current_coverage']:.2f}%")
    if "improvement_from_start" in summary:
        print(f"Improvement from Start: +{summary['improvement_from_start']:.2f}%")
