import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code_search.search import CodeSearcher, iter_source_files


SAMPLE = '''"""demo module."""
import os


def calculate_total(items):
    """sum items."""
    total = 0
    for it in items:
        total = total + it
    return total


class Greeter:
    def greet(self, name):
        return f"hello {name}"


def main():
    print(calculate_total([1, 2, 3]))
'''


class TestCodeSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "demo.py").write_text(SAMPLE, encoding="utf-8")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "config").write_text("calculate_total", encoding="utf-8")
        (self.root / "util.py").write_text("from demo import calculate_total\n", encoding="utf-8")
        self.cs = CodeSearcher(self.root, ctx=1)

    def tearDown(self):
        self.tmp.cleanup()

    def test_skip_dotgit(self):
        files = [p.name for p in iter_source_files(self.root)]
        self.assertNotIn("config", files)
        self.assertIn("demo.py", files)

    def test_identifier(self):
        res = self.cs.search_identifier("calculate_total")
        paths = [r.path for r in res]
        self.assertGreaterEqual(len(res), 3)
        self.assertTrue(any("demo.py" in p for p in paths))

    def test_regex(self):
        res = self.cs.search_regex(r"def\s+\w+")
        names = [r.text for r in res]
        self.assertTrue(any("def calculate_total" in n for n in names))
        self.assertTrue(any("def main" in n for n in names))

    def test_fuzzy(self):
        res = self.cs.search_fuzzy("sum items")
        self.assertGreaterEqual(len(res), 1)
        self.assertIn("sum items", res[0].text)

    def test_locate_function(self):
        res = self.cs.search_identifier("total")
        in_fn = [r for r in res if "total = total" in r.text]
        self.assertTrue(in_fn)
        fn = self.cs.locate_function(in_fn[0])
        self.assertEqual(fn, "def calculate_total")

    def test_render_context(self):
        res = self.cs.search_identifier("main")
        line = [r for r in res if "def main" in r.text]
        self.assertTrue(line)
        out = line[0].render(ctx=1)
        self.assertIn("print(calculate_total", out)


if __name__ == "__main__":
    unittest.main()
