import assert from './assert'
import type { GameDefinition } from './GameDefinition'

export interface Crafter {
  name: string
  image: string
}

export interface Thing {
  name: string
  image: string
  ingredientOf: Transformation[]
  productOf: Transformation[]
}

export interface Transformation {
  name: string
  image: string
  ingredients: { thing: Thing }[]
  products: { thing: Thing }[]
  crafters: Crafter[]
}

export interface Game {
  crafters: Record<string, Crafter>
  things: Record<string, Thing>
  transformations: Record<string, Transformation>
}

export function make(definition: GameDefinition): Game {
  const crafters: Record<string, Crafter> = {}
  for (const crafter of definition.crafters) {
    crafters[crafter.name] = {
      name: crafter.name,
      image: definition.images[crafter.imageIndex],
    }
  }

  const things: Record<string, Thing> = {}
  for (const thing of definition.things) {
    things[thing.name] = {
      name: thing.name,
      image: definition.images[thing.imageIndex],
      ingredientOf: [],
      productOf: [],
    }
  }

  const transformations: Record<string, Transformation> = {}
  for (const recipe of definition.transformations) {
    assert(recipe.kind === 'recipe')
    transformations[recipe.name] = {
      name: recipe.name,
      image: definition.images[recipe.imageIndex],
      ingredients: recipe.ingredients.map((ingredient) => ({
        thing: things[ingredient.thing],
      })),
      products: recipe.products.map((product) => ({ thing: things[product.thing] })),
      crafters: recipe.crafters.map((crafter) => crafters[crafter]),
    }
  }

  for (const recipe of Object.values(transformations)) {
    for (const ingredient of recipe.ingredients) {
      ingredient.thing.ingredientOf.push(recipe)
    }
    for (const product of recipe.products) {
      product.thing.productOf.push(recipe)
    }
  }

  return { crafters, things, transformations }
}
