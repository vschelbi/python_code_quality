#!/usr/bin/env python

"""
Pre-commit hook to add license headers to Python files.
"""

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from string import Template

DEFAULT_COMPANY = "COMPANY NAME"

# The two boilerplate lines below the copyright line. They double as a fingerprint for
# recognising our own header no matter which company name it was written with, so that
# changing --company rewrites the existing header instead of stacking a second one on top
# of it. Unrelated third-party copyright notices lack these lines and are left untouched.
LICENSE_BODY = """# All rights reserved. Redistribution in source and/or binary forms,
# with or without modification, is not permitted."""

LICENSE_HEADER = Template("# Copyright (c) ${years}. ${company}.\n" + LICENSE_BODY + "\n")

# Copyright line with any company name; group 1 is the year(s), group 2 the company.
COPYRIGHT_LINE_REGEX = re.compile(
    r"^# Copyright \(c\) (\d{4}(?:-\d{4})?)\. (.+)\.[ \t]*$", re.MULTILINE
)


def _find_header_match(content: str) -> re.Match[str] | None:
    """Find our license header in content, whichever company name it was written with.

    A copyright line only counts as ours when it is directly followed by our boilerplate,
    so unrelated third-party copyright notices are ignored.
    """
    for match in COPYRIGHT_LINE_REGEX.finditer(content):
        if content[match.end() :].startswith("\n" + LICENSE_BODY):
            return match
    return None


def _is_header_start(lines: list[str], idx: int) -> bool:
    """Check whether our license header starts at lines[idx], under any company name."""
    if idx >= len(lines) or not COPYRIGHT_LINE_REGEX.search(lines[idx]):
        return False
    body_lines = LICENSE_BODY.split("\n")
    return lines[idx + 1 : idx + 1 + len(body_lines)] == body_lines


def _get_git_year(file_path: Path, git_args: list[str]) -> int | None:
    """Get year from git log command, returning None if failed."""
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%ad", "--date=format:%Y"]
            + git_args
            + [str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            year_str = result.stdout.strip().split("\n")[0]
            return int(year_str)
    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    return None


def get_file_years(file_path: Path) -> str:
    """Get the appropriate year or year range for the copyright header.

    Returns the creation year, or a range if the file was modified in a different year.
    """
    current_year = datetime.now().year
    creation_year = None
    last_modified_year = None
    has_staged_changes = False

    # Check if file has staged changes (indicating current year modification)
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            has_staged_changes = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Try to get creation year from git history
    creation_year = _get_git_year(file_path, ["--reverse"])
    last_modified_year = _get_git_year(file_path, ["-1"])

    # Fallback to file modification time if git is not available or fails
    if creation_year is None:
        try:
            stat = file_path.stat()
            creation_year = datetime.fromtimestamp(stat.st_mtime).year
            last_modified_year = creation_year
        except (OSError, ValueError):
            creation_year = current_year
            last_modified_year = current_year

    # If we have git info, use last modified year, otherwise use creation year
    if last_modified_year is None:
        last_modified_year = creation_year

    # If file has staged changes, the effective last modification year is current year
    if has_staged_changes:
        last_modified_year = current_year

    # If file was created and last modified in different years, use range
    if creation_year != last_modified_year:
        return f"{creation_year}-{last_modified_year}"
    return str(creation_year)


def _read_file_content(file_path: Path) -> str | None:
    """Read file content safely, returning None on error."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None


def _write_file_content(file_path: Path, content: str) -> bool:
    """Write file content safely, returning True on success."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except IOError as e:
        print(f"Error writing {file_path}: {e}", file=sys.stderr)
        return False


def _extract_shebang_lines(lines: list[str]) -> tuple[list[str], int]:
    """Extract shebang and encoding lines from the beginning of file."""
    shebang_lines = []
    content_start_idx = 0

    for i, line in enumerate(lines):
        if (
            line.startswith("#!")
            or line.startswith("# -*- coding:")
            or line.startswith("# coding:")
        ):
            shebang_lines.append(line)
            content_start_idx = i + 1
        else:
            break

    return shebang_lines, content_start_idx


def _skip_empty_lines_after_index(lines: list[str], start_idx: int) -> int:
    """Skip empty lines starting from given index, return new index."""
    i = start_idx
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def _find_and_replace_copyright_block(
    lines: list[str], start_idx: int, correct_license: str
) -> list[str]:
    """Find existing copyright block and replace it with correct license."""
    new_lines = lines[:start_idx]
    i = start_idx

    while i < len(lines):
        line = lines[i]
        # Match the copyright line plus our boilerplate, so only our own header is replaced
        if _is_header_start(lines, i):
            # Skip the entire copyright block (3 lines)
            i += 3
            # Add the correct license header
            new_lines.extend(correct_license.split("\n"))
            # Add remaining lines
            new_lines.extend(lines[i:])
            break
        new_lines.append(line)
        i += 1

    return new_lines


def update_existing_license_header(file_path: Path, company: str) -> bool:
    """Update existing license header with correct company and year(s) if needed.

    Returns:
        True if the file was modified, False otherwise.
    """
    if not has_license_header(file_path):
        return False
    original_content = _read_file_content(file_path)

    if original_content is None:
        return False

    # Generate the correct license header
    correct_license = get_license_header(file_path, company).strip()
    lines = original_content.split("\n")

    # Skip shebang and encoding lines
    shebang_lines, content_start = _extract_shebang_lines(lines)
    new_lines = shebang_lines.copy()

    # Skip empty lines after shebang
    i = _skip_empty_lines_after_index(lines, content_start)
    new_lines.extend(lines[content_start:i])

    # Find and replace copyright block
    result_lines = _find_and_replace_copyright_block(lines, i, correct_license)
    new_content = "\n".join(result_lines)

    # Only write if content changed
    if new_content != original_content:
        return _write_file_content(file_path, new_content)

    return False


def get_license_header(file_path: Path, company: str) -> str:
    """Generate the license header with the given company and appropriate year(s)."""
    years = get_file_years(file_path)
    return LICENSE_HEADER.substitute(years=years, company=company)


def has_license_header(file_path: Path) -> bool:
    """Check if a Python file already has our license header, under any company name."""
    content = _read_file_content(file_path)
    if content is None:
        return False

    return _find_header_match(content) is not None


def _build_new_content_with_license(original_content: str, license_header: str) -> str:
    """Build new file content with license header inserted in the correct position."""
    lines = original_content.split("\n")
    shebang_lines, content_start_idx = _extract_shebang_lines(lines)

    new_content_parts = []

    # Add shebang lines if they exist
    if shebang_lines:
        new_content_parts.extend(shebang_lines)
        new_content_parts.append("")

    # Add license header
    new_content_parts.append(license_header.rstrip())
    new_content_parts.append("")  # Empty line after license

    # Add remaining content, skipping leading empty lines
    remaining_lines = lines[content_start_idx:]
    while remaining_lines and not remaining_lines[0].strip():
        remaining_lines.pop(0)

    if remaining_lines:
        new_content_parts.extend(remaining_lines)

    new_content = "\n".join(new_content_parts)

    # Ensure file ends with newline
    if new_content and not new_content.endswith("\n"):
        new_content += "\n"

    return new_content


def add_license_header(file_path: Path, company: str) -> bool:
    """Add license header to a Python file if it doesn't already exist.

    Returns:
        True if the file was modified, False otherwise.
    """
    if has_license_header(file_path):
        return False

    original_content = _read_file_content(file_path)
    if original_content is None:
        return False

    # Generate the license header with appropriate year(s)
    license_header = get_license_header(file_path, company)
    new_content = _build_new_content_with_license(original_content, license_header)

    return _write_file_content(file_path, new_content)


def _needs_header_update(file_path: Path, company: str) -> bool:
    """Check if the license header's company or year(s) need updating."""
    content = _read_file_content(file_path)
    if content is None:
        return False

    match = _find_header_match(content)

    if match:
        existing_years, existing_company = match.group(1), match.group(2)
        return existing_years != get_file_years(file_path) or existing_company != company

    # If no copyright found, it needs updating
    return True


def _process_file_dry_run(file_path: Path, company: str, force_update: bool) -> bool:
    """Process a file in dry-run mode. Returns True if file would be modified."""
    filename = str(file_path)

    if not has_license_header(file_path):
        print(f"[ ] Would add license header to: {filename}")
        return True
    if force_update:
        print(f"[ ] Would force update license header in: {filename}")
        return True
    if _needs_header_update(file_path, company):
        print(f"[ ] Would update license header in: {filename}")
        return True

    return False


def _process_file(file_path: Path, company: str, force_update: bool) -> bool:
    """Process a file for real. Returns True if file was modified."""
    filename = str(file_path)

    if not has_license_header(file_path):
        if add_license_header(file_path, company):
            print(f"[x] Added license header to: {filename}")
            return True
    if force_update:
        if update_existing_license_header(file_path, company):
            print(f"[x] Force updated license header in: {filename}")
            return True
    # Try to update existing header
    if update_existing_license_header(file_path, company):
        print(f"[x] Updated license header in: {filename}")
        return True

    return False


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the license header hook."""
    parser = argparse.ArgumentParser(description="Add license headers to Python files")
    parser.add_argument("filenames", nargs="*", help="Filenames to check and potentially modify")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be modified without making changes",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Update all license headers even if they already exist",
    )
    parser.add_argument(
        "--company",
        default=DEFAULT_COMPANY,
        help=f"Copyright holder to write into the header (default: {DEFAULT_COMPANY!r})",
    )

    args = parser.parse_args(argv)
    modified_files = []

    for filename in args.filenames:
        file_path = Path(filename)

        # Skip non-Python files or non-existent files
        if file_path.suffix != ".py" or not file_path.exists():
            continue

        if args.dry_run and _process_file_dry_run(file_path, args.company, args.force_update):
            modified_files.append(filename)
        elif _process_file(file_path, args.company, args.force_update):
            modified_files.append(filename)

    if modified_files:
        count = len(modified_files)
        action = "would be updated" if args.dry_run else "Successfully updated"
        print(f"\nSummary: {action} {count} file{'s' if count != 1 else ''}")
        return 1  # Return 1 to indicate files were modified (pre-commit convention)

    return 0


if __name__ == "__main__":
    sys.exit(main())
