"""Run the independent coordinator fixtures; public/hidden accuracy is separate."""
from pathlib import Path
import unittest


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1] / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
