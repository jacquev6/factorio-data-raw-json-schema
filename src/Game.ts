import assert from './assert'
import type { GameDefinition } from './GameDefinition'

export interface Thing {
  kind: 'item' | 'fluid'
  name: string
  image: string
  ingredientOf: Recipe[]
  productOf: Recipe[]
}

export interface Recipe {
  name: string
  image: string
  ingredients: { thing: Thing }[]
  products: { thing: Thing }[]
}

export interface Game {
  things: Record<string, Thing>
  recipes: Record<string, Recipe>
}

export function make(definition: GameDefinition): Game {
  const things: Record<string, Thing> = {}
  for (const thing of definition.things) {
    things[thing.name] = {
      kind: thing.kind,
      name: thing.name,
      image: definition.images[thing.imageIndex],
      ingredientOf: [],
      productOf: [],
    }
  }

  const recipes: Record<string, Recipe> = {}
  for (const recipe of definition.transformations) {
    assert(recipe.kind === 'recipe')
    recipes[recipe.name] = {
      name: recipe.name,
      image: definition.images[recipe.imageIndex],
      ingredients: recipe.ingredients.map((ingredient) => ({
        thing: things[ingredient.thing.name],
      })),
      products: recipe.products.map((product) => ({ thing: things[product.thing.name] })),
    }
  }

  for (const recipe of Object.values(recipes)) {
    for (const ingredient of recipe.ingredients) {
      ingredient.thing.ingredientOf.push(recipe)
    }
    for (const product of recipe.products) {
      product.thing.productOf.push(recipe)
    }
  }

  return { things, recipes }
}
