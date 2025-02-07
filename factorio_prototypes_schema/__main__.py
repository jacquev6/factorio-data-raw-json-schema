#!/usr/bin/env python3

from __future__ import annotations

import abc
import json
import sys

# from bs4 import BeautifulSoup


# factorio_location = os.environ["FACTORIO_LOCATION"]
# prototypes_location = "src/FactorioDataRaw.ts"

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def json_value(value: JsonValue) -> JsonValue:
    """
    Identity function that asserts that the input is a valid JSON value and erases its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


class FactorioSchema:
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

    class ObjectTypeDefinition(TypeDefinition):
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


def main() -> None:
    schema = FactorioSchema(
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
        types=[
            FactorioSchema.ObjectTypeDefinition(
                "ItemIngredientPrototype",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string", "const": "item"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.ObjectTypeDefinition(
                "FluidIngredientPrototype",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string", "const": "fluid"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.UnionTypeDefinition(
                "IngredientPrototype",
                types=[
                    {"$ref": "#/definitions/ItemIngredientPrototype"},
                    {"$ref": "#/definitions/FluidIngredientPrototype"},
                ],
            ),
            FactorioSchema.ObjectTypeDefinition(
                "ItemProductPrototype",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string", "const": "item"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.ObjectTypeDefinition(
                "FluidProductPrototype",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string", "const": "fluid"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.UnionTypeDefinition(
                "ProductPrototype",
                types=[{"$ref": "#/definitions/ItemProductPrototype"}, {"$ref": "#/definitions/FluidProductPrototype"}],
            ),
        ],
        prototypes=[
            FactorioSchema.ObjectTypeDefinition(
                "PrototypeBase",
                properties=[
                    FactorioSchema.Property(name="type", type={"type": "string"}, required=True),
                    FactorioSchema.Property(name="name", type={"type": "string"}, required=True),
                ],
            ),
            FactorioSchema.ObjectTypeDefinition("Prototype", base="PrototypeBase", properties=[]),
            FactorioSchema.ObjectTypeDefinition("ItemPrototype", base="Prototype", properties=[]),
            FactorioSchema.ObjectTypeDefinition(
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
            FactorioSchema.ObjectTypeDefinition(
                "CraftingMachinePrototype",
                base="Prototype",
                properties=[
                    FactorioSchema.Property(
                        name="crafting_categories", type={"type": "array", "items": {"type": "string"}}
                    )
                ],
            ),
            FactorioSchema.ObjectTypeDefinition(
                "CharacterPrototype",
                base="Prototype",
                properties=[
                    FactorioSchema.Property(
                        name="crafting_categories", type={"type": "array", "items": {"type": "string"}}
                    )
                ],
            ),
        ],
    )
    # prototypes = {name: extract_prototype_definition(name) for name in extract_all_prototype_names()}
    # type_names = extract_all_type_names()
    # print(f"Found {len(prototypes)} prototypes and {len(type_names)} types")
    json.dump(schema.to_json_value(), sys.stdout, indent=2)


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


# def read_file(*stem):
#     with open(os.path.join(factorio_location, "doc-html", *stem[:-1], stem[-1] + ".html")) as f:
#         return BeautifulSoup(f.read(), 'html.parser')


if __name__ == "__main__":
    main()
