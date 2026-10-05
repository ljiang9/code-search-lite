"""命令行入口：python -m code_search <root> --ident foo | --regex 'def \\w+' | --fuzzy '...'"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .search import CodeSearcher


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="code-search", description="轻量级代码库搜索")
    ap.add_argument("root", help="要搜索的源码根目录")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ident", help="按标识符精确词边界搜索")
    g.add_argument("--regex", help="按正则表达式搜索")
    g.add_argument("--fuzzy", help="按近似文本搜索")
    ap.add_argument("--ctx", type=int, default=2, help="上下文行数（默认 2）")
    ap.add_argument("--sim", type=float, default=0.72, help="模糊匹配阈值（默认 0.72）")
    ap.add_argument("--func", action="store_true", help="同时定位所属函数/类")
    ap.add_argument("--ext", action="append", help="限定扩展名，可多次，如 --ext .py")
    args = ap.parse_args(argv)

    if not Path(args.root).exists():
        print(f"目录不存在: {args.root}", file=sys.stderr)
        return 2

    cs = CodeSearcher(args.root, ctx=args.ctx, similarity=args.sim)
    exts = {e if e.startswith(".") else "." + e for e in args.ext} if args.ext else None
    if args.ident:
        results = cs.search_identifier(args.ident, exts)
    elif args.regex:
        results = cs.search_regex(args.regex, exts)
    else:
        results = cs.search_fuzzy(args.fuzzy, exts)

    if not results:
        print("（无匹配）")
        return 1

    for r in results:
        print(f"\n=== {r.path}:{r.line}  [{r.kind}] ===")
        print(r.render(ctx=args.ctx))
        if args.func:
            fn = cs.locate_function(r)
            if fn:
                print(f"  └─ 所属: {fn}")
    print(f"\n共 {len(results)} 条命中。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
