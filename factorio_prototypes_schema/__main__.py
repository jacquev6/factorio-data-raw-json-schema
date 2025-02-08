#!/usr/bin/env python3

from __future__ import annotations

from typing import Any, Iterable
import abc
import json
import os
import sys

from bs4 import BeautifulSoup
import bs4


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
    simple_types_mapping: dict[str, JsonValue] = {
        "string": {"type": "string"},
        "float": {"type": "number"},
        "double": {"type": "number"},
        "bool": {"type": "boolean"},
        "uint8": {"type": "integer", "minimum": 0, "maximum": 255},
        "uint16": {"type": "integer", "minimum": 0, "maximum": 65535},
        "uint32": {"type": "integer", "minimum": 0, "maximum": 4294967295},
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
                        | d.to_json_dict()
                    )
                    for d in self.types
                }
                | {
                    d.name: json_value(
                        {"description": json_value(f"https://lua-api.factorio.com/stable/prototypes/{d.name}.html")}
                        | d.to_json_dict()
                    )
                    for d in self.prototypes
                }
            ),
        }

    class TypeDefinition(abc.ABC):
        def __init__(self, name: str) -> None:
            self.name = name

        @abc.abstractmethod
        def to_json_dict(self) -> dict[str, JsonValue]:
            pass

    class Property:
        # @todo Give a more specific type to 'type'
        def __init__(self, *, name: str, type: JsonValue, required: bool = False) -> None:
            self.name = name
            self.type = type
            self.required = required

    class StructTypeDefinition(TypeDefinition):
        def __init__(self, name: str, *, base: str | None = None, properties: list[FactorioSchema.Property]):
            super().__init__(name)
            self.base = base
            self.properties = properties

        def to_json_dict(self) -> dict[str, JsonValue]:
            required = [json_value(p.name) for p in self.properties if p.required]
            self_type = {"type": "object", "properties": json_value({p.name: p.type for p in self.properties})} | (
                {"required": json_value(required)} if required else {}
            )
            if self.base is None:
                assert len(self.properties) > 0
                return self_type
            else:
                if len(self.properties) == 0:
                    return {"allOf": [{"$ref": f"#/definitions/{self.base}"}]}  # @todo Consider removing the "allOf"
                else:
                    return {"allOf": [{"$ref": f"#/definitions/{self.base}"}, self_type]}

    class UnionTypeDefinition(TypeDefinition):
        def __init__(self, name: str, *, types: list[JsonValue]):
            super().__init__(name)
            self.types = types

        def to_json_dict(self) -> dict[str, JsonValue]:
            return {"anyOf": self.types}


def main(factorio_location: str) -> None:
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
            "fluid": "ItemPrototype",
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
        types=list(extract_all_types(factorio_location)),
        prototypes=[
            FactorioSchema.StructTypeDefinition(
                "PrototypeBase",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.StructTypeDefinition("Prototype", base="PrototypeBase", properties=[]),
            FactorioSchema.StructTypeDefinition("ItemPrototype", base="Prototype", properties=[]),
            FactorioSchema.StructTypeDefinition(
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
            ),
            FactorioSchema.StructTypeDefinition(
                "CraftingMachinePrototype",
                base="Prototype",
                properties=[
                    FactorioSchema.Property(
                        name="crafting_categories", type={"type": "array", "items": {"type": "string"}}
                    )
                ],
            ),
            FactorioSchema.StructTypeDefinition(
                "CharacterPrototype",
                base="Prototype",
                properties=[
                    FactorioSchema.Property(
                        name="crafting_categories", type={"type": "array", "items": {"type": "string"}}
                    )
                ],
            ),
        ],
    ).to_json_value()

    # Ad-hoc patches because the doc doesn't match the actual data
    # types/ItemProductPrototype.html#amount_min is documented as uint16 but is some sort of floating point in e.g. 'speed-module-recycling'
    assert (
        schema["definitions"]["ItemProductPrototype"]["properties"]["amount"]
        == FactorioSchema.simple_types_mapping["uint16"]
    )
    schema["definitions"]["ItemProductPrototype"]["properties"]["amount"] = {"type": "number"}

    json.dump(schema, sys.stdout, indent=2)


def extract_all_types(factorio_location: str) -> Iterable[FactorioSchema.TypeDefinition]:
    for type_name in [
        "ItemID",
        "FluidID",
        "FluidAmount",
        "ItemIngredientPrototype",
        "FluidIngredientPrototype",
        "IngredientPrototype",
        "ItemProductPrototype",
        "FluidProductPrototype",
        "ResearchProgressProductPrototype",
        "ProductPrototype",
    ]:
        yield extract_type(factorio_location, type_name)


def extract_type(factorio_location: str, type_name: str) -> FactorioSchema.TypeDefinition:
    soup = read_file(factorio_location, "types", type_name)

    kind_soup = tag(tag(soup.find("h2")).find("span"))
    kind_link_soup = kind_soup.find("a")
    if kind_link_soup is None:
        match kind_soup.text.strip(" :\xa0"):
            case "struct":

                def extract_properties() -> Iterable[FactorioSchema.Property]:
                    for h3_soup in (tag(el) for el in tag(soup.find("div", id="attributes-body-main")).find_all("h3")):
                        property_name = tag(h3_soup.contents[0]).contents[0].text.strip()
                        type_soup = tag(tag(tag(h3_soup.contents[0]).contents[1]).contents[1])

                        if type_soup.name == "a":
                            property_type = FactorioSchema.simple_types_mapping.get(type_soup.text.strip())
                            if property_type is None:
                                property_type = {"$ref": f"#/definitions/{type_soup.text}"}
                        elif type_soup.name == "code":
                            property_type = {"type": "string", "const": type_soup.text.strip().strip('"')}
                        else:
                            property_type = None

                        optional = h3_soup.contents[1].text.strip() == "optional"

                        if property_type is None:
                            debug(property_name, type_soup)
                        else:
                            yield FactorioSchema.Property(name=property_name, type=property_type, required=not optional)

                return FactorioSchema.StructTypeDefinition(name=type_name, properties=list(extract_properties()))
            case "union":

                def extract_union_types() -> Iterable[JsonValue]:
                    for span_soup in (tag(el) for el in soup.find_all("span", class_="docs-attribute-name")):
                        yield {"$ref": f"#/definitions/{tag(span_soup.contents[0]).text}"}

                return FactorioSchema.UnionTypeDefinition(name=type_name, types=list(extract_union_types()))
            case _:
                assert False, (type_name, soup.find("h2"))
    else:
        return FactorioSchema.UnionTypeDefinition(
            name=type_name, types=[FactorioSchema.simple_types_mapping[kind_link_soup.text]]
        )


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


# def extract_all_type_names():
#     types = set()
#     for a in read_file("types").find_all('a'):
#         link = a.get("href")
#         if link is not None and link.startswith("types/"):
#             type = link.split("#")[0].split("/")[-1]
#             assert type.endswith(".html")
#             types.add(type[:-5])
#     assert "IngredientPrototype" in types
#     assert "ItemIngredientPrototype" in types
#     return {"IngredientPrototype", "ItemIngredientPrototype"}


def read_file(factorio_location: str, *stem: str) -> BeautifulSoup:
    with open(os.path.join(factorio_location, "doc-html", *stem[:-1], stem[-1] + ".html")) as f:
        return BeautifulSoup(f.read(), "html.parser")


if __name__ == "__main__":
    main(sys.argv[1])
