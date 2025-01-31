// https://github.com/cypress-io/cypress/issues/28420#issuecomment-2061755942
import { mount } from 'cypress/vue'

declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount
    }
  }
}
