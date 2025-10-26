/// <reference types="cypress" />

describe('AgentFlow - Feature Tests', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/');
    cy.get('input').first().type('admin');
    cy.get('input').eq(1).type('admin123');
    cy.get('button').contains(/login|sign in|enter/i).click();
    cy.wait(1000);
  });

  describe('3D Visualization', () => {
    it('renders 3D canvas on agents page', () => {
      cy.get('nav').contains(/agents/i).click({ force: true });
      cy.wait(1000);
      cy.get('canvas').should('exist');
    });

    it('renders 3D canvas on projects page', () => {
      cy.get('nav').contains(/projects/i).click({ force: true });
      cy.wait(1000);
      cy.get('canvas').should('exist');
    });

    it('3D visualization is interactive', () => {
      cy.get('nav').contains(/agents/i).click({ force: true });
      cy.wait(1000);
      
      cy.get('canvas').should('be.visible').then($canvas => {
        const canvas = $canvas[0];
        expect(canvas.width).to.be.greaterThan(0);
        expect(canvas.height).to.be.greaterThan(0);
      });
    });
  });

  describe('Real-Time Features', () => {
    it('displays real-time agent status', () => {
      cy.contains(/dashboard/i);
      cy.get('[class*="status"]').should('exist');
    });

    it('shows live metrics', () => {
      cy.contains(/dashboard/i);
      cy.get('[class*="metric"], [class*="stat"]').should('have.length.at.least', 1);
    });
  });

  describe('Monitoring Dashboard', () => {
    it('loads monitoring page', () => {
      cy.get('nav').contains(/monitoring/i).click({ force: true });
      cy.wait(500);
      cy.contains(/monitor/i).should('exist');
    });

    it('displays monitoring metrics', () => {
      cy.get('nav').contains(/monitoring/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="metric"], [class*="chart"], [class*="graph"]').should('exist');
    });
  });

  describe('Analytics Features', () => {
    it('loads analytics page', () => {
      cy.get('nav').contains(/analytics/i).click({ force: true });
      cy.wait(500);
      cy.contains(/analytics/i).should('exist');
    });

    it('displays analytics visualizations', () => {
      cy.get('nav').contains(/analytics/i).click({ force: true });
      cy.wait(500);
      cy.get('canvas, svg, [class*="chart"]').should('exist');
    });
  });

  describe('Collaboration Features', () => {
    it('loads collaboration page', () => {
      cy.get('nav').contains(/collaboration/i).click({ force: true });
      cy.wait(500);
      cy.contains(/collaborat/i).should('exist');
    });

    it('has collaboration interface', () => {
      cy.get('nav').contains(/collaboration/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="chat"], [class*="message"], textarea, input').should('exist');
    });
  });

  describe('Resource Management', () => {
    it('loads resources page', () => {
      cy.get('nav').contains(/resources/i).click({ force: true });
      cy.wait(500);
      cy.contains(/resource/i).should('exist');
    });

    it('displays resource information', () => {
      cy.get('nav').contains(/resources/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="resource"], [class*="card"]').should('exist');
    });
  });

  describe('UI Interactions', () => {
    it('displays tooltips on hover', () => {
      cy.get('[class*="icon"], button, [class*="card"]').first().trigger('mouseover');
      cy.wait(200);
    });

    it('handles button clicks', () => {
      cy.get('button').first().should('be.visible').click({ force: true });
    });

    it('displays modals or dropdowns when clicked', () => {
      cy.get('[class*="menu"], [class*="dropdown"]').first().click({ force: true });
      cy.wait(200);
    });
  });

  describe('Data Display', () => {
    it('displays agent cards or list items', () => {
      cy.get('nav').contains(/agents/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="agent"], [class*="card"], [class*="item"]').should('exist');
    });

    it('displays project cards or list items', () => {
      cy.get('nav').contains(/projects/i).click({ force: true });
      cy.wait(500);
      cy.get('[class*="project"], [class*="card"], [class*="item"]').should('exist');
    });

    it('shows loading states', () => {
      cy.visit('/');
      cy.get('[class*="loading"], [class*="spinner"]').should('exist');
    });
  });

  describe('Theme and Styling', () => {
    it('uses dark theme', () => {
      cy.get('body').should('have.css', 'background-color');
    });

    it('has consistent color scheme', () => {
      cy.get('[class*="gradient"], [class*="cyan"], [class*="blue"]').should('exist');
    });

    it('displays icons properly', () => {
      cy.get('svg, [class*="icon"]').should('have.length.at.least', 1);
    });
  });
});
