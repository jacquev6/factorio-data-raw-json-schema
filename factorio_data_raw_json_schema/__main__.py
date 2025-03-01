import json

import click

from . import crawling
from . import extraction
from . import patching
from . import schema


@click.group()
def main() -> None:
    pass


@main.command()
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
def extract(
    doc_root: str,
    output: click.utils.LazyFile,
    do_patch: bool,
    limit_to: list[str],
    include_descendants: bool,
    forbid: list[str],
    workers: int,
) -> None:
    crawler = crawling.Crawler(doc_root)

    doc = extraction.extract(crawler=crawler, workers=workers)
    if do_patch:
        patching.patch_doc(doc)
    json_schema = schema.make_json_schema(
        doc,
        limit_to_prototype_names=limit_to or None,
        include_descendants=include_descendants,
        forbid_type_names=forbid,
    )
    json.dump(json_schema, output, indent=2)


if __name__ == "__main__":
    main()
