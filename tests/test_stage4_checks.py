from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_stage4 import _digest


class Stage4CheckTests(unittest.TestCase):
    def test_sql_digest_is_the_same_for_lf_and_crlf(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            lf = root / "lf.sql"
            crlf = root / "crlf.sql"
            lf.write_bytes(b"select 1;\nselect 2;\n")
            crlf.write_bytes(b"select 1;\r\nselect 2;\r\n")
            self.assertEqual(_digest(lf), _digest(crlf))


if __name__ == "__main__":
    unittest.main()
