from typing import Any
import typing

from .schema import Schema, JsonDict


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


def patch_schema(schema: Schema) -> None:
    # https://lua-api.factorio.com/2.0.28/types/WorkingVisualisations.html#shift_animation_waypoint_stop_duration is documented as uint16
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".wet_mining_graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".wet_mining_graphics_set.shift_animation_waypoint_stop_duration'
    schema.get_type_def("WorkingVisualisations", Schema.StructTypeExpression).get_property_type(
        "shift_animation_waypoint_stop_duration", Schema.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/ItemProductPrototype.html#amount is documented as uint16
    # but is some kind of floating point number in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."accumulator-recycling".results[0].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."accumulator-recycling".results[1].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[0].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[1].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[2].amount'
    # And many other recycling recipes.
    schema.get_type_def("ItemProductPrototype", Schema.StructTypeExpression).get_property_type(
        "amount", Schema.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/TechnologySlotStyleSpecification.html#level_offset_y is documented as int32
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_offset_y'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_offset_y'
    schema.get_type_def("TechnologySlotStyleSpecification", Schema.StructTypeExpression).get_property_type(
        "level_offset_y", Schema.RefTypeExpression
    ).ref = "double"
    # (Probably applies to level_offset_x as well)
    schema.get_type_def("TechnologySlotStyleSpecification", Schema.StructTypeExpression).get_property_type(
        "level_offset_x", Schema.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/TechnologySlotStyleSpecification.html#level_range_offset_y is documented as int32
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_range_offset_y'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_range_offset_y'
    schema.get_type_def("TechnologySlotStyleSpecification", Schema.StructTypeExpression).get_property_type(
        "level_range_offset_y", Schema.RefTypeExpression
    ).ref = "double"
    # (Probably applies to level_range_offset_x as well)
    schema.get_type_def("TechnologySlotStyleSpecification", Schema.StructTypeExpression).get_property_type(
        "level_range_offset_x", Schema.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/BaseAttackParameters.html#lead_target_for_projectile_delay is documented as uint32
    # but is some kind of floating point number in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."big-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."medium-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."small-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    schema.get_type_def("BaseAttackParameters", Schema.StructTypeExpression).get_property_type(
        "lead_target_for_projectile_delay", Schema.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/WorkingVisualisations.html#working_visualisations is documented as array[WorkingVisualisation]
    # but is actually an object, with string keys looking like integers in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."big-mining-drill".graphics_set.working_visualisations'
    # Note that is is an array as expected in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.working_visualisations'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.working_visualisations'
    schema.get_type_def("WorkingVisualisations", Schema.StructTypeExpression).set_property_type(
        "working_visualisations",
        Schema.UnionTypeExpression(
            members=[
                schema.get_type_def("WorkingVisualisations", Schema.StructTypeExpression).get_property_type(
                    "working_visualisations"
                ),
                Schema.StructTypeExpression(
                    base=None,
                    properties=[],
                    overridden_properties=[],
                    custom_properties=schema.get_type_def("WorkingVisualisations", Schema.StructTypeExpression)
                    .get_property_type("working_visualisations", Schema.ArrayTypeExpression)
                    .content,
                ),
            ]
        ),
    )

    # Properties 'factoriopedia_recycling_recipe_categories', 'feedback_screenshot_file_name', 'feedback_screenshot_subfolder_name', 'gui_move_switch_vibration', 'space_platform_acceleration_expression', 'starmap_orbit_clicked_color', 'starmap_orbit_default_color', 'starmap_orbit_disabled_color' and 'starmap_orbit_hovered_color'
    # are not documented in https://lua-api.factorio.com/2.0.28/prototypes/UtilityConstants.html
    # but are present in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.utility-constants.default'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'utility-constants.default'
    for property_name in [
        "factoriopedia_recycling_recipe_categories",
        "feedback_screenshot_file_name",
        "feedback_screenshot_subfolder_name",
        "gui_move_switch_vibration",
        "space_platform_acceleration_expression",
        "starmap_orbit_clicked_color",
        "starmap_orbit_default_color",
        "starmap_orbit_disabled_color",
        "starmap_orbit_hovered_color",
    ]:
        schema.get_prototype("UtilityConstants").properties.append(
            Schema.Property(names=[property_name], type=Schema.unconstrained_type, required=False)
        )

    # Property 'impact_trigger' is not documented in https://lua-api.factorio.com/2.0.28/prototypes/CargoPodPrototype.html
    # but is present in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."cargo-pod"."cargo-pod"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '"cargo-pod"."cargo-pod"'
    schema.get_prototype("CargoPodPrototype").properties.append(
        Schema.Property(names=["impact_trigger"], type=Schema.unconstrained_type, required=False)
    )

    # Property 'track_coverage_during_drag_building' is not documented in https://lua-api.factorio.com/2.0.28/prototypes/ElectricPolePrototype.html
    # but is present in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."electric-pole"."big-electric-pole"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '"electric-pole"."big-electric-pole"'
    schema.get_prototype("ElectricPolePrototype").properties.append(
        Schema.Property(names=["track_coverage_during_drag_building"], type=Schema.unconstrained_type, required=False)
    )

    # Property 'default_roboport_count_output_signal' is not documented in https://lua-api.factorio.com/2.0.28/prototypes/RoboportPrototype.html
    # but is present in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.roboport.roboport'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'roboport.roboport'
    schema.get_prototype("RoboportPrototype").properties.append(
        Schema.Property(names=["default_roboport_count_output_signal"], type=Schema.unconstrained_type, required=False)
    )

    # Property 'factoriopedia_durability_description_key' is not documented in https://lua-api.factorio.com/2.0.28/prototypes/ToolPrototype.html
    # but is present in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."military-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."production-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."chemical-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."logistic-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."automation-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."utility-science-pack"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.tool."space-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."utility-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."space-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."logistic-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."electromagnetic-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."production-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."military-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."agricultural-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."automation-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."promethium-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."chemical-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."metallurgic-science-pack"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq 'tool."cryogenic-science-pack"'
    schema.get_prototype("ToolPrototype").properties.append(
        Schema.Property(
            names=["factoriopedia_durability_description_key"], type=Schema.unconstrained_type, required=False
        )
    )

    # https://lua-api.factorio.com/2.0.28/types/CranePartDyingEffect.html#particle_effects is documented as 'array[CreateParticleTriggerEffectItem]'
    # but is a single 'CreateParticleTriggerEffectItem' in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."agricultural-tower"."agricultural-tower".crane.parts[0].dying_effect.particle_effects'
    schema.get_type_def("CranePartDyingEffect", Schema.StructTypeExpression).set_property_type(
        "particle_effects",
        Schema.UnionTypeExpression(
            members=[
                schema.get_type_def("CranePartDyingEffect", Schema.StructTypeExpression).get_property_type(
                    "particle_effects"
                ),
                schema.get_type_def("CranePartDyingEffect", Schema.StructTypeExpression)
                .get_property_type("particle_effects", Schema.ArrayTypeExpression)
                .content,
            ]
        ),
    )

    # https://lua-api.factorio.com/2.0.28/prototypes/ShortcutPrototype.html#action doesn't mention "redo" as a possible value
    # but that value is used in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.shortcut.redo.action'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.shortcut.redo.action'
    schema.get_prototype("ShortcutPrototype").get_property_type("action", Schema.UnionTypeExpression).members.append(
        Schema.LiteralStringTypeExpression(value="redo")
    )

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition doesn't mention "late-research" as a possible value
    # and is not overridden in https://lua-api.factorio.com/2.0.28/prototypes/DontBuildEntityAchievementPrototype.html
    # but that value is used in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-build-entity-achievement"."logistic-network-embargo".objective_condition'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-build-entity-achievement"."logistic-network-embargo".objective_condition'
    schema.get_prototype("AchievementPrototypeWithCondition").get_property_type(
        "objective_condition", Schema.UnionTypeExpression
    ).members.append(Schema.LiteralStringTypeExpression(value="late-research"))

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilityConstants.html#space_platform_default_speed_formula is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-constants".default'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-constants".default'
    schema.get_prototype("UtilityConstants").get_property("space_platform_default_speed_formula").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/SpaceLocationPrototype.html#gravity_pull is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."space-location"."space-location-unknown"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."space-location"."space-location-unknown"'
    schema.get_prototype("SpaceLocationPrototype").get_property("gravity_pull").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/EditorControllerPrototype.html#ignore_surface_conditions is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."editor-controller".default'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."editor-controller".default'
    schema.get_prototype("EditorControllerPrototype").get_property("ignore_surface_conditions").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-kill-manually-achievement"."keeping-your-hands-clean"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-use-entity-in-energy-production-achievement".solaris'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-kill-manually-achievement"."keeping-your-hands-clean"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-research-before-researching-achievement"."rush-to-space"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-use-entity-in-energy-production-achievement".solaris'
    schema.get_prototype("AchievementPrototypeWithCondition").get_property("objective_condition").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilitySprites.html#cursor_box documents attribute 'rts_selected' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    schema.get_prototype("UtilitySprites").get_property_type("cursor_box", Schema.StructTypeExpression).get_property(
        "rts_selected"
    ).required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilitySprites.html#cursor_box documents attribute 'rts_to_be_selected' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    schema.get_prototype("UtilitySprites").get_property_type("cursor_box", Schema.StructTypeExpression).get_property(
        "rts_to_be_selected"
    ).required = False

    # https://lua-api.factorio.com/2.0.28/types/SingleGraphicProcessionLayer.html#frames documents attribute 'frame' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.procession."default-b".timeline.layers[5].frames[0]'
    # (and many others)
    typing.cast(
        Schema.StructTypeExpression,
        schema.get_type_def("SingleGraphicProcessionLayer", Schema.StructTypeExpression)
        .get_property_type("frames", Schema.ArrayTypeExpression)
        .content,
    ).get_property("frame").required = False

    # https://lua-api.factorio.com/2.0.28/types/ProcessionTimeline.html#audio_events is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.procession."default-intermezzo".timeline'
    schema.get_type_def("ProcessionTimeline", Schema.StructTypeExpression).get_property("audio_events").required = False

    # https://lua-api.factorio.com/2.0.28/types/RailPictureSet.html#rail_endings is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."rail-ramp"."dummy-rail-ramp".pictures'
    schema.get_type_def("RailPictureSet", Schema.StructTypeExpression).get_property("rail_endings").required = False

    # https://lua-api.factorio.com/2.0.28/types/SpriteSource.html#filename is documented as required
    # but is absent from:
    #  cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.wall."stone-wall".pictures.ending_left'
    # (and many others)
    schema.get_type_def("SpriteSource", Schema.StructTypeExpression).get_property("filename").required = False

    # https://lua-api.factorio.com/2.0.28/types/NeighbourConnectableConnectionDefinition.html#location documents attributes 'direction' as a 'MapPosition'
    # but it's an integer in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."fusion-reactor"."fusion-reactor".neighbour_connectable.connections'
    # (probably a https://lua-api.factorio.com/2.0.28/defines.html#defines.direction)
    schema.get_type_def("NeighbourConnectableConnectionDefinition", Schema.StructTypeExpression).get_property_type(
        "location", Schema.StructTypeExpression
    ).set_property_type("direction", Schema.RefTypeExpression(ref="uint8"))

    # https://lua-api.factorio.com/2.0.28/types/BoundingBox.html is documented as a 2-tuple,
    # but the prose explains it can also be a 3-tuple with a 'float' as third element.
    schema.get_type_def("BoundingBox", Schema.UnionTypeExpression).members.append(
        Schema.TupleTypeExpression(
            members=typing.cast(
                Schema.TupleTypeExpression, schema.get_type_def("BoundingBox", Schema.UnionTypeExpression).members[1]
            ).members
            + [Schema.RefTypeExpression(ref="float")]
        )
    )

    # https://lua-api.factorio.com/2.0.28/types/SingleGraphicProcessionLayer.html#frames documents attribute 'timestamp' as 'MapTick', which is an alias for 'uint64'
    # but it's some kind of floating point number in:
    #  cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.procession."planet-to-platform-a".timeline.layers[33].frames[0].timestamp'
    typing.cast(
        Schema.StructTypeExpression,
        schema.get_type_def("SingleGraphicProcessionLayer", Schema.StructTypeExpression)
        .get_property_type("frames", Schema.ArrayTypeExpression)
        .content,
    ).set_property_type("timestamp", Schema.RefTypeExpression(ref="double"))

    # https://lua-api.factorio.com/2.0.28/types/Sound.html doesn't mention a plain string (filename) as a possible value
    # but many sounds are plain filenames:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."rocket-silo"."rocket-silo".alarm_sound'
    # (and many others)
    schema.get_type_def("Sound", Schema.UnionTypeExpression).members.append(Schema.RefTypeExpression(ref="string"))

    # https://lua-api.factorio.com/2.0.28/types/CreateDecorativesTriggerEffectItem.html#type is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.turret."medium-worm-turret".spawn_decoration[0]'
    # (and many others)
    schema.get_type_def("CreateDecorativesTriggerEffectItem", Schema.StructTypeExpression).get_property(
        "type"
    ).required = False

    # @todo Document documentation issue
    schema.get_type_def("CreateParticleTriggerEffectItem", Schema.StructTypeExpression).get_property(
        "type"
    ).required = False
    schema.get_type_def("CreateParticleTriggerEffectItem", Schema.StructTypeExpression).get_property(
        "particle_name"
    ).required = False
    schema.get_type_def("CreateParticleTriggerEffectItem", Schema.StructTypeExpression).get_property(
        "initial_height"
    ).required = False
    schema.get_type_def("TriggerEffectItem", Schema.StructTypeExpression).set_property_type(
        "repeat_count", Schema.RefTypeExpression(ref="double")
    )
    schema.get_type_def("CreateParticleTriggerEffectItem", Schema.StructTypeExpression).set_property_type(
        "tail_length_deviation", Schema.RefTypeExpression(ref="double")
    )
    schema.get_type_def("BeamTriggerDelivery", Schema.StructTypeExpression).set_property_type(
        "max_length", Schema.RefTypeExpression(ref="double")
    )
    schema.get_type_def("DamageTileTriggerEffectItem", Schema.StructTypeExpression).get_property_type(
        "type", Schema.LiteralStringTypeExpression
    ).value = "damage-tile"
