# AgentFlow Frontend - Developer Quick Start

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run linter
npm run lint

# Format code
npm run format
```

## 📁 Directory Structure

```
src/
├── components/       # Reusable UI components
│   └── common/      # Shared components (LoadingSpinner, ErrorBoundary, etc.)
├── features/        # Feature modules (agents, projects, dashboard, etc.)
├── pages/           # Top-level page components
├── hooks/           # Custom React hooks
├── services/        # API, WebSocket, Logger, Security, Cache
├── store/           # State management (AppContext, Redux)
├── config/          # Configuration and constants
├── utils/           # Utility functions
├── styles/          # Global CSS
└── assets/          # Images, fonts, etc.
```

## 📝 Import Path Patterns

### From Root (`src/`)
```javascript
import App from './App';
import { useApp } from './store/AppContext';
```

### From Features (`src/features/xxx/`)
```javascript
import { useApp } from '../../store/AppContext';
import { SomeComponent } from '../../components/SomeComponent';
import { LocalComponent } from './LocalComponent';
```

### From Components (`src/components/`)
```javascript
import { useApp } from '../store/AppContext';
import { api } from '../services/api';
import { CommonComponent } from './common/CommonComponent';
```

### From Pages (`src/pages/`)
```javascript
import { useApp } from '../store/AppContext';
import { SomeComponent } from '../components/SomeComponent';
```

## 🎨 Tech Stack

- **React 18** - UI library
- **React Router** - Routing
- **Zustand** - Primary state management
- **Redux Toolkit** - Complex state management
- **Firebase** - Backend services
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Three.js** - 3D visualizations
- **Framer Motion** - Animations

## 🔧 Available Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start development server (port 3000) |
| `npm run build` | Create production build |
| `npm test` | Run tests |
| `npm run lint` | Check code quality |
| `npm run lint:fix` | Fix linting issues |
| `npm run format` | Format code with Prettier |
| `npm run analyze` | Analyze bundle size |

## 🏗️ Adding New Features

### 1. Create Feature Module
```bash
mkdir -p src/features/my-feature
```

### 2. Create Files
```javascript
// src/features/my-feature/MyFeaturePage.jsx
import React from 'react';
import { useApp } from '../../store/AppContext';

export const MyFeaturePage = () => {
  const { user } = useApp();
  
  return (
    <div className="container mx-auto p-4">
      <h1>My Feature</h1>
    </div>
  );
};
```

### 3. Create State Management (if needed)
```javascript
// src/features/my-feature/myFeatureSlice.js
import { createSlice } from '@reduxjs/toolkit';

const myFeatureSlice = createSlice({
  name: 'myFeature',
  initialState: { data: [] },
  reducers: {
    setData: (state, action) => {
      state.data = action.payload;
    }
  }
});

export const { setData } = myFeatureSlice.actions;
export default myFeatureSlice.reducer;
```

### 4. Add Route
```javascript
// src/App.js
const MyFeaturePage = lazy(() => import('./features/my-feature/MyFeaturePage'));

// In component:
{page === 'my-feature' && <MyFeaturePage />}
```

## 🎯 Best Practices

### Component Structure
```javascript
import React, { useState, useEffect } from 'react';
import { useApp } from '../../store/AppContext';
import { Icon } from 'lucide-react';

export const MyComponent = ({ prop1, prop2 }) => {
  // 1. Hooks
  const { user } = useApp();
  const [state, setState] = useState(null);
  
  // 2. Effects
  useEffect(() => {
    // Effect logic
  }, []);
  
  // 3. Handlers
  const handleClick = () => {
    // Handler logic
  };
  
  // 4. Render
  return (
    <div className="my-component">
      {/* JSX */}
    </div>
  );
};
```

### File Naming
- Components: `PascalCase.jsx` (e.g., `MyComponent.jsx`)
- Hooks: `camelCase.js` (e.g., `useMyHook.js`)
- Utils: `camelCase.js` (e.g., `formatDate.js`)
- Styles: `kebab-case.css` (e.g., `my-component.css`)

### Import Order
```javascript
// 1. React and external libraries
import React, { useState } from 'react';
import { motion } from 'framer-motion';

// 2. Internal services and utils
import { api } from '../../services/api';
import { formatDate } from '../../utils/formatDate';

// 3. Components
import { Button } from '../../components/Button';

// 4. Styles and assets
import './styles.css';
```

## 🔒 Security Guidelines

1. **Never commit secrets** - Use environment variables
2. **Sanitize user input** - Use `security.sanitizeInput()`
3. **Use HTTPS** - Always in production
4. **Validate data** - Both client and server side
5. **Keep dependencies updated** - Run `npm audit` regularly

## 🐛 Common Issues

### Build Fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Import Errors
- Check relative path depth (`../` vs `../../`)
- Verify file exists at expected location
- Check for typos in import statement

### Missing Dependencies
```bash
npm install <package-name>
```

## 📚 Resources

- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Zustand](https://github.com/pmndrs/zustand)
- [Redux Toolkit](https://redux-toolkit.js.org)
- [Lucide Icons](https://lucide.dev)

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test: `npm run lint && npm run build`
3. Commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Create Pull Request

## 📞 Support

For issues or questions:
- Check documentation in `/docs`
- Review `REORGANIZATION_COMPLETE.md` for detailed info
- Contact the team

---

**Last Updated:** October 2025
**Version:** 1.0.0
