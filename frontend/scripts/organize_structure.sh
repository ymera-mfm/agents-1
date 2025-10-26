#!/bin/bash

# Create proper directory structure
mkdir -p src/components/agents
mkdir -p src/components/collaboration
mkdir -p src/components/common
mkdir -p src/components/projects
mkdir -p src/components/resources
mkdir -p src/context
mkdir -p src/hooks
mkdir -p src/pages
mkdir -p src/services
mkdir -p src/styles
mkdir -p src/utils
mkdir -p public
mkdir -p config
mkdir -p store

# Move files to correct locations
mv src_App.js.js src/App.js
mv src_index.js.js src/index.js

# Move components
mv src_components_Navigation.jsx.js src/components/Navigation.jsx
mv src_components_agents_*.js src/components/agents/
mv src_components_collaboration_*.js src/components/collaboration/
mv src_components_common_*.js src/components/common/
mv src_components_projects_*.js src/components/projects/
mv src_components_resources_*.js src/components/resources/

# Move context
mv src_context_*.js src/context/

# Move hooks
mv src_hooks_*.js src/hooks/

# Move pages
mv src_pages_*.js src/pages/

# Move services
mv src_services_*.js src/services/

# Move styles
mv src_styles_*.css src/styles/

# Move utils
mv src_utils_*.js src/utils/

# Move public files
mv public_index.html.html public/index.html

# Move config files
mv config_production.js.jsx config/production.js

# Move store
mv store_index.js.jsx store/index.js

# Move package.json
mv package.json.json package.json

# Move other component files
mv components_*.jsx src/components/
mv hooks_*.jsx src/hooks/
mv services_*.jsx src/services/

# Clean up file extensions
find src -name "*.js.js" -exec bash -c 'mv "$1" "${1%.js}"' _ {} \;
find src -name "*.jsx.js" -exec bash -c 'mv "$1" "${1%.js}"' _ {} \;
find src -name "*.jsx.jsx" -exec bash -c 'mv "$1" "${1%.jsx}.jsx"' _ {} \;
find config -name "*.js.jsx" -exec bash -c 'mv "$1" "${1%.jsx}"' _ {} \;
find store -name "*.js.jsx" -exec bash -c 'mv "$1" "${1%.jsx}"' _ {} \;

echo "Project structure organized successfully!"
