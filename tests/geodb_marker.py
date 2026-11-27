"""Marker for tests that need the gitignored data/geodata.db."""
import pytest

from pipeline.geo import DEFAULT_DB_PATH

# data/geodata.db is gitignored (127 MB, built by scripts/build_geodata.py): fresh clones, worktrees and CI lack it.
# Tests that resolve real places skip there instead of failing with misleading geo assertions.
needs_geodb = pytest.mark.skipif(not DEFAULT_DB_PATH.exists(),
                                 reason="needs data/geodata.db (gitignored; build it with scripts/build_geodata.py)")
