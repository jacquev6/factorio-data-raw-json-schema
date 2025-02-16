from typing import Iterable
import re

import bs4
import joblib
import lark
import tqdm

from .crawling import Crawler
from .schema import Schema, JsonValue


def extract(crawler: Crawler) -> Schema:
    extractor = _Extractor(crawler)

    with tqdm.tqdm(total=2) as progress:
        extractor.extract_all_type_names()
        progress.total += len(extractor.all_type_names)
        progress.update(1)
        extractor.extract_all_prototype_names()
        progress.total += len(extractor.all_prototype_names)
        progress.update(1)
        for _ in extractor.extract_all_types():
            progress.update(1)
        for _ in extractor.extract_all_prototypes():
            progress.update(1)

    return extractor.make_schema()


class _Extractor:
    def __init__(self, crawler: Crawler) -> None:
        self.crawler = crawler
        self.all_type_names: set[str] = set()
        self.all_prototype_names: set[str] = set()
        self.types: list[Schema.TypeDefinition] = []
        self.prototypes: list[tuple[str | None, Schema.StructTypeDefinition]] = []

    def extract_all_type_names(self) -> None:
        def gen() -> Iterable[str]:
            for a in self.crawler.get("types").find_all("a"):
                link = tag(a).get("href")
                if link is not None and str(link).startswith("types/"):
                    type = str(link).split("#")[0].split("/")[-1]
                    assert type.endswith(".html")
                    yield type[:-5]

        self.all_type_names = set(gen())

    def extract_all_prototype_names(self) -> None:
        def gen() -> Iterable[str]:
            for a in self.crawler.get("prototypes").find_all("a"):
                link = tag(a).get("href")
                if link is not None and str(link).startswith("prototypes/"):
                    prototype = str(link).split("#")[0].split("/")[-1]
                    assert prototype.endswith(".html")
                    yield prototype[:-5]

        self.all_prototype_names = set(gen())

    def extract_all_types(self) -> Iterable[None]:
        for type in joblib.Parallel(n_jobs=-1, return_as="generator")(
            joblib.delayed(self._extract_type)(type_name) for type_name in sorted(self.all_type_names)
        ):
            self.types.append(type)
            yield None

    def extract_all_prototypes(self) -> Iterable[None]:
        for key, prototype in joblib.Parallel(n_jobs=-1, return_as="generator")(
            joblib.delayed(self._extract_prototype)(prototype_name)
            for prototype_name in sorted(self.all_prototype_names)
        ):
            self.prototypes.append((key, prototype))
            yield None

    def _extract_type(self, type_name: str) -> Schema.TypeDefinition:
        if type_name in ["Data", "DataExtendMethod", "AnyPrototype"]:
            return Schema.TypeDefinition(name=type_name, definition={})

        soup = self.crawler.get("types", type_name)

        h2_text = tag(soup.find("h2")).text
        if (m := re.match(r"^" + type_name + r"\s*::\s*(.*?)\s*(Example code)?$", h2_text)) is not None:
            local_types = {
                name: Schema.TypeDefinition(name=name, definition={"anyOf": [{"$ref": f"#/definitions/{name}"}]})
                for name in self.all_type_names
            }

            type_expression = m.group(1).replace(" - abstract", "")
            if "struct" in type_expression:
                properties_div_soup = soup.find("div", id="attributes-body-main")
                local_types["struct"] = Schema.StructTypeDefinition(
                    name=type_name,
                    base=extract_struct_base(soup),
                    properties=list(extract_struct_properties(type_name, properties_div_soup, self.all_type_names)),
                    additional_properties=False,
                )

            if "union" in type_expression:
                local_types["union"] = Schema.UnionTypeDefinition(
                    name=type_name, types=list(extract_union_members(soup, self.all_type_names))
                )

            try:
                type_expression_tree = type_expression_parser.parse(type_expression)
                return Schema.TypeDefinition(
                    name=type_name,
                    definition=TypeExpressionTransformer(set(), local_types).transform(type_expression_tree),
                )
            except lark.exceptions.LarkError:
                assert False, f"failed to parse type expression: {type_expression!r}"
        elif (m := re.match(r"^" + type_name + r"\s* builtin\s*(Example code)?$", h2_text)) is not None:
            return Schema.TypeDefinition(name=type_name, definition=Schema.builtin_types[type_name])
        else:
            assert False, f"failed to regex-match type header: {h2_text!r}"

    def _extract_prototype(self, prototype_name: str) -> tuple[str | None, Schema.StructTypeDefinition]:
        soup = self.crawler.get("prototypes", prototype_name)
        properties = list(
            extract_struct_properties(prototype_name, soup.find("div", id="attributes-body-main"), self.all_type_names)
        )

        overridden_properties_soup = soup.find("div", id="attributes-body-overridden")
        if overridden_properties_soup is not None:
            properties.extend(
                extract_struct_properties(prototype_name, overridden_properties_soup, self.all_type_names)
            )

        additional_properties: JsonValue = False
        custom_properties_div_soup = soup.find("div", id="custom_properties")
        if custom_properties_div_soup is not None:
            custom_properties_text = tag(tag(tag(custom_properties_div_soup).parent).find("h3")).text
            assert custom_properties_text.startswith("Custom properties  \xa0::\xa0string → ")
            custom_properties_type_name = custom_properties_text[32:]
            # print(f"Custom props: {custom_properties_type_name}", file=sys.stderr)
            additional_properties = {"$ref": f"#/definitions/{custom_properties_type_name}"}

        return extract_prototype_key(soup), Schema.StructTypeDefinition(
            prototype_name,
            base=extract_struct_base(soup),
            properties=properties,
            additional_properties=additional_properties,
        )

    def make_schema(self) -> Schema:
        return Schema(types=self.types, prototypes=self.prototypes)


def extract_union_members(soup: bs4.element.PageElement | None, global_types: set[str]) -> Iterable[JsonValue]:
    if soup is not None:
        for span_soup in (tag(el) for el in tag(soup).find_all("span", class_="docs-attribute-name")):
            yield TypeExpressionTransformer(
                global_types,
                {
                    # I believe 'DamageEntityTriggerEffectItem' is a typo in https://lua-api.factorio.com/2.0.28/types/TriggerEffect.html
                    # and actually refers to 'DamageTriggerEffectItem'
                    "DamageEntityTriggerEffectItem": Schema.TypeDefinition(
                        name="DamageEntityTriggerEffectItem",
                        definition={"$ref": "#/definitions/DamageTriggerEffectItem"},
                    )
                },
            ).transform(type_expression_parser.parse(str(span_soup.text).strip()))


def extract_prototype_key(soup: bs4.BeautifulSoup) -> str | None:
    text = str(tag(soup.find("h2")).text)
    if "abstract" in text:
        return None
    else:
        parts = text.split(" ")
        assert len(parts) >= 2, parts
        key = parts[1]
        if key == "":  # Space Age icon
            key = parts[2]
        assert key.startswith("'") and key.endswith("'"), key
        return key[1:-1]


def extract_struct_base(soup: bs4.BeautifulSoup) -> str | None:
    base_soup = soup.find(string=re.compile(r"Inherits from"))
    if base_soup is not None:
        base_link_soup = tag(base_soup.parent).find("a")
        assert base_link_soup is not None
        base = base_link_soup.text
        assert isinstance(base, str)
        return base

    return None


def extract_struct_properties(
    type_name: str, properties_div_soup: bs4.element.PageElement | None, global_types: set[str]
) -> Iterable[Schema.Property]:
    if properties_div_soup is not None:
        for property_div_soup in (tag(el) for el in tag(properties_div_soup).find_all("div", recursive=False)):
            property_header_soup = tag(property_div_soup.find("h3", recursive=False))
            property_names = str(tag(property_header_soup.contents[0]).contents[0]).strip().split(" or ")

            local_types: dict[str, Schema.TypeDefinition] = {}
            for local_type_div_soup in (tag(el) for el in property_div_soup.find_all("div", class_="inline-type")):
                local_type_header_text = tag(local_type_div_soup.find("h4")).text
                if (m := re.match(r"^(.*?)\s*::\s*(.*?)\s*$", local_type_header_text)) is not None:
                    local_type_name = m.group(1)
                    match m.group(2):
                        case "struct":
                            local_type_properties = list(
                                extract_struct_properties(
                                    f"{type_name}.{local_type_name}",
                                    tag(local_type_div_soup.find("h2", string="Properties")).next_sibling,
                                    global_types,
                                )
                            )
                            local_types[local_type_name] = Schema.StructTypeDefinition(
                                local_type_name,
                                base=None,
                                properties=local_type_properties,
                                additional_properties=False,
                            )
                        case "union":
                            local_types[local_type_name] = Schema.UnionTypeDefinition(
                                name=local_type_name,
                                types=list(
                                    extract_union_members(
                                        tag(local_type_div_soup.find("h4", string="Union members")).next_sibling,
                                        global_types,
                                    )
                                ),
                            )
                        case local_type_expression:
                            try:
                                local_type_expression_tree = type_expression_parser.parse(local_type_expression)
                                local_types[local_type_name] = Schema.TypeDefinition(
                                    name=local_type_name,
                                    definition=TypeExpressionTransformer(global_types, local_types).transform(
                                        local_type_expression_tree
                                    ),
                                )
                            except lark.exceptions.LarkError:
                                assert False, f"failed to parse local type expression: {local_type_expression!r}"
                else:
                    assert False, f"failed to regex-match local type header: {local_type_header_text!r}"

            property_header_text = property_header_soup.text
            m = re.match(
                r"^" + " or ".join(property_names) + r"\s*::\s*(.*?)\s*(optional)?\s*(new|changed)?$",
                property_header_text,
            )
            assert m is not None, f"failed to regex-match property header: {property_header_text!r}"
            optional = m.group(2) == "optional"

            match m.group(1):
                case "union":
                    property_type = Schema.UnionTypeDefinition(
                        name="property",
                        types=list(
                            extract_union_members(
                                tag(property_div_soup.find("h4", string="Union members")).next_sibling, global_types
                            )
                        ),
                    ).definition
                case type_expression:
                    try:
                        type_expression_tree = type_expression_parser.parse(type_expression)
                        property_type = TypeExpressionTransformer(global_types, local_types).transform(
                            type_expression_tree
                        )
                    except lark.exceptions.LarkError:
                        assert (
                            False
                        ), f"failed to parse type expression for {type_name}.{property_names[0]}: {type_expression!r}"

            for property_name in property_names:
                # @todo When there are multiple property names, and the property is not optional, enforce that at least one property name is present
                yield Schema.Property(
                    name=property_name, type=property_type, required=not optional and len(property_names) == 1
                )


type_expression_parser = lark.Lark(
    r"""
    type_expression : named_type | literal_string | literal_integer | array_type | union_type | dictionary_type | tuple_type | adhoc_type

    named_type : CNAME
    literal_string : ESCAPED_STRING
    literal_integer : INT
    array_type : "array" "[" type_expression "]"
    union_type : type_expression "or" type_expression
    dictionary_type : "dictionary" "[" type_expression "→" type_expression "]"
    tuple_type : "{" type_expression ("," type_expression)* "}"
    adhoc_type : "defines.inventory"

    %import common.ESCAPED_STRING
    %import common.INT
    %import common.CNAME
    %import common.WS
    %ignore WS
    %ignore "\xa0"
    """,
    start="type_expression",
)


class TypeExpressionTransformer(lark.Transformer[lark.Token, dict[str, JsonValue]]):
    def __init__(self, global_types: set[str], local_types: dict[str, Schema.TypeDefinition]) -> None:
        self.global_types = global_types
        self.local_types = local_types

    def type_expression(self, items: list[JsonValue]) -> JsonValue:
        return items[0]

    def named_type(self, items: list[str]) -> JsonValue:
        type_name = items[0]
        if type_name == "true":
            return {"type": "boolean", "const": True}
        elif type_name == "false":
            return {"type": "boolean", "const": False}
        elif type_name in self.global_types:
            return {"$ref": f"#/definitions/{type_name}"}
        elif type_name in self.local_types:
            return self.local_types[type_name].definition
        else:
            assert False, f"unknown type: {type_name!r}"

    def literal_string(self, items: list[str]) -> JsonValue:
        value = items[0]
        assert value.startswith('"') and value.endswith('"')
        return {"type": "string", "const": value.strip('"')}

    def literal_integer(self, items: list[str]) -> JsonValue:
        value = items[0]
        return {"type": "integer", "const": int(value)}

    def array_type(self, items: list[JsonValue]) -> JsonValue:
        return {
            "oneOf": [
                {"type": "array", "items": items[0]},
                # Empty arrays are serialized as {} instead of []
                {"type": "object", "additionalProperties": False},
            ]
        }

    def union_type(self, items: list[JsonValue]) -> JsonValue:
        members: list[JsonValue] = []
        for item in items:
            if isinstance(item, dict) and item.get("anyOf") is not None:
                assert isinstance(item["anyOf"], list)
                members.extend(item["anyOf"])
            else:
                members.append(item)
        return {"anyOf": members}

    def dictionary_type(self, items: list[JsonValue]) -> JsonValue:
        return {"type": "object", "additionalProperties": items[1], "propertyNames": items[0]}

    def tuple_type(self, items: list[JsonValue]) -> JsonValue:
        return {"type": "array", "items": items, "minItems": len(items), "maxItems": len(items)}

    def adhoc_type(self, items: list[str]) -> JsonValue:
        return {"type": "integer"}


def tag(tag: bs4.element.PageElement | None) -> bs4.element.Tag:
    """
    Assert at runtime that a PageElement is actually a Tag.
    (Tag is a subclass of PageElement.)
    Helps with static type checking.
    """
    assert isinstance(tag, bs4.element.Tag), f"{tag!r} is not a Tag"
    return tag
