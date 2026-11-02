import json
import tempfile
import unittest
from pathlib import Path

from random_persona import pick


def make_dir(names):
    d = Path(tempfile.mkdtemp())
    for n in names:
        (d / f"{n}.md").write_text(f"voice of {n}")
    (d / "active.md").symlink_to("off.md")
    return d


class RandomPersona(unittest.TestCase):
    def test_off_is_never_picked(self):
        d = make_dir(["eri", "nagisa", "off"])
        self.assertTrue(all(json.loads(pick(d))["hookSpecificOutput"]["additionalContext"].find("voice of off") < 0 for _ in range(50)))

    def test_active_link_points_at_the_pick_and_context_carries_its_text(self):
        d = make_dir(["eri", "off"])
        out = json.loads(pick(d))["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SessionStart")
        self.assertEqual((d / "active.md").readlink(), Path("eri.md"))
        self.assertIn("voice of eri", out["additionalContext"])

    def test_every_candidate_can_be_picked(self):
        d = make_dir(["eri", "nagisa", "villainess", "off"])
        seen = {(d / "active.md").readlink().stem for _ in range(100) if pick(d)}
        self.assertEqual(seen, {"eri", "nagisa", "villainess"})


if __name__ == "__main__":
    unittest.main()
