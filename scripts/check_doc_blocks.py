"""Check (or fix) import order inside the fenced python blocks of ``docs/``.

The docs ship copy-pasteable snippets, so a block whose imports are out of order
teaches a reader something the project's own ``ruff check`` would reject. This
script extracts every fenced ``python`` block that contains imports, runs ruff's
isort rule over all of them in a single pass, and reports the offenders.

Blocks that are teaching fragments rather than valid modules (``# ... fields
...`` placeholders, snippets indented inside an admonition) are skipped: they
cannot be parsed, so import order is not meaningful for them. A leading
``# path/to/file.py`` header comment is detached before the check and re-attached
after a fix, so isort cannot drag it down next to an import.

Usage:
    python scripts/check_doc_blocks.py          # check, exit 1 on findings
    python scripts/check_doc_blocks.py --fix    # rewrite the blocks in place
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import NamedTuple

RUFF_CONFIG = 'lint.isort.known-first-party = ["apps", "config", "blog"]'
LINE_LENGTH = "88"
BLOCK_RE = re.compile(r"```python\n(.*?)```", re.S)
DOCS = pathlib.Path("docs")


class Block(NamedTuple):
    """One fenced python block that is worth checking.

    Attributes:
        path: The markdown file the block lives in.
        index: The block's position among the file's python blocks.
        header: Leading comment/blank lines detached from the code.
        code: The block body handed to ruff.
        span: The block's ``(start, end)`` offsets inside the markdown source.
    """

    path: pathlib.Path
    index: int
    header: str
    code: str
    span: tuple[int, int]


def split_header(raw: str) -> tuple[str, str]:
    """Split a block into its leading comment header and its code.

    Args:
        raw: The full block body as written in the markdown file.

    Returns:
        A ``(header, code)`` pair; the header is empty when the block starts
        straight into code.
    """
    lines = raw.split("\n")
    header: list[str] = []
    while lines and (lines[0].startswith("#") or not lines[0].strip()):
        header.append(lines.pop(0))
    return "\n".join(header), "\n".join(lines)


def collect() -> list[Block]:
    """Collect every doc block whose import order can be checked.

    Returns:
        The parseable blocks that contain at least one import statement.
    """
    blocks: list[Block] = []
    for path in sorted(DOCS.rglob("*.md")):
        text = path.read_text()
        for index, match in enumerate(BLOCK_RE.finditer(text)):
            header, code = split_header(match.group(1))
            if "import " not in code:
                continue
            try:
                ast.parse(code)
            except SyntaxError:
                continue
            blocks.append(Block(path, index, header, code, match.span()))
    return blocks


def run_ruff(directory: pathlib.Path, fix: bool) -> str:
    """Run ruff's isort rule over every extracted block at once.

    Args:
        directory: Temporary directory holding one file per block.
        fix: Whether ruff should rewrite the files instead of only reporting.

    Returns:
        Ruff's concise stdout.
    """
    command = [
        "ruff",
        "check",
        "--isolated",
        "--config",
        RUFF_CONFIG,
        "--select",
        "I001",
        "--line-length",
        LINE_LENGTH,
        "--output-format",
        "concise",
        str(directory),
    ]
    if fix:
        command.append("--fix")
    try:
        return subprocess.run(command, capture_output=True, text=True).stdout
    except FileNotFoundError:
        print("ruff não encontrado — rode via `make docs-lint` ou `uv run`.")
        raise SystemExit(1) from None


def main() -> int:
    """Check or fix the docs' blocks and report the outcome.

    Returns:
        ``0`` when every block is sorted (or was fixed), ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="rewrite the blocks")
    args = parser.parse_args()

    blocks = collect()
    with tempfile.TemporaryDirectory() as tmp:
        directory = pathlib.Path(tmp)
        for number, block in enumerate(blocks):
            (directory / f"{number}.py").write_text(block.code)

        offenders = {
            int(line.split(":", 1)[0].rsplit("/", 1)[-1].removesuffix(".py"))
            for line in run_ruff(directory, fix=False).splitlines()
            if "I001" in line
        }
        if not offenders:
            print(f"OK: {len(blocks)} blocos de código com imports em ordem.")
            return 0

        if not args.fix:
            print(f"{len(offenders)} bloco(s) com imports fora de ordem:\n")
            for number in sorted(offenders):
                block = blocks[number]
                print(f"  {block.path}  bloco #{block.index}")
            print("\nRode: make docs-fix")
            return 1

        run_ruff(directory, fix=True)

        by_path: dict[pathlib.Path, list[int]] = {}
        for number in offenders:
            by_path.setdefault(blocks[number].path, []).append(number)

        for path, numbers in by_path.items():
            text = path.read_text()
            ordered = sorted(numbers, key=lambda n: blocks[n].span[0], reverse=True)
            for number in ordered:
                block = blocks[number]
                fixed = (directory / f"{number}.py").read_text().rstrip("\n")
                body = f"{block.header}\n{fixed}\n" if block.header else f"{fixed}\n"
                start, end = block.span
                text = text[:start] + "```python\n" + body + "```" + text[end:]
            path.write_text(text)

        print(f"Corrigidos {len(offenders)} bloco(s) em {len(by_path)} arquivo(s).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
