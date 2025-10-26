// Custom Cypress commands

// Login command
Cypress.Commands.add('login', (email = 'test@example.com', password = 'password123') => {
  cy.visit('/login');
  cy.get('input[type="email"], input[type="text"]').type(email);
  cy.get('input[type="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('not.include', '/login');
});

// Logout command
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="logout-button"], button:contains("Logout")').click();
  cy.url().should('include', '/login');
});

// Wait for API call
Cypress.Commands.add('waitForApi', (alias) => {
  cy.wait(`@${alias}`).its('response.statusCode').should('eq', 200);
});

// Check loading state
Cypress.Commands.add('checkLoading', () => {
  cy.get('[data-testid="loading"], .loading, .spinner').should('exist');
});

// Wait for loading to complete
Cypress.Commands.add('waitForLoading', () => {
  cy.get('[data-testid="loading"], .loading, .spinner', { timeout: 10000 })
    .should('not.exist');
});

// Drag and drop command
Cypress.Commands.add('drag', { prevSubject: 'element' }, (subject, targetEl) => {
  cy.wrap(subject)
    .trigger('mousedown', { which: 1 })
    .trigger('mousemove', { clientX: 100, clientY: 100 })
    .get(targetEl)
    .trigger('mousemove')
    .trigger('mouseup', { force: true });
});

// Tab key navigation
Cypress.Commands.add('tab', { prevSubject: 'optional' }, (subject) => {
  const el = subject ? cy.wrap(subject) : cy.focused();
  return el.trigger('keydown', { keyCode: 9, which: 9, key: 'Tab' });
});

// Assert accessibility
Cypress.Commands.add('checkAccessibility', (context, options) => {
  cy.injectAxe();
  cy.checkA11y(context, options);
});

// Take screenshot with custom name
Cypress.Commands.add('captureScreen', (name) => {
  cy.screenshot(name, { capture: 'fullPage' });
});

// Assert no console errors
Cypress.Commands.add('assertNoConsoleErrors', () => {
  cy.window().then((win) => {
    expect(win.console.error).to.have.callCount(0);
  });
});

// Mock API response
Cypress.Commands.add('mockApi', (method, url, response, alias) => {
  cy.intercept(method, url, response).as(alias);
});

// Set local storage item
Cypress.Commands.add('setLocalStorage', (key, value) => {
  cy.window().then((win) => {
    win.localStorage.setItem(key, JSON.stringify(value));
  });
});

// Get local storage item
Cypress.Commands.add('getLocalStorage', (key) => {
  return cy.window().then((win) => {
    return JSON.parse(win.localStorage.getItem(key));
  });
});

// Clear specific local storage item
Cypress.Commands.add('clearLocalStorageItem', (key) => {
  cy.window().then((win) => {
    win.localStorage.removeItem(key);
  });
});

// Test responsive design
Cypress.Commands.add('testResponsive', (selector, viewports) => {
  viewports.forEach((viewport) => {
    cy.viewport(viewport.width, viewport.height);
    cy.get(selector).should('be.visible');
  });
});

// Fill form
Cypress.Commands.add('fillForm', (formData) => {
  Object.keys(formData).forEach((key) => {
    cy.get(`[name="${key}"]`).clear().type(formData[key]);
  });
});

// Assert URL contains
Cypress.Commands.add('urlContains', (path) => {
  cy.url().should('include', path);
});

// Assert element has text
Cypress.Commands.add('hasText', { prevSubject: true }, (subject, text) => {
  cy.wrap(subject).should('contain.text', text);
});

// Click outside element
Cypress.Commands.add('clickOutside', () => {
  cy.get('body').click(0, 0);
});

// Hover over element
Cypress.Commands.add('hover', { prevSubject: true }, (subject) => {
  cy.wrap(subject).trigger('mouseover');
});

// Double click
Cypress.Commands.add('dblclick', { prevSubject: true }, (subject) => {
  cy.wrap(subject).dblclick();
});

// Assert element count
Cypress.Commands.add('assertCount', { prevSubject: true }, (subject, count) => {
  cy.wrap(subject).should('have.length', count);
});
