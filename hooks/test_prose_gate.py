import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from prose_gate import main


def use(name, **args):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": args}]}})


LOAD = use("Skill", skill="humanizer")
READ = use("Read", file_path="/home/u/.config/claude/skills/humanizer/references/patterns.md")


def decision(path, lines):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
        f.write("\n".join(lines))
        f.flush()
        stdin = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}, "transcript_path": f.name})
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(out):
            main()
    return out.getvalue()


class ProseGateTest(unittest.TestCase):
    def test_denies_readme_and_issue_form_until_skill_loaded_and_patterns_read(self):
        for path in ["/r/README.md", "/r/.github/ISSUE_TEMPLATE/loading-screen.yml"]:
            self.assertIn("load the `humanizer` skill", decision(path, []))
            self.assertIn("patterns.md", decision(path, [LOAD]))
            self.assertNotIn("patterns.md", decision(path, [READ]))
            self.assertEqual("", decision(path, [LOAD, READ]))

    def test_counts_patterns_read_through_bash(self):
        cat = use("Bash", command="cat ~/.config/claude/skills/humanizer/references/patterns.md | head -150")
        self.assertEqual("", decision("/r/docs/a.md", [LOAD, cat]))

    def test_allows_code_and_private_notes_without_skill(self):
        for path in ["/r/src/a.py", "/r/.github/workflows/ci.yml", "/h/.claude/projects/p/memory/x.md",
                     "/r/.claude/context/working-notes.md", "/tmp/scratch/notes.md"]:
            self.assertEqual("", decision(path, []), path)


if __name__ == "__main__":
    unittest.main()
