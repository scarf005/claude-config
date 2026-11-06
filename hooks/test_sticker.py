import json
import tempfile
import unittest
from pathlib import Path

from sticker import check, inject

PACK = "/pack"
ROWS = [f"dir\t{PACK}", "001.png\tsuccess\t좋네요", "002.png\tsuccess nice\t개추", "003.png\tfail\t죄송"]


def make_dir(persona="nagisa", index=True):
    d = Path(tempfile.mkdtemp())
    (d / f"{persona}.md").write_text("voice")
    (d / "active.md").symlink_to(f"{persona}.md")
    (d / "stickers").mkdir()
    if index:
        (d / "stickers" / f"{persona}.tsv").write_text("\n".join(ROWS))
    return d


def ctx(d):
    return json.loads(inject(d))["hookSpecificOutput"]["additionalContext"]


class Inject(unittest.TestCase):
    def test_lists_every_mood_with_a_sticker_of_that_mood(self):
        lines = ctx(make_dir()).splitlines()[1:]
        self.assertEqual({l.split(":")[0] for l in lines}, {"- success", "- nice", "- fail"})
        self.assertTrue(all(l.split(": ")[1].startswith(PACK) for l in lines))
        self.assertIn("003.png", next(l for l in lines if l.startswith("- fail")))

    def test_picks_vary_between_prompts(self):
        d = make_dir()
        self.assertGreater(len({next(l for l in ctx(d).splitlines() if l.startswith("- success")) for _ in range(50)}), 1)

    def test_persona_without_index_injects_nothing(self):
        self.assertEqual(inject(make_dir("off", index=False)), "")


class Check(unittest.TestCase):
    def run_check(self, text, **extra):
        return check(make_dir(), {"last_assistant_message": text, **extra})

    def test_reply_ending_with_a_pack_sticker_passes(self):
        self.assertEqual(self.run_check(f"끝이에요\n\n{PACK}/001.png"), "")

    def test_reply_without_sticker_blocks_with_candidates(self):
        out = json.loads(self.run_check("끝이에요"))
        self.assertEqual(out["decision"], "block")
        self.assertIn(PACK, out["reason"])
        self.assertIn("only", out["reason"])

    def test_sticker_buried_above_the_tail_blocks(self):
        self.assertTrue(self.run_check(f"{PACK}/001.png\na\nb\nc"))

    def test_second_stop_does_not_block_again(self):
        self.assertEqual(self.run_check("끝이에요", stop_hook_active=True), "")

    def test_persona_without_index_never_blocks(self):
        self.assertEqual(check(make_dir("off", index=False), {"last_assistant_message": "끝"}), "")


if __name__ == "__main__":
    unittest.main()
