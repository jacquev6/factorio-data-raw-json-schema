import json
from typing import TextIO

import click

from . import extraction
from . import patching


@click.group()
def main() -> None:
    pass


@main.command()
# @todo Replace factorio-location by a --doc-root option defaulting to https://lua-api.factorio.com/stable/ and suggesting the use of file:///path/to/factorio/doc-html/
@click.argument("factorio-location", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True)
@click.argument("output", type=click.File("w"), default="-")
@click.option(
    "--do-patch/--skip-patch",
    default=True,
    help='Apply ad-hoc patches to the schema (see "Quirks" section in the README)',
    show_default=True,
)
def extract(factorio_location: str, output: TextIO, do_patch: bool) -> None:
    schema = extraction.extract(factorio_location)
    if do_patch:
        patching.patch(schema)
    json.dump(schema, output, indent=2)


if __name__ == "__main__":
    main()
