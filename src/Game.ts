import * as zip from '@zip.js/zip.js'

import assert from './assert'
import { type DataRaw, itemPrototypeKeys } from './FactorioDataRaw'

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

function ensureArray<T>(a: T[] | {} | undefined): T[] {
  return Array.isArray(a) ? a : []
}

export async function loadGame(file: Blob): Promise<Game> {
  const zipReader = new zip.ZipReader(new zip.BlobReader(file))
  const entriesByName = Object.fromEntries(
    (await zipReader.getEntries()).map((entry) => [entry.filename, entry]),
  )
  const hasScriptOutput = Object.keys(entriesByName).includes('script-output/')

  type CheckedEntry = zip.Entry & { getData<T>(writer: zip.Writer<T>): Promise<T> }
  function getEntry(entryName: string): CheckedEntry {
    if (hasScriptOutput) {
      entryName = `script-output/${entryName}`
    }
    const entry = entriesByName[entryName]
    assert(entry !== undefined)
    assert(entry.getData !== undefined)
    return entry as CheckedEntry // @todo Remove this type assertion; the runtime assertion on previous line should be enough
  }

  function readEntry(entryName: string): Promise<string> {
    return getEntry(entryName).getData(new zip.TextWriter())
  }

  function readImageAsDataURL(entryName: string): Promise<string> {
    return getEntry(entryName).getData(new zip.Data64URIWriter('image/png'))
  }

  const dataRaw: DataRaw = JSON.parse(await readEntry('data-raw-dump.json'))

  const things: Record<string, Thing> = {}
  for (const key of itemPrototypeKeys) {
    for (const item of Object.values(dataRaw[key] ?? {})) {
      things[item.name] = {
        kind: 'item',
        name: item.name,
        image: await readImageAsDataURL(`item/${item.name}.png`),
        ingredientOf: [],
        productOf: [],
      }
    }
  }
  for (const fluid of Object.values(dataRaw.fluid)) {
    things[fluid.name] = {
      kind: 'fluid',
      name: fluid.name,
      image: await readImageAsDataURL(`fluid/${fluid.name}.png`),
      ingredientOf: [],
      productOf: [],
    }
  }

  const recipes: Record<string, Recipe> = {}
  for (const recipe of Object.values(dataRaw.recipe)) {
    recipes[recipe.name] = {
      name: recipe.name,
      image: await readImageAsDataURL(`recipe/${recipe.name}.png`),
      ingredients: ensureArray(recipe.ingredients)
        .map((ingredientPrototype) => ({ thing: things[ingredientPrototype.name] }))
        .filter((ingredient) => ingredient.thing !== undefined),
      products: ensureArray(recipe.results)
        .map((productPrototype) => ({ thing: things[productPrototype.name] }))
        .filter((result) => result.thing !== undefined),
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
