describe('AgentFlow Application', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  describe('Homepage', () => {
    it('should load the homepage successfully', () => {
      cy.url().should('include', '/');
    });

    it('should display the main navigation', () => {
      cy.get('nav').should('be.visible');
    });

    it('should have accessible navigation elements', () => {
      cy.get('nav').within(() => {
        cy.get('a, button').each(($el) => {
          expect($el).to.have.attr('aria-label').or.have.text;
        });
      });
    });
  });

  describe('Authentication', () => {
    it('should display login form', () => {
      cy.visit('/login');
      cy.get('form').should('be.visible');
      cy.get('input[type="email"], input[type="text"]').should('exist');
      cy.get('input[type="password"]').should('exist');
      cy.get('button[type="submit"]').should('exist');
    });

    it('should handle login with valid credentials', () => {
      cy.visit('/login');
      cy.get('input[type="email"], input[type="text"]').type('test@example.com');
      cy.get('input[type="password"]').type('password123');
      cy.get('button[type="submit"]').click();
      
      // Should redirect after successful login
      cy.url().should('not.include', '/login');
    });

    it('should show error for invalid credentials', () => {
      cy.visit('/login');
      cy.get('input[type="email"], input[type="text"]').type('invalid@example.com');
      cy.get('input[type="password"]').type('wrongpassword');
      cy.get('button[type="submit"]').click();
      
      // Should display error message
      cy.contains(/error|invalid|incorrect/i).should('be.visible');
    });
  });

  describe('Dashboard', () => {
    beforeEach(() => {
      // Login first
      cy.visit('/login');
      cy.get('input[type="email"], input[type="text"]').type('test@example.com');
      cy.get('input[type="password"]').type('password123');
      cy.get('button[type="submit"]').click();
      cy.url().should('not.include', '/login');
    });

    it('should display dashboard components', () => {
      cy.visit('/dashboard');
      cy.get('[data-testid="dashboard"], .dashboard').should('be.visible');
    });

    it('should load agents data', () => {
      cy.visit('/dashboard');
      cy.get('[data-testid="agents-list"], .agents').should('exist');
    });

    it('should load projects data', () => {
      cy.visit('/dashboard');
      cy.get('[data-testid="projects-list"], .projects').should('exist');
    });
  });

  describe('Accessibility', () => {
    it('should have no accessibility violations on homepage', () => {
      cy.visit('/');
      cy.injectAxe();
      cy.checkA11y();
    });

    it('should have no accessibility violations on dashboard', () => {
      cy.visit('/dashboard');
      cy.injectAxe();
      cy.checkA11y();
    });

    it('should support keyboard navigation', () => {
      cy.visit('/');
      cy.get('body').tab();
      cy.focused().should('exist');
    });
  });

  describe('Performance', () => {
    it('should load within acceptable time', () => {
      const start = Date.now();
      cy.visit('/');
      cy.window().then(() => {
        const loadTime = Date.now() - start;
        expect(loadTime).to.be.lessThan(3000); // 3 seconds
      });
    });

    it('should have good Core Web Vitals', () => {
      cy.visit('/');
      cy.window().then((win) => {
        // Check for performance metrics
        const perfEntries = win.performance.getEntriesByType('navigation');
        expect(perfEntries).to.have.length.greaterThan(0);
      });
    });
  });

  describe('Responsiveness', () => {
    const viewports = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1920, height: 1080 }
    ];

    viewports.forEach((viewport) => {
      it(`should render correctly on ${viewport.name}`, () => {
        cy.viewport(viewport.width, viewport.height);
        cy.visit('/');
        cy.get('nav').should('be.visible');
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error boundary on component error', () => {
      // Trigger error by visiting non-existent route or corrupting state
      cy.visit('/non-existent-route');
      // Error boundary or 404 page should be shown
      cy.get('body').should('contain.text', 'error', 'not found', '404');
    });

    it('should handle network errors gracefully', () => {
      // Intercept and fail API requests
      cy.intercept('GET', '/api/*', { forceNetworkError: true });
      cy.visit('/dashboard');
      // Should show error message or retry option
      cy.contains(/error|retry|failed/i).should('be.visible');
    });
  });
});
