*factorio-data-raw-json-schema* provides a JSON schema for the output of `factorio --dump-data-raw`

What
====

[Factorio](https://factorio.com/) is an wonderful automation game, with extensive modding support built-in.
Mods change the game by modifying `Data.raw`, a data structure described in [the LUA API documentation](https://lua-api.factorio.com/latest/types/Data.html#raw) of the game.
Factorio provides a command-line option `--dump-data-raw` that outputs this data structure in JSON format in file `script-output/data-raw-dump.json`.

This repository provides a [JSON schema](https://json-schema.org/) for this file.

Why
===

Factorio and its mods are complex enough to motivate people to write tools to assist players.

Some awesome examples (not by me):
- [factoriolab](https://factoriolab.github.io)
- [Foreman2](https://github.com/DanielKote/Foreman2)
- [KirkMcDonald's calculator](https://kirkmcdonald.github.io)

These tools need to know the items and recipes in the game, and can obtain them using `data-raw-dump.json`.

But this file is huge and complex, and uses dynamic typing (*i.e.* many objects can have multiple types), making it difficult to process without static typing. Part of the difficulty comes from the fact that the base game does not use the full flexibility of its modding system. So if a tool handles `data-raw-dump.json` for the base game, there is no guaranty it will work with all mods.

With the JSON schemas provided by this repository, one can generate static types for the language they write their tools in.
For example, Python users can use [datamodel-codegen](https://koxudaxi.github.io/datamodel-code-generator/) to generate [Pydantic](https://docs.pydantic.dev/latest/) models or plain [dataclasses](https://docs.python.org/3/library/dataclasses.html). TypeScript users can use [json-schema-to-typescript](https://www.npmjs.com/package/json-schema-to-typescript).

Then, it's "just" a matter of validating the input file (using a JSON schema validation library) and using the data with full support for IDE autocompletion and static validation of your code. If the typing system of your language is strong enough, you'll *know* that you've handled all corner cases.

Using the schema
================

Just [download it](https://raw.githubusercontent.com/jacquev6/factorio-data-raw-json-schema/refs/heads/main/factorio-data-raw-json-schema.json) from GitHub.

How
===

This is the fun(?) part: we parse the HTML documentation. Don't look too close, you'll burn your eyes.
