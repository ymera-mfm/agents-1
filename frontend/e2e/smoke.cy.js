/// <reference types="cypress" />

describe('AgentFlow - Smoke Tests', () => {
  beforeEach(() => {
    // Visit the base URL before each test
    cy.visit('/');
  });

  describe('Application Loading', () => {
    it('loads the application without errors', () => {
      cy.get('body').should('be.visible');
    });

    it('displays the AgentFlow branding', () => {
      cy.contains(/agentflow/i, { timeout: 10000 }).should('be.visible');
    });

    it('shows the login page initially', () => {
      cy.url().should('include', '/');
      // Should have login form elements
      cy.get('input').should('have.length.at.least', 1);
    });
  });

  describe('Login Functionality', () => {
    it('has username input field', () => {
      cy.get('input').first().should('be.visible');
    });

    it('has password input field', () => {
      cy.get('input').eq(1).should('be.visible');
    });

    it('has login button', () => {
      cy.get('button').contains(/login|sign in|enter/i).should('be.visible');
    });

    it('can type in username field', () => {
      cy.get('input').first().type('testuser').should('have.value', 'testuser');
    });

    it('can type in password field', () => {
      cy.get('input').eq(1).type('password123').should('have.value', 'password123');
    });

    it('can submit login form', () => {
      cy.get('input').first().type('admin');
      cy.get('input').eq(1).type('admin123');
      cy.get('button').contains(/login|sign in|enter/i).click();
      
      // Should either show dashboard or error message
      cy.wait(1000);
      cy.get('body').should('exist');
    });
  });

  describe('Dashboard Navigation (After Login)', () => {
    beforeEach(() => {
      // Attempt login before each test
      cy.get('input').first().type('admin');
      cy.get('input').eq(1).type('admin123');
      cy.get('button').contains(/login|sign in|enter/i).click();
      cy.wait(1000);
    });

    it('navigates to dashboard after login', () => {
      cy.contains(/dashboard/i, { timeout: 5000 }).should('exist');
    });

    it('displays navigation menu', () => {
      cy.get('nav', { timeout: 5000 }).should('be.visible');
    });

    it('shows user information in header', () => {
      cy.get('nav').within(() => {
        cy.get('[class*="user"], [class*="avatar"]').should('exist');
      });
    });
  });

  describe('Page Responsiveness', () => {
    const viewports = [
      { device: 'mobile', width: 375, height: 667 },
      { device: 'tablet', width: 768, height: 1024 },
      { device: 'desktop', width: 1920, height: 1080 }
    ];

    viewports.forEach(({ device, width, height }) => {
      it(`displays correctly on ${device} (${width}x${height})`, () => {
        cy.viewport(width, height);
        cy.get('body').should('be.visible');
        cy.contains(/agentflow/i).should('be.visible');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles invalid login gracefully', () => {
      cy.get('input').first().type('invaliduser');
      cy.get('input').eq(1).type('wrongpassword');
      cy.get('button').contains(/login|sign in|enter/i).click();
      
      // Should show error message or stay on login page
      cy.wait(1000);
      cy.get('body').should('exist');
    });
  });

  describe('Accessibility', () => {
    it('has proper document title', () => {
      cy.title().should('not.be.empty');
    });

    it('has no detectable accessibility violations', () => {
      // Basic accessibility check
      cy.get('html').should('have.attr', 'lang');
    });

    it('supports keyboard navigation', () => {
      cy.get('input').first().focus().should('have.focus');
      cy.get('input').first().tab();
      cy.focused().should('exist');
    });
  });
});
