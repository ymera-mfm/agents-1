# Automated Cleanup Script - Usage Guide

## Overview

The `02_automated_cleanup.py` script provides comprehensive automated cleanup for the YMERA backend repository. It intelligently removes duplicate files and old versions while maintaining safety through automatic backups.

## Features

### 1. Smart Duplicate Removal
- Analyzes duplicate file groups
- Keeps the best version based on:
  - Location (prefers core/, agents/, engines/ directories)
  - Path length (shorter paths preferred)
  - Alphabetical order (as tiebreaker)
- Removes other duplicates automatically

### 2. Old Version Cleanup
- Identifies files with multiple versions
- Keeps the newest/most complete version based on:
  - Main/production status (no suffix or _production)
  - File size/lines of code (larger is usually more complete)
- Removes outdated versions automatically

### 3. Safety Features
- **Automatic Backups**: All removed files backed up to `cleanup/backup/`
- **Confirmation Required**: Must type 'yes' to proceed
- **Detailed Logging**: Complete log of all actions in `cleanup_log.json`
- **Error Handling**: Continues on errors, reports issues

## Prerequisites

Before running the automated cleanup:

1. **Run Analysis First**:
   ```bash
   python3 cleanup/01_analyze_repository.py
   ```
   This generates `cleanup/01_analysis_report.json` which the cleanup script needs.

2. **Review Analysis Report**:
   ```bash
   cat cleanup/01_ANALYSIS_REPORT.md
   ```
   Understand what will be removed before proceeding.

## Usage

### Basic Usage

```bash
cd /path/to/ymera_y

# Run the automated cleanup
python3 cleanup/02_automated_cleanup.py

# When prompted, type 'yes' to proceed or 'no' to abort
```

### What Happens

The script will:

1. **Load Analysis**: Reads `cleanup/01_analysis_report.json`
2. **Remove Duplicates**: 
   - Shows which file is kept
   - Removes other duplicates
   - Backs up all removed files
3. **Remove Old Versions**:
   - Shows which version is kept
   - Removes outdated versions
   - Backs up all removed files
4. **Save Log**: Creates `cleanup/backup/cleanup_log.json`

### Example Output

```
================================================================================
AUTOMATED CLEANUP
================================================================================

⚠️  This will:
   - Remove duplicate files
   - Remove old versions
   - Backup all removed files

Proceed? (yes/no): yes

1. Removing duplicates...

   Keeping: extensions.py
   ✅ Removed: api_extensions.py
      Reason: Duplicate of extensions.py

2. Removing old versions...

   Base: metrics
   Keeping: metrics.py (399 lines)
   ✅ Removed: metrics_old.py
      Reason: Old version of metrics.py

3. Saving cleanup log...

   Log saved: /path/to/ymera_y/cleanup/backup/cleanup_log.json

================================================================================
✅ Cleanup Complete!
   Removed: 8 files
   Backup: /path/to/ymera_y/cleanup/backup
================================================================================
```

## Backup & Recovery

### Backup Location

All removed files are backed up to:
```
cleanup/backup/
├── api_extensions.py
├── api.gateway.py
├── metrics_old.py
└── cleanup_log.json
```

### Recovery

To restore a removed file:

```bash
# View backup contents
ls -la cleanup/backup/

# Restore a file
cp cleanup/backup/path/to/file.py path/to/file.py
```

### Cleanup Log

The `cleanup_log.json` contains:
- Timestamp of cleanup
- Total files removed
- Detailed actions for each file
- Reason for removal
- Backup location

Example:
```json
{
  "timestamp": "2025-10-21T03:30:00",
  "removed_files": 8,
  "actions": [
    {
      "action": "remove",
      "file": "api_extensions.py",
      "reason": "Duplicate of extensions.py",
      "backup": "cleanup/backup/api_extensions.py",
      "timestamp": "2025-10-21T03:30:01"
    }
  ],
  "files": ["api_extensions.py", "..."]
}
```

## Comparison with Other Scripts

### vs. 02_remove_duplicates.py

| Feature | 02_automated_cleanup.py | 02_remove_duplicates.py |
|---------|------------------------|-------------------------|
| **Purpose** | Comprehensive automated cleanup | Targeted duplicate removal |
| **Data Source** | Analysis JSON file | Hardcoded list |
| **Duplicates** | All detected duplicates | Specific known duplicates |
| **Versions** | ✅ Yes, removes old versions | ❌ No |
| **Mode** | Interactive confirmation | Dry-run + execute flags |
| **Smart Selection** | ✅ Yes (location, size, etc.) | Manual specification |
| **Backup Location** | cleanup/backup/ | cleanup/backups/TIMESTAMP/ |

**When to use each:**
- **02_automated_cleanup.py**: For comprehensive cleanup of duplicates AND versions
- **02_remove_duplicates.py**: For Phase 2 specific duplicates only

## Safety Notes

1. **Always review analysis first**: Understand what will be removed
2. **Backups are created automatically**: All removed files are safe
3. **Script asks for confirmation**: You must type 'yes' to proceed
4. **Can be safely re-run**: Already-removed files are skipped
5. **Git can restore**: Use `git checkout -- file.py` for git-tracked files

## Troubleshooting

### Analysis file not found
```
❌ Analysis file not found!
   Run: python3 cleanup/01_analyze_repository.py
```
**Solution**: Run the analysis script first to generate the required JSON file.

### File not found during removal
```
⚠️  Skip (not found): path/to/file.py
```
**Solution**: File was already removed or never existed. This is safe to ignore.

### Error during removal
```
❌ Error removing path/to/file.py: Permission denied
```
**Solution**: Check file permissions or if file is in use. The script continues with other files.

## Next Steps

After running automated cleanup:

1. **Verify Changes**:
   ```bash
   git status
   git diff
   ```

2. **Run Tests** (if available):
   ```bash
   pytest
   ```

3. **Review Removed Files**:
   ```bash
   cat cleanup/backup/cleanup_log.json
   ```

4. **Commit Changes**:
   ```bash
   git add -u
   git commit -m "Automated cleanup: remove duplicates and old versions"
   ```

5. **Continue to Next Phase**: See `cleanup/README.md` for Phase 3 and beyond.

## Related Documentation

- **Analysis Results**: `cleanup/01_ANALYSIS_REPORT.md`
- **Phase 2 Summary**: `PHASE2_COMPLETE.md`
- **Implementation Guide**: `cleanup/README.md`
- **Getting Started**: `cleanup/GETTING_STARTED.md`
- **Index**: `cleanup/INDEX.md`
