# Pre-commit Setup

**For developers who just want the shared code-quality hooks running in their own repository.**

This guide covers *only* the local pre-commit hooks. You can ignore everything about GitHub Actions and reusable
workflows — none of that is needed to run the hooks locally. (If you *also* want the same checks enforced on pull
requests later, see [README.md](README.md); it is independent of this setup and can be added at any time.)

> [!IMPORTANT]
> If your organisation or account is not `vschelbi`, replace `vschelbi` with the correct one in every command and
> snippet below.

## What you get

Six hooks, run automatically on the Python files you are about to commit:

| Hook | What it does | Modifies your files? |
|---|---|---|
| `isort` | Sorts and groups imports (`black` profile, 99-char lines) | Yes |
| `black` | Formats code to 99-char lines | Yes |
| `flake8` | PEP 8 / error linting (100-char limit, `E203` ignored) | No — reports only |
| `mypy` | Static type checking against the shared config | No — reports only |
| `pylint` | Deeper static analysis against the shared `.pylintrc` | No — reports only |
| `license-header` | Adds copyright headers (optional, off by default) | Yes |

The 99 vs 100 gap is intentional: black formats to 99, the linters allow 100, so black-formatted code never trips
them.

The `mypy` and `pylint` hooks bring the shared configuration with them — you do **not** need to copy `.pylintrc`,
`mypy.ini`, or `mypy-pydantic.ini` into your repository. They are read from the pinned version of this repository.
(`mypy` automatically uses the pydantic-aware config when `pydantic` is importable in your environment.)

## Prerequisites

The hooks run the linters from **your active Python environment** rather than installing their own isolated copies.
So the tools must be installed in the environment you commit from (your conda env, venv, …):

```bash
pip install -r https://raw.githubusercontent.com/vschelbi/python_code_quality/v2.0.0/requirements.txt
```

This installs the tool versions pinned for that release, the same ones the GitHub Action uses. Use the same tag as
the `rev:` in your config, and re-run it after every `rev:` bump. Create the environment with the Python version from
your repository's `.python-version` file; [README.md](README.md#creating-the-environment) shows how with venv, pyenv,
uv or conda.

If your repository is a uv project with a `uv.lock`, skip the `pip install` above: `uv sync` would remove the tools
again. Pin them in your `pyproject.toml` instead, as shown in
[README.md](README.md#projects-managed-with-uv-uvlock).

If a tool is missing you will get a `command not found` / `mypy not found` error from the corresponding hook, not a
lint failure.

The hooks work the same on **Linux, macOS and Windows** — the shared scripts are plain Python and only ever shell out
to `git`.

The one requirement that matters on every platform: **use a venv or conda env, and have it active in the shell you
commit from.** The `mypy`, `pylint` and `license-header` hooks run through `#!/usr/bin/env python`, so they use the
first `python` on `PATH`, and *that* interpreter is the one which must be able to import `mypy` and `pylint`. Every
venv and conda env provides a `python`, on all three platforms.

Platform notes:

- **macOS** — there is no `/usr/bin/python` on macOS 12.3 and later, so an activated environment is *not* optional
  here. Installing the linters into bare Homebrew Python with `pip install --user` and no environment will fail with
  `env: python: No such file or directory`.
- **macOS / Linux** — a GUI git client launched from Finder or a desktop launcher does not inherit your shell's
  `PATH`, so hooks can fail there while working fine in a terminal.
- **Windows** — works normally. pre-commit reads the shebang itself rather than relying on the OS, so no extra setup
  is needed beyond an activated environment.

## Setup

### 1. Add the config file

Create `.pre-commit-config.yaml` in the **root of your repository** with this content:

```yaml
repos:
  - repo: https://github.com/vschelbi/python_code_quality
    rev: v2.0.0  # Pin to a specific version for stability
    hooks:
      # - id: license-header        # Optional, see below
      - id: isort
      - id: black
      - id: flake8
      - id: mypy
      - id: pylint
```

You can also copy it from this repository instead of typing it out — it is
[`templates/.pre-commit-config.yaml`](templates/.pre-commit-config.yaml).

Comment out any hook you do not want. Order matters for the two formatters: `isort` before `black`.

### 2. Install the git hook

From your repository root:

```bash
pre-commit install
```

This writes a `.git/hooks/pre-commit` script. It is a one-time, per-clone step — everyone working on the repository
has to run it themselves, and it needs re-running after a fresh clone.

### 3. Check it works

```bash
pre-commit run --all-files
```

The first run clones and caches this repository (into `~/.cache/pre-commit`), so it takes a few seconds longer than
later runs. On an existing codebase expect isort/black to reformat a lot and pylint/mypy to report plenty — that is
normal, and fixing it is a separate decision from setting up the hooks.

## Everyday use

Once installed, `git commit` runs the hooks on your **staged** `.py` files only.

- **A formatter changed your files** (`isort`, `black`) — the commit is aborted and the reformatted files are left in
  your working tree, unstaged. Review, `git add` them, and commit again. This is expected behaviour, not an error.
- **A linter failed** (`flake8`, `mypy`, `pylint`) — the commit is aborted and nothing was changed. Fix the reported
  issues yourself.
- **Bypass the hooks for one commit:**

  ```bash
  git commit --no-verify -m "wip"
  ```

- **Run a single hook, or run everything manually:**

  ```bash
  pre-commit run pylint --all-files
  pre-commit run --all-files
  ```

Hooks only look at Python files, so commits touching only docs, YAML, or data pass straight through.

## Updating to a newer version

The `rev:` in your config is a fixed tag, so nothing about your checks changes until you decide to update — updates
are opt-in.

To see what is available:

```bash
git ls-remote --tags https://github.com/vschelbi/python_code_quality
```

Then either edit `rev:` in your `.pre-commit-config.yaml` by hand, or let pre-commit move it to the latest tag:

```bash
pre-commit autoupdate
```

Commit the resulting change to `.pre-commit-config.yaml` so your whole team moves together. Then re-install the tools
from the new tag's `requirements.txt` (see [Prerequisites](#prerequisites)), since a new tag can pin new versions.

## Optional: license headers

Uncomment `- id: license-header` in your config to have copyright headers added to Python files that lack them (and
have the year corrected on files that already have one):

```python
# Copyright (c) 2026. Acme AG.
# All rights reserved. Redistribution in source and/or binary forms,
# with or without modification, is not permitted.
```

**Set your own copyright holder** with `--company`, otherwise the header is written with the placeholder
`COMPANY NAME`:

```yaml
      - id: license-header
        args: [--company, "Acme AG"]
```

The year is derived per file from git history — the creation year, or a range like `2024-2026` if the file has been
modified in a later year.

There is also `- id: license-header-force`, which rewrites **all** headers rather than just missing or outdated ones
— useful as a one-off for a bulk change, and best commented out again afterwards. Because an `args:` override
*replaces* the hook's defaults rather than adding to them, you must repeat `--force-update` if you also pass
`--company`:

```yaml
      - id: license-header-force
        args: [--force-update, --company, "Acme AG"]
```

> [!NOTE]
> Changing `--company` later is safe: an existing header is rewritten in place rather than a second one being added
> on top. Recognition is based on the two boilerplate lines, not the company name, so unrelated third-party
> copyright notices in vendored files are left alone.

> [!TIP]
> The hooks only touch files you are committing. To stamp an existing codebase in one go, run
> `pre-commit run license-header --all-files`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found`, or `Error: mypy not found` | The tool is missing from your active environment — see [Prerequisites](#prerequisites). Also check you activated the right env. |
| `env: python: No such file or directory` (macOS) | No `python` on `PATH` — macOS 12.3+ has no `/usr/bin/python`. Activate a venv or conda env, which always provides one. |
| Hooks pass in a terminal but fail in a GUI git client | The GUI app does not inherit your shell `PATH`, so it cannot find `python` or the linters. Commit from a terminal, or launch the client from a terminal with the env activated. |
| Hooks do not run on commit at all | `pre-commit install` was never run in this clone, or you are committing with `--no-verify`. |
| Stale or corrupted hook cache, weird errors after a version bump | `pre-commit clean`, then re-run. |
| `rev` no longer resolves | The tag was removed or renamed — pick a current one via `git ls-remote --tags …`. |
| Reformatting fights with your editor | Point your editor's black/isort at 99-character lines so it agrees with the hooks. |
