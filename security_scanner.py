"""
Security Scanner - Automated security auditing and vulnerability detection
"""

import re
import os
import json
import hashlib
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class SecurityScanner:
    """Automated security scanner for code and configuration"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        self.patterns = self._load_security_patterns()
        
    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """Load security patterns to check"""
        return {
            'secrets': [
                r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',
                r'(?i)(password|passwd|pwd)\s*[:=]\s*["\'][^"\']{8,}',
                r'(?i)(secret|token)\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',
                r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[:=]',
                r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[:=]',
            ],
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%s',
                r'\.raw\s*\(',
                r'SELECT.*FROM.*WHERE.*\+',
            ],
            'xss': [
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'eval\s*\(',
            ],
            'insecure_functions': [
                r'pickle\.loads?\(',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
            ]
        }
        
    def scan_directory(self, directory: str) -> Dict[str, Any]:
        """Scan entire directory for security issues"""
        self.vulnerabilities = []
        self.warnings = []
        
        for root, dirs, files in os.walk(directory):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.env', '.config', '.yml', '.yaml')):
                    file_path = os.path.join(root, file)
                    self._scan_file(file_path)
                    
        return self._generate_report()
        
    def _scan_file(self, file_path: str):
        """Scan single file for security issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for secrets
            for pattern in self.patterns['secrets']:
                matches = re.finditer(pattern, content)
                for match in matches:
                    self.vulnerabilities.append({
                        'type': 'CRITICAL',
                        'category': 'Hardcoded Secret',
                        'file': file_path,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Potential hardcoded secret or credential found',
                        'match': match.group(0)[:50] + '...'
                    })
                    
            # Check for SQL injection vulnerabilities
            if file_path.endswith('.py'):
                for pattern in self.patterns['sql_injection']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.warnings.append({
                            'type': 'HIGH',
                            'category': 'SQL Injection Risk',
                            'file': file_path,
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Potential SQL injection vulnerability'
                        })
                        
            # Check for XSS vulnerabilities
            if file_path.endswith(('.js', '.ts')):
                for pattern in self.patterns['xss']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.warnings.append({
                            'type': 'HIGH',
                            'category': 'XSS Risk',
                            'file': file_path,
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Potential XSS vulnerability'
                        })
                        
            # Check for insecure functions
            if file_path.endswith('.py'):
                for pattern in self.patterns['insecure_functions']:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.warnings.append({
                            'type': 'MEDIUM',
                            'category': 'Insecure Function',
                            'file': file_path,
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Use of potentially insecure function'
                        })
                        
        except Exception as e:
            self.warnings.append({
                'type': 'INFO',
                'category': 'Scan Error',
                'file': file_path,
                'description': f'Error scanning file: {str(e)}'
            })
            
    def _generate_report(self) -> Dict[str, Any]:
        """Generate security scan report"""
        return {
            'scan_date': datetime.now().isoformat(),
            'summary': {
                'total_issues': len(self.vulnerabilities) + len(self.warnings),
                'critical_issues': len([v for v in self.vulnerabilities if v['type'] == 'CRITICAL']),
                'high_issues': len([w for w in self.warnings if w['type'] == 'HIGH']),
                'medium_issues': len([w for w in self.warnings if w['type'] == 'MEDIUM']),
                'low_issues': len([w for w in self.warnings if w['type'] == 'LOW'])
            },
            'vulnerabilities': self.vulnerabilities,
            'warnings': self.warnings,
            'recommendations': self._generate_recommendations()
        }
        
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if any(v['category'] == 'Hardcoded Secret' for v in self.vulnerabilities):
            recommendations.append('Move all secrets and credentials to environment variables or secure vault')
            
        if any(w['category'] == 'SQL Injection Risk' for w in self.warnings):
            recommendations.append('Use parameterized queries or ORM to prevent SQL injection')
            
        if any(w['category'] == 'XSS Risk' for w in self.warnings):
            recommendations.append('Sanitize all user input and use secure DOM manipulation methods')
            
        if any(w['category'] == 'Insecure Function' for w in self.warnings):
            recommendations.append('Replace insecure functions with safer alternatives')
            
        return recommendations
        
    def check_dependencies(self, requirements_file: str) -> Dict[str, Any]:
        """Check dependencies for known vulnerabilities"""
        issues = []
        
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Basic check - in production, use safety or snyk
                        if '==' in line:
                            package, version = line.split('==')
                            issues.append({
                                'type': 'INFO',
                                'package': package.strip(),
                                'version': version.strip(),
                                'recommendation': 'Check for latest version and security advisories'
                            })
        except Exception as e:
            return {'error': str(e)}
            
        return {
            'dependencies_checked': len(issues),
            'issues': issues
        }


class SecurityAuditor:
    """Comprehensive security auditor"""
    
    def __init__(self):
        self.scanner = SecurityScanner()
        
    def run_full_audit(self, base_dir: str) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        results = {
            'audit_date': datetime.now().isoformat(),
            'code_scan': self.scanner.scan_directory(base_dir),
            'configuration_check': self._check_configurations(base_dir),
            'permissions_check': self._check_permissions(base_dir),
            'encryption_check': self._check_encryption(base_dir)
        }
        
        # Calculate risk score
        results['risk_score'] = self._calculate_risk_score(results)
        results['overall_status'] = self._determine_status(results['risk_score'])
        
        return results
        
    def _check_configurations(self, base_dir: str) -> Dict[str, Any]:
        """Check configuration security"""
        issues = []
        
        # Check for debug mode in production
        config_files = ['.env', 'config.py', 'settings.py']
        for config_file in config_files:
            config_path = os.path.join(base_dir, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        if re.search(r'(?i)debug\s*=\s*true', content):
                            issues.append({
                                'type': 'HIGH',
                                'file': config_path,
                                'issue': 'Debug mode enabled'
                            })
                except:
                    pass
                    
        return {'issues': issues}
        
    def _check_permissions(self, base_dir: str) -> Dict[str, Any]:
        """Check file permissions"""
        issues = []
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Check if sensitive files are readable by all
                    if file in ['.env', 'config.py', 'settings.py']:
                        stat_info = os.stat(file_path)
                        if stat_info.st_mode & 0o004:  # Others can read
                            issues.append({
                                'type': 'MEDIUM',
                                'file': file_path,
                                'issue': 'Sensitive file is world-readable'
                            })
                except:
                    pass
                    
        return {'issues': issues}
        
    def _check_encryption(self, base_dir: str) -> Dict[str, Any]:
        """Check encryption implementation"""
        issues = []
        
        # Check for weak encryption patterns
        weak_patterns = [
            (r'md5\s*\(', 'MD5 is cryptographically broken'),
            (r'sha1\s*\(', 'SHA1 is weak for security purposes'),
            (r'DES|3DES', 'DES/3DES are outdated encryption algorithms')
        ]
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for pattern, description in weak_patterns:
                                if re.search(pattern, content):
                                    issues.append({
                                        'type': 'MEDIUM',
                                        'file': file_path,
                                        'issue': description
                                    })
                    except:
                        pass
                        
        return {'issues': issues}
        
    def _calculate_risk_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        code_scan = results.get('code_scan', {})
        summary = code_scan.get('summary', {})
        
        score += summary.get('critical_issues', 0) * 25
        score += summary.get('high_issues', 0) * 10
        score += summary.get('medium_issues', 0) * 5
        score += summary.get('low_issues', 0) * 1
        
        return min(score, 100)
        
    def _determine_status(self, risk_score: float) -> str:
        """Determine overall security status"""
        if risk_score < 20:
            return 'EXCELLENT'
        elif risk_score < 40:
            return 'GOOD'
        elif risk_score < 60:
            return 'FAIR'
        elif risk_score < 80:
            return 'POOR'
        else:
            return 'CRITICAL'
