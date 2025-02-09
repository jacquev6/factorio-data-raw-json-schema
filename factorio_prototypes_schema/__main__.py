#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Iterable
import json
import os
import re
import sys

from bs4 import BeautifulSoup
import bs4
import click
import tqdm


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def debug(*arg: Any, **kwds: Any) -> None:
    print(*arg, **kwds, file=sys.stderr)


def json_value(value: JsonValue) -> JsonValue:
    """
    Statically assert that a value is a JsonValue and erase its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


class FactorioSchema:
    builtin_types: dict[str, dict[str, JsonValue]] = {
        "string": {"type": "string"},
        "float": {"type": "number"},
        "double": {"type": "number"},
        "bool": {"type": "boolean"},
        "uint8": {"type": "integer", "minimum": 0, "maximum": 255},
        "uint16": {"type": "integer", "minimum": 0, "maximum": 65535},
        "uint32": {"type": "integer", "minimum": 0, "maximum": 4294967295},
        "uint64": {"type": "integer", "minimum": 0, "maximum": 18446744073709551615},
        "int8": {"type": "integer", "minimum": -128, "maximum": 127},
        "int16": {"type": "integer", "minimum": -32768, "maximum": 32767},
        "int32": {"type": "integer", "minimum": -2147483648, "maximum": 2147483647},
        "int64": {"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807},
    }

    def __init__(
        self, *, properties: dict[str, str], types: list[TypeDefinition], prototypes: list[TypeDefinition]
    ) -> None:
        self.properties = properties
        self.types = types
        self.prototypes = prototypes

    def to_json_value(self) -> JsonValue:
        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": {
                k: {"type": "object", "additionalProperties": {"$ref": f"#/definitions/{v}"}}
                for k, v in self.properties.items()
            },
            "definitions": (
                {
                    d.name: json_value(
                        {"description": json_value(f"https://lua-api.factorio.com/stable/types/{d.name}.html")}
                        | d.definition
                    )
                    for d in self.types
                }
                | {
                    d.name: json_value(
                        {"description": json_value(f"https://lua-api.factorio.com/stable/prototypes/{d.name}.html")}
                        | d.definition
                    )
                    for d in self.prototypes
                }
            ),
        }

    class TypeDefinition:
        def __init__(self, *, name: str, definition: dict[str, JsonValue]) -> None:
            self.name = name
            self.definition = definition

    class Property:
        # @todo Give a more specific type to 'type'
        def __init__(self, *, name: str, type: JsonValue, required: bool = False) -> None:
            self.name = name
            self.type = type
            self.required = required

    @staticmethod
    def StructTypeDefinition(
        name: str, *, base: str | None = None, properties: list[FactorioSchema.Property]
    ) -> TypeDefinition:
        required = [json_value(p.name) for p in properties if p.required]
        self_definition = {"type": "object", "properties": json_value({p.name: p.type for p in properties})} | (
            {"required": json_value(required)} if required else {}
        )
        if base is None:
            if len(properties) > 0:
                definition = self_definition
            else:
                definition = {"type": "object"}
        else:
            if len(properties) == 0:
                definition = {"allOf": [{"$ref": f"#/definitions/{base}"}]}  # @todo Consider removing the "allOf"
            else:
                definition = {"allOf": [{"$ref": f"#/definitions/{base}"}, self_definition]}
        return FactorioSchema.TypeDefinition(name=name, definition=definition)

    @staticmethod
    def UnionTypeDefinition(*, name: str, types: list[JsonValue]) -> TypeDefinition:
        return FactorioSchema.TypeDefinition(name=name, definition={"anyOf": types})


@click.command()
@click.argument("factorio_location")
@click.option("--load-types")
@click.option("--load-prototypes")
def main(factorio_location: str, load_types: str | None, load_prototypes: str | None) -> None:
    if load_types is None:
        types = list(extract_all_types(factorio_location))
    else:
        types = list(load_all_types(factorio_location, load_types))

    if load_prototypes is None:
        prototypes = list(extract_all_prototypes(factorio_location, {type.name for type in types}))
    else:
        prototypes = list(load_all_prototypes(factorio_location, load_prototypes))

    schema: Any = FactorioSchema(
        properties={
            # @todo Extract
            "ammo": "AmmoItemPrototype",
            "armor": "ArmorPrototype",
            "assembling-machine": "AssemblingMachinePrototype",
            "blueprint": "BlueprintItemPrototype",
            "blueprint-book": "BlueprintBookPrototype",
            "capsule": "CapsulePrototype",
            "character": "CharacterPrototype",
            "copy-paste-tool": "CopyPasteToolPrototype",
            "deconstruction-item": "DeconstructionItemPrototype",
            "fluid": "FluidPrototype",
            "furnace": "FurnacePrototype",
            "gun": "GunPrototype",
            "item": "ItemPrototype",
            "item-with-entity-data": "ItemWithEntityDataPrototype",
            "module": "ModulePrototype",
            "rail-planner": "RailPlannerPrototype",
            "recipe": "RecipePrototype",
            "repair-tool": "RepairToolPrototype",
            "rocket-silo": "RocketSiloPrototype",
            "selection-tool": "SelectionToolPrototype",
            "space-platform-starter-pack": "SpacePlatformStarterPackPrototype",
            "spidertron-remote": "SpidertronRemotePrototype",
            "tool": "ToolPrototype",
            "upgrade-item": "UpgradeItemPrototype",
        },
        types=types,
        prototypes=prototypes,
    ).to_json_value()

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
    if (
        schema["definitions"].get("TriggerEffect", {}).get("anyOf", [{}])[0].get("$ref", {})
        == "#/definitions/DamageEntityTriggerEffectItem"
    ):
        schema["definitions"]["TriggerEffect"]["anyOf"][0]["$ref"] = "#/definitions/DamageTriggerEffectItem"
    else:
        debug("Failed to patch TriggerEffect")

    # types/TriggerEffect.html refers to non-documented type DamageEntityTriggerEffectItem,
    # and types/DamageTriggerEffectItem.html is documented but used nowhere

    # Empty arrays are serialized as {} instead of []
    # (patched in the generated schema because this must be done everywhere)

    # I'm fed up with documenting every single patch
    schema["definitions"]["WorkingVisualisations"]["properties"]["working_visualisations"] = {}

    # Ad-hoc patches because our extraction tool is weak
    # ==================================================

    # LocalisedString is a union of string and list[LocalisedString]
    if schema["definitions"].get("LocalisedString", {}).get("anyOf", []) == [{"$ref": "#/definitions/string"}]:
        schema["definitions"]["LocalisedString"]["anyOf"].append(
            {"type": "array", "item": {"$ref": "#/definitions/LocalisedString"}}
        )
    else:
        debug("Failed to patch LocalisedString")

    # IconSequencePositioning.inventory_index comes from "defines"
    if schema["definitions"].get("IconSequencePositioning", {}).get("properties", {}).get("inventory_index", {}) == {
        "$ref": "#/definitions/defines.inventory"
    }:
        del schema["definitions"]["IconSequencePositioning"]["properties"]["inventory_index"]
    else:
        debug("Failed to patch IconSequencePositioning")

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


def extract_all_types(factorio_location: str) -> Iterable[FactorioSchema.TypeDefinition]:
    all_type_names = set(extract_all_type_names(factorio_location))
    for type_name in tqdm.tqdm(sorted(all_type_names)):
        try:
            yield extract_type(factorio_location, type_name, all_type_names)
        except AssertionError as exc:
            debug(f"Failed to extract type {type_name!r}: {exc}")
            yield FactorioSchema.TypeDefinition(name=type_name, definition={})


def load_all_types(factorio_location: str, load_types: str) -> Iterable[FactorioSchema.TypeDefinition]:
    with open(load_types) as f:
        previous_schema = json.load(f)
    for type_name in sorted(set(extract_all_type_names(factorio_location))):
        definition = previous_schema["definitions"].get(type_name)
        if definition is not None:
            yield FactorioSchema.TypeDefinition(name=type_name, definition=definition)


def extract_all_type_names(factorio_location: str) -> Iterable[str]:
    for a in read_file(factorio_location, "types").find_all("a"):
        link = tag(a).get("href")
        if link is not None and str(link).startswith("types/"):
            type = str(link).split("#")[0].split("/")[-1]
            assert type.endswith(".html")
            yield type[:-5]


def extract_type(factorio_location: str, type_name: str, all_type_names: set[str]) -> FactorioSchema.TypeDefinition:
    assert type_name not in ["Data", "DataExtendMethod", "AnyPrototype"], "ignored"

    soup = read_file(factorio_location, "types", type_name)

    h2_text = tag(soup.find("h2")).text
    if (m := re.match(r"^" + type_name + r"\s*::\s*(.*?)\s*(Example code)?$", h2_text)) is not None:
        type_kind = m.group(1)
        if type_kind in all_type_names:
            return FactorioSchema.UnionTypeDefinition(name=type_name, types=[{"$ref": f"#/definitions/{type_kind}"}])
        else:
            match type_kind:
                case "struct" | "struct - abstract":
                    return FactorioSchema.StructTypeDefinition(
                        name=type_name,
                        base=extract_struct_base(soup),
                        properties=list(extract_struct_properties(type_name, soup, all_type_names)),
                    )
                case "union":
                    return FactorioSchema.UnionTypeDefinition(name=type_name, types=list(extract_union_members(soup)))
        assert False, f"unsupported type kind: {type_kind!r}"
    elif (m := re.match(r"^" + type_name + r"\s* builtin\s*(Example code)?$", h2_text)) is not None:
        return FactorioSchema.TypeDefinition(name=type_name, definition=FactorioSchema.builtin_types[type_name])
    else:
        assert False, f"failed to parse type header: {h2_text!r}"


def extract_all_prototypes(factorio_location: str, known_types: set[str]) -> Iterable[FactorioSchema.TypeDefinition]:
    for prototype_name in tqdm.tqdm(sorted(set(extract_all_prototype_names(factorio_location)))):
        try:
            yield extract_prototype(factorio_location, prototype_name, known_types)
        except AssertionError as exc:
            debug(f"Failed to extract prototype {prototype_name!r}: {exc}")
            yield FactorioSchema.TypeDefinition(name=prototype_name, definition={})


def load_all_prototypes(factorio_location: str, load_prototypes: str) -> Iterable[FactorioSchema.TypeDefinition]:
    with open(load_prototypes) as f:
        previous_schema = json.load(f)
    for prototype_name in sorted(set(extract_all_prototype_names(factorio_location))):
        definition = previous_schema["definitions"].get(prototype_name)
        if definition is not None:
            yield FactorioSchema.TypeDefinition(name=prototype_name, definition=definition)


def extract_all_prototype_names(factorio_location: str) -> Iterable[str]:
    for a in read_file(factorio_location, "prototypes").find_all("a"):
        link = tag(a).get("href")
        if link is not None and str(link).startswith("prototypes/"):
            prototype = str(link).split("#")[0].split("/")[-1]
            assert prototype.endswith(".html")
            yield prototype[:-5]


def extract_prototype(
    factorio_location: str, prototype_name: str, known_types: set[str]
) -> FactorioSchema.TypeDefinition:
    soup = read_file(factorio_location, "prototypes", prototype_name)

    return FactorioSchema.StructTypeDefinition(
        prototype_name,
        base=extract_struct_base(soup),
        properties=list(extract_struct_properties(prototype_name, soup, known_types)),
    )


def extract_union_members(soup: bs4.BeautifulSoup) -> Iterable[JsonValue]:
    for span_soup in (tag(el) for el in soup.find_all("span", class_="docs-attribute-name")):
        content_soup = span_soup.contents[0]
        if isinstance(content_soup, bs4.element.Tag) and content_soup.name == "code":
            value = content_soup.text.strip()
            if value.startswith('"') and value.endswith('"'):
                yield {"type": "string", "const": value.strip('"')}
            else:
                yield {"type": "integer", "const": int(value)}
        else:
            yield {"$ref": f"#/definitions/{content_soup.text.strip()}"}


def extract_struct_base(soup: bs4.BeautifulSoup) -> str | None:
    base_soup = soup.find(string=re.compile(r"Inherits from"))
    if base_soup is not None:
        base_link_soup = tag(base_soup.parent).find("a")
        assert base_link_soup is not None
        base = base_link_soup.text
        assert isinstance(base, str)
        return base

    return None


def extract_struct_properties(
    type_name: str, soup: bs4.BeautifulSoup, known_types: set[str]
) -> Iterable[FactorioSchema.Property]:
    main_soup = soup.find("div", id="attributes-body-main")
    if main_soup is not None:
        for div_soup in (tag(el) for el in tag(main_soup).find_all("div", recursive=False)):
            for h3_soup in (tag(el) for el in div_soup.find_all("h3", recursive=False)):
                property_name = str(tag(h3_soup.contents[0]).contents[0].text).strip()
                try:
                    h3_text = h3_soup.text
                    if (
                        m := re.match(r"^" + property_name + r"\s*::\s*(.*?)\s*(optional)?\s*(new)?$", h3_text)
                    ) is not None:
                        type_kind = m.group(1)
                        optional = m.group(2) == "optional"

                        options: list[JsonValue] = []
                        for option_kind in type_kind.split(" or "):
                            if option_kind in known_types:
                                options.append({"$ref": f"#/definitions/{option_kind}"})
                            elif (
                                option_kind.startswith("array[")
                                and option_kind.endswith("]")
                                and option_kind[6:-1] in known_types
                            ):
                                options.append(
                                    {"type": "array", "items": {"$ref": f"#/definitions/{option_kind[6:-1]}"}}
                                )
                                # Empty arrays are serialized as {} instead of []
                                options.append({"type": "object", "additionalProperties": False})
                            elif option_kind.startswith('"') and option_kind.endswith('"'):
                                options.append({"type": "string", "const": option_kind.strip('"')})
                            else:
                                assert (
                                    False
                                ), f"unsupported option in struct property kind: {type_kind!r} -> {option_kind!r}"

                        if len(options) == 1:
                            yield FactorioSchema.Property(name=property_name, type=options[0], required=not optional)
                        else:
                            yield FactorioSchema.Property(
                                name=property_name, type={"oneOf": options}, required=not optional
                            )
                    else:
                        assert False, f"failed to parse property header: {h3_text!r}"
                except AssertionError as exc:
                    debug(f"Failed to extract property {type_name}.{property_name}: {exc}")
                    yield FactorioSchema.Property(name=property_name, type={}, required="optional" not in h3_soup.text)


def tag(tag: bs4.element.PageElement | None) -> bs4.element.Tag:
    """
    Assert at runtime that a PageElement is actually a Tag.
    (Tag is a subclass of PageElement.)
    Helps with static type checking.
    """
    assert isinstance(tag, bs4.element.Tag), f"{tag!r} is not a Tag"
    return tag


def read_file(factorio_location: str, *stem: str) -> BeautifulSoup:
    with open(os.path.join(factorio_location, "doc-html", *stem[:-1], stem[-1] + ".html")) as f:
        return BeautifulSoup(f.read(), "html.parser")


if __name__ == "__main__":
    main()
