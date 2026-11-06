import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from release_gate import check_release_files


class ReleaseGateTests(unittest.TestCase):
    def test_repository_passes_release_gate(self):
        self.assertEqual([], check_release_files(ROOT))

    def test_missing_evidence_fails_gate(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            self.assertTrue(check_release_files(Path(folder)))


if __name__ == "__main__":
    unittest.main()
