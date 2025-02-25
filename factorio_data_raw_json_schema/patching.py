import typing

from .schema import Schema, JsonMaker, JsonDict


# I believe 'DamageEntityTriggerEffectItem' is a typo in https://lua-api.factorio.com/2.0.28/types/TriggerEffect.html
# and actually refers to 'DamageTriggerEffectItem'
local_types_for_union: dict[str, Schema.TypeExpression] = {
    "DamageEntityTriggerEffectItem": Schema.RefTypeExpression(ref="DamageTriggerEffectItem")
}


# Empty arrays are serialized as {} instead of []
def array_to_json_definition(self: Schema.ArrayTypeExpression, maker: JsonMaker) -> JsonDict:
    return {
        "oneOf": [
            {"type": "array", "items": self.content.make_json_definition(maker)},
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

    # @todo Document documentation issues
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
