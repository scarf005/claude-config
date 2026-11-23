import json
import tempfile
import unittest
from pathlib import Path

from sticker import check, inject

PACK = "/pack"
OTHER = "/other pack"
ROWS = [f"dir\t{PACK}", "001.png\tsuccess\t좋네요", "002.png\tsuccess nice\t개추", "003.png\tfail\t죄송"]


def make_dir(persona="nagisa", index=True):
    d = Path(tempfile.mkdtemp())
    (d / f"{persona}.md").write_text("voice")
    (d / "active.md").symlink_to(f"{persona}.md")
    (d / "stickers").mkdir()
    if index:
        (d / "stickers" / f"{persona}.tsv").write_text("\n".join(ROWS))
    (d / "stickers" / "eri.tsv").write_text("\n".join(ROWS).replace(PACK, OTHER))
    return d


def session(d, persona, sid="sid"):
    (d / "s").mkdir(exist_ok=True)
    (d / "s" / sid).write_text(persona)


def ctx(d, sid="sid"):
    return json.loads(inject(d, d / "s", {"session_id": sid}))["hookSpecificOutput"]["additionalContext"]


def sections(d):
    out, name = {}, None
    for l in ctx(d).splitlines()[1:]:
        if l.endswith(":") and not l.startswith("-"):
            name = out.setdefault(l[:-1], [])
        else:
            name.append(l)
    return out


class Inject(unittest.TestCase):
    def test_lists_every_mood_with_a_sticker_of_that_mood(self):
        lines = sections(make_dir())["nagisa"]
        self.assertEqual({l.split(":")[0] for l in lines}, {"- success", "- nice", "- fail"})
        self.assertTrue(all(l.split(": ")[1].startswith(PACK) for l in lines))
        self.assertIn("003.png", next(l for l in lines if l.startswith("- fail")))

    def test_lists_only_the_pack_of_the_active_persona(self):
        self.assertEqual(set(sections(make_dir())), {"nagisa"})

    def test_session_persona_wins_over_the_shared_link(self):
        d = make_dir()
        session(d, "eri")
        out = sections(d)
        self.assertEqual(set(out), {"eri"})
        self.assertTrue(all(l.split(": ")[1].startswith(OTHER) for l in out["eri"]))

    def test_picks_vary_between_prompts(self):
        d = make_dir()
        self.assertGreater(len({next(l for l in ctx(d).splitlines() if l.startswith("- success")) for _ in range(50)}), 1)

    def test_output_only_prompt_asks_for_no_stickers(self):
        d = make_dir()
        for prompt in ["show the diff", "로그 출력해 주세요", "결과만 보여주세요", "print only the path"]:
            out = json.loads(inject(d, d / "s", {"session_id": "sid", "prompt": prompt}))
            self.assertNotIn(PACK, out["hookSpecificOutput"]["additionalContext"], prompt)

    def test_persona_without_index_injects_nothing(self):
        self.assertEqual(inject(d := make_dir("off", index=False), d / "s", {}), "")


class Check(unittest.TestCase):
    def run_check(self, text, **extra):
        return check(d := make_dir(), d / "s", {"last_assistant_message": text, **extra})

    def test_reply_ending_with_a_pack_sticker_passes(self):
        self.assertEqual(self.run_check(f"끝이에요\n\n{PACK}/001.png"), "")

    def test_reply_without_sticker_blocks_with_index_path(self):
        d = make_dir()
        out = json.loads(check(d, d / "s", {"last_assistant_message": "끝이에요"}))
        self.assertEqual(out["decision"], "block")
        self.assertIn(f"{d}/stickers/nagisa.tsv", out["reason"])
        self.assertNotIn("001.png", out["reason"])
        self.assertIn("only", out["reason"])

    def test_sticker_of_another_persona_pack_blocks(self):
        self.assertTrue(self.run_check(f"끝이에요\n\n{OTHER}/001.png"))

    def test_sticker_buried_above_the_tail_blocks(self):
        self.assertTrue(self.run_check(f"{PACK}/001.png\na\nb\nc"))

    def test_second_stop_does_not_block_again(self):
        self.assertEqual(self.run_check("끝이에요", stop_hook_active=True), "")

    def test_reply_to_output_only_prompt_passes_and_next_prompt_blocks_again(self):
        d = make_dir()
        inject(d, d / "s", {"session_id": "sid", "prompt": "show the diff"})
        self.assertEqual(check(d, d / "s", {"session_id": "sid", "last_assistant_message": "diff"}), "")
        inject(d, d / "s", {"session_id": "sid", "prompt": "훅 충돌도 고쳐주세요"})
        self.assertTrue(check(d, d / "s", {"session_id": "sid", "last_assistant_message": "끝이에요"}))

    def test_persona_without_index_never_blocks(self):
        self.assertEqual(check(d := make_dir("off", index=False), d / "s", {"last_assistant_message": "끝"}), "")


if __name__ == "__main__":
    unittest.main()
