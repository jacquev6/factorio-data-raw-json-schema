from typing import Any

from .schema import Schema, JsonValue, JsonDict


# I believe 'DamageEntityTriggerEffectItem' is a typo in https://lua-api.factorio.com/2.0.28/types/TriggerEffect.html
# and actually refers to 'DamageTriggerEffectItem'
local_types_for_union: dict[str, Schema.TypeExpression] = {
    "DamageEntityTriggerEffectItem": Schema.RefTypeExpression(ref="DamageTriggerEffectItem")
}


# Empty arrays are serialized as {} instead of []
def array_to_json_definition(self: Schema.ArrayTypeExpression, schema: Schema) -> JsonDict:
    return {
        "oneOf": [
            {"type": "array", "items": self.content.make_json_definition(schema)},
            {"type": "object", "additionalProperties": False},
        ]
    }


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

    def add_to_dict(path: str, key: str, value: JsonValue) -> None:
        patch(path, lambda x: {**x, key: value})

    def replace_in_value(path: str, pattern: str, replacement: str) -> None:
        def fn(x: str) -> str:
            return x.replace(pattern, replacement)

        patch(path, fn)

    # Ad-hoc patches because the doc doesn't match the actual data
    # ============================================================

    # https://lua-api.factorio.com/2.0.28/types/ItemProductPrototype.html#amount_min is documented as uint16
    # @todo Identify counter-example(s)
    replace_in_value("definitions.ItemProductPrototype.properties.amount.$ref", "uint16", "double")

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilitySprites.html#cursor_box documents these two attributes as required
    # @todo Identify counter-example(s)
    remove_from_list("definitions.UtilitySprites.properties.cursor_box.required", "rts_selected")
    remove_from_list("definitions.UtilitySprites.properties.cursor_box.required", "rts_to_be_selected")

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilityConstants.html#space_platform_default_speed_formula is documented as required
    # @todo Identify counter-example(s)
    remove_from_list("definitions.UtilityConstants.required", "space_platform_default_speed_formula")

    # https://lua-api.factorio.com/2.0.28/prototypes/SpaceLocationPrototype.html#gravity_pull is documented as required
    # @todo Identify counter-example(s)
    remove_from_list("definitions.SpaceLocationPrototype.required", "gravity_pull")

    # https://lua-api.factorio.com/2.0.28/prototypes/EditorControllerPrototype.html#ignore_surface_conditions is documented as required
    # @todo Identify counter-example(s)
    remove_from_list("definitions.EditorControllerPrototype.required", "ignore_surface_conditions")

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition is documented as required
    # @todo Identify counter-example(s)
    remove_from_list("definitions.DontResearchBeforeResearchingAchievementPrototype.required", "objective_condition")
    remove_from_list("definitions.DontUseEntityInEnergyProductionAchievementPrototype.required", "objective_condition")
    remove_from_list("definitions.DontKillManuallyAchievementPrototype.required", "objective_condition")

    # https://lua-api.factorio.com/2.0.28/prototypes/ShortcutPrototype.html#action doesn't mention "redo" as a possible value
    add_to_list("definitions.ShortcutPrototype.properties.action.anyOf", {"type": "string", "const": "redo"})

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition doesn't mention "late-research" as a possible value
    # and is not overridden in https://lua-api.factorio.com/2.0.28/prototypes/DontBuildEntityAchievementPrototype.html
    add_to_list(
        "definitions.DontBuildEntityAchievementPrototype.properties.objective_condition.anyOf",
        {"type": "string", "const": "late-research"},
    )

    # Undocumented properties
    add_to_dict("definitions.ToolPrototype.properties", "factoriopedia_durability_description_key", {})
    add_to_dict("definitions.CargoPodPrototype.properties", "impact_trigger", {})
    add_to_dict("definitions.ElectricPolePrototype.properties", "track_coverage_during_drag_building", {})
    add_to_dict("definitions.RoboportPrototype.properties", "default_roboport_count_output_signal", {})
    add_to_dict("definitions.UtilityConstants.properties", "factoriopedia_recycling_recipe_categories", {})
    add_to_dict("definitions.UtilityConstants.properties", "feedback_screenshot_file_name", {})
    add_to_dict("definitions.UtilityConstants.properties", "feedback_screenshot_subfolder_name", {})
    add_to_dict("definitions.UtilityConstants.properties", "gui_move_switch_vibration", {})
    add_to_dict("definitions.UtilityConstants.properties", "space_platform_acceleration_expression", {})
    add_to_dict("definitions.UtilityConstants.properties", "starmap_orbit_clicked_color", {})
    add_to_dict("definitions.UtilityConstants.properties", "starmap_orbit_default_color", {})
    add_to_dict("definitions.UtilityConstants.properties", "starmap_orbit_disabled_color", {})
    add_to_dict("definitions.UtilityConstants.properties", "starmap_orbit_hovered_color", {})

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
    # Removing next line requires handling overridden properties in types (https://lua-api.factorio.com/2.0.28/types/DoubleSliderStyleSpecification.html#type)
    remove_all_constraints("StyleSpecification")
    remove_all_constraints("ThrusterGraphicsSet")
    remove_all_constraints("Trigger")
    remove_all_constraints("CargoBayConnectableGraphicsSet")
    remove_all_constraints("LayeredSpriteVariations")

    # Preemptive: this type uses "Fade" as a base, but "Fade" is not a struct. Deal with that later.
    remove_all_constraints("PersistentWorldAmbientSoundsDefinitionCrossfade")
