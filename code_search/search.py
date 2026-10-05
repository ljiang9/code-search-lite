"""核心搜索逻辑：遍历目录源码，按标识符 / 正则 / 近似文本检索，函数级定位并展示上下文。"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


# 默认跳过的目录与扩展名（仅源码类）
SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", "node_modules",
             ".venv", "venv", "dist", "build", ".mypy_cache", ".pytest_cache"}
SOURCE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".h",
               ".cpp", ".cc", ".hpp", ".go", ".rs", ".rb", ".php", ".swift",
               ".kt", ".sh", ".bash", ".zsh", ".sql", ".html", ".css"}
DEFAULT_SIMILARITY = 0.72


@dataclass
class SearchResult:
    path: str
    line: int
    text: str
    kind: str
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)

    def render(self, ctx: int = 2) -> str:
        lines = []
        start = self.line - len(self.context_before)
        for i, ln in enumerate(self.context_before):
            lines.append(f"{start + i:>6}  {ln.rstrip()}")
        lines.append(f"{self.line:>6}: {self.text.rstrip()}")
        for i, ln in enumerate(self.context_after):
            lines.append(f"{self.line + 1 + i:>6}  {ln.rstrip()}")
        return "\n".join(lines)


def iter_source_files(root, exts=None):
    root = Path(root).resolve()
    extset = {e.lower() for e in (exts or SOURCE_EXTS)}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in extset:
                yield p


def _read_lines(p: Path):
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, UnicodeError):
        return []


def _slice_context(lines, idx, ctx):
    before = lines[max(0, idx - ctx):idx]
    after = lines[idx + 1:idx + 1 + ctx]
    return before, after


class CodeSearcher:
    def __init__(self, root, ctx=2, similarity=DEFAULT_SIMILARITY):
        self.root = Path(root).resolve()
        self.ctx = ctx
        self.similarity = similarity

    def search_identifier(self, ident, exts=None):
        pat = re.compile(rf"\b{re.escape(ident)}\b")
        out = []
        for p in iter_source_files(self.root, exts):
            lines = _read_lines(p)
            for i, ln in enumerate(lines):
                if pat.search(ln):
                    before, after = _slice_context(lines, i, self.ctx)
                    out.append(SearchResult(str(p), i + 1, ln, "identifier", before, after))
        return out

    def search_regex(self, pattern, exts=None):
        pat = re.compile(pattern)
        out = []
        for p in iter_source_files(self.root, exts):
            lines = _read_lines(p)
            for i, ln in enumerate(lines):
                if pat.search(ln):
                    before, after = _slice_context(lines, i, self.ctx)
                    out.append(SearchResult(str(p), i + 1, ln, "regex", before, after))
        return out

    def search_fuzzy(self, query, exts=None, cutoff=None):
        cutoff = self.similarity if cutoff is None else cutoff
        out = []
        q = query.strip()
        for p in iter_source_files(self.root, exts):
            lines = _read_lines(p)
            for i, ln in enumerate(lines):
                if not ln.strip():
                    continue
                score = SequenceMatcher(None, q.lower(), ln.strip().lower()).ratio()
                if score >= cutoff:
                    before, after = _slice_context(lines, i, self.ctx)
                    out.append(SearchResult(str(p), i + 1, ln,
                                            f"fuzzy({score:.2f})", before, after))
        return out

    def locate_function(self, result: SearchResult):
        lines = _read_lines(Path(result.path))
        pat = re.compile(r"^\s*(def|func|function|class)\s+(\w+)")
        nearest = None
        for i in range(result.line - 1, -1, -1):
            m = pat.match(lines[i]) if i < len(lines) else None
            if m:
                nearest = f"{m.group(1)} {m.group(2)}"
                break
        return nearest
