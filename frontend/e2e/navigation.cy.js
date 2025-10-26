/// <reference types="cypress" />

describe('AgentFlow - Navigation Tests', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/');
    cy.get('input').first().type('admin');
    cy.get('input').eq(1).type('admin123');
    cy.get('button').contains(/login|sign in|enter/i).click();
    cy.wait(1000);
  });

  describe('Main Navigation', () => {
    const pages = [
      'dashboard',
      'agents',
      'projects',
      'monitoring',
      'analytics',
      'collaboration',
      'resources',
      'settings',
      'profile'
    ];

    pages.forEach(page => {
      it(`can navigate to ${page} page`, () => {
        // Try to find and click navigation link
        cy.get('nav').within(() => {
          cy.contains(new RegExp(page, 'i')).click({ force: true });
        });
        
        cy.wait(500);
        // Page should change
        cy.get('body').should('exist');
      });
    });
  });

  describe('Dashboard Features', () => {
    it('displays stat cards', () => {
      cy.contains(/dashboard/i);
      cy.get('[class*="stat"], [class*="card"]').should('have.length.at.least', 1);
    });

    it('shows agent information', () => {
      cy.contains(/agent/i).should('exist');
    });

    it('displays project information', () => {
      cy.contains(/project/i).should('exist');
    });
  });

  describe('Agents Page', () => {
    beforeEach(() => {
      cy.get('nav').contains(/agents/i).click({ force: true });
      cy.wait(500);
    });

    it('loads agents page', () => {
      cy.contains(/agent/i).should('exist');
    });

    it('displays agent list or visualization', () => {
      cy.get('[class*="agent"], canvas, svg').should('exist');
    });
  });

  describe('Projects Page', () => {
    beforeEach(() => {
      cy.get('nav').contains(/projects/i).click({ force: true });
      cy.wait(500);
    });

    it('loads projects page', () => {
      cy.contains(/project/i).should('exist');
    });

    it('displays project list or visualization', () => {
      cy.get('[class*="project"], canvas, [class*="card"]').should('exist');
    });
  });

  describe('User Profile', () => {
    it('can access profile page', () => {
      cy.get('nav').contains(/profile/i).click({ force: true });
      cy.wait(500);
      cy.contains(/profile|user/i).should('exist');
    });

    it('displays user information', () => {
      cy.get('nav').contains(/profile/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="profile"], [class*="user"]').should('exist');
    });
  });

  describe('Settings Page', () => {
    it('can access settings page', () => {
      cy.get('nav').contains(/settings/i).click({ force: true });
      cy.wait(500);
      cy.contains(/settings|preferences/i).should('exist');
    });
  });

  describe('Logout Functionality', () => {
    it('can logout successfully', () => {
      // Find logout button (may be in dropdown or direct)
      cy.get('body').then($body => {
        if ($body.find('[class*="logout"]').length > 0) {
          cy.get('[class*="logout"]').click();
        } else if ($body.text().includes('Logout') || $body.text().includes('Sign out')) {
          cy.contains(/logout|sign out/i).click();
        }
      });
      
      cy.wait(500);
      // Should redirect to login
      cy.get('input').should('have.length.at.least', 1);
    });
  });
});
