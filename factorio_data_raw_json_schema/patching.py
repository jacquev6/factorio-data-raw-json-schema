import typing

from . import factorio_documentation as fd
from .factorio_documentation import JsonDict


# I believe 'DamageEntityTriggerEffectItem' is a typo in https://lua-api.factorio.com/2.0.28/types/TriggerEffect.html
# and actually refers to 'DamageTriggerEffectItem'
local_types_for_union: dict[str, fd.TypeExpression] = {
    "DamageEntityTriggerEffectItem": fd.RefTypeExpression(ref="DamageTriggerEffectItem")
}


# Empty arrays are serialized as {} instead of []
def array_to_json_definition(content: JsonDict) -> JsonDict:
    return {"oneOf": [{"type": "array", "items": content}, {"type": "object", "additionalProperties": False}]}


def patch_doc(doc: fd.Doc) -> None:
    # https://lua-api.factorio.com/2.0.28/types/WorkingVisualisations.html#shift_animation_waypoint_stop_duration is documented as uint16
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".wet_mining_graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.shift_animation_waypoint_stop_duration'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".wet_mining_graphics_set.shift_animation_waypoint_stop_duration'
    doc.get_type_def("WorkingVisualisations", fd.StructTypeExpression).get_property_type(
        "shift_animation_waypoint_stop_duration", fd.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/ItemProductPrototype.html#amount is documented as uint16
    # but is some kind of floating point number in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."accumulator-recycling".results[0].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."accumulator-recycling".results[1].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[0].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[1].amount'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.recipe."active-provider-chest-recycling".results[2].amount'
    # And many other recycling recipes.
    doc.get_type_def("ItemProductPrototype", fd.StructTypeExpression).get_property_type(
        "amount", fd.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/TechnologySlotStyleSpecification.html#level_offset_y is documented as int32
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_offset_y'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_offset_y'
    doc.get_type_def("TechnologySlotStyleSpecification", fd.StructTypeExpression).get_property_type(
        "level_offset_y", fd.RefTypeExpression
    ).ref = "double"
    # (Probably applies to level_offset_x as well)
    doc.get_type_def("TechnologySlotStyleSpecification", fd.StructTypeExpression).get_property_type(
        "level_offset_x", fd.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/TechnologySlotStyleSpecification.html#level_range_offset_y is documented as int32
    # but is some kind of floating point number in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_range_offset_y'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_range_offset_y'
    doc.get_type_def("TechnologySlotStyleSpecification", fd.StructTypeExpression).get_property_type(
        "level_range_offset_y", fd.RefTypeExpression
    ).ref = "double"
    # (Probably applies to level_range_offset_x as well)
    doc.get_type_def("TechnologySlotStyleSpecification", fd.StructTypeExpression).get_property_type(
        "level_range_offset_x", fd.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/BaseAttackParameters.html#lead_target_for_projectile_delay is documented as uint32
    # but is some kind of floating point number in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."big-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."medium-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."segmented-unit"."small-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    doc.get_type_def("BaseAttackParameters", fd.StructTypeExpression).get_property_type(
        "lead_target_for_projectile_delay", fd.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.28/types/WorkingVisualisations.html#working_visualisations is documented as array[WorkingVisualisation]
    # but is actually an object, with string keys looking like integers in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."big-mining-drill".graphics_set.working_visualisations'
    # Note that is is an array as expected in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.working_visualisations'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.working_visualisations'
    doc.get_type_def("WorkingVisualisations", fd.StructTypeExpression).set_property_type(
        "working_visualisations",
        fd.UnionTypeExpression(
            members=[
                doc.get_type_def("WorkingVisualisations", fd.StructTypeExpression).get_property_type(
                    "working_visualisations"
                ),
                fd.StructTypeExpression(
                    base=None,
                    properties=[],
                    overridden_properties=[],
                    custom_properties=doc.get_type_def("WorkingVisualisations", fd.StructTypeExpression)
                    .get_property_type("working_visualisations", fd.ArrayTypeExpression)
                    .content,
                ),
            ]
        ),
    )

    # https://lua-api.factorio.com/2.0.28/types/CranePartDyingEffect.html#particle_effects is documented as 'array[CreateParticleTriggerEffectItem]'
    # but is a single 'CreateParticleTriggerEffectItem' in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."agricultural-tower"."agricultural-tower".crane.parts[0].dying_effect.particle_effects'
    doc.get_type_def("CranePartDyingEffect", fd.StructTypeExpression).set_property_type(
        "particle_effects",
        fd.UnionTypeExpression(
            members=[
                doc.get_type_def("CranePartDyingEffect", fd.StructTypeExpression).get_property_type("particle_effects"),
                doc.get_type_def("CranePartDyingEffect", fd.StructTypeExpression)
                .get_property_type("particle_effects", fd.ArrayTypeExpression)
                .content,
            ]
        ),
    )

    # https://lua-api.factorio.com/2.0.28/prototypes/ShortcutPrototype.html#action doesn't mention "redo" as a possible value
    # but that value is used in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.shortcut.redo.action'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.shortcut.redo.action'
    doc.get_prototype("ShortcutPrototype").get_property_type("action", fd.UnionTypeExpression).members.append(
        fd.LiteralStringTypeExpression(value="redo")
    )

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition doesn't mention "late-research" as a possible value
    # and is not overridden in https://lua-api.factorio.com/2.0.28/prototypes/DontBuildEntityAchievementPrototype.html
    # but that value is used in:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-build-entity-achievement"."logistic-network-embargo".objective_condition'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-build-entity-achievement"."logistic-network-embargo".objective_condition'
    doc.get_prototype("AchievementPrototypeWithCondition").get_property_type(
        "objective_condition", fd.UnionTypeExpression
    ).members.append(fd.LiteralStringTypeExpression(value="late-research"))

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilityConstants.html#space_platform_default_speed_formula is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-constants".default'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-constants".default'
    doc.get_prototype("UtilityConstants").get_property("space_platform_default_speed_formula").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/SpaceLocationPrototype.html#gravity_pull is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."space-location"."space-location-unknown"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."space-location"."space-location-unknown"'
    doc.get_prototype("SpaceLocationPrototype").get_property("gravity_pull").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/EditorControllerPrototype.html#ignore_surface_conditions is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."editor-controller".default'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."editor-controller".default'
    doc.get_prototype("EditorControllerPrototype").get_property("ignore_surface_conditions").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/AchievementPrototypeWithCondition.html#objective_condition is documented as required
    # but is absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-kill-manually-achievement"."keeping-your-hands-clean"'
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."dont-use-entity-in-energy-production-achievement".solaris'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-kill-manually-achievement"."keeping-your-hands-clean"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-research-before-researching-achievement"."rush-to-space"'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."dont-use-entity-in-energy-production-achievement".solaris'
    doc.get_prototype("AchievementPrototypeWithCondition").get_property("objective_condition").required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilitySprites.html#cursor_box documents attribute 'rts_selected' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    doc.get_prototype("UtilitySprites").get_property_type("cursor_box", fd.StructTypeExpression).get_property(
        "rts_selected"
    ).required = False

    # https://lua-api.factorio.com/2.0.28/prototypes/UtilitySprites.html#cursor_box documents attribute 'rts_to_be_selected' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    doc.get_prototype("UtilitySprites").get_property_type("cursor_box", fd.StructTypeExpression).get_property(
        "rts_to_be_selected"
    ).required = False

    # https://lua-api.factorio.com/2.0.28/types/SingleGraphicProcessionLayer.html#frames documents attribute 'frame' as required
    # but it's absent from:
    #   cat game-definitions/base-2.0.28/script-output/data-raw-dump.json | jq '.procession."default-b".timeline.layers[5].frames[0]'
    # (and many others)
    typing.cast(
        fd.StructTypeExpression,
        doc.get_type_def("SingleGraphicProcessionLayer", fd.StructTypeExpression)
        .get_property_type("frames", fd.ArrayTypeExpression)
        .content,
    ).get_property("frame").required = False

    # https://lua-api.factorio.com/2.0.28/types/ProcessionTimeline.html#audio_events is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.procession."default-intermezzo".timeline'
    doc.get_type_def("ProcessionTimeline", fd.StructTypeExpression).get_property("audio_events").required = False

    # https://lua-api.factorio.com/2.0.28/types/RailPictureSet.html#rail_endings is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."rail-ramp"."dummy-rail-ramp".pictures'
    doc.get_type_def("RailPictureSet", fd.StructTypeExpression).get_property("rail_endings").required = False

    # https://lua-api.factorio.com/2.0.28/types/SpriteSource.html#filename is documented as required
    # but is absent from:
    #  cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.wall."stone-wall".pictures.ending_left'
    # (and many others)
    doc.get_type_def("SpriteSource", fd.StructTypeExpression).get_property("filename").required = False

    # https://lua-api.factorio.com/2.0.28/types/NeighbourConnectableConnectionDefinition.html#location documents attributes 'direction' as a 'MapPosition'
    # but it's an integer in:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."fusion-reactor"."fusion-reactor".neighbour_connectable.connections'
    # (probably a https://lua-api.factorio.com/2.0.28/defines.html#defines.direction)
    doc.get_type_def("NeighbourConnectableConnectionDefinition", fd.StructTypeExpression).get_property_type(
        "location", fd.StructTypeExpression
    ).set_property_type("direction", fd.RefTypeExpression(ref="uint8"))

    # https://lua-api.factorio.com/2.0.28/types/BoundingBox.html is documented as a 2-tuple,
    # but the prose explains it can also be a 3-tuple with a 'float' as third element.
    doc.get_type_def("BoundingBox", fd.UnionTypeExpression).members.append(
        fd.TupleTypeExpression(
            members=typing.cast(
                fd.TupleTypeExpression, doc.get_type_def("BoundingBox", fd.UnionTypeExpression).members[1]
            ).members
            + [fd.RefTypeExpression(ref="float")]
        )
    )

    # https://lua-api.factorio.com/2.0.28/types/SingleGraphicProcessionLayer.html#frames documents attribute 'timestamp' as 'MapTick', which is an alias for 'uint64'
    # but it's some kind of floating point number in:
    #  cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.procession."planet-to-platform-a".timeline.layers[33].frames[0].timestamp'
    typing.cast(
        fd.StructTypeExpression,
        doc.get_type_def("SingleGraphicProcessionLayer", fd.StructTypeExpression)
        .get_property_type("frames", fd.ArrayTypeExpression)
        .content,
    ).set_property_type("timestamp", fd.RefTypeExpression(ref="double"))

    # https://lua-api.factorio.com/2.0.28/types/Sound.html doesn't mention a plain string (filename) as a possible value
    # but many sounds are plain filenames:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '."rocket-silo"."rocket-silo".alarm_sound'
    # (and many others)
    doc.get_type_def("Sound", fd.UnionTypeExpression).members.append(fd.RefTypeExpression(ref="string"))

    # https://lua-api.factorio.com/2.0.28/types/CreateDecorativesTriggerEffectItem.html#type is documented as required
    # but is absent from:
    #   cat game-definitions/space-age-2.0.28/script-output/data-raw-dump.json | jq '.turret."medium-worm-turret".spawn_decoration[0]'
    # (and many others)
    doc.get_type_def("CreateDecorativesTriggerEffectItem", fd.StructTypeExpression).get_property(
        "type"
    ).required = False

    # @todo Document documentation issues
    doc.get_type_def("CreateParticleTriggerEffectItem", fd.StructTypeExpression).get_property("type").required = False
    doc.get_type_def("CreateParticleTriggerEffectItem", fd.StructTypeExpression).get_property(
        "particle_name"
    ).required = False
    doc.get_type_def("CreateParticleTriggerEffectItem", fd.StructTypeExpression).get_property(
        "initial_height"
    ).required = False
    doc.get_type_def("TriggerEffectItem", fd.StructTypeExpression).set_property_type(
        "repeat_count", fd.RefTypeExpression(ref="double")
    )
    doc.get_type_def("CreateParticleTriggerEffectItem", fd.StructTypeExpression).set_property_type(
        "tail_length_deviation", fd.RefTypeExpression(ref="double")
    )
    doc.get_type_def("BeamTriggerDelivery", fd.StructTypeExpression).set_property_type(
        "max_length", fd.RefTypeExpression(ref="double")
    )
    doc.get_type_def("DamageTileTriggerEffectItem", fd.StructTypeExpression).get_property_type(
        "type", fd.LiteralStringTypeExpression
    ).value = "damage-tile"
