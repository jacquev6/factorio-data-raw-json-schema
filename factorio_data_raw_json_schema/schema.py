from __future__ import annotations

from typing import Literal
import dataclasses

from . import patching


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict = dict[str, JsonValue]


def json_value(value: JsonValue) -> JsonValue:
    """
    Statically assert that a value is a JsonValue and erase its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


class Schema:
    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class BuiltinTypeExpression:
        kind: Literal["builtin"] = "builtin"
        json_definition: JsonDict

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return self.json_definition

    builtin_types: dict[str, BuiltinTypeExpression] = {
        "string": BuiltinTypeExpression(json_definition={"type": "string"}),
        "float": BuiltinTypeExpression(json_definition={"type": "number"}),
        "double": BuiltinTypeExpression(json_definition={"type": "number"}),
        "bool": BuiltinTypeExpression(json_definition={"type": "boolean"}),
        "uint8": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 255}),
        "uint16": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 65535}),
        "uint32": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 4294967295}),
        "uint64": BuiltinTypeExpression(
            json_definition={"type": "integer", "minimum": 0, "maximum": 18446744073709551615}
        ),
        "int8": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": -128, "maximum": 127}),
        "int16": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": -32768, "maximum": 32767}),
        "int32": BuiltinTypeExpression(
            json_definition={"type": "integer", "minimum": -2147483648, "maximum": 2147483647}
        ),
        "int64": BuiltinTypeExpression(
            json_definition={"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807}
        ),
    }

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class LiteralBoolTypeExpression:
        kind: Literal["literal_bool"] = "literal_bool"
        value: bool

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {"type": "boolean", "const": self.value}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class LiteralStringTypeExpression:
        kind: Literal["literal_string"] = "literal_string"
        value: str

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {"type": "string", "const": self.value}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class LiteralIntegerTypeExpression:
        kind: Literal["literal_integer"] = "literal_integer"
        value: int

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {"type": "integer", "const": self.value}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class RefTypeExpression:
        kind: Literal["ref"] = "ref"
        ref: str

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {"$ref": f"#/definitions/{self.ref}"}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class UnionTypeExpression:
        kind: Literal["union"] = "union"
        members: list[Schema.TypeExpression]

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {"anyOf": [member.make_json_definition(referable_types) for member in self.members]}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class ArrayTypeExpression:
        kind: Literal["array"] = "array"
        content: Schema.TypeExpression

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return patching.array_to_json_definition(self, referable_types)

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class DictionaryTypeExpression:
        kind: Literal["dictionary"] = "dictionary"
        keys: Schema.TypeExpression
        values: Schema.TypeExpression

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {
                "type": "object",
                "additionalProperties": self.values.make_json_definition(referable_types),
                "propertyNames": self.keys.make_json_definition(referable_types),
            }

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class Property:
        names: list[str]
        type: Schema.TypeExpression
        required: bool = False

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class StructTypeExpression:
        kind: Literal["struct"] = "struct"
        base: str | None
        properties: list[Schema.Property]

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            required = [json_value(name) for p in self.properties if p.required for name in p.names]
            self_definition = {
                "type": "object",
                "properties": json_value(
                    {name: p.type.make_json_definition(referable_types) for p in self.properties for name in p.names}
                ),
            } | ({"required": json_value(required)} if required else {})
            if self.base is None:
                if len(self.properties) > 0:
                    return self_definition
                else:
                    return {"type": "object"}
            else:
                if len(self.properties) == 0:
                    return {"allOf": [{"$ref": f"#/definitions/{self.base}"}]}  # @todo Consider removing the "allOf"
                else:
                    return {"allOf": [{"$ref": f"#/definitions/{self.base}"}, self_definition]}

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class StructTypeExpression2:
        kind: Literal["struct"] = "struct"
        base: str | None
        properties: list[Schema.Property]
        overridden_properties: list[Schema.Property]
        custom_properties: Schema.TypeExpression | None

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            properties: JsonDict = {}
            required: dict[str, bool] = {}

            def rec(prototype: Schema.StructTypeExpression2) -> None:
                if prototype.base is not None:
                    base = referable_types[prototype.base]
                    assert isinstance(base, Schema.StructTypeExpression2)
                    rec(base)
                all_properties = prototype.properties + prototype.overridden_properties
                properties.update(
                    {name: p.type.make_json_definition(referable_types) for p in all_properties for name in p.names}
                )
                # @todo When there are multiple property names, and the property is required, enforce that at least one property name is present
                required.update({name: p.required for p in all_properties for name in p.names if len(p.names) == 1})

            rec(self)

            definition: JsonDict = {
                # @todo Add "type": "object" (unless added somewhere else)
                "properties": properties
            }

            if self.custom_properties is None:
                definition["additionalProperties"] = False
            else:
                definition["additionalProperties"] = self.custom_properties.make_json_definition(referable_types)

            if any(required.values()):
                definition["required"] = [json_value(v) for v in sorted(k for k, v in required.items() if v)]

            return definition

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class TupleTypeExpression:
        kind: Literal["tuple"] = "tuple"
        members: list[Schema.TypeExpression]

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return {
                "type": "array",
                "items": [member.make_json_definition(referable_types) for member in self.members],
                "minItems": len(self.members),
                "maxItems": len(self.members),
            }

    TypeExpression = (
        BuiltinTypeExpression
        | LiteralBoolTypeExpression
        | LiteralStringTypeExpression
        | LiteralIntegerTypeExpression
        | RefTypeExpression
        | UnionTypeExpression
        | ArrayTypeExpression
        | DictionaryTypeExpression
        | StructTypeExpression
        | StructTypeExpression2
        | TupleTypeExpression
    )

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class Type:
        name: str
        definition: Schema.TypeExpression

    @dataclasses.dataclass(frozen=True, kw_only=True, repr=False, eq=False)
    class Prototype:
        name: str
        key: str | None
        base: str | None

        properties: list[Schema.Property]
        overridden_properties: list[Schema.Property]
        custom_properties: Schema.TypeExpression | None

        def make_definition(self) -> Schema.TypeExpression:
            type_property = (
                None
                if self.key is None
                else Schema.Property(
                    names=["type"], type=Schema.LiteralStringTypeExpression(value=self.key), required=True
                )
            )

            return Schema.StructTypeExpression2(
                base=self.base,
                properties=self.properties + list(filter(None, [type_property])),
                overridden_properties=self.overridden_properties,
                custom_properties=self.custom_properties,
            )

        def make_json_definition(self, referable_types: dict[str, Schema.TypeExpression]) -> JsonDict:
            return self.make_definition().make_json_definition(referable_types)

    def __init__(self, *, types: list[Type], prototypes: list[Prototype]) -> None:
        self.types = types
        self.prototypes = prototypes

    def to_json_value(self) -> JsonValue:
        properties = {
            prototype.key: json_value(
                {"type": "object", "additionalProperties": {"$ref": f"#/definitions/{prototype.name}"}}
            )
            for prototype in self.prototypes
            if prototype.key is not None
        }

        referable_types = {prototype.name: prototype.make_definition() for prototype in self.prototypes} | {
            type.name: type.definition for type in self.types
        }

        type_definitions: JsonDict = {
            type.name: json_value(
                {"description": json_value(f"https://lua-api.factorio.com/stable/types/{type.name}.html")}
                | type.definition.make_json_definition(referable_types)
            )
            for type in self.types
        }

        # @todo Add "additionalProperties": false to all definitions

        prototype_definitions: JsonDict = {
            prototype.name: (
                {
                    # @todo Fix URL (s/types/prototypes/)
                    "description": json_value(f"https://lua-api.factorio.com/stable/types/{prototype.name}.html")
                }
                | prototype.make_json_definition(referable_types)
            )
            for prototype in self.prototypes
            if prototype.key is not None
        }

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
            "definitions": type_definitions | prototype_definitions,
        }
