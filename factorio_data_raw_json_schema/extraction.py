from typing import Iterable, Literal
import re

import bs4
import joblib
import lark
import tqdm

from . import patching
from .crawling import Crawler
from .schema import Schema


def extract(*, crawler: Crawler, workers: int) -> Schema:
    extractor = _Extractor(crawler=crawler, workers=workers)

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
    def __init__(self, *, crawler: Crawler, workers: int) -> None:
        self.crawler = crawler
        self._workers = workers
        self.all_type_names: set[str] = set()
        self.all_prototype_names: set[str] = set()
        self.types: list[Schema.Type] = []
        self.prototypes: list[Schema.Prototype] = []

    def extract_all_type_names(self) -> None:
        def gen() -> Iterable[str]:
            for a in self.crawler.get("types").find_all("a"):
                link = tag(a).get("href")
                if link is not None and str(link).startswith("types/"):
                    type = str(link).split("#")[0].split("/")[-1]
                    assert type.endswith(".html")
                    yield type[:-5]

        self.all_type_names = set(gen()) - {"Data", "DataExtendMethod", "AnyPrototype"}

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
        for type in joblib.Parallel(n_jobs=self._workers, return_as="generator")(
            joblib.delayed(self._extract_type)(type_name) for type_name in sorted(self.all_type_names)
        ):
            self.types.append(type)
            yield None

    def extract_all_prototypes(self) -> Iterable[None]:
        for prototype in joblib.Parallel(n_jobs=self._workers, return_as="generator")(
            joblib.delayed(self._extract_prototype)(prototype_name)
            for prototype_name in sorted(self.all_prototype_names)
        ):
            self.prototypes.append(prototype)
            yield None

    def _extract_type(self, type_name: str) -> Schema.Type:
        soup = self.crawler.get("types", type_name)

        h2_text = tag(soup.find("h2")).text
        if (m := re.match(r"^" + type_name + r"\s*::\s*(.*?)\s*(Example code)?$", h2_text)) is not None:
            local_types: dict[str, Schema.TypeExpression] = {
                name: Schema.UnionTypeExpression(members=[Schema.RefTypeExpression(ref=name)])
                for name in self.all_type_names
            }

            type_expression = m.group(1).replace(" - abstract", "")
            if "struct" in type_expression:
                properties_div_soup = soup.find("div", id="attributes-body-main")
                local_types["struct"] = Schema.StructTypeExpression(
                    base=extract_struct_base(soup),
                    properties=list(extract_struct_properties(type_name, properties_div_soup, self.all_type_names)),
                    overridden_properties=[],
                    custom_properties=None,
                )

            if "union" in type_expression:
                local_types["union"] = Schema.UnionTypeExpression(
                    members=list(extract_union_members(soup, self.all_type_names))
                )

            try:
                type_expression_tree = type_expression_parser.parse(type_expression)
                return Schema.Type(
                    name=type_name,
                    definition=TypeExpressionTransformer(set(), local_types).transform(type_expression_tree),
                )
            except lark.exceptions.LarkError:
                assert False, f"failed to parse type expression: {type_expression!r}"
        elif (m := re.match(r"^" + type_name + r"\s* builtin\s*(Example code)?$", h2_text)) is not None:
            return Schema.Type(name=type_name, definition=Schema.builtin_types[type_name])
        else:
            assert False, f"failed to regex-match type header: {h2_text!r}"

    def _extract_prototype(self, prototype_name: str) -> Schema.Prototype:
        soup = self.crawler.get("prototypes", prototype_name)
        properties = list(
            extract_struct_properties(prototype_name, soup.find("div", id="attributes-body-main"), self.all_type_names)
        )

        overridden_properties_soup = soup.find("div", id="attributes-body-overridden")
        if overridden_properties_soup is None:
            overridden_properties = []
        else:
            overridden_properties = list(
                extract_struct_properties(prototype_name, overridden_properties_soup, self.all_type_names)
            )

        custom_properties_div_soup = soup.find("div", id="custom_properties")
        if custom_properties_div_soup is None:
            custom_properties: Schema.TypeExpression | Literal[False] = False
        else:
            custom_properties_text = tag(tag(tag(custom_properties_div_soup).parent).find("h3")).text
            assert custom_properties_text.startswith("Custom properties  \xa0::\xa0string → ")
            custom_properties_type_name = custom_properties_text[32:]
            custom_properties = Schema.RefTypeExpression(ref=custom_properties_type_name)

        return Schema.Prototype(
            name=prototype_name,
            key=extract_prototype_key(soup),
            base=extract_struct_base(soup),
            properties=properties,
            overridden_properties=overridden_properties,
            custom_properties=custom_properties,
        )

    def make_schema(self) -> Schema:
        return Schema(types=self.types, prototypes=self.prototypes)


def extract_union_members(
    soup: bs4.element.PageElement | None, global_types: set[str]
) -> Iterable[Schema.TypeExpression]:
    if soup is not None:
        transformer = TypeExpressionTransformer(global_types, patching.local_types_for_union)

        for span_soup in (tag(el) for el in tag(soup).find_all("span", class_="docs-attribute-name")):
            yield transformer.transform(type_expression_parser.parse(str(span_soup.text).strip()))


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

            local_types: dict[str, Schema.TypeExpression] = {}
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
                            local_types[local_type_name] = Schema.StructTypeExpression(
                                base=None,
                                properties=local_type_properties,
                                overridden_properties=[],
                                custom_properties=None,
                            )
                        case "union":
                            local_types[local_type_name] = Schema.UnionTypeExpression(
                                members=list(
                                    extract_union_members(
                                        tag(local_type_div_soup.find("h4", string="Union members")).next_sibling,
                                        global_types,
                                    )
                                )
                            )
                        case local_type_expression:
                            try:
                                local_type_expression_tree = type_expression_parser.parse(local_type_expression)
                                local_types[local_type_name] = TypeExpressionTransformer(
                                    global_types, local_types
                                ).transform(local_type_expression_tree)
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
                    property_type: Schema.TypeExpression = Schema.UnionTypeExpression(
                        members=list(
                            extract_union_members(
                                tag(property_div_soup.find("h4", string="Union members")).next_sibling, global_types
                            )
                        )
                    )
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

            yield Schema.Property(
                names=property_names, type=property_type, required=not optional and len(property_names) == 1
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


class TypeExpressionTransformer(lark.Transformer[lark.Token, Schema.TypeExpression]):
    def __init__(self, global_types: set[str], local_types: dict[str, Schema.TypeExpression]) -> None:
        self.global_types = global_types
        self.local_types = local_types

    def type_expression(self, items: list[Schema.TypeExpression]) -> Schema.TypeExpression:
        return items[0]

    def named_type(self, items: list[str]) -> Schema.TypeExpression:
        type_name = items[0]
        if type_name == "true":
            return Schema.LiteralBoolTypeExpression(value=True)
        elif type_name == "false":
            return Schema.LiteralBoolTypeExpression(value=False)
        elif type_name in self.global_types:
            return Schema.RefTypeExpression(ref=type_name)
        elif type_name in self.local_types:
            return self.local_types[type_name]
        else:
            assert False, f"unknown type: {type_name!r}"

    def literal_string(self, items: list[str]) -> Schema.TypeExpression:
        value = items[0]
        assert value.startswith('"') and value.endswith('"')
        return Schema.LiteralStringTypeExpression(value=value.strip('"'))

    def literal_integer(self, items: list[str]) -> Schema.TypeExpression:
        value = items[0]
        return Schema.LiteralIntegerTypeExpression(value=int(value))

    def array_type(self, items: list[Schema.TypeExpression]) -> Schema.TypeExpression:
        return Schema.ArrayTypeExpression(content=items[0])

    def union_type(self, items: list[Schema.TypeExpression]) -> Schema.TypeExpression:
        members: list[Schema.TypeExpression] = []
        for item in items:
            if item.kind == "union":
                members.extend(item.members)
            else:
                members.append(item)
        return Schema.UnionTypeExpression(members=members)

    def dictionary_type(self, items: list[Schema.TypeExpression]) -> Schema.TypeExpression:
        return Schema.DictionaryTypeExpression(keys=items[0], values=items[1])

    def tuple_type(self, items: list[Schema.TypeExpression]) -> Schema.TypeExpression:
        return Schema.TupleTypeExpression(members=items)

    def adhoc_type(self, items: list[str]) -> Schema.TypeExpression:
        return Schema.builtin_types["uint8"]


def tag(tag: bs4.element.PageElement | None) -> bs4.element.Tag:
    """
    Assert at runtime that a PageElement is actually a Tag.
    (Tag is a subclass of PageElement.)
    Helps with static type checking.
    """
    assert isinstance(tag, bs4.element.Tag), f"{tag!r} is not a Tag"
    return tag
