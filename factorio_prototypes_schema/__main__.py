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
            "ammo": "ItemPrototype",
            "armor": "ItemPrototype",
            "assembling-machine": "CraftingMachinePrototype",
            "blueprint": "ItemPrototype",
            "blueprint-book": "ItemPrototype",
            "capsule": "ItemPrototype",
            "character": "CharacterPrototype",
            "copy-paste-tool": "ItemPrototype",
            "deconstruction-item": "ItemPrototype",
            "fluid": "Prototype",
            "furnace": "CraftingMachinePrototype",
            "gun": "ItemPrototype",
            "item": "ItemPrototype",
            "item-with-entity-data": "ItemPrototype",
            "module": "ItemPrototype",
            "rail-planner": "ItemPrototype",
            "recipe": "RecipePrototype",
            "repair-tool": "ItemPrototype",
            "rocket-silo": "CraftingMachinePrototype",
            "selection-tool": "ItemPrototype",
            "space-platform-starter-pack": "ItemPrototype",
            "spidertron-remote": "ItemPrototype",
            "tool": "ItemPrototype",
            "upgrade-item": "ItemPrototype",
        },
        types=types,
        prototypes=prototypes,
    ).to_json_value()

    if load_types is None:
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
        if (
            schema["definitions"].get("TriggerEffect", {}).get("anyOf", [{}])[0].get("$ref", {})
            == "#/definitions/DamageEntityTriggerEffectItem"
        ):
            schema["definitions"]["TriggerEffect"]["anyOf"][0]["$ref"] = "#/definitions/DamageTriggerEffectItem"
        else:
            debug("Failed to patch TriggerEffect")

        # types/TriggerEffect.html refers to non-documented type DamageEntityTriggerEffectItem,
        # and types/DamageTriggerEffectItem.html is documented but used nowhere

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
        if schema["definitions"].get("IconSequencePositioning", {}).get("properties", {}).get(
            "inventory_index", {}
        ) == {"$ref": "#/definitions/defines.inventory"}:
            del schema["definitions"]["IconSequencePositioning"]["properties"]["inventory_index"]
        else:
            debug("Failed to patch IconSequencePositioning")

        # RandomRange can be {min: double, max: double}
        if schema["definitions"].get("RandomRange", {}).get("anyOf", [{}])[0] == {"$ref": "#/definitions/{"}:
            schema["definitions"]["RandomRange"]["anyOf"] = schema["definitions"]["RandomRange"]["anyOf"][1:]
        else:
            debug("Failed to patch RandomRange")

    json.dump(schema, sys.stdout, indent=2)


def extract_all_types(factorio_location: str) -> Iterable[FactorioSchema.TypeDefinition]:
    for type_name in tqdm.tqdm(sorted(set(extract_all_type_names(factorio_location)))):
        if type_name in ["Data", "DataExtendMethod", "AnyPrototype"]:
            continue
        try:
            yield extract_type(factorio_location, type_name)
        except:
            debug("Failed to extract type:", type_name)
            raise


def load_all_types(factorio_location: str, load_types: str) -> Iterable[FactorioSchema.TypeDefinition]:
    with open(load_types) as f:
        previous_schema = json.load(f)
    for type_name in sorted(set(extract_all_type_names(factorio_location))):
        if type_name in ["Data", "DataExtendMethod", "AnyPrototype"]:
            continue
        yield FactorioSchema.TypeDefinition(name=type_name, definition=previous_schema["definitions"][type_name])


def extract_all_type_names(factorio_location: str) -> Iterable[str]:
    for a in read_file(factorio_location, "types").find_all("a"):
        link = tag(a).get("href")
        if link is not None and str(link).startswith("types/"):
            type = str(link).split("#")[0].split("/")[-1]
            assert type.endswith(".html")
            yield type[:-5]


def extract_type(factorio_location: str, type_name: str) -> FactorioSchema.TypeDefinition:
    soup = read_file(factorio_location, "types", type_name)

    kind_soup = tag(tag(soup.find("h2")).find("span"))
    kind_link_soup = kind_soup.find("a")
    if kind_link_soup is None:
        match kind_soup.text.strip(" :\xa0"):
            case "struct" | "struct - abstract" | "struct or array[struct]":

                return FactorioSchema.StructTypeDefinition(
                    name=type_name,
                    base=extract_struct_base(soup),
                    properties=list(extract_struct_properties(type_name, soup)),
                )

            case "union" | "union or array[union]" | "array[union]":

                def extract_union_types() -> Iterable[JsonValue]:
                    for span_soup in (tag(el) for el in soup.find_all("span", class_="docs-attribute-name")):
                        content_soup = span_soup.contents[0]
                        if isinstance(content_soup, bs4.element.Tag) and content_soup.name == "code":
                            yield {"type": "string", "const": content_soup.text.strip().strip('"')}
                        else:
                            yield {"$ref": f"#/definitions/{content_soup.text.strip()}"}

                return FactorioSchema.UnionTypeDefinition(name=type_name, types=list(extract_union_types()))

            case "builtin":
                return FactorioSchema.TypeDefinition(name=type_name, definition=FactorioSchema.builtin_types[type_name])
            case _:
                assert False, (type_name, soup.find("h2"))
    else:
        return FactorioSchema.UnionTypeDefinition(
            name=type_name, types=[{"$ref": f"#/definitions/{kind_link_soup.text}"}]
        )


def extract_all_prototypes(factorio_location: str) -> Iterable[FactorioSchema.TypeDefinition]:
    yield extract_prototype(factorio_location, "PrototypeBase")
    yield extract_prototype(factorio_location, "Prototype")
    yield extract_prototype(factorio_location, "ItemPrototype")
    yield FactorioSchema.StructTypeDefinition(
        "RecipePrototype",
        base="Prototype",
        properties=[
            FactorioSchema.Property(
                name="ingredients",
                type={
                    "oneOf": [
                        {"type": "array", "items": {"$ref": "#/definitions/IngredientPrototype"}},
                        {"type": "object", "additionalProperties": False},
                    ]
                },
            ),
            FactorioSchema.Property(
                name="results",
                type={
                    "oneOf": [
                        {"type": "array", "items": {"$ref": "#/definitions/ProductPrototype"}},
                        {"type": "object", "additionalProperties": False},
                    ]
                },
            ),
            FactorioSchema.Property(name="category", type={"type": "string"}),
        ],
    )
    yield FactorioSchema.StructTypeDefinition(
        "CraftingMachinePrototype",
        base="Prototype",
        properties=[
            FactorioSchema.Property(name="crafting_categories", type={"type": "array", "items": {"type": "string"}})
        ],
    )
    yield FactorioSchema.StructTypeDefinition(
        "CharacterPrototype",
        base="Prototype",
        properties=[
            FactorioSchema.Property(name="crafting_categories", type={"type": "array", "items": {"type": "string"}})
        ],
    )


def extract_prototype(factorio_location: str, prototype_name: str) -> FactorioSchema.TypeDefinition:
    soup = read_file(factorio_location, "prototypes", prototype_name)

    return FactorioSchema.StructTypeDefinition(
        prototype_name, base=extract_struct_base(soup), properties=list(extract_struct_properties(prototype_name, soup))
    )


def extract_struct_base(soup: bs4.BeautifulSoup) -> str | None:
    base_soup = soup.find(string=re.compile(r"Inherits from"))
    if base_soup is not None:
        base_link_soup = tag(base_soup.parent).find("a")
        assert base_link_soup is not None
        base = base_link_soup.text
        assert isinstance(base, str)
        return base

    return None


def extract_struct_properties(type_name: str, soup: bs4.BeautifulSoup) -> Iterable[FactorioSchema.Property]:
    main_soup = soup.find("div", id="attributes-body-main")
    if main_soup is not None:
        for div_soup in (tag(el) for el in tag(main_soup).find_all("div", recursive=False)):
            for h3_soup in (tag(el) for el in div_soup.find_all("h3", recursive=False)):
                property_name = tag(h3_soup.contents[0]).contents[0].text.strip()

                if (type_name, property_name) in [
                    ("ItemPrototype", "close_sound"),
                    ("ItemPrototype", "drop_sound"),
                    ("ItemPrototype", "flags"),
                    ("ItemPrototype", "icons"),
                    ("ItemPrototype", "inventory_move_sound"),
                    ("ItemPrototype", "layers"),
                    ("ItemPrototype", "open_sound"),
                    ("ItemPrototype", "pick_sound"),
                    ("ItemPrototype", "pictures"),
                    ("ItemPrototype", "random_tint_color"),
                    ("ItemPrototype", "rocket_launch_products"),
                    ("ItemPrototype", "spoil_to_trigger_result"),
                ]:
                    continue

                try:
                    try:
                        type_soup = tag(tag(tag(h3_soup.contents[0]).contents[1]).contents[1])
                    except IndexError:
                        debug("Failed to extract property:", type_name, property_name)
                        continue

                    if type_soup.name == "a":
                        property_type = json_value({"$ref": f"#/definitions/{type_soup.text}"})
                    elif type_soup.name == "code":
                        property_type = json_value({"type": "string", "const": type_soup.text.strip().strip('"')})
                    else:
                        property_type = json_value(None)

                    optional = h3_soup.contents[1].text.strip() == "optional"

                    yield FactorioSchema.Property(name=property_name, type=property_type, required=not optional)
                except:
                    debug("Failed to extract property:", type_name, property_name)
                    raise


def tag(tag: bs4.element.PageElement | None) -> bs4.element.Tag:
    """
    Assert at runtime that a PageElement is actually a Tag.
    (Tag is a subclass of PageElement.)
    Helps with static type checking.
    """
    assert isinstance(tag, bs4.element.Tag)
    return tag


# def extract_all_prototype_names():
#     prototypes = set()
#     for a in read_file("prototypes").find_all('a'):
#         link = a.get("href")
#         if link is not None and link.startswith("prototypes/"):
#             prototype = link.split("#")[0].split("/")[-1]
#             assert prototype.endswith(".html")
#             prototypes.add(prototype[:-5])
#     return sorted(prototypes)


# def extract_prototype_definition(name):
#     print(f"Extracting prototype {name}")
#     soup = read_file("prototypes", name)
#     attributes = soup.find(id="attributes-body-main")
#     if attributes is None:
#         pass
#     else:
#         for h3 in attributes.find_all("h3"):
#             try:
#                 name = h3.contents[0].contents[0].text.strip()
#                 link_to_type = h3.contents[0].contents[1].contents[1]
#                 assert link_to_type["href"] == f"../types/{link_to_type.text}.html"
#                 type = link_to_type.text.strip()
#                 optional = h3.contents[1].text.strip() == "optional"
#                 # print(f"  {name}: {type}{' (optional)' if optional else ''}")
#             except:
#                 print(h3)
#     return None


def read_file(factorio_location: str, *stem: str) -> BeautifulSoup:
    with open(os.path.join(factorio_location, "doc-html", *stem[:-1], stem[-1] + ".html")) as f:
        return BeautifulSoup(f.read(), "html.parser")


if __name__ == "__main__":
    main()
