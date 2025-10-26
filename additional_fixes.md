# 🔐 CRITICAL SECURITY & CONFIGURATION FIXES

## ⚠️ URGENT: EXPOSED API KEYS DETECTED

### 🚨 SECURITY BREACH IN DOCUMENT: `1.txt`

**CRITICAL FINDING**: Your uploaded file `1.txt` contains **EXPOSED API KEYS AND SECRETS**

```
❌ EXPOSED CREDENTIALS FOUND:
- Prisma JWT Token (Full token exposed)
- JSONbin Master Key (bcrypt hash exposed)
- Access Key (bcrypt hash exposed)
- Wrik Client ID & Secret (FULL CREDENTIALS)
- Explorium API Key (FULL KEY)
- Azure SSH Key (FULL PRIVATE KEY)
- ElevenLabs API Key (FULL KEY)
- OpenRouter API Keys (MULTIPLE KEYS)
- Firecrawl API Key (FULL KEY)
- PostHog API Key (FULL KEY)
- Supabase JWT Token (FULL TOKEN)
```

---

## 🔥 IMMEDIATE ACTIONS REQUIRED

### 1. REVOKE ALL EXPOSED CREDENTIALS (DO THIS NOW!)

#### Prisma
```bash
# Go to Prisma dashboard
# Navigate to: Settings → API Keys
# Delete exposed token: eyJraWQiOiJUa0hEN...
# Generate new token
```

#### Wrik
```bash
# Revoke exposed credentials immediately
Client ID: GhxFxi6f
Client Secret: vwmqumGKflsI... (EXPOSED)
# Generate new OAuth credentials
```

#### Azure SSH Key
```bash
# The SSH key is FULLY EXPOSED
# 1. Remove from all Azure VMs immediately
# 2. Generate new SSH keypair:
ssh-keygen -t rsa -b 4096 -C "azure-secure-key"
# 3. Update all Azure resources
```

#### ElevenLabs
```bash
# Revoke: sk_bf1540902d9fc7200339727d78385956fa2533f5af392320
# Generate new API key from dashboard
```

#### OpenRouter
```bash
# Revoke both exposed keys:
# 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
# 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
```

#### Firecrawl
```bash
# Revoke: fc-6d5c511fa7c7441b93a1fd441cbdc553
```

#### PostHog
```bash
# Revoke: phx_zbBo1DS2QXOLhDFnsdDwhNIWHoyqy8RMjPL2Sn3ZT83cMFq
```

#### Supabase
```bash
# Revoke JWT token immediately
# The exposed token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# Generate new anon key from Supabase dashboard
```

---

## 🛡️ SECURE CREDENTIAL MANAGEMENT

### Step 1: Remove Exposed File
```bash
# Delete the exposed file immediately
rm 1.txt

# Check git history (if committed)
git log --all --full-history -- "*1.txt"

# If found in git, use BFG Repo-Cleaner
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 1.txt" \
  --prune-empty --tag-name-filter cat -- --all
```

### Step 2: Create Secure Environment File
```bash
# Create .env file (NOT committed to git)
touch .env
chmod 600 .env  # Owner read/write only
```

### Step 3: Add to .gitignore
```bash
# Add to .gitignore immediately
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore
echo "secrets/" >> .gitignore
echo "1.txt" >> .gitignore

git add .gitignore
git commit -m "Add sensitive files to gitignore"
```

---

## 📋 SECURE .ENV TEMPLATE

Create this file as `.env.template` (safe to commit):

```bash
# =============================================================================
# YMERA PLATFORM - SECURE ENVIRONMENT VARIABLES
# =============================================================================
# INSTRUCTIONS:
# 1. Copy this file to .env
# 2. Replace all placeholder values with real credentials
# 3. NEVER commit .env to version control
# =============================================================================

# -----------------------------------------------------------------------------
# APPLICATION SETTINGS
# -----------------------------------------------------------------------------
APP_NAME=YMERA Enterprise Platform
APP_VERSION=4.0.0
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=REPLACE_WITH_SECURE_RANDOM_KEY_MIN_32_CHARS

# -----------------------------------------------------------------------------
# DATABASE
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ymera_db
REDIS_URL=redis://localhost:6379/0

# -----------------------------------------------------------------------------
# SECURITY
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=REPLACE_WITH_SECURE_JWT_SECRET
ENCRYPTION_KEY=REPLACE_WITH_FERNET_KEY

# -----------------------------------------------------------------------------
# PRISMA (REPLACE EXPOSED TOKEN)
# -----------------------------------------------------------------------------
PRISMA_TOKEN=GENERATE_NEW_TOKEN_FROM_DASHBOARD

# -----------------------------------------------------------------------------
# JSONBIN (REPLACE EXPOSED KEYS)
# -----------------------------------------------------------------------------
JSONBIN_MASTER_KEY=GENERATE_NEW_MASTER_KEY
JSONBIN_ACCESS_KEY=GENERATE_NEW_ACCESS_KEY

# -----------------------------------------------------------------------------
# WRIK (REPLACE EXPOSED CREDENTIALS)
# -----------------------------------------------------------------------------
WRIK_CLIENT_ID=GENERATE_NEW_CLIENT_ID
WRIK_CLIENT_SECRET=GENERATE_NEW_CLIENT_SECRET

# -----------------------------------------------------------------------------
# EXPLORIUM (REPLACE EXPOSED KEY)
# -----------------------------------------------------------------------------
EXPLORIUM_API_KEY=GENERATE_NEW_API_KEY

# -----------------------------------------------------------------------------
# AZURE (REPLACE EXPOSED SSH KEY)
# -----------------------------------------------------------------------------
AZURE_SSH_KEY_PATH=/path/to/new/private/key
AZURE_SSH_PUBLIC_KEY=GENERATE_NEW_PUBLIC_KEY

# -----------------------------------------------------------------------------
# ELEVENLABS (REPLACE EXPOSED KEY)
# -----------------------------------------------------------------------------
ELEVENLABS_API_KEY=GENERATE_NEW_API_KEY

# -----------------------------------------------------------------------------
# OPENROUTER (REPLACE EXPOSED KEYS)
# -----------------------------------------------------------------------------
OPENROUTER_API_KEY_1=GENERATE_NEW_API_KEY_1
OPENROUTER_API_KEY_2=GENERATE_NEW_API_KEY_2

# -----------------------------------------------------------------------------
# FIRECRAWL (REPLACE EXPOSED KEY)
# -----------------------------------------------------------------------------
FIRECRAWL_API_KEY=GENERATE_NEW_API_KEY

# -----------------------------------------------------------------------------
# POSTHOG (REPLACE EXPOSED KEY)
# -----------------------------------------------------------------------------
POSTHOG_API_KEY=GENERATE_NEW_API_KEY

# -----------------------------------------------------------------------------
# SUPABASE (REPLACE EXPOSED TOKEN)
# -----------------------------------------------------------------------------
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=GENERATE_NEW_ANON_KEY
SUPABASE_SERVICE_KEY=GENERATE_NEW_SERVICE_KEY

# -----------------------------------------------------------------------------
# AI SERVICES (From your env files)
# -----------------------------------------------------------------------------
# Claude API Keys
CLAUDE_API_KEY_1=sk-ant-REPLACE
CLAUDE_API_KEY_2=sk-ant-REPLACE
CLAUDE_API_KEY_3=sk-ant-REPLACE
CLAUDE_API_KEY_4=sk-ant-REPLACE
CLAUDE_API_KEY_5=sk-ant-REPLACE
CLAUDE_API_KEY_6=sk-ant-REPLACE
CLAUDE_API_KEY_7=sk-ant-REPLACE

# OpenAI API Keys
OPENAI_API_KEY_1=sk-REPLACE
OPENAI_API_KEY_2=sk-REPLACE
OPENAI_API_KEY_3=sk-REPLACE
OPENAI_API_KEY_4=sk-REPLACE
OPENAI_API_KEY_5=sk-REPLACE

# Gemini API Keys
GEMINI_API_KEY_1=REPLACE
GEMINI_API_KEY_2=REPLACE
GEMINI_API_KEY_3=REPLACE
GEMINI_API_KEY_4=REPLACE
GEMINI_API_KEY_5=REPLACE

# DeepSeek API Keys
DEEPSEEK_API_KEY_1=REPLACE
DEEPSEEK_API_KEY_2=REPLACE
DEEPSEEK_API_KEY_3=REPLACE
DEEPSEEK_API_KEY_4=REPLACE
DEEPSEEK_API_KEY_5=REPLACE

# Groq API Keys
GROQ_API_KEY_1=REPLACE
GROQ_API_KEY_2=REPLACE
GROQ_API_KEY_3=REPLACE
GROQ_API_KEY_4=REPLACE
GROQ_API_KEY_5=REPLACE

# GitHub Tokens
GITHUB_TOKEN_1=ghp_REPLACE
GITHUB_TOKEN_2=ghp_REPLACE
GITHUB_TOKEN_ADMIN=ghp_REPLACE

# Pinecone
PINECONE_API_KEY=REPLACE
PINECONE_ENVIRONMENT=REPLACE
```

---

## 🔒 SECURE CREDENTIAL LOADER

Create `backend/app/CORE_CONFIGURATION/secure_config.py`:

```python
"""
YMERA Enterprise - Secure Configuration Manager
Handles sensitive credentials with encryption and validation
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logging.warning("cryptography not available, encryption disabled")


@dataclass
class SecureCredential:
    """Secure credential container"""
    name: str
    value: str
    encrypted: bool = False
    last_rotated: Optional[str] = None


class SecureConfigManager:
    """
    Secure configuration manager with credential encryption,
    validation, and rotation tracking.
    """
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.logger = logging.getLogger("ymera.secure_config")
        self._credentials: Dict[str, SecureCredential] = {}
        self._encryption_key = None
        
        # Initialize encryption
        if ENCRYPTION_AVAILABLE:
            self._initialize_encryption()
        
        # Load environment variables
        self._load_environment()
    
    def _initialize_encryption(self):
        """Initialize Fernet encryption"""
        key_file = Path("keys/config_encryption.key")
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            # Generate new encryption key
            self._encryption_key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
            key_file.chmod(0o600)
            self.logger.info("Generated new config encryption key")
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        if not self.env_file.exists():
            self.logger.warning(f"Environment file not found: {self.env_file}")
            return
        
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Store credential
                    self._credentials[key] = SecureCredential(
                        name=key,
                        value=value,
                        encrypted=False
                    )
                    
                    # Set environment variable
                    os.environ[key] = value
        
        self.logger.info(f"Loaded {len(self._credentials)} credentials")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        credential = self._credentials.get(key)
        if credential:
            return credential.value
        return os.getenv(key, default)
    
    def validate_required_credentials(self, required: list) -> tuple[bool, list]:
        """
        Validate that all required credentials are present.
        
        Returns:
            Tuple of (all_present: bool, missing: list)
        """
        missing = []
        
        for key in required:
            value = self.get(key)
            if not value or value.startswith('REPLACE') or value.startswith('GENERATE'):
                missing.append(key)
        
        return len(missing) == 0, missing
    
    def mask_credential(self, value: str, visible_chars: int = 4) -> str:
        """Mask credential for logging"""
        if not value or len(value) <= visible_chars * 2:
            return "***"
        
        return f"{value[:visible_chars]}...{value[-visible_chars:]}"
    
    def get_credential_status(self) -> Dict[str, Any]:
        """Get status of all credentials"""
        status = {
            "total_credentials": len(self._credentials),
            "configured": 0,
            "missing": 0,
            "placeholder": 0,
            "details": {}
        }
        
        for key, cred in self._credentials.items():
            if not cred.value:
                status["missing"] += 1
                status["details"][key] = "MISSING"
            elif cred.value.startswith(('REPLACE', 'GENERATE', 'your-')):
                status["placeholder"] += 1
                status["details"][key] = "PLACEHOLDER"
            else:
                status["configured"] += 1
                status["details"][key] = "CONFIGURED"
        
        return status


# Global secure config instance
_secure_config: Optional[SecureConfigManager] = None


def get_secure_config() -> SecureConfigManager:
    """Get global secure configuration manager"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfigManager()
    return _secure_config


def validate_production_readiness() -> tuple[bool, Dict[str, Any]]:
    """
    Validate that all production credentials are configured.
    
    Returns:
        Tuple of (ready: bool, report: dict)
    """
    config = get_secure_config()
    
    # Critical credentials required for production
    required_credentials = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'ENCRYPTION_KEY',
    ]
    
    all_present, missing = config.validate_required_credentials(required_credentials)
    
    status = config.get_credential_status()
    
    report = {
        "production_ready": all_present and status["placeholder"] == 0,
        "critical_missing": missing,
        "credential_status": status,
        "recommendations": []
    }
    
    # Add recommendations
    if missing:
        report["recommendations"].append(
            f"Configure missing credentials: {', '.join(missing)}"
        )
    
    if status["placeholder"] > 0:
        report["recommendations"].append(
            f"Replace {status['placeholder']} placeholder values with real credentials"
        )
    
    return report["production_ready"], report


__all__ = [
    'SecureConfigManager',
    'SecureCredential',
    'get_secure_config',
    'validate_production_readiness',
]
```

---

## 🔍 CREDENTIAL AUDIT SCRIPT

Create `scripts/audit_credentials.py`:

```python
#!/usr/bin/env python3
"""
Credential Security Audit Script
Checks for exposed credentials and validates configuration
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def scan_for_patterns(file_path: Path, patterns: dict) -> List[Tuple[str, str, int]]:
    """Scan file for sensitive patterns"""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append((pattern_name, line.strip(), line_num))
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return findings


def audit_project():
    """Audit project for security issues"""
    
    print("=" * 80)
    print("YMERA CREDENTIAL SECURITY AUDIT")
    print("=" * 80)
    
    # Patterns to detect
    sensitive_patterns = {
        'API Key': r'(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}',
        'Secret Key': r'(secret[_-]?key|secretkey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}',
        'JWT Token': r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        'AWS Key': r'AKIA[0-9A-Z]{16}',
        'Private Key': r'-----BEGIN (RSA |)PRIVATE KEY-----',
        'Password': r'password\s*[:=]\s*["\'][^"\']{8,}',
        'Bearer Token': r'Bearer\s+[a-zA-Z0-9_-]{20,}',
        'SSH Key': r'ssh-rsa\s+AAAA[0-9A-Za-z+/]+',
    }
    
    # Files to scan
    project_root = Path('.')
    exclude_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}
    exclude_files = {'.pyc', '.pyo', '.so'}
    
    findings = []
    files_scanned = 0
    
    print("\n🔍 Scanning project files...")
    
    for file_path in project_root.rglob('*'):
        # Skip directories and excluded paths
        if file_path.is_dir():
            continue
        
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        
        if file_path.suffix in exclude_files:
            continue
        
        # Scan file
        file_findings = scan_for_patterns(file_path, sensitive_patterns)
        if file_findings:
            findings.extend([(file_path, *f) for f in file_findings])
        
        files_scanned += 1
    
    # Report findings
    print(f"\n📊 Scanned {files_scanned} files\n")
    
    if findings:
        print(f"⚠️  FOUND {len(findings)} POTENTIAL SECURITY ISSUES:\n")
        
        for file_path, pattern_name, line, line_num in findings:
            print(f"❌ {file_path}:{line_num}")
            print(f"   Type: {pattern_name}")
            print(f"   Content: {line[:80]}...")
            print()
        
        print("\n🚨 ACTION REQUIRED:")
        print("1. Review all findings above")
        print("2. Remove or encrypt sensitive data")
        print("3. Add files to .gitignore")
        print("4. Rotate compromised credentials")
        
        return False
    else:
        print("✅ No obvious security issues detected")
        print("\nNote: This is a basic scan. Manual review is still recommended.")
        return True


if __name__ == "__main__":
    audit_project()
```

Run audit:
```bash
python scripts/audit_credentials.py
```

---

## 📝 DEPLOYMENT SECURITY CHECKLIST

### Before Production Deployment:

- [ ] ✅ All exposed credentials revoked and regenerated
- [ ] ✅ `.env` file created with real credentials
- [ ] ✅ `.env` added to `.gitignore`
- [ ] ✅ Exposed files (`1.txt`) deleted
- [ ] ✅ Git history cleaned of sensitive data
- [ ] ✅ Credential audit script passed
- [ ] ✅ SSH keys regenerated and deployed
- [ ] ✅ All API keys tested and working
- [ ] ✅ Database credentials secured
- [ ] ✅ Redis password set
- [ ] ✅ Encryption keys generated
- [ ] ✅ JWT secrets set to strong values
- [ ] ✅ File permissions set correctly (600 for .env, 600 for keys)
- [ ] ✅ Secrets management system configured (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] ✅ Monitoring and alerting for credential access
- [ ] ✅ Backup encryption keys stored securely offline

---

## 🎯 SUMMARY

**Total Critical Issues Fixed**: 5 Main Issues + Multiple Security Vulnerabilities

1. ✅ **ERROR #3**: Core Engine utils import - FIXED
2. ✅ **Exposed Credentials**: Security breach documented - ACTION REQUIRED
3. ✅ **Missing Utils Module**: Complete utilities created - FIXED
4. ✅ **Incomplete CoreEngine**: Enhanced with production features - FIXED
5. ✅ **Configuration Security**: Secure config manager created - FIXED

**Current Status**: 🔴 **SECURITY BREACH - IMMEDIATE ACTION REQUIRED**

**Next Steps**:
1. IMMEDIATELY revoke all exposed credentials
2. Generate new credentials for all services
3. Update .env with new credentials
4. Run security audit
5. Proceed with deployment only after credentials are secured

---

**DO NOT DEPLOY UNTIL ALL CREDENTIALS ARE SECURED!**
