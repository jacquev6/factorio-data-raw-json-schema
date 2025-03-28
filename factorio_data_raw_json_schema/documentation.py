from __future__ import annotations

import abc
import dataclasses
import typing


T = typing.TypeVar("T")


E = typing.TypeVar("E")


class TypeExpression(abc.ABC):
    @abc.abstractmethod
    def accept(self, visitor: TypeExpressionVisitor[E]) -> E: ...


@dataclasses.dataclass
class BuiltinTypeExpression(TypeExpression):
    name: str

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_builtin(self.name)


@dataclasses.dataclass
class LiteralBoolTypeExpression(TypeExpression):
    value: bool

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_literal_bool(self.value)


@dataclasses.dataclass
class LiteralStringTypeExpression(TypeExpression):
    value: str

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_literal_string(self.value)


@dataclasses.dataclass
class LiteralIntegerTypeExpression(TypeExpression):
    value: int

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_literal_integer(self.value)


@dataclasses.dataclass
class RefTypeExpression(TypeExpression):
    ref: str

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_ref(self.ref)


@dataclasses.dataclass
class UnionTypeExpression(TypeExpression):
    members: list[TypeExpression]

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_union([member.accept(visitor) for member in self.members])


@dataclasses.dataclass
class ArrayTypeExpression(TypeExpression):
    content: TypeExpression

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_array(self.content.accept(visitor))


@dataclasses.dataclass
class DictionaryTypeExpression(TypeExpression):
    keys: TypeExpression
    values: TypeExpression

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_dictionary(self.keys.accept(visitor), self.values.accept(visitor))


@dataclasses.dataclass
class Property:
    names: list[str]
    type: TypeExpression
    required: bool = False


@dataclasses.dataclass
class StructTypeExpression(TypeExpression):
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

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        def visit_properties(properties: list[Property]) -> list[VisitedProperty[E]]:
            return [
                VisitedProperty(names=property.names, type=property.type.accept(visitor), required=property.required)
                for property in properties
            ]

        return visitor.visit_struct(
            base_name=self.base,
            properties=visit_properties(self.properties),
            overridden_properties=visit_properties(self.overridden_properties),
            custom_properties=(None if self.custom_properties is None else self.custom_properties.accept(visitor)),
        )


@dataclasses.dataclass
class TupleTypeExpression(TypeExpression):
    members: list[TypeExpression]

    def accept(self, visitor: TypeExpressionVisitor[E]) -> E:
        return visitor.visit_tuple([member.accept(visitor) for member in self.members])


@dataclasses.dataclass
class VisitedProperty[E]:
    names: list[str]
    type: E
    required: bool = False


class TypeExpressionVisitor[E](abc.ABC):
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
    def visit_struct(
        self,
        base_name: str | None,
        properties: list[VisitedProperty[E]],
        overridden_properties: list[VisitedProperty[E]],
        custom_properties: E | None,
    ) -> E: ...

    @abc.abstractmethod
    def visit_tuple(self, members: list[E]) -> E: ...


@dataclasses.dataclass
class Type:
    name: str
    definition: TypeExpression


@dataclasses.dataclass
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
        properties = list(self.properties)
        if self.key is not None:
            properties.append(Property(names=["type"], type=LiteralStringTypeExpression(value=self.key), required=True))

        return StructTypeExpression(
            base=self.base,
            properties=properties,
            overridden_properties=self.overridden_properties,
            custom_properties=self.custom_properties,
        )


@dataclasses.dataclass
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
