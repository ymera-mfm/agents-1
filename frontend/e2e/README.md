# E2E Testing Documentation

This document provides comprehensive information about the End-to-End (E2E) testing infrastructure for the AgentFlow application.

## Overview

The E2E test suite uses [Playwright](https://playwright.dev/) to test critical user flows and ensure the application works correctly across different browsers and devices.

## Test Structure

```
e2e/
├── auth/                    # Authentication tests
│   └── login.spec.js
├── dashboard/               # Dashboard functionality tests
│   └── dashboard.spec.js
├── features/                # Feature-specific tests
│   ├── agent-visualization.spec.js
│   └── projects.spec.js
├── integration/             # Integration tests
│   ├── api.spec.js
│   └── state.spec.js
├── performance/             # Performance tests
│   └── load-times.spec.js
├── accessibility/           # Accessibility tests
│   └── a11y.spec.js
└── visual/                  # Visual regression tests
    └── snapshots.spec.js
```

## Installation

### Prerequisites

- Node.js >= 18.0.0
- npm >= 8.0.0

### Setup

1. Install dependencies:
```bash
npm install
```

2. Install Playwright browsers:
```bash
npx playwright install
```

## Running Tests

### All Tests
```bash
npm run test:e2e
```

### Specific Test File
```bash
npx playwright test e2e/auth/login.spec.js
```

### Specific Browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### View Test Report
```bash
npm run test:e2e:report
```

## Test Categories

### 1. Authentication Tests (`e2e/auth/`)

Tests for user authentication flows:
- Login page display
- Valid credential login
- Invalid credential handling
- Logout functionality

### 2. Dashboard Tests (`e2e/dashboard/`)

Tests for dashboard functionality:
- Component rendering
- Navigation between pages
- Data display
- Mobile responsiveness

### 3. Feature Tests (`e2e/features/`)

Tests for specific application features:

#### Project Management (`projects.spec.js`)
- Create new projects
- Edit existing projects
- Delete projects

#### Agent 3D Visualization (`agent-visualization.spec.js`)
- 3D canvas loading
- Control interactions
- Agent information display

### 4. Integration Tests (`e2e/integration/`)

Tests for system integration:

#### API Integration (`api.spec.js`)
- Successful API requests
- Error handling
- Network timeout handling

#### State Management (`state.spec.js`)
- User preference persistence
- State maintenance across navigation

### 5. Performance Tests (`e2e/performance/`)

Tests for application performance:
- Dashboard load time (< 3 seconds)
- Lazy loading verification
- Lighthouse score validation (optional)

### 6. Accessibility Tests (`e2e/accessibility/`)

Tests for accessibility compliance:
- Automated accessibility scanning (axe-core)
- Keyboard navigation
- ARIA label verification

### 7. Visual Regression Tests (`e2e/visual/`)

Tests for visual consistency:
- Desktop screenshot comparison
- Mobile view screenshot comparison

## Configuration

The Playwright configuration is defined in `playwright.config.js`:

- **Test Directory**: `./e2e`
- **Base URL**: `http://localhost:3000`
- **Browsers**: Chromium, Firefox, WebKit
- **Mobile Devices**: Pixel 5, iPhone 12
- **Retries**: 2 (in CI), 0 (locally)
- **Screenshots**: On failure only
- **Trace**: On first retry

## CI/CD Integration

The tests are configured to run in CI/CD environments with:
- Automatic server startup
- Retry on failure (2 retries)
- Single worker execution for stability
- HTML report generation

## Writing New Tests

### Test Template

```javascript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

### Best Practices

1. **Use Descriptive Test Names**: Clearly describe what the test validates
2. **Isolate Tests**: Each test should be independent and not rely on others
3. **Use Page Object Pattern**: For complex flows, create page objects
4. **Wait for Elements**: Use `waitForSelector` or `expect` with retry logic
5. **Mock API Calls**: Use `page.route()` to mock API responses when needed
6. **Clean Up**: Reset state after tests if necessary

### Selectors Priority

1. **User-facing attributes**: `text=`, `aria-label`, `placeholder`
2. **Semantic HTML**: `role=`, `<button>`, `<input>`
3. **Test IDs**: `data-testid`
4. **CSS selectors**: `.class`, `#id` (last resort)

## Test Data Requirements

### Authentication
- Valid credentials: `test@example.com` / `password123`
- Invalid credentials: Any non-matching combination

### Mock API Responses
Tests use `page.route()` to mock API responses. See individual test files for specific mock data.

## Troubleshooting

### Tests Failing Locally

1. **Check if the development server is running**:
   ```bash
   npm start
   ```

2. **Clear Playwright cache**:
   ```bash
   npx playwright install --force
   ```

3. **Update snapshots** (for visual tests):
   ```bash
   npx playwright test --update-snapshots
   ```

### Debugging Tips

1. **Use headed mode** to see what's happening:
   ```bash
   npx playwright test --headed
   ```

2. **Use debug mode** for step-by-step debugging:
   ```bash
   npx playwright test --debug
   ```

3. **Add `page.pause()`** in your test to pause execution:
   ```javascript
   test('my test', async ({ page }) => {
     await page.goto('/');
     await page.pause(); // Pauses here
   });
   ```

4. **Check screenshots** in `test-results/` directory after failures

## Known Issues

1. **Visual tests may fail** on first run - run with `--update-snapshots` to generate baseline images
2. **Mobile Safari tests require macOS** - WebKit on Linux may have slight differences
3. **3D visualization tests** may be flaky due to canvas rendering timing - adjust wait times if needed

## Maintenance

### Updating Tests

- Review and update tests when UI changes
- Update selectors if component structure changes
- Regenerate visual snapshots when design changes
- Keep test data synchronized with backend changes

### Performance Benchmarks

Current performance targets:
- Dashboard load time: < 3 seconds
- API response time: < 1 second
- Canvas initialization: < 2 seconds

Review and adjust these benchmarks based on actual performance data.

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Axe-core Documentation](https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright)
- [Writing Tests Guide](https://playwright.dev/docs/writing-tests)

## Support

For issues or questions about E2E tests:
1. Check the [troubleshooting section](#troubleshooting)
2. Review test logs in `playwright-report/`
3. Contact the development team

---

Last updated: October 2025
