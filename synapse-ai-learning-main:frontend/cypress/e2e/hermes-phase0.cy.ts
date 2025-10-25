// Hermes Phase 0
/**
 * Hermes flow E2E tests
 * Tests the basic Analyze -> Plan workflow
 */

describe('Hermes Flow', () => { // Hermes Phase 0
  beforeEach(() => {
    // Hermes Phase 0 - Visit Hermes landing page
    cy.visit('/hermes')
  })

  it('should display Hermes landing page', () => { // Hermes Phase 0
    cy.contains('Welcome to Hermes').should('be.visible')
    cy.contains('Create Your First Plan').should('be.visible')
  })

  it('should navigate to analyze page', () => { // Hermes Phase 0
    cy.contains('Create Your First Plan').click()
    cy.url().should('include', '/hermes/analyze')
    cy.contains('Analyze Content').should('be.visible')
  })

  it('should submit plan request with handle', () => { // Hermes Phase 0
    // Navigate to analyze page
    cy.visit('/hermes/analyze')
    
    // Fill in handle
    cy.get('input[id="handle"]').type('testcreator')
    
    // Select goal
    cy.get('#goal').click()
    cy.contains('Growth').click()
    
    // Submit form
    cy.contains('Generate Plan').click()
    
    // Should navigate to plan page
    cy.url().should('match', /\/hermes\/plan\/[a-f0-9-]+/)
    
    // Should show plan status
    cy.contains('Content Plan').should('be.visible')
  })

  it('should display queued/running status on plan page', () => { // Hermes Phase 0
    // Visit a stub plan page
    const stubPlanId = '123e4567-e89b-12d3-a456-426614174000'
    cy.visit(`/hermes/plan/${stubPlanId}`)
    
    // Should show status (queued, running, ready, or failed)
    cy.contains(/Queued|Analyzing|Ready|Failed/).should('be.visible')
    
    // Should show plan ID
    cy.contains(stubPlanId).should('be.visible')
  })

  it('should submit plan request with links', () => { // Hermes Phase 0
    cy.visit('/hermes/analyze')
    
    // Switch to links tab
    cy.contains('Video Links').click()
    
    // Fill in links
    cy.get('textarea[id="links"]').type(
      'https://tiktok.com/@user/video/123\nhttps://tiktok.com/@user/video/456'
    )
    
    // Select goal
    cy.get('#goal').click()
    cy.contains('Leads').click()
    
    // Submit
    cy.contains('Generate Plan').click()
    
    // Should navigate to plan page
    cy.url().should('match', /\/hermes\/plan\/[a-f0-9-]+/)
  })

  it('should require either handle or links', () => { // Hermes Phase 0
    cy.visit('/hermes/analyze')
    
    // Try to submit without handle
    cy.contains('Generate Plan').click()
    
    // Should show error toast
    cy.contains('Please enter a creator handle').should('be.visible')
  })

  it('should validate goal selection', () => { // Hermes Phase 0
    cy.visit('/hermes/analyze')
    
    // Fill in handle
    cy.get('input[id="handle"]').type('testcreator')
    
    // Goal should have a default value
    cy.get('#goal').should('have.value', 'GROWTH')
  })
})

describe('Hermes Feature Flag', () => { // Hermes Phase 0
  it('should respect VITE_HERMES_ENABLED flag', () => {
    // Hermes Phase 0 - This test assumes HERMES_ENABLED=true by default
    // In CI/CD, you would test both enabled and disabled states
    cy.visit('/hermes')
    
    // If enabled, should show landing page
    cy.get('body').then(($body) => {
      if (Cypress.env('VITE_HERMES_ENABLED') !== 'false') {
        cy.contains('Welcome to Hermes').should('be.visible')
      } else {
        cy.contains('Hermes Not Enabled').should('be.visible')
      }
    })
  })
})

describe('Labs Feature Flag', () => { // Hermes Phase 0
  it('should show labs only when VITE_LABS_ENABLED=true', () => {
    // Hermes Phase 0 - Labs should be hidden by default
    cy.visit('/library')
    
    cy.get('nav').then(($nav) => {
      if (Cypress.env('VITE_LABS_ENABLED') === 'true') {
        cy.contains('Labs').should('be.visible')
      } else {
        cy.contains('Labs').should('not.exist')
      }
    })
  })
})
