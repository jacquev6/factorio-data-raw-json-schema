#!/usr/bin/env python3

# import os

# from bs4 import BeautifulSoup

from .json_schema import (
    CoreAndValidationSpecificationsMetaSchema as JsonSchema,
    SimpleTypes as JsonTypes,
)


# factorio_location = os.environ["FACTORIO_LOCATION"]
# prototypes_location = "src/FactorioDataRaw.ts"


def main():
    schema = JsonSchema(
        field_schema="https://json-schema.org/draft/2019-09/schema",
        title="Factorio Data.raw",
        type=JsonTypes.object,
        properties={
            "ammo": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "armor": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "assembling-machine": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/CraftingMachinePrototype"
                ),
            ),
            "blueprint": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "blueprint-book": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "capsule": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "character": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/CharacterPrototype"
                ),
            ),
            "copy-paste-tool": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "deconstruction-item": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "fluid": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "furnace": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/CraftingMachinePrototype"
                ),
            ),
            "gun": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "item": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "item-with-entity-data": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "module": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "rail-planner": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "recipe": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/RecipePrototype"
                ),
            ),
            "repair-tool": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "rocket-silo": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/CraftingMachinePrototype"
                ),
            ),
            "selection-tool": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "space-platform-starter-pack": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "spidertron-remote": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "tool": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
            "upgrade-item": JsonSchema(
                type=JsonTypes.object,
                additionalProperties=JsonSchema(
                    field_ref="#/definitions/ItemPrototype"
                ),
            ),
        },
        definitions={
            # Types
            "ItemIngredientPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/types/ItemIngredientPrototype.html",
                type=JsonTypes.object,
                properties={
                    "type": JsonSchema(type=JsonTypes.string, const="item"),
                    "name": JsonSchema(type=JsonTypes.string),
                },
                required=["type", "name"],
            ),
            "FluidIngredientPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/types/FluidIngredientPrototype.html",
                type=JsonTypes.object,
                properties={
                    "type": JsonSchema(type=JsonTypes.string, const="fluid"),
                    "name": JsonSchema(type=JsonTypes.string),
                },
                required=["type", "name"],
            ),
            "IngredientPrototype": JsonSchema(
                anyOf=[
                    JsonSchema(field_ref="#/definitions/ItemIngredientPrototype"),
                    JsonSchema(field_ref="#/definitions/FluidIngredientPrototype"),
                ],
            ),
            "ItemProductPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/types/ItemProductPrototype.html",
                type=JsonTypes.object,
                properties={
                    "type": JsonSchema(type=JsonTypes.string, const="item"),
                    "name": JsonSchema(type=JsonTypes.string),
                },
                required=["type", "name"],
            ),
            "FluidProductPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/types/FluidProductPrototype.html",
                type=JsonTypes.object,
                properties={
                    "type": JsonSchema(type=JsonTypes.string, const="fluid"),
                    "name": JsonSchema(type=JsonTypes.string),
                },
                required=["type", "name"],
            ),
            "ProductPrototype": JsonSchema(
                anyOf=[
                    JsonSchema(field_ref="#/definitions/ItemProductPrototype"),
                    JsonSchema(field_ref="#/definitions/FluidProductPrototype"),
                ],
            ),
            # Prototypes
            "PrototypeBase": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/PrototypeBase.html",
                type=JsonTypes.object,
                properties={
                    "type": JsonSchema(type=JsonTypes.string),
                    "name": JsonSchema(type=JsonTypes.string),
                },
                required=["type", "name"],
            ),
            "Prototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/Prototype.html",
                allOf=[
                    JsonSchema(field_ref="#/definitions/PrototypeBase"),
                ],
            ),
            "ItemPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/ItemPrototype.html",
                allOf=[
                    JsonSchema(field_ref="#/definitions/Prototype"),
                ],
            ),
            "RecipePrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/RecipePrototype.html",
                allOf=[
                    JsonSchema(field_ref="#/definitions/Prototype"),
                    JsonSchema(
                        type=JsonTypes.object,
                        properties={
                            "ingredients": JsonSchema(
                                oneOf=[
                                    JsonSchema(
                                        type=JsonTypes.array,
                                        items=JsonSchema(
                                            field_ref="#/definitions/IngredientPrototype"
                                        ),
                                    ),
                                    JsonSchema(
                                        type=JsonTypes.object,
                                        additionalProperties=False,
                                    ),
                                ]
                            ),
                            "results": JsonSchema(
                                oneOf=[
                                    JsonSchema(
                                        type=JsonTypes.array,
                                        items=JsonSchema(
                                            field_ref="#/definitions/ProductPrototype"
                                        ),
                                    ),
                                    JsonSchema(
                                        type=JsonTypes.object,
                                        additionalProperties=False,
                                    ),
                                ]
                            ),
                            "category": JsonSchema(type=JsonTypes.string),
                        },
                    ),
                ],
            ),
            "CraftingMachinePrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/CraftingMachinePrototype.html",
                allOf=[
                    JsonSchema(field_ref="#/definitions/Prototype"),
                    JsonSchema(
                        type=JsonTypes.object,
                        properties={
                            "crafting_categories": JsonSchema(
                                type=JsonTypes.array,
                                items=JsonSchema(type=JsonTypes.string),
                            )
                        },
                    ),
                ],
            ),
            "CharacterPrototype": JsonSchema(
                description="https://lua-api.factorio.com/stable/prototypes/CharacterPrototype.html",
                allOf=[
                    JsonSchema(field_ref="#/definitions/Prototype"),
                    JsonSchema(
                        type=JsonTypes.object,
                        properties={
                            "crafting_categories": JsonSchema(
                                type=JsonTypes.array,
                                items=JsonSchema(type=JsonTypes.string),
                            )
                        },
                    ),
                ],
            ),
        },
    )
    # prototypes = {name: extract_prototype_definition(name) for name in extract_all_prototype_names()}
    # type_names = extract_all_type_names()
    # print(f"Found {len(prototypes)} prototypes and {len(type_names)} types")
    print(schema.model_dump_json(exclude_unset=True, by_alias=True, indent=2))


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
