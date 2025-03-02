from __future__ import annotations

from typing import Iterable
import enum
import itertools
import sys
import typing

import networkx as nx

from . import documentation
from . import patching


JsonValue = None | bool | int | float | str | typing.Collection["JsonValue"] | typing.Mapping[str, "JsonValue"]
JsonDict = dict[str, JsonValue]


def make_json_schema(
    doc: documentation.Doc,
    *,
    strict_numbers: bool,
    limit_to_prototype_names: Iterable[str] | None,
    include_descendants: bool,
    forbid_type_names: Iterable[str],
) -> JsonValue:
    return JsonSchemaMaker(
        doc=doc,
        strict_numbers=strict_numbers,
        limit_to_prototype_names=limit_to_prototype_names,
        include_descendants=include_descendants,
        forbid_type_names=forbid_type_names,
    ).json_schema


class Forbidden(enum.Enum):
    # https://github.com/python/typing/issues/236#issuecomment-227180301
    forbidden = 0


forbidden: typing.Final = Forbidden.forbidden


JsonDictOrForbidden = JsonDict | Forbidden


class JsonSchemaMaker:
    def __init__(
        self,
        *,
        doc: documentation.Doc,
        strict_numbers: bool,
        limit_to_prototype_names: Iterable[str] | None,
        include_descendants: bool,
        forbid_type_names: Iterable[str],
    ) -> None:
        self.doc = doc
        self.strict_numbers = strict_numbers

        self.all_type_definitions_by_name = {type.name: type.definition for type in doc.types} | {
            prototype.name: prototype.make_definition() for prototype in doc.prototypes
        }

        self.forbidden_type_names = set(forbid_type_names)
        self.extend_forbidden_type_names()

        prototype_names_to_include = set(
            self.make_prototype_names_to_include(limit_to_prototype_names, include_descendants)
        )
        self.prototypes_to_include = [
            prototype for prototype in self.doc.prototypes if prototype.name in prototype_names_to_include
        ]

        type_names_to_include = set(self.make_type_names_to_include())
        self.types_to_include = [type for type in self.doc.types if type.name in type_names_to_include]

        self.json_schema = self.make_json_schema()

    def extend_forbidden_type_names(self) -> None:
        # A type is forbidden if either:
        # - it is explicitly forbidden by the user
        # - it is a union with at least one forbidden member
        # - it is an array with a forbidden content type
        # - it is a dictionary with a forbidden key type or value type
        # - it is a tuple with at least one forbidden member
        # - it is a struct with a forbidden base type
        # - it is a struct whose properties are all forbidden
        # (Those rules are implemented in the 'JsonDefinitionMaker' visitor)
        # Because of that last point, being forbidden is not captured by a graph like "if this type is forbidden then this other type is forbidden".
        # So, being forbidden is not a transitive property, and cannot be computed using 'nx.transitive_closure'.
        # (Strictly speaking, there might be a graph where the nodes are set of types, but I don't feel like this would be any simpler.)
        # So instead, we iteratively check if any new type is forbidden.
        some_type_is_newly_forbidden = True
        while some_type_is_newly_forbidden:
            some_type_is_newly_forbidden = False
            for type in self.doc.types:
                if type.name not in self.forbidden_type_names and self.is_now_forbidden(type.definition):
                    self.forbidden_type_names.add(type.name)
                    some_type_is_newly_forbidden = True

    def is_now_forbidden(self, t: documentation.TypeExpression) -> bool:
        # @todo Try one more time to decouple making the JSON schema from checking if a type is forbidden
        return (
            t.accept(
                JsonDefinitionMaker(self.forbidden_type_names, self.all_type_definitions_by_name, self.strict_numbers)
            )
            is forbidden
        )

    def make_prototype_names_to_include(
        self, limit_to_prototype_names: Iterable[str] | None, include_descendants: bool
    ) -> Iterable[str]:
        def gen() -> Iterable[documentation.Prototype]:
            if limit_to_prototype_names is None:
                for prototype in self.doc.prototypes:
                    yield prototype
            else:
                prototypes_by_name = {prototype.name: prototype for prototype in self.doc.prototypes}

                seed_prototype_names = {name + "Prototype" for name in limit_to_prototype_names}
                for prototype_name in seed_prototype_names:
                    yield prototypes_by_name[prototype_name]

                if include_descendants:
                    parent_children_graph: nx.DiGraph[str] = nx.DiGraph()
                    for prototype in self.doc.prototypes:
                        if prototype.base is not None:
                            parent_children_graph.add_edge(prototype.base, prototype.name)

                    parent_descendants_graph = nx.transitive_closure(parent_children_graph)
                    for prototype_name in seed_prototype_names:
                        for descendant_name in parent_descendants_graph[prototype_name]:
                            yield prototypes_by_name[descendant_name]

        for prototype in gen():
            if prototype.key is not None:
                yield prototype.name

    def make_type_names_to_include(self) -> Iterable[str]:
        all_types_needed_by = nx.transitive_closure(
            nx.DiGraph(
                {
                    name: self.gather_types_needed_by(definition)
                    for (name, definition) in itertools.chain(
                        (
                            (type.name, type.definition)
                            for type in self.doc.types
                            if type.name not in self.forbidden_type_names
                        ),
                        ((prototype.name, prototype.make_definition()) for prototype in self.prototypes_to_include),
                    )
                }
            )
        )

        for prototype in self.prototypes_to_include:
            yield from all_types_needed_by[prototype.name]

    def gather_types_needed_by(self, t: documentation.TypeExpression) -> Iterable[str]:
        return set(t.accept(NeededTypesGatherer(self.forbidden_type_names, self.all_type_definitions_by_name)))

    def make_json_schema(self) -> JsonDict:
        properties = {
            prototype.key: typing.cast(
                JsonDict,
                self.make_json_definition(
                    documentation.StructTypeExpression(
                        base=None,
                        properties=[],
                        overridden_properties=[],
                        custom_properties=documentation.RefTypeExpression(ref=prototype.name),
                    )
                ),
            )
            for prototype in self.prototypes_to_include
        }

        definitions = {
            type.name: {"description": f"https://lua-api.factorio.com/stable/types/{type.name}.html"}
            | typing.cast(JsonDict, self.make_json_definition(type.definition))
            for type in self.types_to_include
        } | {
            prototype.name: {"description": f"https://lua-api.factorio.com/stable/prototypes/{prototype.name}.html"}
            | typing.cast(JsonDict, self.make_json_definition(prototype.make_definition()))
            for prototype in self.prototypes_to_include
        }

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": properties,
            "definitions": definitions,
        }

    def make_json_definition(self, t: documentation.TypeExpression) -> JsonDictOrForbidden:
        return t.accept(
            JsonDefinitionMaker(self.forbidden_type_names, self.all_type_definitions_by_name, self.strict_numbers)
        )


E = typing.TypeVar("E")


class BaseTypeExpressionVisitor[E](documentation.TypeExpressionVisitor[E]):
    def __init__(
        self, forbidden_type_names: set[str], all_type_definitions_by_name: dict[str, documentation.TypeExpression]
    ) -> None:
        self.forbidden_type_names = forbidden_type_names
        self.all_type_definitions_by_name = all_type_definitions_by_name

    def get_type_definition(self, name: str) -> documentation.TypeExpression | Forbidden:
        if name in self.forbidden_type_names:
            return forbidden

        return self.all_type_definitions_by_name[name]

    def maybe_visit_base(self, base_name: str | None) -> E | Forbidden | None:
        if base_name is not None:
            base_type = self.get_type_definition(base_name)
            if base_type is forbidden:
                return forbidden
            elif isinstance(base_type, documentation.StructTypeExpression):
                return base_type.accept(self)
            elif isinstance(base_type, documentation.UnionTypeExpression):
                for member in base_type.members:
                    if isinstance(member, documentation.StructTypeExpression):
                        return member.accept(self)
                else:
                    print(
                        f"{base_name} has union type and is used as a base, but it has no member of struct type",
                        file=sys.stderr,
                    )
            else:
                print(f"{base_name} is used as a base but has unexpected type: {base_type.__class__}", file=sys.stderr)
        return None


class JsonDefinitionMaker(BaseTypeExpressionVisitor[JsonDictOrForbidden]):
    strict_builtins = {
        "string": JsonDict({"type": "string"}),
        "float": JsonDict({"type": "number"}),
        "double": JsonDict({"type": "number"}),
        "bool": JsonDict({"type": "boolean"}),
        "uint8": JsonDict({"type": "integer", "minimum": 0, "maximum": 255}),
        "uint16": JsonDict({"type": "integer", "minimum": 0, "maximum": 65535}),
        "uint32": JsonDict({"type": "integer", "minimum": 0, "maximum": 4294967295}),
        "uint64": JsonDict({"type": "integer", "minimum": 0, "maximum": 18446744073709551615}),
        "int8": JsonDict({"type": "integer", "minimum": -128, "maximum": 127}),
        "int16": JsonDict({"type": "integer", "minimum": -32768, "maximum": 32767}),
        "int32": JsonDict({"type": "integer", "minimum": -2147483648, "maximum": 2147483647}),
        "int64": JsonDict({"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807}),
    }

    lenient_builtins = {
        "string": JsonDict({"type": "string"}),
        "float": JsonDict({"type": "number"}),
        "double": JsonDict({"type": "number"}),
        "bool": JsonDict({"type": "boolean"}),
        "uint8": JsonDict({"type": "number"}),
        "uint16": JsonDict({"type": "number"}),
        "uint32": JsonDict({"type": "number"}),
        "uint64": JsonDict({"type": "number"}),
        "int8": JsonDict({"type": "number"}),
        "int16": JsonDict({"type": "number"}),
        "int32": JsonDict({"type": "number"}),
        "int64": JsonDict({"type": "number"}),
    }

    def __init__(
        self,
        forbidden_type_names: set[str],
        all_type_definitions_by_name: dict[str, documentation.TypeExpression],
        strict_numbers: bool,
    ) -> None:
        super().__init__(forbidden_type_names, all_type_definitions_by_name)
        self.builtins = self.strict_builtins if strict_numbers else self.lenient_builtins

    def visit_builtin(self, name: str) -> JsonDict:
        return self.builtins[name]

    def visit_literal_bool(self, value: bool) -> JsonDict:
        return {"type": "boolean", "const": value}

    def visit_literal_string(self, value: str) -> JsonDict:
        return {"type": "string", "const": value}

    def visit_literal_integer(self, value: int) -> JsonDict:
        return {"type": "integer", "const": value}

    def visit_ref(self, ref: str) -> JsonDictOrForbidden:
        if self.get_type_definition(ref) is forbidden:
            return forbidden
        else:
            return {"$ref": f"#/definitions/{ref}"}

    def visit_union(self, members: list[JsonDictOrForbidden]) -> JsonDictOrForbidden:
        anyOf: list[JsonValue] = []
        for member in members:
            if member is forbidden:
                return forbidden
            anyOf.append(member)
        return {"anyOf": anyOf}

    def visit_array(self, content: JsonDictOrForbidden) -> JsonDictOrForbidden:
        if content is forbidden:
            return forbidden
        return patching.array_to_json_definition(content)

    def visit_dictionary(self, keys: JsonDictOrForbidden, values: JsonDictOrForbidden) -> JsonDictOrForbidden:
        if keys is forbidden or values is forbidden:
            return forbidden
        return {"type": "object", "additionalProperties": values, "propertyNames": keys}

    def visit_struct(
        self,
        base_name: str | None,
        properties: list[documentation.VisitedProperty[JsonDictOrForbidden]],
        overridden_properties: list[documentation.VisitedProperty[JsonDictOrForbidden]],
        custom_properties: JsonDictOrForbidden | None,
    ) -> JsonDictOrForbidden:
        base_definition = self.maybe_visit_base(base_name) or {}

        if base_definition is forbidden:
            return forbidden

        json_properties = typing.cast(JsonDict, base_definition.get("properties", {}))
        required_by_name = {k: True for k in typing.cast(list[str], base_definition.get("required", []))}
        json_custom_properties = typing.cast(JsonDict | None, base_definition.get("additionalProperties", None))
        json_all_of = typing.cast(list[JsonDict], base_definition.get("allOf", []))

        for property in itertools.chain(properties, overridden_properties):
            for name in property.names:
                if property.type is forbidden:
                    json_properties.pop(name, None)
                else:
                    json_properties[name] = property.type
            if len(property.names) == 1:
                required_by_name[property.names[0]] = property.required
            else:
                for name in property.names:
                    required_by_name[name] = False
                json_all_of.append({"anyOf": [{"required": [name]} for name in property.names]})

        if custom_properties is not None:
            assert json_custom_properties is None
            assert not custom_properties is forbidden
            json_custom_properties = custom_properties

        definition: JsonDict = {"type": "object"}

        if len(json_properties) > 0:
            definition["properties"] = json_properties

        if custom_properties is None:
            if len(json_properties) == 0:
                return forbidden
        else:
            definition["additionalProperties"] = json_custom_properties

        json_required = [name for name in json_properties.keys() if required_by_name.get(name, False)]
        if len(json_required) > 0:
            definition["required"] = json_required

        if len(json_all_of) > 0:
            definition["allOf"] = json_all_of

        return definition

    def visit_tuple(self, members: list[JsonDictOrForbidden]) -> JsonDictOrForbidden:
        items = []
        for member in members:
            if member is forbidden:
                return forbidden
            items.append(member)
        return {"type": "array", "items": items, "minItems": len(members), "maxItems": len(members)}


class NeededTypesGatherer(BaseTypeExpressionVisitor[Iterable[str]]):
    def visit_builtin(self, name: str) -> Iterable[str]:
        return []

    def visit_literal_bool(self, value: bool) -> Iterable[str]:
        return []

    def visit_literal_string(self, value: str) -> Iterable[str]:
        return []

    def visit_literal_integer(self, value: int) -> Iterable[str]:
        return []

    def visit_ref(self, ref: str) -> Iterable[str]:
        if self.get_type_definition(ref) is not forbidden:
            yield ref

    def visit_union(self, members: list[Iterable[str]]) -> Iterable[str]:
        for member in members:
            yield from member

    def visit_array(self, content: Iterable[str]) -> Iterable[str]:
        return content

    def visit_dictionary(self, keys: Iterable[str], values: Iterable[str]) -> Iterable[str]:
        yield from keys
        yield from values

    def visit_struct(
        self,
        base_name: str | None,
        properties: list[documentation.VisitedProperty[Iterable[str]]],
        overridden_properties: list[documentation.VisitedProperty[Iterable[str]]],
        custom_properties: Iterable[str] | None,
    ) -> Iterable[str]:
        references_needed_by_base = self.maybe_visit_base(base_name)
        assert not references_needed_by_base is forbidden

        if references_needed_by_base is not None:
            yield from references_needed_by_base

        for property in itertools.chain(properties, overridden_properties):
            yield from property.type
        if custom_properties is not None:
            yield from custom_properties

    def visit_tuple(self, members: list[Iterable[str]]) -> Iterable[str]:
        for member in members:
            yield from member
