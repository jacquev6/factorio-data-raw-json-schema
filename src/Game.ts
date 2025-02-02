import assert from './assert'
import { type DataRaw, itemPrototypeKeys } from './FactorioDataRaw'

export interface Item {
  name: string
  ingredientOf: Recipe[]
  productOf: Recipe[]
}

export interface Recipe {
  name: string
  ingredients: { item: Item }[]
  products: { item: Item }[]
}

export interface Game {
  items: Record<string, Item>
  recipes: Record<string, Recipe>
}

function ensureArray<T>(a: T[] | {} | undefined): T[] {
  return Array.isArray(a) ? a : []
}

export function makeGame(dataRaw: DataRaw): Game {
  const items: Record<string, Item> = Object.fromEntries(
    itemPrototypeKeys
      .flatMap((key) => Object.entries(dataRaw[key]))
      .map(([name, itemPrototype]) => {
        assert(name === itemPrototype.name)
        return [
          name,
          {
            name,
            ingredientOf: [],
            productOf: [],
          },
        ]
      }),
  )
  let recipes: Record<string, Recipe> = Object.fromEntries(
    Object.entries(dataRaw.recipe).map(([name, recipe]) => {
      assert(name === recipe.name)
      return [
        name,
        {
          name,
          ingredients: ensureArray(recipe.ingredients)
            .map((ingredientPrototype) => {
              if (ingredientPrototype.type === 'fluid') {
                return undefined
              } else {
                assert(ingredientPrototype.type === 'item')
                const item = items[ingredientPrototype.name]
                if (item === undefined) {
                  console.log(`Item not found: ${ingredientPrototype.name}`)
                }
                return {
                  kind: 'item' as const,
                  item,
                }
              }
            })
            .filter((ingredient) => ingredient !== undefined)
            .filter((ingredient) => ingredient.item !== undefined),
          products: ensureArray(recipe.results)
            .map((productPrototype) => ({
              item: items[productPrototype.name],
            }))
            .filter((result) => result.item !== undefined),
        },
      ]
    }),
  )

  recipes = Object.fromEntries(
    Object.entries(recipes).filter(([name, recipe]) => !name.includes('recycling')),
  )

  for (const recipe of Object.values(recipes)) {
    for (const ingredient of recipe.ingredients) {
      ingredient.item.ingredientOf.push(recipe)
    }
    for (const product of recipe.products) {
      product.item.productOf.push(recipe)
    }
  }

  return { items, recipes }
}
