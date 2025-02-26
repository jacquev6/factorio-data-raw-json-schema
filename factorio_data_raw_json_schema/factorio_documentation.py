from __future__ import annotations

import itertools
import sys
from typing import Callable, Iterable, Literal
import dataclasses
import typing

from . import patching


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict = dict[str, JsonValue]


def json_value(value: JsonValue) -> JsonValue:
    """
    Statically assert that a value is a JsonValue and erase its concrete type.
    Helps with type checking where invariant (as opposed to covariant or contravariant) containers are involved (e.g. list and dict).
    """
    return value


class Forbidden(Exception):
    pass


T = typing.TypeVar("T")


@dataclasses.dataclass(kw_only=True, eq=False)
class BuiltinTypeExpression:
    kind: Literal["builtin"] = "builtin"
    json_definition: JsonDict

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return self.json_definition


builtin_types: dict[str, BuiltinTypeExpression] = {
    "string": BuiltinTypeExpression(json_definition={"type": "string"}),
    "float": BuiltinTypeExpression(json_definition={"type": "number"}),
    "double": BuiltinTypeExpression(json_definition={"type": "number"}),
    "bool": BuiltinTypeExpression(json_definition={"type": "boolean"}),
    "uint8": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 255}),
    "uint16": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 65535}),
    "uint32": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 4294967295}),
    "uint64": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": 0, "maximum": 18446744073709551615}),
    "int8": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": -128, "maximum": 127}),
    "int16": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": -32768, "maximum": 32767}),
    "int32": BuiltinTypeExpression(json_definition={"type": "integer", "minimum": -2147483648, "maximum": 2147483647}),
    "int64": BuiltinTypeExpression(
        json_definition={"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807}
    ),
}

unconstrained_type = BuiltinTypeExpression(json_definition={})


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralBoolTypeExpression:
    kind: Literal["literal_bool"] = "literal_bool"
    value: bool

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {"type": "boolean", "const": self.value}


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralStringTypeExpression:
    kind: Literal["literal_string"] = "literal_string"
    value: str

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {"type": "string", "const": self.value}


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralIntegerTypeExpression:
    kind: Literal["literal_integer"] = "literal_integer"
    value: int

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {"type": "integer", "const": self.value}


@dataclasses.dataclass(kw_only=True, eq=False)
class RefTypeExpression:
    kind: Literal["ref"] = "ref"
    ref: str

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {"$ref": maker.make_reference(True, self.ref)}


@dataclasses.dataclass(kw_only=True, eq=False)
class UnionTypeExpression:
    kind: Literal["union"] = "union"
    members: list[TypeExpression]

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {"anyOf": [member.make_json_definition(maker) for member in self.members]}


@dataclasses.dataclass(kw_only=True, eq=False)
class ArrayTypeExpression:
    kind: Literal["array"] = "array"
    content: TypeExpression

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return patching.array_to_json_definition(self, maker)


@dataclasses.dataclass(kw_only=True, eq=False)
class DictionaryTypeExpression:
    kind: Literal["dictionary"] = "dictionary"
    keys: TypeExpression
    values: TypeExpression

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {
            "type": "object",
            "additionalProperties": self.values.make_json_definition(maker),
            "propertyNames": self.keys.make_json_definition(maker),
        }


@dataclasses.dataclass(kw_only=True, eq=False)
class Property:
    names: list[str]
    type: TypeExpression
    required: bool = False


@dataclasses.dataclass(kw_only=True, eq=False)
class StructTypeExpression:
    kind: Literal["struct"] = "struct"
    base: str | None
    properties: list[Property]
    overridden_properties: list[Property]
    custom_properties: TypeExpression | None

    def get_property(self, name: str) -> Property:
        for property in self.properties:
            if name in property.names:
                return property
        raise ValueError(f"Property {name!r} not found")

    @typing.overload
    def get_property_type(self, name: str) -> TypeExpression: ...
    @typing.overload
    def get_property_type(self, name: str, t: type[T]) -> T: ...
    def get_property_type(self, name: str, t: type[T] | None = None) -> TypeExpression | T:
        property = self.get_property(name)
        if t is not None:
            assert isinstance(property.type, t), property
        return property.type

    def set_property_type(self, name: str, type: TypeExpression) -> None:
        property = self.get_property(name)
        property.type = type

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        properties: JsonDict = {}
        required: dict[str, bool] = {}

        def rec(prototype: StructTypeExpression) -> None:
            if prototype.base is not None:
                base = maker.get_referable_type(prototype.base)
                if isinstance(base, StructTypeExpression):
                    rec(base)
                elif isinstance(base, UnionTypeExpression):
                    for member in base.members:
                        if isinstance(member, StructTypeExpression):
                            rec(member)
                            break
                        else:
                            print(
                                f"{prototype.base} has union type and is used as a base, but it has no member of struct type",
                                file=sys.stderr,
                            )
                else:
                    print(f"{prototype.base} is used as a base but has unexpected type: {base.kind}", file=sys.stderr)

            for property in itertools.chain(prototype.properties, prototype.overridden_properties):
                try:
                    property_definition = property.type.make_json_definition(maker)
                except Forbidden:
                    continue
                else:
                    for name in property.names:
                        properties[name] = property_definition
                    # @todo When there are multiple property names, and the property is required, enforce that at least one property name is present
                    if len(property.names) == 1:
                        required[property.names[0]] = property.required

        rec(self)

        if len(properties) == 0 and self.custom_properties is None:
            raise Forbidden

        definition: JsonDict = {"type": "object", "properties": properties}

        if self.custom_properties is None:
            pass
        else:
            definition["additionalProperties"] = self.custom_properties.make_json_definition(maker)

        if any(required.values()):
            definition["required"] = [
                json_value(property_name) for property_name in properties.keys() if required.get(property_name, False)
            ]

        return definition


@dataclasses.dataclass(kw_only=True, eq=False)
class TupleTypeExpression:
    kind: Literal["tuple"] = "tuple"
    members: list[TypeExpression]

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return {
            "type": "array",
            "items": [member.make_json_definition(maker) for member in self.members],
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
    | TupleTypeExpression
)


@dataclasses.dataclass(kw_only=True, eq=False)
class Type:
    name: str
    definition: TypeExpression


@dataclasses.dataclass(kw_only=True, eq=False)
class Prototype:
    name: str
    key: str | None
    base: str | None

    properties: list[Property]
    overridden_properties: list[Property]
    custom_properties: TypeExpression | None

    def get_property(self, name: str) -> Property:
        for property in self.properties:
            if name in property.names:
                return property
        raise ValueError(f"Property {name!r} not found")

    @typing.overload
    def get_property_type(self, name: str) -> TypeExpression: ...
    @typing.overload
    def get_property_type(self, name: str, t: type[T]) -> T: ...
    def get_property_type(self, name: str, t: type[T] | None = None) -> TypeExpression | T:
        property = self.get_property(name)
        if t is not None:
            assert isinstance(property.type, t), property
        return property.type

    def set_property_type(self, name: str, type: TypeExpression) -> None:
        property = self.get_property(name)
        property.type = type

    def make_definition(self) -> TypeExpression:
        type_property = (
            None
            if self.key is None
            else Property(names=["type"], type=LiteralStringTypeExpression(value=self.key), required=True)
        )

        return StructTypeExpression(
            base=self.base,
            properties=self.properties + list(filter(None, [type_property])),
            overridden_properties=self.overridden_properties,
            custom_properties=self.custom_properties,
        )

    def make_json_definition(self, maker: JsonSchemaMaker) -> JsonDict:
        return self.make_definition().make_json_definition(maker)


@dataclasses.dataclass(kw_only=True, eq=False)
class Doc:
    types: list[Type]
    prototypes: list[Prototype]

    @typing.overload
    def get_type_def(self, name: str) -> TypeExpression: ...
    @typing.overload
    def get_type_def(self, name: str, t: type[T]) -> T: ...
    def get_type_def(self, name: str, t: type[T] | None = None) -> TypeExpression | T:
        for type in self.types:
            if type.name == name:
                if t is not None:
                    assert isinstance(type.definition, t), type
                return type.definition
        raise ValueError(f"Type {name!r} not found")

    def get_prototype(self, name: str) -> Prototype:
        for prototype in self.prototypes:
            if prototype.name == name:
                return prototype
        raise ValueError(f"Prototype {name!r} not found")


def make_json_schema(
    doc: Doc,
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


class JsonSchemaMaker:
    def __init__(
        self,
        *,
        doc: Doc,
        make_reference: Callable[[bool, str], str] | None,
        limit_to_prototype_names: Iterable[str] | None,
        include_descendants: bool,
        forbid_type_names: Iterable[str],
    ) -> None:
        self.doc = doc

        self.types_by_name = {type.name: type for type in doc.types}
        self.prototypes_by_name = {prototype.name: prototype for prototype in doc.prototypes}

        self.__references_needed: set[str] = set()

        if make_reference is None:
            self.do_make_reference: Callable[[bool, str], str] = lambda deep, name: f"#/definitions/{name}"
        else:
            self.do_make_reference = make_reference

        self.__init_forbidden_type_names(forbid_type_names)
        # self.forbidden_type_names: set[str] = set()

        self.prototypes_to_include = set(
            self.__init_prototypes_to_include(limit_to_prototype_names, include_descendants)
        )

        self.references_needed_by = dict(self.__init_references_needed_by())

    def __init_forbidden_type_names(self, forbid_type_names: Iterable[str]) -> None:
        self.forbidden_type_names = set(forbid_type_names)

        # @todo Use a proper graph exploration algorithm!
        while True:
            some_type_is_newly_forbidden = False
            for type in self.doc.types:
                if type.name not in self.forbidden_type_names:
                    self.__references_needed = set()
                    try:
                        type.definition.make_json_definition(self)
                    except Forbidden:
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

    def __init_references_needed_by(self) -> Iterable[tuple[str, set[str]]]:
        # This function relies on side-effects: 'make_reference' modifies 'self.references_needed'
        # Rationale: keep the many 'TypeExpression' classes simple: they only need to define 'make_json_definition',
        # and not some variant of 'gather_references_needed'.

        for prototype in self.doc.prototypes:
            self.__references_needed = set()
            prototype.make_json_definition(self)  # Trigger the side-effect
            yield prototype.name, self.__references_needed

        for type in self.doc.types:
            if type.name not in self.forbidden_type_names:
                self.__references_needed = set()
                type.definition.make_json_definition(self)  # Trigger the side-effect
                yield type.name, self.__references_needed

        self.__references_needed = set()

    def make_reference(self, deep: bool, name: str) -> str:
        if name in self.forbidden_type_names:
            assert name in self.types_by_name
            raise Forbidden

        self.__references_needed.add(name)  # Side effect for '__init_references_needed_by'
        return self.do_make_reference(deep, name)

    def get_referable_type(self, name: str) -> TypeExpression:
        if name in self.forbidden_type_names:
            assert name in self.types_by_name
            raise Forbidden

        type = self.types_by_name.get(name)
        if type is None:
            return self.prototypes_by_name[name].make_definition()
        else:
            return type.definition

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
            | type.definition.make_json_definition(self)
            for type in self.doc.types
            if type.name not in self.forbidden_type_names
        } | {
            prototype.name: {
                "description": json_value(f"https://lua-api.factorio.com/stable/prototypes/{prototype.name}.html")
            }
            | prototype.make_json_definition(self)
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
