import os
import shutil
from typing import Any, Callable, Iterable
import json
import typing

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
    "--split/--no-split", default=False, help="Split the schema into multiple files, one per type.", show_default=True
)
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
    "--workers", type=int, default=-1, help="Number of worker threads to use. Default is the number of CPU cores."
)
def extract(
    doc_root: str,
    output: click.utils.LazyFile,
    split: bool,
    do_patch: bool,
    limit_to: list[str],
    include_descendants: bool,
    workers: int,
) -> None:
    crawler = crawling.Crawler(doc_root)

    # @todo Add --forbid flag to list types that are excluded from the schema. E.g. --forbi Sound --forbid Sprite would remove all attributes related to these types
    
    if split:
        definitions_dir = os.path.splitext(output.name)[0]
        shutil.rmtree(definitions_dir, ignore_errors=True)
        os.makedirs(definitions_dir, exist_ok=True)
        make_reference: Callable[[bool, str], str] | None = (
            lambda deep, name: f"{'../' if deep else ''}{definitions_dir}/{name}.json"
        )
    else:
        make_reference = None

    schema = extraction.extract(crawler=crawler, workers=workers)
    if do_patch:
        patching.patch_schema(schema)
    json_schema = schema.to_json(
        make_reference=make_reference, limit_to=limit_to or None, include_descendants=include_descendants
    )
    if split:
        assert make_reference is not None
        definitions = typing.cast(dict[str, dict[str, Any]], json_schema.pop("definitions"))
        for name, value in definitions.items():
            with open(make_reference(False, name), "w") as f:
                json.dump({"$schema": json_schema["$schema"]} | value, f, indent=2)
    json.dump(json_schema, output, indent=2)


if __name__ == "__main__":
    main()
