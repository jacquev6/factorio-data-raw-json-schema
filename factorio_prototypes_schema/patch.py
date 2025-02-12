from typing import Any
import json
import sys


def debug(*arg: Any, **kwds: Any) -> None:
    print(*arg, **kwds, file=sys.stderr)


def main() -> None:
    schema = json.load(sys.stdin)

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

    # types/ItemStackIndex.html documents ItemStackIndex an alias for uint16
    # but it's set to "dynamic" in blueprint book
    if schema["definitions"].get("ItemStackIndex", {}).get("anyOf", []) == [{"$ref": "#/definitions/uint16"}]:
        schema["definitions"]["ItemStackIndex"]["anyOf"].append({"type": "string", "const": "dynamic"})
    else:
        debug("Failed to patch ItemStackIndex")

    # types/TriggerEffect.html documents DamageTileTriggerEffectItem as having type="damage-tile",
    # but DamageTileTriggerEffectItem.html documents it as having type="damage"

    # types/TriggerEffect.html refers to non-documented type DamageEntityTriggerEffectItem,
    # and types/DamageTriggerEffectItem.html is documented but used nowhere

    # Empty arrays are serialized as {} instead of []
    # (patched in the generated schema because this must be done everywhere)

    # I'm fed up with documenting every single patch
    schema["definitions"]["WorkingVisualisations"]["properties"]["working_visualisations"] = {}
    schema["definitions"]["CharacterPrototype"]["allOf"][1]["properties"]["synced_footstep_particle_triggers"] = {}
    schema["definitions"]["TriggerEffect"] = {
        "description": "https://lua-api.factorio.com/stable/types/TriggerEffect.html"
    }
    schema["definitions"]["Animation4Way"] = {
        "description": "https://lua-api.factorio.com/stable/types/Animation4Way.html"
    }
    schema["definitions"]["Sound"] = {"description": "https://lua-api.factorio.com/stable/types/Sound.html"}
    schema["definitions"]["Sprite4Way"] = {"description": "https://lua-api.factorio.com/stable/types/Sprite4Way.html"}
    schema["definitions"]["WorkingSound"] = {
        "description": "https://lua-api.factorio.com/stable/types/WorkingSound.html"
    }

    # Ad-hoc patches because our extraction tool is weak
    # ==================================================

    # RandomRange can be {min: double, max: double}
    if schema["definitions"].get("RandomRange", {}).get("anyOf", [{}])[0] == {"$ref": "#/definitions/{"}:
        schema["definitions"]["RandomRange"]["anyOf"] = schema["definitions"]["RandomRange"]["anyOf"][1:]
    else:
        debug("Failed to patch RandomRange")

    # Property "filename" is mandatory in types/SpriteSource.html
    # but overridden to be optional in types/Sprite.html
    # So, for the moment, we make it optional in SpriteSource
    if "filename" in schema["definitions"].get("SpriteSource", {}).get("required", []):
        schema["definitions"]["SpriteSource"]["required"].remove("filename")
    else:
        debug("Failed to patch SpriteSource")

    json.dump(schema, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
