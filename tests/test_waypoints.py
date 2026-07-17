import tempfile
import unittest
from pathlib import Path

from silkroad.waypoints import ensure_waypoint, read_waypoint_marker


class WaypointTests(unittest.TestCase):
    def test_ensure_waypoint_installs_marker_and_standard_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            waypoint = Path(tmp) / "installed-waypoint"
            ensure_waypoint(waypoint, "installed")

            self.assertTrue((waypoint / "waystation.json").exists())
            self.assertTrue((waypoint / "signposts").is_dir())
            self.assertTrue((waypoint / "cache").is_dir())
            self.assertTrue((waypoint / "bazaar").is_dir())

            marker = read_waypoint_marker(waypoint)
            self.assertEqual(marker["type"], "waystation")
            self.assertEqual(marker["name"], "installed")


if __name__ == "__main__":
    unittest.main()
