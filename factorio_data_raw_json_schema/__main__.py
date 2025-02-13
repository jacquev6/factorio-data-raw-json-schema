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
def extract(factorio_location: str, output: TextIO) -> None:
    schema = extraction.extract(factorio_location)
    json.dump(schema, output, indent=2)


@main.command()
@click.argument("input", type=click.File("r"), default="-")
@click.argument("output", type=click.File("w"), default="-")
def patch(input: TextIO, output: TextIO) -> None:
    schema = json.load(input)
    patching.patch(schema)
    json.dump(schema, output, indent=2)


if __name__ == "__main__":
    main()
