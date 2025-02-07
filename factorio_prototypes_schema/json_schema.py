# generated by datamodel-codegen:
#   filename:  <stdin>

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    PositiveFloat,
    RootModel,
    conint,
    constr,
)


class Core(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    field_id: Optional[constr(pattern=r'^[^#]*#?$')] = Field(None, alias='$id')
    field_schema: Optional[AnyUrl] = Field(None, alias='$schema')
    field_anchor: Optional[constr(pattern=r'^[A-Za-z][-A-Za-z0-9.:_]*$')] = Field(
        None, alias='$anchor'
    )
    field_ref: Optional[str] = Field(None, alias='$ref')
    field_recursiveRef: Optional[str] = Field(None, alias='$recursiveRef')
    field_recursiveAnchor: Optional[bool] = Field(False, alias='$recursiveAnchor')
    field_vocabulary: Optional[Dict[str, bool]] = Field(None, alias='$vocabulary')
    field_comment: Optional[str] = Field(None, alias='$comment')
    field_defs: Optional[Dict[str, Any]] = Field({}, alias='$defs')


class SchemaArray(RootModel[List[Any]]):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    root: List[Any] = Field(..., min_length=1)


class NonNegativeInteger(RootModel[conint(ge=0)]):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    root: conint(ge=0)


class NonNegativeIntegerDefault0(RootModel[NonNegativeInteger]):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    root: NonNegativeInteger


class SimpleTypes(Enum):
    array = 'array'
    boolean = 'boolean'
    integer = 'integer'
    null = 'null'
    number = 'number'
    object = 'object'
    string = 'string'


class StringArray(RootModel[List[str]]):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    root: List[str]


class MetaData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    title: Optional[str] = None
    description: Optional[str] = None
    default: Optional[Any] = None
    deprecated: Optional[bool] = False
    readOnly: Optional[bool] = False
    writeOnly: Optional[bool] = False
    examples: Optional[List] = None


class Format(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    format: Optional[str] = None


class Content(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    contentMediaType: Optional[str] = None
    contentEncoding: Optional[str] = None
    contentSchema: Optional[Any] = None


class Applicator(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    additionalItems: Optional[Any] = None
    unevaluatedItems: Optional[Any] = None
    items: Optional[Union[Any, SchemaArray]] = None
    contains: Optional[Any] = None
    additionalProperties: Optional[Any] = None
    unevaluatedProperties: Optional[Any] = None
    properties: Optional[Dict[str, Any]] = {}
    patternProperties: Optional[Dict[str, Any]] = {}
    dependentSchemas: Optional[Dict[str, Any]] = None
    propertyNames: Optional[Any] = None
    if_: Optional[Any] = Field(None, alias='if')
    then: Optional[Any] = None
    else_: Optional[Any] = Field(None, alias='else')
    allOf: Optional[SchemaArray] = None
    anyOf: Optional[SchemaArray] = None
    oneOf: Optional[SchemaArray] = None
    not_: Optional[Any] = Field(None, alias='not')


class Validation(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    multipleOf: Optional[PositiveFloat] = None
    maximum: Optional[float] = None
    exclusiveMaximum: Optional[float] = None
    minimum: Optional[float] = None
    exclusiveMinimum: Optional[float] = None
    maxLength: Optional[NonNegativeInteger] = None
    minLength: Optional[NonNegativeIntegerDefault0] = None
    pattern: Optional[str] = None
    maxItems: Optional[NonNegativeInteger] = None
    minItems: Optional[NonNegativeIntegerDefault0] = None
    uniqueItems: Optional[bool] = False
    maxContains: Optional[NonNegativeInteger] = None
    minContains: Optional[NonNegativeInteger] = Field(
        default_factory=lambda: NonNegativeInteger.model_validate(1)
    )
    maxProperties: Optional[NonNegativeInteger] = None
    minProperties: Optional[NonNegativeIntegerDefault0] = None
    required: Optional[StringArray] = None
    dependentRequired: Optional[Dict[str, StringArray]] = None
    const: Optional[Any] = None
    enum: Optional[List] = None
    type: Optional[Union[SimpleTypes, List[SimpleTypes]]] = None


class CoreAndValidationSpecificationsMetaSchema(
    Core, Applicator, Validation, MetaData, Format, Content
):
    model_config = ConfigDict(
        populate_by_name=True,
    )
    definitions: Optional[Dict[str, Any]] = {}
    dependencies: Optional[Dict[str, Union[Any, StringArray]]] = None
