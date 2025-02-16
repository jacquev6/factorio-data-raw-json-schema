from typing import Any
import sys


def debug(*arg: Any, **kwds: Any) -> None:
    print(*arg, **kwds, file=sys.stderr)


def patch(schema: Any) -> None:
    def remove_all_constraints(type_name: str) -> None:
        schema["definitions"][type_name] = {"description": schema["definitions"][type_name]["description"]}

    # Ad-hoc patches because the doc doesn't match the actual data
    # ============================================================

    # types/ItemProductPrototype.html#amount_min is documented as uint16
    # but is some sort of floating point in e.g. 'speed-module-recycling'
    if schema["definitions"].get("ItemProductPrototype", {}).get("properties", {}).get("amount", {}) == {
        "$ref": "#/definitions/uint16"
    }:
        schema["definitions"]["ItemProductPrototype"]["properties"]["amount"] = {"$ref": "#/definitions/double"}
    else:
        debug("Failed to patch ItemProductPrototype")

    # types/TriggerEffect.html documents DamageTileTriggerEffectItem as having type="damage-tile",
    # but DamageTileTriggerEffectItem.html documents it as having type="damage"

    # types/TriggerEffect.html refers to non-documented type DamageEntityTriggerEffectItem,
    # and types/DamageTriggerEffectItem.html is documented but used nowhere

    # Empty arrays are serialized as {} instead of []
    # (patched in the generated schema because this must be done everywhere)

    # I'm fed up with documenting every single patch
    schema["definitions"]["WorkingVisualisations"]["properties"]["working_visualisations"] = {}
    schema["definitions"]["CharacterPrototype"]["properties"]["synced_footstep_particle_triggers"] = {}
    remove_all_constraints("TriggerEffect")
    remove_all_constraints("Animation4Way")
    remove_all_constraints("Sound")
    remove_all_constraints("Sprite4Way")
    remove_all_constraints("WorkingSound")
    remove_all_constraints("SpriteVariations")
    remove_all_constraints("Sprite")
    remove_all_constraints("CharacterArmorAnimation")

    # Ad-hoc patches because our extraction tool is weak
    # ==================================================

    # RandomRange can be {min: double, max: double}
    if schema["definitions"].get("RandomRange", {}).get("anyOf", [{}])[0] == {"$ref": "#/definitions/{"}:
        schema["definitions"]["RandomRange"]["anyOf"] = schema["definitions"]["RandomRange"]["anyOf"][1:]
    else:
        debug("Failed to patch RandomRange")
