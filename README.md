*factorio-data-raw-json-schema* provides JSON schemas for the output of `factorio --dump-data-raw`

What
====

[Factorio](https://factorio.com/) is an wonderful automation game, with extensive modding support built-in.
Mods change the game by modifying `Data.raw`, a data structure described in [the LUA API documentation](https://lua-api.factorio.com/latest/types/Data.html#raw) of the game.
Factorio provides a command-line option `--dump-data-raw` that outputs that data structure in JSON format to the file `script-output/data-raw-dump.json`.

This project provides [JSON schemas](https://json-schema.org/) for that file.

Why
===

Factorio and its mods are complex enough to motivate people to write tools to assist players.

Some awesome examples (not by me):
- [factoriolab](https://factoriolab.github.io)
- [Foreman2](https://github.com/DanielKote/Foreman2)
- [KirkMcDonald's calculator](https://kirkmcdonald.github.io)

These tools need to know the items, recipes, *etc.* in the game, and can obtain them using `data-raw-dump.json`.

But that file is huge and complex, and uses dynamic typing (*i.e.* many objects can have multiple types), making it error-prone to process without static typing.
Part of the difficulty comes from the fact that the base game does not use the full flexibility of its own modding system.
So if a tool handles `data-raw-dump.json` for the base game, there is no guaranty it will work with all mods.

With the JSON schemas provided by this project, one can generate static types for the language they write their tools in.
For example, Python users can use [datamodel-codegen](https://koxudaxi.github.io/datamodel-code-generator/) to generate [Pydantic](https://docs.pydantic.dev/latest/) models or plain [dataclasses](https://docs.python.org/3/library/dataclasses.html).
TypeScript users can use [json-schema-to-typescript](https://www.npmjs.com/package/json-schema-to-typescript).

Then, it's "just" a matter of validating the input file (using a JSON schema validation library) and using the data with full support for IDE autocompletion and static validation of your code.
If the typing system of your language is strong enough, you'll *know* that you've handled all corner cases.

Using the schema
================

The full schema
---------------

Just [download it](https://raw.githubusercontent.com/jacquev6/factorio-data-raw-json-schema/refs/heads/main/factorio-data-raw-json-schema.full.json) from GitHub.

The full schema is quite large, and validation against that schema can be quite long.
See next section if this becomes an issue for you.

Partial schemas
---------------

To generate your own schemas, because I have not (yet?) published the package on PyPI, you'll need to `git clone` the repository, then create a virtual environment (`python -m venv .venv`), activate it (`source .venv/bin/activate`) and install the depenceies (`pip install -r requirements.txt`).
You should then be able to run `python -m factorio_data_raw_json_schema --help`.

This project provides two ways to generate *partial* schemas:

- include only some prototypes
- forbid properties of some types

So if you need items and recipes, and don't care about sounds and sprites, you may want to generate a schema with:

    python -m factorio_data_raw_json_schema extract \
      --limit-to Recipe --limit-to Item \
      --forbid SoundDefinition --forbid SpriteSource

(This will also include prototypes derived from `ItemPrototype` or `RecipePrototype`.)

Quirks
======

`data-raw-dump.json` does not conform strictly to the API documentation.
For example, some empty arrays are serialized as `{}`, which in JSON means "empty object".
The schemas produced by this project account for these quirks.

They are documented in [`patching.py`](factorio_data_raw_json_schema/patching.py) and will soon be reported to [the Factorio forum](https://forums.factorio.com/viewforum.php?f=7).

Contribute
==========

Questions, remarks, bugs? [Open an issue](https://github.com/jacquev6/factorio-data-raw-json-schema/issues) or [start a discussion](https://github.com/jacquev6/factorio-data-raw-json-schema/discussions)!

I'm especially interested in the following topics:

- if you find out that the schemas could be stricter, and you can justify that by pointing at the API documentation
- if you find out that the schemas are too strict, and you can provide a `mod-list.json` file that produces a `data-raw-dump.json` that doesn't validate against a generated schema

How
===

This is the fun part: we parse the HTML API documentation.
Like all good things Factorio, this project may be slightly over-engineered.

`documentation.py` provides classes that model the content of the API documentation.
`extraction.py` parses the HTML to create a `documentation.Doc`.
That object is then processed by `schema.py` to create a JSON schema.
`__main__.py` orchestrates all that.
