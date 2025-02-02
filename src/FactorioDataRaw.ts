/***** Types ******/

// All types: https://lua-api.factorio.com/stable/types.html

// https://lua-api.factorio.com/stable/types/ItemIngredientPrototype.html
export interface ItemIngredientPrototype {
  type: 'item'
  name: string
}

// https://lua-api.factorio.com/stable/types/FluidIngredientPrototype.html
export interface FluidIngredientPrototype {
  type: 'fluid'
  name: string
}

// https://lua-api.factorio.com/stable/types/IngredientPrototype.html
export type IngredientPrototype = ItemIngredientPrototype | FluidIngredientPrototype

// https://lua-api.factorio.com/stable/types/ItemProductPrototype.html
export interface ItemProductPrototype {
  type: 'item'
  name: string
}

// https://lua-api.factorio.com/stable/types/FluidProductPrototype.html
export interface FluidProductPrototype {
  type: 'fluid'
  name: string
}

// https://lua-api.factorio.com/stable/types/ProductPrototype.html
export type ProductPrototype = ItemProductPrototype | FluidProductPrototype

/***** Prototypes ******/

// All prototypes: https://lua-api.factorio.com/stable/prototypes.html
// Whole prototypes hierarchy: https://lua-api.factorio.com/stable/auxiliary/prototype-tree.html

// https://lua-api.factorio.com/stable/prototypes/PrototypeBase.html
export interface PrototypeBase {
  name: string
  type: string
}

// https://lua-api.factorio.com/stable/prototypes/Prototype.html
export interface Prototype extends PrototypeBase {}

// https://lua-api.factorio.com/stable/prototypes/ItemPrototype.html
export interface ItemPrototype extends Prototype {}

// https://lua-api.factorio.com/stable/prototypes/RecipePrototype.html
export interface RecipePrototype extends Prototype {
  ingredients?: IngredientPrototype[] | {} // The '| {}' part is not part of the spec, but empty arrays are weirdly serialized as {} in JSON
  results?: ProductPrototype[] | {} // Same as above
}

/***** Data.raw *****/
export interface DataRaw {
  item: Record<string, ItemPrototype>
  recipe: Record<string, RecipePrototype>
}
