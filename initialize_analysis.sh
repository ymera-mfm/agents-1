#!/bin/bash
# initialize_analysis.sh

echo "🚀 STARTING COMPREHENSIVE REPOSITORY ANALYSIS"

# 1. Get all branches
echo "📋 Fetching all branches..."
git fetch --all || true
git branch -a

# 2. Create analysis directory structure
mkdir -p repository_analysis/{agents,modules,engines,systems,configs,database,api,utils}
mkdir -p enhanced_platform/{core,integrations,features,testing,deployment}

# 3. Set up analysis tools
# Backup existing analysis_config.json if it exists
if [ -f analysis_config.json ]; then
    echo "⚠️  analysis_config.json already exists. Backing up to analysis_config.json.bak"
    mv analysis_config.json "analysis_config.json.bak.$(date +%Y%m%d_%H%M%S)"
fi
cat > analysis_config.json << EOF
{
    "analysis_scope": {
        "file_extensions": [".py", ".js", ".ts", ".java", ".go", ".rs", ".md", ".yaml", ".yml", ".json"],
        "exclude_dirs": ["node_modules", ".git", "dist", "build", "vendor"],
        "target_patterns": ["*agent*", "*engine*", "*module*", "*system*", "*manager*", "*service*"]
    },
    "categorization_rules": {
        "agents": ["*agent*", "*bot*", "*assistant*"],
        "modules": ["*module*", "*component*", "*plugin*"],
        "engines": ["*engine*", "*processor*", "*analyzer*"],
        "systems": ["*system*", "*platform*", "*framework*"],
        "configs": ["config*", "setting*", ".env*"]
    }
}
EOF
