import sys
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from results_collectors.regex_collector import RegexCollector


class RegexCollectorTests(unittest.TestCase):
    def test_collect_returns_all_single_group_matches(self):
        collector = RegexCollector(r"value: (-?\d+(?:\.\d+)?)")
        output = "first\nvalue: 1.25\nvalue: -3\n"

        self.assertEqual(collector.collect(output), ["1.25", "-3"])

    def test_collect_returns_first_group_from_multi_group_match(self):
        collector = RegexCollector(r"(score): (-?\d+(?:\.\d+)?)")
        output = "score: 42\n"

        self.assertEqual(collector.collect(output), ["score"])

    def test_collect_returns_empty_when_no_match(self):
        collector = RegexCollector(r"mean: (-?\d+(?:\.\d+)?)")
        output = "nothing here"

        self.assertEqual(collector.collect(output), [])


if __name__ == "__main__":
    unittest.main()
