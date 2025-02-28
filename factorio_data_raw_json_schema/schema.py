from __future__ import annotations

import itertools
from typing import Callable, Iterable

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
    make_reference: Callable[[bool, str], str] | None,
    limit_to_prototype_names: Iterable[str] | None,
    include_descendants: bool,
    forbid_type_names: Iterable[str],
) -> JsonDict:
    return JsonSchemaMaker(
        doc=doc,
        make_reference=make_reference,
        limit_to_prototype_names=limit_to_prototype_names,
        include_descendants=include_descendants,
        forbid_type_names=forbid_type_names,
    ).to_json()


class JsonDefinitionMaker(documentation.TypeExpressionVisitor[JsonDict]):
    def __init__(self, maker: JsonSchemaMaker) -> None:
        self.maker = maker

    def get_base_named(self, name: str) -> documentation.TypeExpression:
        return self.maker.get_referable_type(name)

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

    def visit_ref(self, ref: str) -> JsonDict:
        return {"$ref": self.maker.make_reference(True, ref)}

    def visit_union(self, members: list[JsonDict]) -> JsonDict:
        return {"anyOf": json_value([json_value(member) for member in members])}

    def visit_array(self, content: JsonDict) -> JsonDict:
        return patching.array_to_json_definition(content)

    def visit_dictionary(self, keys: JsonDict, values: JsonDict) -> JsonDict:
        return {"type": "object", "additionalProperties": values, "propertyNames": keys}

    def visit_struct(self, hierarchy: list[documentation.VisitedStruct[JsonDict]]) -> JsonDict:
        properties: JsonDict = {}
        required: dict[str, bool] = {}
        custom_properties: JsonDict | None = None

        for struct in hierarchy:
            for property in itertools.chain(struct.properties, struct.overridden_properties):
                for name in property.names:
                    properties[name] = property.type
                # @todo When there are multiple property names, and the property is required, enforce that at least one property name is present
                if len(property.names) == 1:
                    required[property.names[0]] = property.required

            if struct.custom_properties is not None:
                assert custom_properties is None
                custom_properties = struct.custom_properties

        definition: JsonDict = {"type": "object", "properties": properties}

        if custom_properties is None:
            if len(properties) == 0:
                raise documentation.Forbidden
        else:
            definition["additionalProperties"] = custom_properties

        if any(required.values()):
            definition["required"] = [
                json_value(property_name) for property_name in properties.keys() if required.get(property_name, False)
            ]

        return definition

    def visit_tuple(self, members: list[JsonDict]) -> JsonDict:
        return {
            "type": "array",
            "items": [json_value(member) for member in members],
            "minItems": len(members),
            "maxItems": len(members),
        }


class JsonSchemaMaker:
    def __init__(
        self,
        *,
        doc: documentation.Doc,
        make_reference: Callable[[bool, str], str] | None,
        limit_to_prototype_names: Iterable[str] | None,
        include_descendants: bool,
        forbid_type_names: Iterable[str],
    ) -> None:
        self.doc = doc

        self.types_by_name = {type.name: type for type in doc.types}
        self.prototypes_by_name = {prototype.name: prototype for prototype in doc.prototypes}

        if make_reference is None:
            self.do_make_reference: Callable[[bool, str], str] = lambda deep, name: f"#/definitions/{name}"
        else:
            self.do_make_reference = make_reference

        self.__init_forbidden_type_names(forbid_type_names)

        self.prototypes_to_include = set(
            self.__init_prototypes_to_include(limit_to_prototype_names, include_descendants)
        )

        self.references_needed_by = {
            type.name: type.definition.accept(NeededReferencesGatherer(self))
            for type in self.doc.types
            if type.name not in self.forbidden_type_names
        } | {
            prototype.name: prototype.make_definition().accept(NeededReferencesGatherer(self))
            for prototype in self.doc.prototypes
        }

    def __init_forbidden_type_names(self, forbid_type_names: Iterable[str]) -> None:
        self.forbidden_type_names = set(forbid_type_names)

        # @todo Use a proper graph exploration algorithm!
        while True:
            some_type_is_newly_forbidden = False
            for type in self.doc.types:
                if type.name not in self.forbidden_type_names:
                    try:
                        self.make_json_definition(type.definition)
                    except documentation.Forbidden:
                        self.forbidden_type_names.add(type.name)
                        some_type_is_newly_forbidden = True

            if not some_type_is_newly_forbidden:
                break

    def __init_prototypes_to_include(
        self, limit_to_prototype_names: Iterable[str] | None, include_descendants: bool
    ) -> Iterable[str]:
        if limit_to_prototype_names is None:
            for prototype in self.doc.prototypes:
                yield prototype.name
        else:
            prototypes_by_name = {
                prototype.name: prototype for prototype in self.doc.prototypes if prototype.name is not None
            }

            seed_prototypes = set()
            for name in limit_to_prototype_names:
                name = name + "Prototype"
                assert name in prototypes_by_name, f"Prototype {name!r} not found"
                seed_prototypes.add(name)

            yield from seed_prototypes

            if include_descendants:
                children_by_parent: dict[str, set[str]] = {}
                for prototype in self.doc.prototypes:
                    if prototype.base is not None:
                        children_by_parent.setdefault(prototype.base, set()).add(prototype.name)

                to_explore = set(seed_prototypes)
                while to_explore:
                    name = to_explore.pop()
                    children = children_by_parent.get(name, set())
                    yield from children
                    to_explore |= children

    def make_reference(self, deep: bool, name: str) -> str:
        if name in self.forbidden_type_names:
            assert name in self.types_by_name
            raise documentation.Forbidden

        return self.do_make_reference(deep, name)

    def get_referable_type(self, name: str) -> documentation.TypeExpression:
        if name in self.forbidden_type_names:
            assert name in self.types_by_name
            raise documentation.Forbidden

        type = self.types_by_name.get(name)
        if type is None:
            return self.prototypes_by_name[name].make_definition()
        else:
            return type.definition

    def make_json_definition(self, type: documentation.TypeExpression) -> JsonDict:
        return type.accept(JsonDefinitionMaker(self))

    def to_json(self) -> JsonDict:
        properties = {
            prototype.key: json_value(
                {"type": "object", "additionalProperties": {"$ref": self.make_reference(False, prototype.name)}}
            )
            for prototype in self.doc.prototypes
            if prototype.key is not None and prototype.name in self.prototypes_to_include
        }

        definitions = {
            type.name: {"description": json_value(f"https://lua-api.factorio.com/stable/types/{type.name}.html")}
            | self.make_json_definition(type.definition)
            for type in self.doc.types
            if type.name not in self.forbidden_type_names
        } | {
            prototype.name: {
                "description": json_value(f"https://lua-api.factorio.com/stable/prototypes/{prototype.name}.html")
            }
            | self.make_json_definition(prototype.make_definition())
            for prototype in self.doc.prototypes
            if prototype.key is not None
        }

        references_needed: set[str] = set()
        to_explore = set(self.prototypes_to_include)
        while to_explore:
            name = to_explore.pop()
            if name not in references_needed:
                references_needed.add(name)
                to_explore |= self.references_needed_by.get(name, set())

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "title": "Factorio Data.raw",
            "type": "object",
            "properties": properties,
            "definitions": {name: definition for name, definition in definitions.items() if name in references_needed},
        }


class NeededReferencesGatherer(documentation.TypeExpressionVisitor[set[str]]):
    def __init__(self, maker: JsonSchemaMaker) -> None:
        self.maker = maker

    def get_base_named(self, name: str) -> documentation.TypeExpression:
        return self.maker.get_referable_type(name)

    def visit_builtin(self, name: str) -> set[str]:
        return set()

    def visit_literal_bool(self, value: bool) -> set[str]:
        return set()

    def visit_literal_string(self, value: str) -> set[str]:
        return set()

    def visit_literal_integer(self, value: int) -> set[str]:
        return set()

    def visit_ref(self, ref: str) -> set[str]:
        return {ref}

    def visit_union(self, members: list[set[str]]) -> set[str]:
        return set().union(*members)

    def visit_array(self, content: set[str]) -> set[str]:
        return content

    def visit_dictionary(self, keys: set[str], values: set[str]) -> set[str]:
        return keys | values

    def visit_struct(self, hierarchy: list[documentation.VisitedStruct[set[str]]]) -> set[str]:
        refs = set()

        for struct in hierarchy:
            for property in itertools.chain(struct.properties, struct.overridden_properties):
                refs |= property.type
            if struct.custom_properties is not None:
                refs |= struct.custom_properties

        return refs

    def visit_tuple(self, members: list[set[str]]) -> set[str]:
        return set().union(*members)
