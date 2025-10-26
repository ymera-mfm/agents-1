// Import Cypress commands
import './commands';

// Import axe for accessibility testing
import 'cypress-axe';

// Import code coverage
import '@cypress/code-coverage/support';

// Global before hook
before(() => {
  // Clear all cookies and local storage before tests
  cy.clearCookies();
  cy.clearLocalStorage();
});

// Global beforeEach hook
beforeEach(() => {
  // Preserve session cookies if needed
  cy.session('user-session', () => {
    // Session logic here
  }, {
    validate() {
      // Validation logic
    },
    cacheAcrossSpecs: true
  });
});

// Handle uncaught exceptions
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent Cypress from failing the test on certain errors
  if (err.message.includes('ResizeObserver loop')) {
    return false;
  }
  if (err.message.includes('Script error')) {
    return false;
  }
  return true;
});

// Add custom command to check for console errors
Cypress.on('window:before:load', (win) => {
  cy.spy(win.console, 'error');
  cy.spy(win.console, 'warn');
});
