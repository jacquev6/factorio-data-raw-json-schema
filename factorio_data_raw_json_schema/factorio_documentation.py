from __future__ import annotations

import abc
import sys
from typing import Iterable, Literal
import dataclasses
import typing


class Forbidden(Exception):
    pass


T = typing.TypeVar("T")


@dataclasses.dataclass(kw_only=True, eq=False)
class BuiltinTypeExpression:
    kind: Literal["builtin"] = "builtin"
    name: str


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralBoolTypeExpression:
    kind: Literal["literal_bool"] = "literal_bool"
    value: bool


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralStringTypeExpression:
    kind: Literal["literal_string"] = "literal_string"
    value: str


@dataclasses.dataclass(kw_only=True, eq=False)
class LiteralIntegerTypeExpression:
    kind: Literal["literal_integer"] = "literal_integer"
    value: int


@dataclasses.dataclass(kw_only=True, eq=False)
class RefTypeExpression:
    kind: Literal["ref"] = "ref"
    ref: str


@dataclasses.dataclass(kw_only=True, eq=False)
class UnionTypeExpression:
    kind: Literal["union"] = "union"
    members: list[TypeExpression]


@dataclasses.dataclass(kw_only=True, eq=False)
class ArrayTypeExpression:
    kind: Literal["array"] = "array"
    content: TypeExpression


@dataclasses.dataclass(kw_only=True, eq=False)
class DictionaryTypeExpression:
    kind: Literal["dictionary"] = "dictionary"
    keys: TypeExpression
    values: TypeExpression


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


@dataclasses.dataclass(kw_only=True, eq=False)
class TupleTypeExpression:
    kind: Literal["tuple"] = "tuple"
    members: list[TypeExpression]


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


E = typing.TypeVar("E")


@dataclasses.dataclass(kw_only=True, eq=False)
class VisitedProperty[E]:
    names: list[str]
    type: E
    required: bool = False


@dataclasses.dataclass(kw_only=True, eq=False)
class VisitedStruct[E]:
    base: str | None
    properties: list[VisitedProperty[E]]
    overridden_properties: list[VisitedProperty[E]]
    custom_properties: E | None


class TypeExpressionVisitor[E](abc.ABC):
    @abc.abstractmethod
    def get_base_named(self, name: str) -> TypeExpression: ...

    @abc.abstractmethod
    def visit_builtin(self, name: str) -> E: ...

    @abc.abstractmethod
    def visit_literal_bool(self, value: bool) -> E: ...

    @abc.abstractmethod
    def visit_literal_string(self, value: str) -> E: ...

    @abc.abstractmethod
    def visit_literal_integer(self, value: int) -> E: ...

    @abc.abstractmethod
    def visit_ref(self, ref: str) -> E: ...

    @abc.abstractmethod
    def visit_union(self, members: list[E]) -> E: ...

    @abc.abstractmethod
    def visit_array(self, content: E) -> E: ...

    @abc.abstractmethod
    def visit_dictionary(self, keys: E, values: E) -> E: ...

    @abc.abstractmethod
    def visit_struct(self, hierarchy: list[VisitedStruct[E]]) -> E: ...  # Base first, then derived

    @abc.abstractmethod
    def visit_tuple(self, members: list[E]) -> E: ...


def visit_type_expression(visitor: TypeExpressionVisitor[E], type: TypeExpression) -> E:
    # Should this be implemented as a method 'visit' on each TypeExpression class?
    if isinstance(type, BuiltinTypeExpression):
        return visitor.visit_builtin(type.name)
    elif isinstance(type, LiteralBoolTypeExpression):
        return visitor.visit_literal_bool(type.value)
    elif isinstance(type, LiteralStringTypeExpression):
        return visitor.visit_literal_string(type.value)
    elif isinstance(type, LiteralIntegerTypeExpression):
        return visitor.visit_literal_integer(type.value)
    elif isinstance(type, RefTypeExpression):
        return visitor.visit_ref(type.ref)
    elif isinstance(type, UnionTypeExpression):
        members = [visit_type_expression(visitor, member) for member in type.members]
        return visitor.visit_union(members)
    elif isinstance(type, ArrayTypeExpression):
        content = visit_type_expression(visitor, type.content)
        return visitor.visit_array(content)
    elif isinstance(type, DictionaryTypeExpression):
        keys = visit_type_expression(visitor, type.keys)
        values = visit_type_expression(visitor, type.values)
        return visitor.visit_dictionary(keys, values)
    elif isinstance(type, StructTypeExpression):
        hierarchy: list[VisitedStruct[E]] = []

        def visit_properties(properties: list[Property]) -> Iterable[VisitedProperty[E]]:
            for property in properties:
                try:
                    visited_type = visit_type_expression(visitor, property.type)
                except Forbidden:
                    pass
                else:
                    yield VisitedProperty(names=property.names, type=visited_type, required=property.required)

        def rec(t: StructTypeExpression) -> None:
            if t.base is not None:
                base = visitor.get_base_named(t.base)
                if isinstance(base, StructTypeExpression):
                    rec(base)
                elif isinstance(base, UnionTypeExpression):
                    for member in base.members:
                        if isinstance(member, StructTypeExpression):
                            rec(member)
                            break
                        else:
                            print(
                                f"{t.base} has union type and is used as a base, but it has no member of struct type",
                                file=sys.stderr,
                            )
                else:
                    print(f"{t.base} is used as a base but has unexpected type: {base.kind}", file=sys.stderr)

            hierarchy.append(
                VisitedStruct(
                    base=t.base,
                    properties=list(visit_properties(t.properties)),
                    overridden_properties=list(visit_properties(t.overridden_properties)),
                    custom_properties=(
                        None if t.custom_properties is None else visit_type_expression(visitor, t.custom_properties)
                    ),
                )
            )

        rec(type)

        return visitor.visit_struct(hierarchy)
    elif isinstance(type, TupleTypeExpression):
        members = [visit_type_expression(visitor, member) for member in type.members]
        return visitor.visit_tuple(members)
    else:
        assert False


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
