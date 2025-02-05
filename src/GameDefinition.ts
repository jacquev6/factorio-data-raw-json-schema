import * as zip from '@zip.js/zip.js'

import assert from './assert'
import { type DataRaw, itemPrototypeKeys } from './FactorioDataRaw'

export interface ThingId {
  kind: 'item' | 'fluid'
  name: string
}

export interface ThingDefinition extends ThingId {
  imageIndex: number
}

export interface TransformationDefinition {
  kind: 'recipe'
  name: string
  imageIndex: number
  ingredients: { thing: ThingId }[]
  products: { thing: ThingId }[]
}

export interface GameDefinition {
  images: string[]
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

  const dataRaw: DataRaw = JSON.parse(await readEntry('data-raw-dump.json'))

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

  const things: ThingDefinition[] = []
  for (const key of itemPrototypeKeys) {
    for (const item of Object.values(dataRaw[key] ?? {})) {
      things.push({
        kind: 'item',
        name: item.name,
        imageIndex: await addImage(`item/${item.name}.png`),
      })
    }
  }
  for (const fluid of Object.values(dataRaw.fluid)) {
    things.push({
      kind: 'fluid',
      name: fluid.name,
      imageIndex: await addImage(`fluid/${fluid.name}.png`),
    })
  }

  const transformations: TransformationDefinition[] = []
  for (const recipe of Object.values(dataRaw.recipe)) {
    transformations.push({
      kind: 'recipe',
      name: recipe.name,
      imageIndex: await addImage(`recipe/${recipe.name}.png`),
      ingredients: ensureArray(recipe.ingredients)
        .map((ingredient) => ({ thing: { kind: ingredient.type, name: ingredient.name } }))
        .filter((ingredient) => ingredient.thing !== undefined),
      products: ensureArray(recipe.results)
        .map((product) => ({ thing: { kind: product.type, name: product.name } }))
        .filter((result) => result.thing !== undefined),
    })
  }

  return { images, things, transformations }
}

export default load
