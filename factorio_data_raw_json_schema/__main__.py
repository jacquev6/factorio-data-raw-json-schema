from typing import TextIO
import json

import click

from . import crawling
from . import extraction
from . import patching


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
def extract(doc_root: str, output: TextIO, do_patch: bool) -> None:
    crawler = crawling.Crawler(doc_root)
    schema = extraction.extract(crawler).to_json_value()
    if do_patch:
        patching.patch(schema)
    json.dump(schema, output, indent=2)


if __name__ == "__main__":
    main()
