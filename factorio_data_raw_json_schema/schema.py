from __future__ import annotations

import itertools
import sys
from typing import Iterable
import typing

import networkx as nx

from . import documentation
from . import patching


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict = dict[str, JsonValue]


def json_value(value: JsonValue) -> JsonValue:
    """
    Statically assert that a value is a JsonValue and erase its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


def make_json_schema(
    doc: documentation.Doc,
    *,
    limit_to_prototype_names: Iterable[str] | None,
    include_descendants: bool,
    forbid_type_names: Iterable[str],
) -> JsonDict:
    return JsonSchemaMaker(
        doc=doc,
        limit_to_prototype_names=limit_to_prototype_names,
        include_descendants=include_descendants,
        forbid_type_names=forbid_type_names,
    ).make_json()


class Forbidden(Exception):
    pass


forbidden = Forbidden()


JsonDictOrForbidden = JsonDict | Forbidden


class JsonSchemaMaker:
    def __init__(
        self,
        *,
        doc: documentation.Doc,
        limit_to_prototype_names: Iterable[str] | None,
        include_descendants: bool,
        forbid_type_names: Iterable[str],
    ) -> None:
        self.doc = doc

        self.types_by_name = {type.name: type for type in doc.types}
        self.prototypes_by_name = {prototype.name: prototype for prototype in doc.prototypes}

        self.init_forbidden_type_names(forbid_type_names)

        self.prototypes_to_include = set(self.init_prototypes_to_include(limit_to_prototype_names, include_descendants))

        self.all_references_needed_by = nx.transitive_closure(
            nx.DiGraph(
                {
                    name: self.gather_references_needed_by(definition)
                    for (name, definition) in itertools.chain(
                        (
                            (type.name, type.definition)
                            for type in self.doc.types
                            if type.name not in self.forbidden_type_names
                        ),
                        ((prototype.name, prototype.make_definition()) for prototype in self.doc.prototypes),
                    )
                }
            )
        )

    def init_forbidden_type_names(self, forbid_type_names: Iterable[str]) -> None:
        self.forbidden_type_names = set(forbid_type_names)

        # @todo Use a proper graph exploration algorithm!
        while True:
            some_type_is_newly_forbidden = False
            for type in self.doc.types:
                if type.name not in self.forbidden_type_names:
                    if self.make_json_definition(type.definition) is forbidden:
                        self.forbidden_type_names.add(type.name)
                        some_type_is_newly_forbidden = True

            if not some_type_is_newly_forbidden:
                break

    def init_prototypes_to_include(
        self, limit_to_prototype_names: Iterable[str] | None, include_descendants: bool
    ) -> Iterable[str]:
        if limit_to_prototype_names is None:
            for prototype in self.doc.prototypes:
                yield prototype.name
        else:
            seed_prototypes = {name + "Prototype" for name in limit_to_prototype_names}
            yield from seed_prototypes

            if include_descendants:
                parent_children_graph: nx.DiGraph[str] = nx.DiGraph()
                for prototype in self.doc.prototypes:
                    if prototype.base is not None:
                        parent_children_graph.add_edge(prototype.base, prototype.name)

                parent_descendants_graph = nx.transitive_closure(parent_children_graph)
                for name in seed_prototypes:
                    yield from parent_descendants_graph[name]

    def gather_references_needed_by(self, t: documentation.TypeExpression) -> Iterable[str]:
        return set(t.accept(NeededReferencesGatherer(self)))

    def get_referable_type(self, name: str) -> documentation.TypeExpression:
        if name in self.forbidden_type_names:
            assert name in self.types_by_name
            raise Forbidden

        type = self.types_by_name.get(name)
        if type is None:
            return self.prototypes_by_name[name].make_definition()
        else:
            return type.definition

    def make_json_definition(self, t: documentation.TypeExpression) -> JsonDictOrForbidden:
        return t.accept(JsonDefinitionMaker(self))

    def make_json(self) -> JsonDict:
        properties = {
            prototype.key: json_value(
                typing.cast(
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
            )
            for prototype in self.doc.prototypes
            if prototype.key is not None and prototype.name in self.prototypes_to_include
        }

        references_needed = self.prototypes_to_include | set(
            itertools.chain.from_iterable(self.all_references_needed_by[name] for name in self.prototypes_to_include)
        )

        definitions = {
            type.name: json_value(
                {"description": json_value(f"https://lua-api.factorio.com/stable/types/{type.name}.html")}
                | typing.cast(JsonDict, self.make_json_definition(type.definition))
            )
            for type in self.doc.types
            if type.name not in self.forbidden_type_names and type.name in references_needed
        } | {
            prototype.name: json_value(
                {"description": json_value(f"https://lua-api.factorio.com/stable/prototypes/{prototype.name}.html")}
                | typing.cast(JsonDict, self.make_json_definition(prototype.make_definition()))
            )
            for prototype in self.doc.prototypes
            if prototype.key is not None and prototype.name in references_needed
        }

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": properties,
            "definitions": definitions,
        }


E = typing.TypeVar("E")


class BaseTypeExpressionVisitor[E](documentation.TypeExpressionVisitor[E]):
    def __init__(self, maker: JsonSchemaMaker) -> None:
        self.maker = maker

    def get_referable_type(self, name: str) -> documentation.TypeExpression:
        return self.maker.get_referable_type(name)

    def maybe_visit_base(self, base: str | None) -> E | None:
        if base is not None:
            base_type = self.get_referable_type(base)
            if isinstance(base_type, documentation.StructTypeExpression):
                return base_type.accept(self)
            elif isinstance(base_type, documentation.UnionTypeExpression):
                for member in base_type.members:
                    if isinstance(member, documentation.StructTypeExpression):
                        return member.accept(self)
                else:
                    print(
                        f"{base} has union type and is used as a base, but it has no member of struct type",
                        file=sys.stderr,
                    )
            else:
                print(f"{base} is used as a base but has unexpected type: {base_type.__class__}", file=sys.stderr)
        return None


class JsonDefinitionMaker(BaseTypeExpressionVisitor[JsonDictOrForbidden]):
    def visit_builtin(self, name: str) -> JsonDict:
        return {
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
        }[name]

    def visit_literal_bool(self, value: bool) -> JsonDict:
        return {"type": "boolean", "const": value}

    def visit_literal_string(self, value: str) -> JsonDict:
        return {"type": "string", "const": value}

    def visit_literal_integer(self, value: int) -> JsonDict:
        return {"type": "integer", "const": value}

    def visit_ref(self, ref: str) -> JsonDictOrForbidden:
        try:
            self.get_referable_type(ref)  # Ensure the reference is not forbidden
            return {"$ref": f"#/definitions/{ref}"}
        except Forbidden:
            return forbidden

    def visit_union(self, members: list[JsonDictOrForbidden]) -> JsonDictOrForbidden:
        anyOf: list[JsonValue] = []
        for member in members:
            if isinstance(member, Forbidden):
                return forbidden
            anyOf.append(json_value(member))
        return {"anyOf": anyOf}

    def visit_array(self, content: JsonDictOrForbidden) -> JsonDictOrForbidden:
        if isinstance(content, Forbidden):
            return forbidden
        return patching.array_to_json_definition(content)

    def visit_dictionary(self, keys: JsonDictOrForbidden, values: JsonDictOrForbidden) -> JsonDictOrForbidden:
        if isinstance(keys, Forbidden) or isinstance(values, Forbidden):
            return forbidden
        return {"type": "object", "additionalProperties": values, "propertyNames": keys}

    def visit_struct(
        self,
        base: str | None,
        properties: list[documentation.VisitedProperty[JsonDictOrForbidden]],
        overridden_properties: list[documentation.VisitedProperty[JsonDictOrForbidden]],
        custom_properties: JsonDictOrForbidden | None,
    ) -> JsonDictOrForbidden:
        try:
            base_definition = self.maybe_visit_base(base) or {}
        except Forbidden:
            return forbidden

        if isinstance(base_definition, Forbidden):
            return forbidden

        json_properties = typing.cast(JsonDict, base_definition.get("properties", {}))
        required_by_name = {k: True for k in typing.cast(list[str], base_definition.get("required", []))}
        json_custom_properties = typing.cast(JsonDict | None, base_definition.get("additionalProperties", None))

        for property in itertools.chain(properties, overridden_properties):
            for name in property.names:
                if isinstance(property.type, Forbidden):
                    json_properties.pop(name, None)
                else:
                    json_properties[name] = property.type
            # @todo When there are multiple property names, and the property is required, enforce that at least one property name is present
            if len(property.names) == 1:
                required_by_name[property.names[0]] = property.required
            else:
                for name in property.names:
                    required_by_name[name] = False

        if custom_properties is not None:
            assert json_custom_properties is None
            assert not isinstance(custom_properties, Forbidden)
            json_custom_properties = custom_properties

        definition: JsonDict = {"type": "object"}

        if len(json_properties) > 0:
            definition["properties"] = json_properties

        if custom_properties is None:
            if len(json_properties) == 0:
                return forbidden
        else:
            definition["additionalProperties"] = json_custom_properties

        json_required = [json_value(name) for name in json_properties.keys() if required_by_name.get(name, False)]
        if len(json_required) > 0:
            definition["required"] = json_value(json_required)

        return definition

    def visit_tuple(self, members: list[JsonDictOrForbidden]) -> JsonDictOrForbidden:
        items = []
        for member in members:
            if isinstance(member, Forbidden):
                return forbidden
            items.append(json_value(member))
        return {"type": "array", "items": items, "minItems": len(members), "maxItems": len(members)}


class NeededReferencesGatherer(BaseTypeExpressionVisitor[Iterable[str]]):
    def visit_builtin(self, name: str) -> Iterable[str]:
        return []

    def visit_literal_bool(self, value: bool) -> Iterable[str]:
        return []

    def visit_literal_string(self, value: str) -> Iterable[str]:
        return []

    def visit_literal_integer(self, value: int) -> Iterable[str]:
        return []

    def visit_ref(self, ref: str) -> Iterable[str]:
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
        base: str | None,
        properties: list[documentation.VisitedProperty[Iterable[str]]],
        overridden_properties: list[documentation.VisitedProperty[Iterable[str]]],
        custom_properties: Iterable[str] | None,
    ) -> Iterable[str]:
        references_needed_by_base = self.maybe_visit_base(base)
        if references_needed_by_base is not None:
            yield from references_needed_by_base

        for property in itertools.chain(properties, overridden_properties):
            yield from property.type
        if custom_properties is not None:
            yield from custom_properties

    def visit_tuple(self, members: list[Iterable[str]]) -> Iterable[str]:
        for member in members:
            yield from member
