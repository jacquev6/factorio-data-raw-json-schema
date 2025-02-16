from typing import Any
import sys

from .schema import JsonValue


def debug(*arg: Any, **kwds: Any) -> None:
    print(*arg, **kwds, file=sys.stderr)


def patch(schema: Any) -> None:
    def remove_all_constraints(type_name: str) -> None:
        previous_definition = schema["definitions"][type_name]
        new_definition = {"description": previous_definition["description"]}
        if "type" in previous_definition:
            new_definition["type"] = previous_definition["type"]
        schema["definitions"][type_name] = new_definition

    def patch(path: str, fn: Any) -> None:
        d = schema
        parts = path.split(".")
        for p in parts[:-1]:
            d = d[p]
        d[parts[-1]] = fn(d[parts[-1]])

    def remove_from_list(path: str, key: str) -> None:
        patch(path, lambda x: [v for v in x if v != key])

    def add_to_list(path: str, value: Any) -> None:
        patch(path, lambda x: x + [value])

    def replace_value(path: str, old_value: JsonValue, new_value: JsonValue) -> None:
        def fn(x: JsonValue) -> JsonValue:
            assert x == old_value
            return new_value

        patch(path, fn)

    # Ad-hoc patches because the doc doesn't match the actual data
    # ============================================================

    # Empty arrays are serialized as {} instead of []
    # (patched in 'extraction.py' because this must be done everywhere)

    # I believe 'DamageEntityTriggerEffectItem' is a typo in https://lua-api.factorio.com/2.0.28/types/TriggerEffect.html
    # and actually refers to 'DamageTriggerEffectItem'
    # (patched in 'extraction.py' for simplicity)

    # types/ItemProductPrototype.html#amount_min is documented as uint16
    # but is some sort of floating point in e.g. 'speed-module-recycling'
    replace_value(
        "definitions.ItemProductPrototype.properties.amount.$ref", "#/definitions/uint16", "#/definitions/double"
    )

    remove_from_list("definitions.UtilitySprites.properties.cursor_box.required", "rts_selected")
    remove_from_list("definitions.UtilitySprites.properties.cursor_box.required", "rts_to_be_selected")
    remove_from_list("definitions.UtilityConstants.required", "space_platform_default_speed_formula")
    remove_from_list("definitions.SpaceLocationPrototype.required", "gravity_pull")
    remove_from_list("definitions.EditorControllerPrototype.required", "ignore_surface_conditions")
    remove_from_list("definitions.DontResearchBeforeResearchingAchievementPrototype.required", "objective_condition")
    remove_from_list("definitions.DontUseEntityInEnergyProductionAchievementPrototype.required", "objective_condition")
    remove_from_list("definitions.DontKillManuallyAchievementPrototype.required", "objective_condition")

    add_to_list("definitions.ShortcutPrototype.properties.action.anyOf", {"type": "string", "const": "redo"})
    add_to_list(
        "definitions.DontBuildEntityAchievementPrototype.properties.objective_condition.anyOf",
        {"type": "string", "const": "late-research"},
    )

    # Patches to investigate and document
    remove_all_constraints("AgriculturalCraneProperties")
    remove_all_constraints("Animation")
    remove_all_constraints("AttackParameters")
    remove_all_constraints("BoundingBox")
    remove_all_constraints("CraftingMachineGraphicsSet")
    remove_all_constraints("CreateDecorativesTriggerEffectItem")
    remove_all_constraints("EntityBuildAnimationPiece")
    remove_all_constraints("FootstepTriggerEffectList")
    remove_all_constraints("MiningDrillGraphicsSet")
    remove_all_constraints("NeighbourConnectable")
    remove_all_constraints("ProcessionTimeline")
    remove_all_constraints("RailPictureSet")
    remove_all_constraints("RotatedAnimation")
    remove_all_constraints("RotatedSprite")
    remove_all_constraints("Sound")
    remove_all_constraints("Sprite")
    remove_all_constraints("SpriteVariations")
    remove_all_constraints("Trigger")
    remove_all_constraints("WorkingVisualisations")
