from __future__ import annotations


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def json_value(value: JsonValue) -> JsonValue:
    """
    Statically assert that a value is a JsonValue and erase its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


class Schema:
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
        self, *, types: list[TypeDefinition], prototypes: list[tuple[str | None, StructTypeDefinition]]
    ) -> None:
        self.types = types
        self.prototypes = prototypes

    def to_json_value(self) -> JsonValue:
        properties = {
            key: json_value({"type": "object", "additionalProperties": {"$ref": f"#/definitions/{prototype.name}"}})
            for key, prototype in self.prototypes
            if key is not None
        }

        type_definitions = {
            d.name: json_value(
                {"description": json_value(f"https://lua-api.factorio.com/stable/types/{d.name}.html")} | d.definition
            )
            for d in self.types
        }

        # @todo Add "additionalProperties": false to all definitions

        prototypes_by_name = {prototype.name: prototype for _, prototype in self.prototypes}

        def make_prototype_definition(prototype_name: str) -> dict[str, JsonValue]:
            properties: dict[str, JsonValue] = {}
            required: dict[str, bool] = {}

            def rec(prototype_name: str) -> None:
                prototype = prototypes_by_name[prototype_name]
                if prototype.base is not None:
                    rec(prototype.base)
                properties.update({p.name: p.type for p in prototype.properties})
                required.update({p.name: p.required for p in prototype.properties})

            rec(prototype_name)
            # @todo Constrain 'type' to equal the leaf prototype key

            definition = {
                "description": json_value(f"https://lua-api.factorio.com/stable/types/{prototype_name}.html"),
                "properties": properties,
            }
            if any(required.values()):
                definition["required"] = [json_value(v) for v in sorted(k for k, v in required.items() if v)]
            return definition

        prototype_definitions: dict[str, JsonValue] = {}
        for key, prototype in self.prototypes:
            if key is not None:
                prototype_definitions[prototype.name] = make_prototype_definition(prototype.name)

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": properties,
            "definitions": type_definitions | prototype_definitions,
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
            # self.type = {}
            self.required = required

    class StructTypeDefinition(TypeDefinition):
        def __init__(self, name: str, *, base: str | None, properties: list[Schema.Property]) -> None:
            super().__init__(name=name, definition=self.__make_definition(base, properties))
            self.base = base
            self.properties = properties

        @staticmethod
        def __make_definition(base: str | None, properties: list[Schema.Property]) -> dict[str, JsonValue]:
            required = [json_value(p.name) for p in properties if p.required]
            self_definition = {"type": "object", "properties": json_value({p.name: p.type for p in properties})} | (
                {"required": json_value(required)} if required else {}
            )
            if base is None:
                if len(properties) > 0:
                    return self_definition
                else:
                    return {"type": "object"}
            else:
                if len(properties) == 0:
                    return {"allOf": [{"$ref": f"#/definitions/{base}"}]}  # @todo Consider removing the "allOf"
                else:
                    return {"allOf": [{"$ref": f"#/definitions/{base}"}, self_definition]}

    @staticmethod
    def UnionTypeDefinition(*, name: str, types: list[JsonValue]) -> TypeDefinition:
        return Schema.TypeDefinition(name=name, definition={"anyOf": types})
