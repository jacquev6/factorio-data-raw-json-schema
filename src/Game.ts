import assert from './assert'
import { type DataRaw, itemPrototypeKeys } from './FactorioDataRaw'

export interface Thing {
  kind: 'item' | 'fluid'
  name: string
  ingredientOf: Recipe[]
  productOf: Recipe[]
}

export interface Recipe {
  name: string
  ingredients: { thing: Thing }[]
  products: { thing: Thing }[]
}

export interface Game {
  things: Record<string, Thing>
  recipes: Record<string, Recipe>
}

function ensureArray<T>(a: T[] | {} | undefined): T[] {
  return Array.isArray(a) ? a : []
}

export function makeGame(dataRaw: DataRaw): Game {
  const things: Record<string, Thing> = Object.fromEntries([
    ...itemPrototypeKeys
      .flatMap((key) => Object.entries(dataRaw[key]))
      .map(([name, itemPrototype]) => {
        assert(name === itemPrototype.name)
        return [
          name,
          {
            kind: 'item',
            name,
            ingredientOf: [],
            productOf: [],
          },
        ]
      }),
    ...Object.entries(dataRaw.fluid).map(([name, fluidPrototype]) => {
      assert(name === fluidPrototype.name)
      return [
        name,
        {
          kind: 'fluid',
          name,
          ingredientOf: [],
          productOf: [],
        },
      ]
    }),
  ])

  let recipes: Record<string, Recipe> = Object.fromEntries(
    Object.entries(dataRaw.recipe).map(([name, recipe]) => {
      assert(name === recipe.name)
      return [
        name,
        {
          name,
          ingredients: ensureArray(recipe.ingredients)
            .map((ingredientPrototype) => {
              return { thing: things[ingredientPrototype.name] }
            })
            .filter((ingredient) => ingredient.thing !== undefined),
          products: ensureArray(recipe.results)
            .map((productPrototype) => ({
              thing: things[productPrototype.name],
            }))
            .filter((result) => result.thing !== undefined),
        },
      ]
    }),
  )

  recipes = Object.fromEntries(
    Object.entries(recipes).filter(([name, recipe]) => !name.includes('recycling')),
  )

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
