import tempfile
import unittest
from pathlib import Path

from vpc_graph.discovery import discover_log_files, expand_inputs


def touch(root: Path, relative: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    return path


class DiscoverLogFilesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_finds_minute_chunks_across_days_and_vpcs(self):
        expected = [
            touch(self.root, "vpc-0a1b2c3d/2026/07/01/00-00.log"),
            touch(self.root, "vpc-0a1b2c3d/2026/07/01/00-05.log"),
            touch(self.root, "vpc-0a1b2c3d/2026/07/02/09-30.log"),
            touch(self.root, "vpc-9z8y7x6w/2026/06/30/23-55.log"),
        ]
        self.assertEqual(discover_log_files(self.root), sorted(expected))

    def test_results_are_sorted_chronologically_within_a_vpc(self):
        touch(self.root, "vpc-a/2026/07/02/00-00.log")
        touch(self.root, "vpc-a/2026/07/01/23-55.log")
        names = [p.relative_to(self.root).as_posix() for p in discover_log_files(self.root)]
        self.assertEqual(
            names,
            ["vpc-a/2026/07/01/23-55.log", "vpc-a/2026/07/02/00-00.log"],
        )

    def test_skips_invalid_date_folders(self):
        touch(self.root, "vpc-a/notayear/07/01/00-00.log")
        touch(self.root, "vpc-a/2026/13/01/00-00.log")
        touch(self.root, "vpc-a/2026/07/32/00-00.log")
        good = touch(self.root, "vpc-a/2026/07/01/00-00.log")
        self.assertEqual(discover_log_files(self.root), [good])

    def test_skips_log_files_at_wrong_depth(self):
        touch(self.root, "stray.log")
        touch(self.root, "vpc-a/2026/07/stray.log")
        touch(self.root, "vpc-a/2026/07/01/extra/stray.log")
        good = touch(self.root, "vpc-a/2026/07/01/00-00.log")
        self.assertEqual(discover_log_files(self.root), [good])

    def test_ignores_non_log_files(self):
        touch(self.root, "vpc-a/2026/07/01/notes.txt")
        self.assertEqual(discover_log_files(self.root), [])

    def test_empty_root(self):
        self.assertEqual(discover_log_files(self.root), [])


class ExpandInputsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_mixes_plain_files_and_folders(self):
        plain = touch(self.root, "single.log")
        tree = self.root / "tree"
        chunk = touch(self.root, "tree/vpc-a/2026/07/01/00-00.log")
        self.assertEqual(expand_inputs([plain, tree]), [plain, chunk])

    def test_empty_folder_contributes_nothing(self):
        (self.root / "empty").mkdir()
        self.assertEqual(expand_inputs([self.root / "empty"]), [])


if __name__ == "__main__":
    unittest.main()
