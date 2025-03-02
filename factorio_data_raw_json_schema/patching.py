import typing

from . import documentation
from .schema import JsonDict


# @todo Report to Factorio developers

# Serialization issue
#####################


# Empty arrays are serialized as {} instead of []
# For example:
#   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."assembling-machine"."captive-biter-spawner".allowed_effects'
def array_to_json_definition(content: JsonDict) -> JsonDict:
    return {"oneOf": [{"type": "array", "items": content}, {"type": "object", "additionalProperties": False}]}


# Confusion around TriggerEffect
################################

# https://lua-api.factorio.com/2.0.32/types/TriggerEffect.html refers to type 'DamageEntityTriggerEffectItem', but this type is not linked to its documentation.
# I believe it's a typo and should be 'DamageTriggerEffectItem', documented in https://lua-api.factorio.com/2.0.32/types/DamageTriggerEffectItem.html but not used anywhere.
local_types_for_union: dict[str, documentation.TypeExpression] = {
    "DamageEntityTriggerEffectItem": documentation.RefTypeExpression(ref="DamageTriggerEffectItem")
}


def patch_doc(doc: documentation.Doc) -> None:
    # Confusion around TriggerEffect (continued)
    ################################

    # https://lua-api.factorio.com/2.0.32/types/DamageTileTriggerEffectItem.html#type is documented as "damage"
    # but https://lua-api.factorio.com/2.0.32/types/TriggerEffect.html says it's loaded when the type is "damage-tile"
    doc.get_type_def("DamageTileTriggerEffectItem", documentation.StructTypeExpression).get_property_type(
        "type", documentation.LiteralStringTypeExpression
    ).value = "damage-tile"

    # Looks like a serialization issue
    ##################################

    # https://lua-api.factorio.com/2.0.32/types/WorkingVisualisations.html#working_visualisations is documented as array[WorkingVisualisation]
    # but is actually an object, with string keys looking like integers in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."mining-drill"."big-mining-drill".graphics_set.working_visualisations'
    # Note that is is an array as expected in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.working_visualisations'
    doc.get_type_def("WorkingVisualisations", documentation.StructTypeExpression).set_property_type(
        "working_visualisations",
        documentation.UnionTypeExpression(
            members=[
                doc.get_type_def("WorkingVisualisations", documentation.StructTypeExpression).get_property_type(
                    "working_visualisations"
                ),
                documentation.StructTypeExpression(
                    base=None,
                    properties=[],
                    overridden_properties=[],
                    custom_properties=doc.get_type_def("WorkingVisualisations", documentation.StructTypeExpression)
                    .get_property_type("working_visualisations", documentation.ArrayTypeExpression)
                    .content,
                ),
            ]
        ),
    )

    # Properties documented as integers that are actually floating point numbers
    ############################################################################

    # https://lua-api.factorio.com/2.0.32/types/WorkingVisualisations.html#shift_animation_waypoint_stop_duration is documented as uint16
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."mining-drill"."electric-mining-drill".graphics_set.shift_animation_waypoint_stop_duration'
    doc.get_type_def("WorkingVisualisations", documentation.StructTypeExpression).get_property_type(
        "shift_animation_waypoint_stop_duration", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/ItemProductPrototype.html#amount is documented as uint16
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.recipe."accumulator-recycling".results[0].amount'
    doc.get_type_def("ItemProductPrototype", documentation.StructTypeExpression).get_property_type(
        "amount", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/TechnologySlotStyleSpecification.html#level_offset_y is documented as int32
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_offset_y'
    doc.get_type_def("TechnologySlotStyleSpecification", documentation.StructTypeExpression).get_property_type(
        "level_offset_y", documentation.RefTypeExpression
    ).ref = "double"
    # This probably applies to https://lua-api.factorio.com/2.0.32/types/TechnologySlotStyleSpecification.html#level_offset_x as well
    doc.get_type_def("TechnologySlotStyleSpecification", documentation.StructTypeExpression).get_property_type(
        "level_offset_x", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/TechnologySlotStyleSpecification.html#level_range_offset_y is documented as int32
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."gui-style".default.technology_slot.level_range_offset_y'
    doc.get_type_def("TechnologySlotStyleSpecification", documentation.StructTypeExpression).get_property_type(
        "level_range_offset_y", documentation.RefTypeExpression
    ).ref = "double"
    # This probably applies to https://lua-api.factorio.com/2.0.32/types/TechnologySlotStyleSpecification.html#level_range_offset_x as well
    doc.get_type_def("TechnologySlotStyleSpecification", documentation.StructTypeExpression).get_property_type(
        "level_range_offset_x", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/BaseAttackParameters.html#lead_target_for_projectile_delay is documented as uint32
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."segmented-unit"."big-demolisher".revenge_attack_parameters.lead_target_for_projectile_delay'
    doc.get_type_def("BaseAttackParameters", documentation.StructTypeExpression).get_property_type(
        "lead_target_for_projectile_delay", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/TriggerEffectItem.html#repeat_count is documented as uint16
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.segment."medium-demolisher-segment-x0_6525".update_effects[1].effect[0].repeat_count'
    doc.get_type_def("TriggerEffectItem", documentation.StructTypeExpression).get_property_type(
        "repeat_count", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/CreateParticleTriggerEffectItem.html#tail_length_deviation is documented as uint16
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."optimized-particle"."vulcanus-stone-particle-smoke-small".ended_in_water_trigger_effect[1].tail_length_deviation'
    doc.get_type_def("CreateParticleTriggerEffectItem", documentation.StructTypeExpression).get_property_type(
        "tail_length_deviation", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/BeamTriggerDelivery.html#max_length is documented as uint16
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."chain-active-trigger"."chain-tesla-turret-chain".action.action_delivery.max_length'
    doc.get_type_def("BeamTriggerDelivery", documentation.StructTypeExpression).get_property_type(
        "max_length", documentation.RefTypeExpression
    ).ref = "double"

    # https://lua-api.factorio.com/2.0.32/types/SingleGraphicProcessionLayer.html#frames documents its attribute 'timestamp' as 'MapTick', which is an alias for 'uint64'
    # but it's some kind of floating point number in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.procession."planet-to-platform-a".timeline.layers[33].frames[0].timestamp'
    typing.cast(
        documentation.StructTypeExpression,
        doc.get_type_def("SingleGraphicProcessionLayer", documentation.StructTypeExpression)
        .get_property_type("frames", documentation.ArrayTypeExpression)
        .content,
    ).get_property_type("timestamp", documentation.RefTypeExpression).ref = "double"

    # https://lua-api.factorio.com/stable/prototypes/ItemPrototype.html#spoil_ticks is documented as uint32
    # but is some kind of floating point number in, for example:
    #   cat game-definitions/space-age-with-planet-mods/script-output/data-raw-dump.json | jq '.item."maraxsis-electricity".spoil_ticks'
    doc.get_prototype("ItemPrototype").get_property_type("spoil_ticks", documentation.RefTypeExpression).ref = "double"

    # Properties documented as required that are sometimes absent
    #############################################################

    # https://lua-api.factorio.com/2.0.32/prototypes/UtilityConstants.html#space_platform_default_speed_formula is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."utility-constants".default'
    doc.get_prototype("UtilityConstants").get_property("space_platform_default_speed_formula").required = False

    # https://lua-api.factorio.com/2.0.32/prototypes/SpaceLocationPrototype.html#gravity_pull is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."space-location"."space-location-unknown"'
    doc.get_prototype("SpaceLocationPrototype").get_property("gravity_pull").required = False

    # https://lua-api.factorio.com/2.0.32/prototypes/EditorControllerPrototype.html#ignore_surface_conditions is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."editor-controller".default'
    doc.get_prototype("EditorControllerPrototype").get_property("ignore_surface_conditions").required = False

    # https://lua-api.factorio.com/2.0.32/prototypes/AchievementPrototypeWithCondition.html#objective_condition is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."dont-kill-manually-achievement"."keeping-your-hands-clean"'
    doc.get_prototype("AchievementPrototypeWithCondition").get_property("objective_condition").required = False

    # https://lua-api.factorio.com/2.0.32/prototypes/UtilitySprites.html#cursor_box documents its attribute 'rts_selected' as required
    # but it's absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    doc.get_prototype("UtilitySprites").get_property_type(
        "cursor_box", documentation.StructTypeExpression
    ).get_property("rts_selected").required = False

    # https://lua-api.factorio.com/2.0.32/prototypes/UtilitySprites.html#cursor_box documents its attribute 'rts_to_be_selected' as required
    # but it's absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."utility-sprites".default.cursor_box'
    doc.get_prototype("UtilitySprites").get_property_type(
        "cursor_box", documentation.StructTypeExpression
    ).get_property("rts_to_be_selected").required = False

    # https://lua-api.factorio.com/2.0.32/types/SingleGraphicProcessionLayer.html#frames documents its attribute 'frame' as required
    # but it's absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.procession."platform-to-planet-a".timeline.layers[5].frames[0]'
    typing.cast(
        documentation.StructTypeExpression,
        doc.get_type_def("SingleGraphicProcessionLayer", documentation.StructTypeExpression)
        .get_property_type("frames", documentation.ArrayTypeExpression)
        .content,
    ).get_property("frame").required = False

    # https://lua-api.factorio.com/2.0.32/types/ProcessionTimeline.html#audio_events is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.procession."default-intermezzo".timeline'
    doc.get_type_def("ProcessionTimeline", documentation.StructTypeExpression).get_property(
        "audio_events"
    ).required = False

    # https://lua-api.factorio.com/2.0.32/types/RailPictureSet.html#rail_endings is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."rail-ramp"."dummy-rail-ramp".pictures'
    doc.get_type_def("RailPictureSet", documentation.StructTypeExpression).get_property("rail_endings").required = False

    # https://lua-api.factorio.com/2.0.32/types/SpriteSource.html#filename is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.wall."stone-wall".pictures.ending_left'
    doc.get_type_def("SpriteSource", documentation.StructTypeExpression).get_property("filename").required = False

    # https://lua-api.factorio.com/2.0.32/types/CreateDecorativesTriggerEffectItem.html#type is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.turret."medium-worm-turret".spawn_decoration[0]'
    # (and many others)
    doc.get_type_def("CreateDecorativesTriggerEffectItem", documentation.StructTypeExpression).get_property(
        "type"
    ).required = False

    # https://lua-api.factorio.com/2.0.32/types/CreateParticleTriggerEffectItem.html#type is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.car.tank.track_particle_triggers[2]'
    doc.get_type_def("CreateParticleTriggerEffectItem", documentation.StructTypeExpression).get_property(
        "type"
    ).required = False

    # https://lua-api.factorio.com/2.0.32/types/CreateParticleTriggerEffectItem.html#particle_name is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.car.tank.track_particle_triggers[2]'
    doc.get_type_def("CreateParticleTriggerEffectItem", documentation.StructTypeExpression).get_property(
        "particle_name"
    ).required = False

    # https://lua-api.factorio.com/2.0.32/types/CreateParticleTriggerEffectItem.html#initial_height is documented as required
    # but is absent from, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.car.tank.track_particle_triggers[2]'
    doc.get_type_def("CreateParticleTriggerEffectItem", documentation.StructTypeExpression).get_property(
        "initial_height"
    ).required = False

    # Miscellaneous
    ###############

    # https://lua-api.factorio.com/2.0.32/types/CranePartDyingEffect.html#particle_effects is documented as 'array[CreateParticleTriggerEffectItem]'
    # but is a single 'CreateParticleTriggerEffectItem' in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."agricultural-tower"."agricultural-tower".crane.parts[0].dying_effect.particle_effects'
    doc.get_type_def("CranePartDyingEffect", documentation.StructTypeExpression).set_property_type(
        "particle_effects",
        documentation.UnionTypeExpression(
            members=[
                doc.get_type_def("CranePartDyingEffect", documentation.StructTypeExpression).get_property_type(
                    "particle_effects"
                ),
                doc.get_type_def("CranePartDyingEffect", documentation.StructTypeExpression)
                .get_property_type("particle_effects", documentation.ArrayTypeExpression)
                .content,
            ]
        ),
    )

    # https://lua-api.factorio.com/2.0.32/prototypes/ShortcutPrototype.html#action doesn't mention "redo" as a possible value
    # but that value is used in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '.shortcut.redo.action'
    doc.get_prototype("ShortcutPrototype").get_property_type(
        "action", documentation.UnionTypeExpression
    ).members.append(documentation.LiteralStringTypeExpression(value="redo"))

    # https://lua-api.factorio.com/2.0.32/prototypes/AchievementPrototypeWithCondition.html#objective_condition doesn't mention "late-research" as a possible value
    # and is not overridden in https://lua-api.factorio.com/2.0.32/prototypes/DontBuildEntityAchievementPrototype.html
    # but that value is used in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."dont-build-entity-achievement"."logistic-network-embargo".objective_condition'
    doc.get_prototype("AchievementPrototypeWithCondition").get_property_type(
        "objective_condition", documentation.UnionTypeExpression
    ).members.append(documentation.LiteralStringTypeExpression(value="late-research"))

    # https://lua-api.factorio.com/2.0.32/types/NeighbourConnectableConnectionDefinition.html#location documents its attributes 'direction' as a 'MapPosition'
    # but it's an integer in, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."fusion-reactor"."fusion-reactor".neighbour_connectable.connections[0].location.direction'
    # (probably a https://lua-api.factorio.com/2.0.32/defines.html#defines.direction)
    doc.get_type_def("NeighbourConnectableConnectionDefinition", documentation.StructTypeExpression).get_property_type(
        "location", documentation.StructTypeExpression
    ).set_property_type("direction", documentation.RefTypeExpression(ref="uint8"))

    # https://lua-api.factorio.com/2.0.32/types/BoundingBox.html is documented as a 2-tuple,
    # but the prose explains it can also be a 3-tuple with a 'float' as third element.
    doc.get_type_def("BoundingBox", documentation.UnionTypeExpression).members.append(
        documentation.TupleTypeExpression(
            members=typing.cast(
                documentation.TupleTypeExpression,
                doc.get_type_def("BoundingBox", documentation.UnionTypeExpression).members[1],
            ).members
            + [documentation.RefTypeExpression(ref="float")]
        )
    )

    # https://lua-api.factorio.com/2.0.32/types/Sound.html doesn't mention a plain string (filename) as a possible value
    # but many sounds are plain filenames, for example:
    #   cat game-definitions/space-age/script-output/data-raw-dump.json | jq '."rocket-silo"."rocket-silo".alarm_sound'
    doc.get_type_def("Sound", documentation.UnionTypeExpression).members.append(
        documentation.RefTypeExpression(ref="string")
    )
