# Contributing to nodeflowlite

Thanks for your interest in nodeflowlite! Contributions are welcome, but this
project follows a **maintainer-reviewed** model: all changes land through Pull
Requests that the maintainer reviews and merges.

## How to contribute

1. **Open an issue first** for anything non-trivial (a new feature, an API change,
   a refactor). Small fixes (typos, docs, obvious bugs) can go straight to a PR.
2. **Fork** the repository and create a branch from `main`.
3. Make your change, keeping it focused (one logical change per PR).
4. **Open a Pull Request** against `main`, describing *what* changed and *why*.
5. The maintainer reviews it. Expect questions and requested changes — the goal is
   a clean, minimal, hard-to-misuse API.

Direct pushes to `main` are not accepted: **every change goes through a PR**.

## Coding conventions

nodeflowlite follows strict conventions (see [`CLAUDE.md`](CLAUDE.md) if present, and
the existing code):

- **One class per file**; the file name equals the class name in CamelCase.
- **Interfaces** use `typing.Protocol` with an `Interface` suffix; implementations
  inherit explicitly.
- **Inversion of Control / Dependency Injection** everywhere: depend on interfaces,
  wire concretes only in the composition root.
- **Ports & Adapters**: `core/` stays framework-free (no FastAPI/DB imports); adapters
  depend inward on core interfaces, never the reverse.
- Code (comments, docstrings, messages) in **English**.

## License of contributions

By submitting a contribution, you agree that it is licensed under the project's
[Apache License 2.0](LICENSE), the same license that covers the project.

## Questions

Open an issue or start a discussion. Please be respectful and constructive.
