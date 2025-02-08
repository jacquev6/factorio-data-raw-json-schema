/* eslint-disable */
/**
 * This file was automatically generated by json-schema-to-typescript.
 * DO NOT MODIFY IT BY HAND. Instead, modify the source JSONSchema file,
 * and run json-schema-to-typescript to regenerate this file.
 */

/**
 * https://lua-api.factorio.com/stable/prototypes/ItemPrototype.html
 */
export type ItemPrototype = Prototype
/**
 * https://lua-api.factorio.com/stable/prototypes/Prototype.html
 */
export type Prototype = PrototypeBase
/**
 * https://lua-api.factorio.com/stable/prototypes/CraftingMachinePrototype.html
 */
export type CraftingMachinePrototype = Prototype & {
  crafting_categories?: string[]
}
/**
 * https://lua-api.factorio.com/stable/prototypes/CharacterPrototype.html
 */
export type CharacterPrototype = Prototype & {
  crafting_categories?: string[]
}
/**
 * https://lua-api.factorio.com/stable/prototypes/RecipePrototype.html
 */
export type RecipePrototype = Prototype & {
  ingredients?: IngredientPrototype[] | {}
  results?: ProductPrototype[] | {}
  category?: string
}
/**
 * https://lua-api.factorio.com/stable/types/IngredientPrototype.html
 */
export type IngredientPrototype = ItemIngredientPrototype | FluidIngredientPrototype
/**
 * https://lua-api.factorio.com/stable/types/ProductPrototype.html
 */
export type ProductPrototype = ItemProductPrototype | FluidProductPrototype

export interface FactorioDataRaw {
  ammo?: {
    [k: string]: ItemPrototype
  }
  armor?: {
    [k: string]: ItemPrototype
  }
  'assembling-machine'?: {
    [k: string]: CraftingMachinePrototype
  }
  blueprint?: {
    [k: string]: ItemPrototype
  }
  'blueprint-book'?: {
    [k: string]: ItemPrototype
  }
  capsule?: {
    [k: string]: ItemPrototype
  }
  character?: {
    [k: string]: CharacterPrototype
  }
  'copy-paste-tool'?: {
    [k: string]: ItemPrototype
  }
  'deconstruction-item'?: {
    [k: string]: ItemPrototype
  }
  fluid?: {
    [k: string]: ItemPrototype
  }
  furnace?: {
    [k: string]: CraftingMachinePrototype
  }
  gun?: {
    [k: string]: ItemPrototype
  }
  item?: {
    [k: string]: ItemPrototype
  }
  'item-with-entity-data'?: {
    [k: string]: ItemPrototype
  }
  module?: {
    [k: string]: ItemPrototype
  }
  'rail-planner'?: {
    [k: string]: ItemPrototype
  }
  recipe?: {
    [k: string]: RecipePrototype
  }
  'repair-tool'?: {
    [k: string]: ItemPrototype
  }
  'rocket-silo'?: {
    [k: string]: CraftingMachinePrototype
  }
  'selection-tool'?: {
    [k: string]: ItemPrototype
  }
  'space-platform-starter-pack'?: {
    [k: string]: ItemPrototype
  }
  'spidertron-remote'?: {
    [k: string]: ItemPrototype
  }
  tool?: {
    [k: string]: ItemPrototype
  }
  'upgrade-item'?: {
    [k: string]: ItemPrototype
  }
}
/**
 * https://lua-api.factorio.com/stable/prototypes/PrototypeBase.html
 */
export interface PrototypeBase {
  type: string
  name: string
}
/**
 * https://lua-api.factorio.com/stable/types/ItemIngredientPrototype.html
 */
export interface ItemIngredientPrototype {
  type: 'item'
  name: string
  amount: number
  ignored_by_stats?: number
}
/**
 * https://lua-api.factorio.com/stable/types/FluidIngredientPrototype.html
 */
export interface FluidIngredientPrototype {
  type: 'fluid'
  name: string
}
/**
 * https://lua-api.factorio.com/stable/types/ItemProductPrototype.html
 */
export interface ItemProductPrototype {
  type: 'item'
  name: string
}
/**
 * https://lua-api.factorio.com/stable/types/FluidProductPrototype.html
 */
export interface FluidProductPrototype {
  type: 'fluid'
  name: string
}
