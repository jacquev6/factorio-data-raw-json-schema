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
import lark
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

    # types/TriggerEffect.html refers to non-documented type DamageEntityTriggerEffectItem,
    # and types/DamageTriggerEffectItem.html is documented but used nowhere

    # Empty arrays are serialized as {} instead of []
    # (patched in the generated schema because this must be done everywhere)

    # I'm fed up with documenting every single patch
    schema["definitions"]["WorkingVisualisations"]["properties"]["working_visualisations"] = {}
    schema["definitions"]["CharacterPrototype"]["allOf"][1]["properties"]["synced_footstep_particle_triggers"] = {}

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
        local_types = {
            name: FactorioSchema.TypeDefinition(name=name, definition={"anyOf": [{"$ref": f"#/definitions/{name}"}]})
            for name in all_type_names
        }

        type_expression = m.group(1).replace(" - abstract", "")
        if "struct" in type_expression:
            properties_div_soup = soup.find("div", id="attributes-body-main")
            local_types["struct"] = FactorioSchema.StructTypeDefinition(
                name=type_name,
                base=extract_struct_base(soup),
                properties=list(extract_struct_properties(type_name, properties_div_soup, all_type_names)),
            )
            assert type_expression == "struct", f"failed to match type expression: {type_expression!r}"

        if "union" in type_expression:
            local_types["union"] = FactorioSchema.UnionTypeDefinition(
                name=type_name, types=list(extract_union_members(soup))
            )
            assert type_expression == "union", f"failed to match type expression: {type_expression!r}"

        try:
            type_expression_tree = type_expression_parser.parse(type_expression)
            return FactorioSchema.TypeDefinition(
                name=type_name, definition=TypeExpressionTransformer(set(), local_types).transform(type_expression_tree)
            )
        except lark.exceptions.LarkError:
            assert False, f"failed to parse type expression: {type_expression!r}"
    elif (m := re.match(r"^" + type_name + r"\s* builtin\s*(Example code)?$", h2_text)) is not None:
        return FactorioSchema.TypeDefinition(name=type_name, definition=FactorioSchema.builtin_types[type_name])
    else:
        assert False, f"failed to regex-match type header: {h2_text!r}"


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
    # assert prototype_name in ["WallPrototype"], "ignored"

    soup = read_file(factorio_location, "prototypes", prototype_name)
    properties_div_soup = soup.find("div", id="attributes-body-main")

    return FactorioSchema.StructTypeDefinition(
        prototype_name,
        base=extract_struct_base(soup),
        properties=list(extract_struct_properties(prototype_name, properties_div_soup, known_types)),
    )


def extract_union_members(soup: bs4.element.PageElement | None) -> Iterable[JsonValue]:
    if soup is not None:
        for span_soup in (tag(el) for el in tag(soup).find_all("span", class_="docs-attribute-name")):
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
    type_name: str, properties_div_soup: bs4.element.PageElement | None, global_types: set[str]
) -> Iterable[FactorioSchema.Property]:
    if properties_div_soup is not None:
        for property_div_soup in (tag(el) for el in tag(properties_div_soup).find_all("div", recursive=False)):
            try:
                property_header_soup = tag(property_div_soup.find("h3", recursive=False))
                property_name = str(tag(property_header_soup.contents[0]).contents[0]).strip()

                local_types = {}
                for local_type_div_soup in (tag(el) for el in property_div_soup.find_all("div", class_="inline-type")):
                    local_type_header_text = tag(local_type_div_soup.find("h4")).text
                    if (m := re.match(r"^(.*?)\s*::\s*(.*?)\s*$", local_type_header_text)) is not None:
                        local_type_name = m.group(1)
                        match m.group(2):
                            case "struct":
                                local_type_properties = list(
                                    extract_struct_properties(
                                        f"{type_name}.{local_type_name}",
                                        tag(local_type_div_soup.find("h2", string="Properties")).next_sibling,
                                        global_types,
                                    )
                                )
                                local_types[local_type_name] = FactorioSchema.StructTypeDefinition(
                                    local_type_name, base=None, properties=local_type_properties
                                )
                            case "union":
                                local_types[local_type_name] = FactorioSchema.UnionTypeDefinition(
                                    name=local_type_name,
                                    types=list(
                                        extract_union_members(
                                            tag(local_type_div_soup.find("h4", string="Union members")).next_sibling
                                        )
                                    ),
                                )
                            case local_type_expression:
                                try:
                                    local_type_expression_tree = type_expression_parser.parse(local_type_expression)
                                    local_types[local_type_name] = FactorioSchema.TypeDefinition(
                                        name=local_type_name,
                                        definition=TypeExpressionTransformer(global_types, local_types).transform(
                                            local_type_expression_tree
                                        ),
                                    )
                                except lark.exceptions.LarkError:
                                    assert False, f"failed to parse local type expression: {local_type_expression!r}"
                    else:
                        assert False, f"failed to regex-match local type header: {local_type_header_text!r}"

                property_header_text = property_header_soup.text
                m = re.match(
                    r"^" + property_name + r"\s*::\s*(.*?)\s*(optional)?\s*(new|changed)?$", property_header_text
                )
                assert m is not None, f"failed to regex-match property header: {property_header_text!r}"
                optional = m.group(2) == "optional"

                match m.group(1):
                    case "union":
                        property_type = FactorioSchema.UnionTypeDefinition(
                            name="property",
                            types=list(
                                extract_union_members(
                                    tag(property_div_soup.find("h4", string="Union members")).next_sibling
                                )
                            ),
                        ).definition
                    case type_expression:
                        try:
                            type_expression_tree = type_expression_parser.parse(type_expression)
                            property_type = TypeExpressionTransformer(global_types, local_types).transform(
                                type_expression_tree
                            )
                        except lark.exceptions.LarkError:
                            assert False, f"failed to parse type expression: {type_expression!r}"

                yield FactorioSchema.Property(name=property_name, type=property_type, required=not optional)

            except AssertionError as exc:
                debug(f"Failed to extract property {type_name}.{property_name}: {exc}")
                yield FactorioSchema.Property(
                    name=property_name, type={}, required="optional" not in property_header_soup.text
                )


type_expression_parser = lark.Lark(
    """
    type_expression : named_type | literal_string | array_type | union_type | dictionary_type | tuple_type

    named_type : CNAME
    literal_string : ESCAPED_STRING
    array_type : "array" "[" type_expression "]"
    union_type : type_expression "or" type_expression
    dictionary_type : "dictionary" "[" type_expression "→" type_expression "]"
    tuple_type : "{" type_expression ("," type_expression)* "}"

    %import common.ESCAPED_STRING
    %import common.CNAME
    %import common.WS
    %ignore WS
    %ignore "\xa0"
    """,
    start="type_expression",
)


class TypeExpressionTransformer(lark.Transformer[lark.Token, dict[str, JsonValue]]):
    def __init__(self, global_types: set[str], local_types: dict[str, FactorioSchema.TypeDefinition]) -> None:
        self.global_types = global_types
        self.local_types = local_types

    def type_expression(self, items: list[JsonValue]) -> JsonValue:
        return items[0]

    def named_type(self, items: list[str]) -> JsonValue:
        type_name = items[0]
        if type_name == "true":
            return {"type": "boolean", "const": True}
        elif type_name in self.global_types:
            return {"$ref": f"#/definitions/{type_name}"}
        elif type_name in self.local_types:
            return self.local_types[type_name].definition
        else:
            assert False, f"unknown type: {type_name!r}"

    def literal_string(self, items: list[str]) -> JsonValue:
        value = items[0]
        assert value.startswith('"') and value.endswith('"')
        return {"type": "string", "const": value.strip('"')}

    def array_type(self, items: list[JsonValue]) -> JsonValue:
        return {
            "oneOf": [
                {"type": "array", "items": items[0]},
                # Empty arrays are serialized as {} instead of []
                {"type": "object", "additionalProperties": False},
            ]
        }

    def union_type(self, items: list[JsonValue]) -> JsonValue:
        members: list[JsonValue] = []
        for item in items:
            if isinstance(item, dict) and item.get("oneOf") is not None:
                assert isinstance(item["oneOf"], list)
                members.extend(item["oneOf"])
            else:
                members.append(item)
        return {"oneOf": members}

    def dictionary_type(self, items: list[JsonValue]) -> JsonValue:
        return {"type": "object", "additionalProperties": items[1], "propertyNames": items[0]}

    def tuple_type(self, items: list[JsonValue]) -> JsonValue:
        return {"type": "array", "items": items, "minItems": len(items), "maxItems": len(items)}


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
