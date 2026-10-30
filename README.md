# Python Code Quality

This repository contains our centralized guidelines and templates for linting, formatting, and type checking in Python projects using pre-commit hooks and GitHub Actions. By implementing these standardized quality checks across all Python repositories, we ensure consistent code quality and maintainability throughout our codebase. In particular, we leverage GitHub's reusable workflows to enforce the same standards across all repositories.

> [!IMPORTANT]
> When copying (cloning) this repository, make sure to find and replace all instances of `vschelbi` with your GitHub organisation or account name.

> [!TIP]
> **Just want the hooks running in your own repository?** Read [PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md) instead — a
> short, pre-commit-only guide that skips the GitHub Actions setup entirely. The rest of this README
> is aimed at maintainers of *this* repository: changing the shared checks and cutting new releases.


## Overview

We use a two-stage approach:

1. **GitHub Actions (enforced)** - Automated checks on pull requests. It is up to the reviewers discretion to allow
                                   errors and warnings in the checks.
2. **Pre-commit hooks (optional)** - Local development assistance helping you catch issues before creating a pull
                                     request.

## Quality Checks

The configuration includes the following tools:

- **(Optional) License header** - Automatically adds copyright headers to Python files (pre-commit hooks only)
- **isort** - Automatically sorts import statements for consistent import order and grouping (`black` profile, 99-character lines)
- **black** - Opinionated code formatter with 99-character line limit
- **flake8** - Lightweight PEP 8 compliance and error detection linter (100-character limit, `E203` ignored)
- **pylint** - Comprehensive static code analysis for code smells and bugs (100-character limit)
- **mypy** - Static type checker for Python type hints

### Why we use flake8 and pylint?

While both are linters, they complement each other:

- **flake8** excels at enforcing style consistency and catching straightforward issues quickly
- **pylint** performs deeper semantic analysis to uncover design problems and subtle bugs

## Quick Start

### 1. Copy Template Files

The `templates/` folder contains all the configuration files you need to set up code quality checks in your repository. Simply copy the contents of the templates folder to your repository root:

```bash
# From your repository root, copy the template files
cp -R /path/to/python_code_quality/templates/. .
```

This will copy:

- `.github/workflows/main.yml` - GitHub Actions workflow for automated checks
- `.pre-commit-config.yaml` - Pre-commit hooks configuration

Of course, you can also manually copy the individual files if you prefer.

The `.github` folder in `templates/.github/` will not trigger GitHub Actions in this repository - it's safely nested and only becomes active when copied to your repository root.

### 2. Pin the Python and Tool Versions (required)

The GitHub Action and the pre-commit hooks must run the same Python and the same tool versions, otherwise a check
can pass locally and fail on the pull request. Each version is defined in exactly one place:

| What | Defined in | Read by |
|---|---|---|
| Python version | `.python-version` in **your** repository | `actions/setup-python` in the reusable workflow; uv and pyenv locally |
| Tool versions (pylint, mypy, black, …) | [`requirements.txt`](requirements.txt) in **this** repository, fixed by the release tag | the reusable workflow; your local environment |
| Lint rules | `.pylintrc`, `mypy*.ini` and the hook `args` in **this** repository | the reusable workflow; the pre-commit hooks |

**Python version.** Add a `.python-version` file to your repository root containing just the minor version:

```text
3.14
```

The reusable workflow fails with an explicit error if this file is missing. The pinned tools support Python 3.11 to
3.14. Python 3.15 is not supported yet: pylint crashes there in the `dill` library it uses for parallel runs.

**Tool versions.** Install the pinned tools into your environment, using the same tag as in your workflow and
`.pre-commit-config.yaml`:

```bash
pip install -r https://raw.githubusercontent.com/vschelbi/python_code_quality/v2.0.0/requirements.txt
```

Re-run this after every tag bump. The pre-commit hooks run the tools from your active environment, so they only match
CI if this environment has the pinned versions.

**Keep the tags in sync.** Your repository references this repository's tag in two places, `@v2.0.0` in
`.github/workflows/main.yml` and `rev: v2.0.0` in `.pre-commit-config.yaml`. Always bump both together.

#### Creating the environment

Plain `venv` and `pip` are the default and need nothing else installed. `python -m venv` does **not** read
`.python-version` itself, so call the matching interpreter explicitly:

```bash
python3.14 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r https://raw.githubusercontent.com/vschelbi/python_code_quality/v2.0.0/requirements.txt
```

Alternatives, if you already use them:

- **pyenv** reads `.python-version` and switches `python` to that version in your repository. Install the version once
  with `pyenv install 3.14`, then `python -m venv .venv` picks it automatically.
- **uv** (optional, not required by anything in this repository) reads `.python-version` and downloads that Python if
  it is missing. It replaces the first and last of the commands above:

  ```bash
  uv venv
  source .venv/bin/activate
  uv pip install -r https://raw.githubusercontent.com/vschelbi/python_code_quality/v2.0.0/requirements.txt
  ```

  After activating the venv, run the tools as usual (`pylint …`, `git commit`). No `uv` prefix is needed.
- **conda** ignores `.python-version`. Pass the version yourself: `conda create -n myproject python=3.14`, then
  install the pinned tools with `pip` as above.

> [!NOTE]
> An existing venv keeps the Python it was created with. After changing `.python-version`, delete and recreate it.

### 3. GitHub Actions: No Token Needed

This repository is public, so the reusable workflow checks out the shared configuration files (`.pylintrc`,
`mypy-pydantic.ini`) without any access token or secret.

If the workflow fails to start or cannot check out the shared configuration:

1. **Check repository reference**: Ensure the workflow references `vschelbi/python_code_quality/.github/workflows/main.yml@v2.0.0` (or another valid version tag)
2. **Organization policies**: Some organizations restrict which external reusable workflows may run - check with your GitHub admin

> [!NOTE]
> If you copy this repository into a **private** one, the workflow can no longer read it anonymously. Add a
> `token: ${{ secrets.<YOUR_SECRET> }}` line to the "Checkout shared config" step in
> [the reusable workflow](.github/workflows/main.yml), using a token with "Contents: Read" access to it, and enable
> sharing under Settings → Actions → General → Access
> ([GitHub Docs](https://docs.github.com/en/actions/how-tos/reuse-automations/share-across-private-repositories)).

### 4. Set up Pre-commit Hooks (optional but recommended)

> [!TIP]
> [PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md) covers this step in full detail — prerequisites, everyday use, updating,
> and troubleshooting — without any of the GitHub Actions setup.

If you haven't already copied the template files, you can manually copy the pre-commit configuration:

1. Copy [`.pre-commit-config.yaml`](templates/.pre-commit-config.yaml) from the templates folder to your repository root (or it should already be there if you followed step 1)

2. Install pre-commit:

   ```bash
   pip install pre-commit
   ```

3. Enable pre-commit hooks:

   ```bash
   pre-commit install
   ```

> [!TIP]
> If you encounter issues with pre-commit, try updating to the latest version:
>
> ```bash
> pre-commit clean
> pre-commit autoupdate
> ```

## Updating Quality Checks

To update the centralized quality checks, modify the following files:

- **GitHub Actions**: Update [the reusable workflow](.github/workflows/main.yml)
- **Pre-commit hooks**: Update [the hook definitions](.pre-commit-hooks.yaml) — hook entries, `args` and new hook ids
  go here
- **Pylint configuration**: Modify the [`.pylintrc`](.pylintrc) file
- **Tool versions**: Update the pins in [`requirements.txt`](requirements.txt). Check that every new pin still
  supports the Python versions listed in [step 2](#2-pin-the-python-and-tool-versions-required), and update that list
  if it changes
- **Scripts**: Leave the `#!/usr/bin/env python` shebangs alone — `python3` does not exist in Windows environments and
  breaks the hooks there

> [!IMPORTANT]
> The three hook scripts must stay **executable in git** (mode `100755`). pre-commit runs them directly out of its
> clone of this repository, so a `100644` mode makes every consuming repo fail with
> `Executable ... is not executable` for the `license-header`, `mypy` and `pylint` hooks. The exec bit lives in git's
> index, not in the file, so it can be lost without any visible change to the content:
>
> ```bash
> git ls-files -s -- '*.py'                                                         # all three must read 100755
> git update-index --chmod=+x add_license_header.py setup_mypy.py setup_pylint.py   # fix if not
> ```

> [!NOTE]
> Don't confuse the two pre-commit files:
>
> - [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) — the **central, reusable hook definitions** used by all
>   consuming repositories. Edit this to change the hooks everywhere.
> - [`.pre-commit-config.yaml`](.pre-commit-config.yaml) — this repository *consuming* its own hooks (a copy of
>   [`templates/.pre-commit-config.yaml`](templates/.pre-commit-config.yaml)). It only selects which hook ids run here
>   and pins the version.
>
> Changes to `.pre-commit-hooks.yaml` only reach consumers once committed and tagged. To test edits before tagging,
> run `pre-commit try-repo .`.

### Version Management

We use semantic versioning tags (e.g., `v1.0.0`, `v1.1.0`, `v2.0.0`) for version tracking to ensure stability and predictability. This prevents unexpected changes from affecting your quality checks while making it easy to identify versions.

#### Updating to a New Version

1. **For pre-commit hooks**: 
   - Update the `rev` in `.pre-commit-config.yaml` to the desired version (e.g., `v1.1.0`)
   - Or run `pre-commit autoupdate` to automatically update to the latest version

2. **For GitHub Actions**: 
   - Update the version tag in `.github/workflows/*.yml` (e.g., `@v1.0.0` → `@v1.1.0`)

To see available versions:

```bash
git ls-remote --tags https://github.com/vschelbi/python_code_quality
```

> **Important**: Using semantic version tags means updates are opt-in, giving you control over when to adopt new changes.

#### Creating New Versions

When making updates to this repository, follow semantic versioning:

- **Patch version** (v1.0.0 → v1.0.1): Bug fixes, minor config updates
- **Minor version** (v1.0.0 → v1.1.0): New features, backward-compatible changes
- **Major version** (v1.0.0 → v2.0.0): Breaking changes (e.g., Python version upgrade)

To create a new version:

1. Update version references in files (v1.0.0 → v1.0.1). There are **four** pins and all must match:
   - `templates/.pre-commit-config.yaml`: rev: v1.0.0 → v1.0.1
   - `.pre-commit-config.yaml`: rev: v1.0.0 → v1.0.1
   - `templates/.github/workflows/main.yml`: @v1.0.0 → @v1.0.1
   - `.github/workflows/main.yml`: ref: v1.0.0 → v1.0.1
   - Update the examples in README.md and PRE_COMMIT_SETUP.md, including the `requirements.txt` install URLs

   Check that none were missed:

   ```bash
   grep -rn "v[0-9]*\.[0-9]*\.[0-9]*" --include="*.yaml" --include="*.yml" --include="*.md" .
   ```

2. Stage the changes and make sure the hook scripts are still executable in git
   ```bash
   git add .
   git update-index --chmod=+x add_license_header.py setup_mypy.py setup_pylint.py
   git ls-files -s -- '*.py'   # all three must read 100755
   ```

   Do not skip this. `git add` alone drops the mode change when `core.fileMode=false`, and a script committed as
   `100644` makes every consuming repo fail with `Executable ... is not executable`.

3. Commit and push changes
   ```bash
   git commit -m "fix: update pyling config for attributes" --no-verify
   git push origin main
   ```
4. Create and push tag AFTER commit
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

This ensures the tag points to a commit that already has the correct version numbers — and the correct file modes —
in all files.

> [!NOTE]
> Consuming repositories need to do nothing beyond bumping their own `rev:` / `@version`. pre-commit caches its clone
> per `(repo, rev)` pair, so a new version tag is always fetched fresh — no `chmod`, and no `pre-commit clean`
> required on their side.

## Licensing Requirements (OPTIONAL)

Every Python file in your repository must include the following copyright header at the top:

```python
# Copyright (c) YYYY. COMPANY NAME.
# All rights reserved. Redistribution in source and/or binary forms, 
# with or without modification, is not permitted.
```

Where `YYYY` represents the year the file was originally created. If the file was modified in a different year, the header will automatically show a date range (e.g., `2024-2025`).

`COMPANY NAME` is the default placeholder. Set your own copyright holder with `--company` in your
`.pre-commit-config.yaml`:

```yaml
      - id: license-header
        args: [--company, "Acme AG"]
```

Changing the name later is safe — existing headers are rewritten rather than duplicated.

### License Header Hooks

The pre-commit configuration includes two license header hooks:

- **`license-header`** (default) - Adds missing headers and updates incorrect years
- **`license-header-force`** - Force updates ALL license headers (useful for bulk updates)

The default `license-header` hook will:

- Add license headers to files that don't have them
- Update existing headers with incorrect years (e.g., if a 2024 file now needs "2024-2025")
- Preserve existing shebang lines and place the license header appropriately

To force update all license headers (useful when changing copyright policies), uncomment the `license-header-force` hook in your `.pre-commit-config.yaml`:

```yaml
hooks:
  - id: license-header        # Add missing headers, update incorrect years
  - id: license-header-force  # Uncomment to force update ALL license headers
```

> [!WARNING]
> An `args:` list replaces the hook's defaults instead of adding to them, so combine both options in one list:
> `args: [--force-update, --company, "Acme AG"]`.

## Configuration Philosophy

### Inform-Only Approach

Our checks on pull requests are designed to be informative and not auto-fixing:

- **Fast feedback loop** - Red ❌ indicators show exactly which check failed, encouraging use of pre-commit hooks
- **Clean history** - No "style-bot" commits cluttering `git blame`; every line stays attributed to its author
- **Skill reinforcement** - Developers internalize guidelines by fixing issues themselves

## Usage

1. Copy all template files from the `templates/` folder to your Python project root
2. Follow the Quick Start guide above to configure GitHub Actions and pre-commit hooks
3. Install the required tools in your development environment
4. Commit and enjoy consistent, high-quality Python code!

## Tips

- Use `git commit --no-verify` to bypass pre-commit hooks when needed
- The GitHub Actions only run on Python file changes
- Reviewers have discretion to merge with minor warnings (but Black formatting must pass)
- If pre-commit hooks encounter errors, try `pre-commit clean` and `pre-commit autoupdate` to resolve them
