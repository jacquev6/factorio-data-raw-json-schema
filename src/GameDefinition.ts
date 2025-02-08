import * as zip from '@zip.js/zip.js'
import { validate } from 'jsonschema'

import assert from './assert'
import { type FactorioDataRaw } from './factorio_prototypes_schema'
import dataRawSchema from './factorio_prototypes_schema.json'

export interface CrafterDefinition {
  name: string
  imageIndex: number
  // @todo Display number of module slots
  // @todo Display modules applicable to recipe
  // @todo Display crafting speed
  // @todo Display intrinsic productivity bonus
  // @todo Display energy consumption of burner machines (in kW and user-selected fuel per time unit)
  // @todo Display energy consumption of electric machines (in kW)
}

export interface ThingDefinition {
  name: string
  imageIndex: number
}

export interface TransformationDefinition {
  kind: 'recipe'
  // @todo Support other kinds of transformations:
  // - spoilage
  // - mining
  // - burning (for fuels)
  // What else?
  name: string
  imageIndex: number
  crafters: string[]
  ingredients: { thing: string }[]
  products: { thing: string }[]
  // @todo Separate byproducts from products
  // (a product is in fact a by product if it is used as an ingredient in larger quantities than it is produced)
  // (e.g. U-238 in Kovarex enrichment process, while U-235 is an actual product of that recipe)
}

export interface GameDefinition {
  images: string[]
  crafters: CrafterDefinition[]
  things: ThingDefinition[]
  transformations: TransformationDefinition[]
}

function ensureArray<T>(a: T[] | {} | undefined): T[] {
  return Array.isArray(a) ? a : []
}

export async function load(file: Blob): Promise<GameDefinition> {
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

  const dataRaw: FactorioDataRaw = JSON.parse(await readEntry('data-raw-dump.json'))
  const validationErrors = validate(dataRaw, dataRawSchema).errors
  for (const error of validationErrors) {
    console.error(error)
  }

  const images: string[] = []
  const imageIndexes: Record<string, number> = {}
  async function addImage(path: string) {
    const data = await readImageAsDataURL(path)
    let index = imageIndexes[data]
    if (index === undefined) {
      index = images.length
      images.push(data)
      imageIndexes[data] = index
    }
    return index
  }

  const craftersByRecipeCategory: Record<string, string[]> = {}
  const crafters: CrafterDefinition[] = []
  for (const key of ['character', 'assembling-machine', 'rocket-silo', 'furnace'] as const) {
    for (const entity of Object.values(dataRaw[key] ?? {})) {
      crafters.push({
        name: entity.name,
        imageIndex: await addImage(`entity/${entity.name}.png`),
      })
      for (const category of entity.crafting_categories ?? []) {
        craftersByRecipeCategory[category] ??= []
        craftersByRecipeCategory[category].push(entity.name)
      }
    }
  }

  const things: ThingDefinition[] = []
  for (const key of [
    'ammo',
    'armor',
    'blueprint-book',
    'blueprint',
    'capsule',
    'copy-paste-tool',
    'deconstruction-item',
    'gun',
    'item',
    'item-with-entity-data',
    'module',
    'rail-planner',
    'repair-tool',
    'selection-tool',
    'space-platform-starter-pack',
    'spidertron-remote',
    'tool',
    'upgrade-item',
  ] as const) {
    for (const item of Object.values(dataRaw[key] ?? {})) {
      things.push({
        name: item.name,
        imageIndex: await addImage(`item/${item.name}.png`),
      })
    }
  }
  for (const fluid of Object.values(dataRaw.fluid ?? {})) {
    things.push({
      name: fluid.name,
      imageIndex: await addImage(`fluid/${fluid.name}.png`),
    })
  }

  const transformations: TransformationDefinition[] = []
  for (const recipe of Object.values(dataRaw.recipe ?? {})) {
    transformations.push({
      kind: 'recipe',
      name: recipe.name,
      imageIndex: await addImage(`recipe/${recipe.name}.png`),
      ingredients: ensureArray(recipe.ingredients)
        .map((ingredient) => ({ thing: ingredient.name }))
        .filter((ingredient) => ingredient.thing !== undefined),
      products: ensureArray(recipe.results)
        .map((product) => {
          assert(product.type !== 'research-progress')
          return { thing: product.name }
        })
        .filter((result) => result.thing !== undefined),
      crafters: craftersByRecipeCategory[recipe.category ?? 'crafting'] ?? [],
    })
  }

  return { images, crafters, things, transformations }
}

export default load
