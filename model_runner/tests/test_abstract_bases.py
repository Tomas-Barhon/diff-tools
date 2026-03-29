import sys
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from results_collectors.base_collector import BaseCollector
from runners.base_runner import BaseRunner


class AbstractBaseTests(unittest.TestCase):
    def test_base_runner_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseRunner()

    def test_base_collector_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            BaseCollector()


if __name__ == "__main__":
    unittest.main()
