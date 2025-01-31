import HelloWorld from './HelloWorld.vue'

describe('<HelloWorld />', () => {
  it('renders', () => {
    // see: https://on.cypress.io/mounting-vue
    cy.mount(HelloWorld)

    cy.get('h3:contains("successfully created a project")').should('exist')
  })
})
