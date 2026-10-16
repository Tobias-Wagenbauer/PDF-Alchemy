# Contributing

Thanks for your interest in PDF Alchemy! This project is in its early
planning/scaffolding stage, so contributions right now are especially
valuable for shaping the foundation.

> **Note:** This project was largely written with an AI assistant ("vibe
> coded") and reviewed by the maintainer. Contributions of any kind, including
> review, cleanup and bug reports, are very welcome. If you use AI tools for
> your own contribution, please read and test the result before submitting it.

## Before you start

1. Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) to understand the
   layering (`ui/` → `services/` → `core/`) and why `core/` stays Qt-free.
2. Read [`docs/TECH_STACK.md`](docs/TECH_STACK.md) to understand which
   libraries are approved and why (licensing matters here — please don't add
   a new dependency without checking its license is MIT/BSD/LGPL-compatible,
   or raising it in an issue first).
3. Check [`docs/FEATURES.md`](docs/FEATURES.md) for the current feature
   status before starting work, to avoid duplicate effort.

## How to contribute

1. Open an issue describing the bug/feature before starting significant work,
   so the approach can be discussed first.
2. Fork the repository and create a feature branch:
   `feature/<short-description>`.
3. Keep changes focused — one feature or fix per pull request.
4. Add or update unit tests in `tests/` for any `core/` logic changes.
5. Update relevant documentation (`docs/FEATURES.md` status, `docs/CHANGELOG.md`,
   etc.) as part of the same PR.
6. Open a pull request with a clear description of what changed and why.

## Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Keep `core/` and `services/` modules free of `PySide6` imports (UI-specific
  code belongs in `ui/`).
- Prefer small, readable functions with clear names over clever one-liners.

## Reporting bugs / suggesting features

Please use GitHub Issues and include:

- What you expected to happen vs. what actually happened (for bugs)
- Steps to reproduce, if applicable
- Your OS/Python version

## Code of conduct

Be respectful and constructive. This is a small personal/open-source project
— the goal is to keep collaboration friendly and low-friction.
