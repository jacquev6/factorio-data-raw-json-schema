#!/usr/bin/env python3

import json
# import os

# from bs4 import BeautifulSoup


# factorio_location = os.environ["FACTORIO_LOCATION"]
# prototypes_location = "src/FactorioDataRaw.ts"


def main():
    schema = {
        "$schema": "https://json-schema.org/draft-07/schema",
        "title": "Factorio Data.raw",
        "type": "object",
        "properties": {
            "ammo": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "armor": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "assembling-machine": {"type": "object", "additionalProperties": {"$ref": "#/$defs/CraftingMachinePrototype"}},
            "blueprint": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "blueprint-book": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "capsule": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "character": {"type": "object", "additionalProperties": {"$ref": "#/$defs/CharacterPrototype"}},
            "copy-paste-tool": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "deconstruction-item": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "fluid": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "furnace": {"type": "object", "additionalProperties": {"$ref": "#/$defs/CraftingMachinePrototype"}},
            "gun": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "item": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "item-with-entity-data": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "module": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "rail-planner": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "recipe": {"type": "object", "additionalProperties": {"$ref": "#/$defs/RecipePrototype"}},
            "repair-tool": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "rocket-silo": {"type": "object", "additionalProperties": {"$ref": "#/$defs/CraftingMachinePrototype"}},
            "selection-tool": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "space-platform-starter-pack": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "spidertron-remote": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "tool": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
            "upgrade-item": {"type": "object", "additionalProperties": {"$ref": "#/$defs/ItemPrototype"}},
        },
        "additionalProperties": False,
        "required": [
            "ammo",
            "armor",
            "assembling-machine",
            "blueprint",
            "blueprint-book",
            "capsule",
            "character",
            "copy-paste-tool",
            "deconstruction-item",
            "fluid",
            "furnace",
            "gun",
            "item",
            "item-with-entity-data",
            "module",
            "rail-planner",
            "recipe",
            "repair-tool",
            "rocket-silo",
            "selection-tool",
            "space-platform-starter-pack",
            "spidertron-remote",
            "tool",
            "upgrade-item",
        ],
        "$defs": {
            # Types
            "ItemIngredientPrototype": {
                "description": "https://lua-api.factorio.com/stable/types/ItemIngredientPrototype.html",
                "type": "object",
                "properties": {
                    "type": {"type": "string", "const": "item"},
                    "name": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["type", "name"],
            },
            "FluidIngredientPrototype": {
                "description": "https://lua-api.factorio.com/stable/types/FluidIngredientPrototype.html",
                "type": "object",
                "properties": {
                    "type": {"type": "string", "const": "fluid"},
                    "name": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["type", "name"],
            },
            "IngredientPrototype": {
                "anyOf": [
                    {"$ref": "#/$defs/ItemIngredientPrototype"},
                    {"$ref": "#/$defs/FluidIngredientPrototype"},
                ],
            },
            "ItemProductPrototype": {
                "description": "https://lua-api.factorio.com/stable/types/ItemProductPrototype.html",
                "type": "object",
                "properties": {
                    "type": {"type": "string", "const": "item"},
                    "name": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["type", "name"],
            },
            "FluidProductPrototype": {
                "description": "https://lua-api.factorio.com/stable/types/FluidProductPrototype.html",
                "type": "object",
                "properties": {
                    "type": {"type": "string", "const": "fluid"},
                    "name": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["type", "name"],
            },
            "ProductPrototype": {
                "anyOf": [
                    {"$ref": "#/$defs/ItemProductPrototype"},
                    {"$ref": "#/$defs/FluidProductPrototype"},
                ],
            },
            # Prototypes
            "PrototypeBase": {
                "description": "https://lua-api.factorio.com/stable/prototypes/PrototypeBase.html",
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "name": {"type": "string"},
                },
                "additionalProperties": False,
                "required": ["type", "name"],
            },
            "Prototype": {
                "description": "https://lua-api.factorio.com/stable/prototypes/Prototype.html",
                "allOf": [
                    {"$ref": "#/$defs/PrototypeBase"},
                ],
            },
            "ItemPrototype": {
                "description": "https://lua-api.factorio.com/stable/prototypes/ItemPrototype.html",
                "allOf": [
                    {"$ref": "#/$defs/Prototype"},
                ],
            },
            "RecipePrototype": {
                "description": "https://lua-api.factorio.com/stable/prototypes/RecipePrototype.html",
                "allOf": [
                    {"$ref": "#/$defs/Prototype"},
                    {
                        "type": "object",
                        "properties": {
                            "ingredients": {
                                "type": "array",
                                "items": {"$ref": "#/$defs/IngredientPrototype"},
                            },
                            "results": {
                                "type": "array",
                                "items": {"$ref": "#/$defs/ProductPrototype"},
                            },
                            "category": "string",
                        },
                        "additionalProperties": False,
                    },
                ],
            },
            "CraftingMachinePrototype": {
                "description": "https://lua-api.factorio.com/stable/prototypes/CraftingMachinePrototype.html",
                "allOf": [
                    {"$ref": "#/$defs/Prototype"},
                    {
                        "type": "object",
                        "properties": {
                            "crafting_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "additionalProperties": False,
                    },
                ],
            },
            "CharacterPrototype": {
                "description": "https://lua-api.factorio.com/stable/prototypes/CharacterPrototype.html",
                "allOf": [
                    {"$ref": "#/$defs/Prototype"},
                    {
                        "type": "object",
                        "properties": {
                            "crafting_categories": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "additionalProperties": False,
                    },
                ],
            },
        },
    }
    # prototypes = {name: extract_prototype_definition(name) for name in extract_all_prototype_names()}
    # type_names = extract_all_type_names()
    # print(f"Found {len(prototypes)} prototypes and {len(type_names)} types")
    print(json.dumps(schema, indent=2))


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
