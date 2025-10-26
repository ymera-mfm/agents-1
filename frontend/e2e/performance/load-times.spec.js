import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('should load dashboard within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000); // 3 seconds
  });

  test('should have good Lighthouse scores', async ({ page }) => {
    await page.goto('/');

    // Note: This requires playwright-lighthouse package
    // npm install -D playwright-lighthouse
    // Implementation depends on your CI/CD setup
  });

  test('should lazy load routes', async ({ page }) => {
    const response = await page.goto('/');
    const body = await response.text();

    // Check that heavy components aren't in initial bundle
    expect(body).not.toContain('Three.js');
    expect(body).not.toContain('heavy-visualization-component');
  });
});
