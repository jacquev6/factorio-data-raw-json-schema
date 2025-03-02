import json
import pickle

import click

from . import crawling
from . import extraction
from . import patching
from . import schema


@click.command(help="Generate a JSON schema for Factorio Data.raw from the Factorio Lua API documentation.")
@click.option(
    "--doc-root",
    default="https://lua-api.factorio.com/stable/",
    help="Root URL of the Factorio Lua API documentation. You may want to use something like file:///path/to/factorio/doc-html/ to avoid downloading it, or something like https://lua-api.factorio.com/2.0.28/ or https://lua-api.factorio.com/latest/ to extract from a specific version.",
    show_default=True,
)
@click.argument("output", type=click.File("w"), default="-")
@click.option(
    "--do-patch/--skip-patch",
    default=True,
    help='Apply ad-hoc patches to the schema (see "Quirks" section in the README).',
    show_default=True,
)
@click.option(
    "--strict-numbers/--lenient-numbers",
    default=False,
    help="Add strict constraints on number types (e.g. integer vs. floating point, min/max values for integers). NOT RECOMMENDED because many mods do not follow these constraints.",
    show_default=True,
)
@click.option(
    "--limit-to",
    type=str,
    multiple=True,
    help="Limit the schema to the specified prototypes. Can be specified multiple times.",
)
@click.option(
    "--include-descendants/--no-include-descendants",
    default=True,
    help="Include descendants of the specified prototypes in the schema.",
    show_default=True,
)
@click.option(
    "--forbid",
    type=str,
    multiple=True,
    help="Forbid the specified type from appearing in the schema. Can be specified multiple times.",
)
@click.option(
    "--workers", type=int, default=-1, help="Number of worker threads to use. Default is the number of CPU cores."
)
@click.option("--pickle-doc-to", type=click.File("wb"), hidden=True)
@click.option("--unpickle-doc-from", type=click.File("rb"), hidden=True)
def main(
    doc_root: str,
    output: click.utils.LazyFile,
    do_patch: bool,
    strict_numbers: bool,
    limit_to: list[str],
    include_descendants: bool,
    forbid: list[str],
    workers: int,
    pickle_doc_to: click.utils.LazyFile | None,
    unpickle_doc_from: click.utils.LazyFile | None,
) -> None:
    if unpickle_doc_from is None:
        doc = extraction.extract(crawler=crawling.Crawler(doc_root), workers=workers)
    else:
        doc = pickle.load(unpickle_doc_from)

    if pickle_doc_to is not None:
        pickle.dump(doc, pickle_doc_to)

    if do_patch:
        patching.patch_doc(doc, strict_numbers=strict_numbers)

    json_schema = schema.make_json_schema(
        doc,
        strict_numbers=strict_numbers,
        limit_to_prototype_names=limit_to or None,
        include_descendants=include_descendants,
        forbid_type_names=forbid,
    )

    json.dump(json_schema, output, indent=2)


if __name__ == "__main__":
    main()
