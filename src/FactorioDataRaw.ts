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

export const itemPrototypeKeys = [
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
  // 'item-with-inventory',
  // 'item-with-label',
  // 'item-with-tags',
  'module',
  'rail-planner',
  'repair-tool',
  'selection-tool',
  'space-platform-starter-pack',
  'spidertron-remote',
  'tool',
  'upgrade-item',
] as const

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
  // accumulator: Record<string, Prototype>
  // achievement: Record<string, Prototype>
  // 'active-defense-equipment': Record<string, Prototype>
  // 'agricultural-tower': Record<string, Prototype>
  // 'airborne-pollutant': Record<string, Prototype>
  // 'ambient-sound': Record<string, Prototype>
  ammo: Record<string, ItemPrototype>
  // 'ammo-category': Record<string, Prototype>
  // 'ammo-turret': Record<string, Prototype>
  // 'arithmetic-combinator': Record<string, Prototype>
  armor: Record<string, ItemPrototype>
  // arrow: Record<string, Prototype>
  // 'artillery-flare': Record<string, Prototype>
  // 'artillery-projectile': Record<string, Prototype>
  // 'artillery-turret': Record<string, Prototype>
  // 'artillery-wagon': Record<string, Prototype>
  // 'assembling-machine': Record<string, Prototype>
  // asteroid: Record<string, Prototype>
  // 'asteroid-chunk': Record<string, Prototype>
  // 'asteroid-collector': Record<string, Prototype>
  // 'autoplace-control': Record<string, Prototype>
  // 'battery-equipment': Record<string, Prototype>
  // beacon: Record<string, Prototype>
  // beam: Record<string, Prototype>
  // 'belt-immunity-equipment': Record<string, Prototype>
  blueprint: Record<string, ItemPrototype>
  'blueprint-book': Record<string, ItemPrototype>
  // boiler: Record<string, Prototype>
  // 'build-entity-achievement': Record<string, Prototype>
  // 'burner-generator': Record<string, Prototype>
  // 'burner-usage': Record<string, Prototype>
  capsule: Record<string, ItemPrototype>
  // 'capture-robot': Record<string, Prototype>
  // car: Record<string, Prototype>
  // 'cargo-bay': Record<string, Prototype>
  // 'cargo-landing-pad': Record<string, Prototype>
  // 'cargo-pod': Record<string, Prototype>
  // 'cargo-wagon': Record<string, Prototype>
  // 'chain-active-trigger': Record<string, Prototype>
  // 'change-surface-achievement': Record<string, Prototype>
  // character: Record<string, Prototype>
  // 'character-corpse': Record<string, Prototype>
  // cliff: Record<string, Prototype>
  // 'collision-layer': Record<string, Prototype>
  // 'combat-robot': Record<string, Prototype>
  // 'combat-robot-count-achievement': Record<string, Prototype>
  // 'complete-objective-achievement': Record<string, Prototype>
  // 'constant-combinator': Record<string, Prototype>
  // 'construct-with-robots-achievement': Record<string, Prototype>
  // 'construction-robot': Record<string, Prototype>
  // container: Record<string, Prototype>
  'copy-paste-tool': Record<string, ItemPrototype>
  // corpse: Record<string, Prototype>
  // 'create-platform-achievement': Record<string, Prototype>
  // 'curved-rail-a': Record<string, Prototype>
  // 'curved-rail-b': Record<string, Prototype>
  // 'custom-input': Record<string, Prototype>
  // 'damage-type': Record<string, Prototype>
  // 'decider-combinator': Record<string, Prototype>
  // 'deconstruct-with-robots-achievement': Record<string, Prototype>
  // 'deconstructible-tile-proxy': Record<string, Prototype>
  'deconstruction-item': Record<string, ItemPrototype>
  // 'delayed-active-trigger': Record<string, Prototype>
  // 'deliver-by-robots-achievement': Record<string, Prototype>
  // 'deliver-category': Record<string, Prototype>
  // 'deliver-impact-combination': Record<string, Prototype>
  // 'deplete-resource-achievement': Record<string, Prototype>
  // 'destroy-cliff-achievement': Record<string, Prototype>
  // 'display-panel': Record<string, Prototype>
  // 'dont-build-entity-achievement': Record<string, Prototype>
  // 'dont-craft-manually-achievement': Record<string, Prototype>
  // 'dont-kill-manually-achievement': Record<string, Prototype>
  // 'dont-research-before-researching-achievement': Record<string, Prototype>
  // 'dont-use-entity-in-energy-production-achievement': Record<string, Prototype>
  // 'editor-controller': Record<string, Prototype>
  // 'electric-energy-interface': Record<string, Prototype>
  // 'electric-pole': Record<string, Prototype>
  // 'electric-turret': Record<string, Prototype>
  // 'elevated-curved-rail-a': Record<string, Prototype>
  // 'elevated-curved-rail-b': Record<string, Prototype>
  // 'elevated-half-diagonal-rail': Record<string, Prototype>
  // 'elevated-straight-rail': Record<string, Prototype>
  // 'energy-shield-equipment': Record<string, Prototype>
  // 'entity-ghost': Record<string, Prototype>
  // 'equip-armor-achievement': Record<string, Prototype>
  // 'equipment-category': Record<string, Prototype>
  // 'equipment-ghost': Record<string, Prototype>
  // 'equipment-grid': Record<string, Prototype>
  // explosion: Record<string, Prototype>
  // fire: Record<string, Prototype>
  // fish: Record<string, Prototype>
  // fluid: Record<string, Prototype>
  // 'fluid-turret': Record<string, Prototype>
  // 'fluid-wagon': Record<string, Prototype>
  // font: Record<string, Prototype>
  // 'fuel-category': Record<string, Prototype>
  // furnace: Record<string, Prototype>
  // 'fusion-generator': Record<string, Prototype>
  // 'fusion-reactor': Record<string, Prototype>
  // gate: Record<string, Prototype>
  // generator: Record<string, Prototype>
  // 'generator-equipment': Record<string, Prototype>
  // 'god-controller': Record<string, Prototype>
  // 'group-attack-achievement': Record<string, Prototype>
  // 'gui-style': Record<string, Prototype>
  gun: Record<string, ItemPrototype>
  // 'half-diagonal-rail': Record<string, Prototype>
  // 'heat-interface': Record<string, Prototype>
  // 'heat-pipe': Record<string, Prototype>
  // 'highlight-box': Record<string, Prototype>
  // 'impact-category': Record<string, Prototype>
  // 'infinity-container': Record<string, Prototype>
  // 'infinity-pipe': Record<string, Prototype>
  // inserter: Record<string, Prototype>
  // 'inventory-bonus-equipment': Record<string, Prototype>
  item: Record<string, ItemPrototype>
  // 'item-entity': Record<string, Prototype>
  // 'item-group': Record<string, Prototype>
  // 'item-request-proxy': Record<string, Prototype>
  // 'item-subgroup': Record<string, Prototype>
  'item-with-entity-data': Record<string, ItemPrototype>
  // 'kill-achievement': Record<string, Prototype>
  // lab: Record<string, Prototype>
  // lamp: Record<string, Prototype>
  // 'land-mine': Record<string, Prototype>
  // 'lane-splitter': Record<string, Prototype>
  // 'legacy-curved-rail': Record<string, Prototype>
  // 'legacy-straight-rail': Record<string, Prototype>
  // lightning: Record<string, Prototype>
  // 'lightning-attractor': Record<string, Prototype>
  // 'linked-belt': Record<string, Prototype>
  // 'linked-container': Record<string, Prototype>
  // loader: Record<string, Prototype>
  // 'loader-1x1': Record<string, Prototype>
  // locomotive: Record<string, Prototype>
  // 'logistic-container': Record<string, Prototype>
  // 'logistic-robot': Record<string, Prototype>
  // 'map-gen-presets': Record<string, Prototype>
  // 'map-settings': Record<string, Prototype>
  // market: Record<string, Prototype>
  // 'mining-drill': Record<string, Prototype>
  module: Record<string, ItemPrototype>
  // 'module-category': Record<string, Prototype>
  // 'module-transfer-achievement': Record<string, Prototype>
  // 'mouse-cursor': Record<string, Prototype>
  // 'movement-bonus-equipment': Record<string, Prototype>
  // 'night-vision-equipment': Record<string, Prototype>
  // 'noise-expression': Record<string, Prototype>
  // 'noise-function': Record<string, Prototype>
  // 'offshore-pump': Record<string, Prototype>
  // 'optimized-decorative': Record<string, Prototype>
  // 'optimized-particle': Record<string, Prototype>
  // 'particle-source': Record<string, Prototype>
  // pipe: Record<string, Prototype>
  // 'pipe-to-ground': Record<string, Prototype>
  // 'place-equipment-achievement': Record<string, Prototype>
  // planet: Record<string, Prototype>
  // plant: Record<string, Prototype>
  // 'player-damaged-achievement': Record<string, Prototype>
  // 'power-switch': Record<string, Prototype>
  // procession: Record<string, Prototype>
  // 'procession-layer-inheritance-group': Record<string, Prototype>
  // 'produce-achievement': Record<string, Prototype>
  // 'produce-per-hour-achievement': Record<string, Prototype>
  // 'programmable-speaker': Record<string, Prototype>
  // projectile: Record<string, Prototype>
  // pump: Record<string, Prototype>
  // quality: Record<string, Prototype>
  // radar: Record<string, Prototype>
  // 'rail-chain-signal': Record<string, Prototype>
  'rail-planner': Record<string, ItemPrototype>
  // 'rail-ramp': Record<string, Prototype>
  // 'rail-remnants': Record<string, Prototype>
  // 'rail-signal': Record<string, Prototype>
  // 'rail-support': Record<string, Prototype>
  // reactor: Record<string, Prototype>
  recipe: Record<string, RecipePrototype>
  // 'recipe-category': Record<string, Prototype>
  // 'remote-controller': Record<string, Prototype>
  'repair-tool': Record<string, ItemPrototype>
  // 'research-achievement': Record<string, Prototype>
  // 'research-with-science-pack-achievement': Record<string, Prototype>
  // resource: Record<string, Prototype>
  // 'resource-category': Record<string, Prototype>
  // roboport: Record<string, Prototype>
  // 'roboport-equipment': Record<string, Prototype>
  // 'rocket-silo': Record<string, Prototype>
  // 'rocket-silo-rocket': Record<string, Prototype>
  // 'rocket-silo-rocket-shadow': Record<string, Prototype>
  // segment: Record<string, Prototype>
  // 'segmented-unit': Record<string, Prototype>
  'selection-tool': Record<string, ItemPrototype>
  // 'selector-combinator': Record<string, Prototype>
  // 'shoot-achievement': Record<string, Prototype>
  // shortcut: Record<string, Prototype>
  // 'simple-entity': Record<string, Prototype>
  // 'simple-entity-with-force': Record<string, Prototype>
  // 'simple-entity-with-owner': Record<string, Prototype>
  // 'smoke-with-trigger': Record<string, Prototype>
  // 'solar-panel': Record<string, Prototype>
  // 'solar-panel-equipment': Record<string, Prototype>
  // 'space-connection': Record<string, Prototype>
  // 'space-connection-distance-traveled-achievement': Record<string, Prototype>
  // 'space-location': Record<string, Prototype>
  // 'space-platform-hub': Record<string, Prototype>
  'space-platform-starter-pack': Record<string, ItemPrototype>
  // 'spectator-controller': Record<string, Prototype>
  // 'speech-bubble': Record<string, Prototype>
  // 'spider-leg': Record<string, Prototype>
  // 'spider-unit': Record<string, Prototype>
  // 'spider-vehicle': Record<string, Prototype>
  'spidertron-remote': Record<string, ItemPrototype>
  // splitter: Record<string, Prototype>
  // sprite: Record<string, Prototype>
  // sticker: Record<string, Prototype>
  // 'storage-tank': Record<string, Prototype>
  // 'straight-rail': Record<string, Prototype>
  // stream: Record<string, Prototype>
  // surface: Record<string, Prototype>
  // 'surface-property': Record<string, Prototype>
  // technology: Record<string, Prototype>
  // 'temporary-container': Record<string, Prototype>
  // thruster: Record<string, Prototype>
  // tile: Record<string, Prototype>
  // 'tile-effect': Record<string, Prototype>
  // 'tile-ghost': Record<string, Prototype>
  // 'tips-and-tricks-item': Record<string, Prototype>
  // 'tips-and-tricks-item-category': Record<string, Prototype>
  tool: Record<string, ItemPrototype>
  // 'train-path-achievement': Record<string, Prototype>
  // 'train-stop': Record<string, Prototype>
  // 'transport-belt': Record<string, Prototype>
  // tree: Record<string, Prototype>
  // 'trigger-target-type': Record<string, Prototype>
  // 'trivial-smoke': Record<string, Prototype>
  // turret: Record<string, Prototype>
  // tutorial: Record<string, Prototype>
  // 'underground-belt': Record<string, Prototype>
  // unit: Record<string, Prototype>
  // 'unit-spawner': Record<string, Prototype>
  'upgrade-item': Record<string, ItemPrototype>
  // 'use-entity-in-energy-production-achievement': Record<string, Prototype>
  // 'use-item-achievement': Record<string, Prototype>
  // 'utility-constants': Record<string, Prototype>
  // 'utility-sounds': Record<string, Prototype>
  // 'utility-sprites': Record<string, Prototype>
  // 'virtual-signal': Record<string, Prototype>
  // wall: Record<string, Prototype>
}
