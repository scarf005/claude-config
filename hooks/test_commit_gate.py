import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from commit_gate import COMMIT, has, main, needs_humanizer, needs_review


def use(name, **args):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": args}]}})


EDIT = use("Edit", file_path="a.ts")
STAT = use("Bash", command="git diff --shortstat upstream/main... && git diff upstream/main...")


class CommitGateTest(unittest.TestCase):
    def test_commit_commands_match_and_prose_does_not(self):
        for cmd in ["git commit -m x", "cd /r && git -c a=b -C /p commit -q", "git add a; git commit --amend",
                    "GIT_AUTHOR_DATE=x git commit", "env git commit", "git --no-pager commit",
                    "git -c user.name='a b' commit", "bash -c 'git commit -m x'", "cat <<EOF\nx\nEOF\ngit commit"]:
            self.assertTrue(has(COMMIT, cmd), cmd)
        for cmd in ["git commit-tree HEAD^{tree}", 'gh pr create --body "run git commit"', "echo git commit",
                    "python3 - <<'EOF'\ns = 'x; git commit'\nEOF"]:
            self.assertFalse(has(COMMIT, cmd), cmd)

    def test_edit_after_measurement_needs_review(self):
        self.assertTrue(needs_review([EDIT]))
        self.assertTrue(needs_review([EDIT, STAT, use("Bash", command="sed -i s/a/b/ f")]))
        self.assertTrue(needs_review([EDIT, use("Bash", command="git diff --shortstat && git commit -m x")]))
        for cmd in ["git diff --stat", "git diff --check", "git show -s HEAD", "git show HEAD:a.ts"]:
            self.assertTrue(needs_review([EDIT, use("Bash", command="git diff --shortstat; " + cmd)]), cmd)
        for cmd in ["cat > a.ts <<EOF\nx\nEOF", "git cherry-pick x", "perl -pi -e s/a/b/ f", "cp b a.ts"]:
            self.assertTrue(needs_review([EDIT, STAT, use("Bash", command=cmd)]), cmd)

    def test_measurement_after_last_edit_allows_commit(self):
        for cmd in ['rg "sed -i" docs', "make 2>&1 > /dev/null", "echo 1 -> 3", "run > /tmp/log",
                    'git commit -m "perf: x" -m "3 > 2"', "git add a && git commit -m '<b> c'",
                    'git commit -m "perf: x\n\n- a > b"']:
            self.assertFalse(needs_review([EDIT, STAT, use("Bash", command=cmd)]), cmd)
        self.assertFalse(needs_review([EDIT, use("Bash", command="git --no-pager diff --shortstat main..."),
                                       use("Bash", command="git log -p main..")]))
        self.assertFalse(needs_review([EDIT, use("Bash", command="git diff --shortstat upstream/main...HEAD"),
                                       use("Bash", command="git -C /r show HEAD")]))

    def test_shortstat_needs_the_whole_branch(self):
        for cmd in ["git diff --shortstat", "git diff --cached --shortstat", "git diff --shortstat HEAD",
                    "git diff --shortstat HEAD~1...", "git diff --shortstat @{u}..."]:
            self.assertTrue(needs_review([EDIT, use("Bash", command=cmd), STAT.replace("--shortstat", "")]), cmd)
        self.assertFalse(needs_review(["not json", "123", '{"type": "assistant", "message": "x"}',
                                       use("Bash", command=["not", "str"])]))

    def test_one_humanizer_load_covers_the_whole_session(self):
        skill = use("Skill", skill="humanizer")
        compact = json.dumps({"type": "system", "subtype": "compact_boundary"})
        self.assertTrue(needs_humanizer([EDIT]))
        self.assertFalse(needs_humanizer([EDIT, skill, STAT]))
        # The deny message asks to load the skill and then rewrite the comments; that rewrite is an edit.
        self.assertFalse(needs_humanizer([EDIT, skill, EDIT, STAT]))
        # Compaction keeps loaded skills in context.
        self.assertFalse(needs_humanizer([skill, compact, EDIT]))

    def test_denies_commit_in_other_repo_without_humanizer(self):
        # Edit README in ../other, review, then `cd ../other && git commit`: deny, though session cwd has no diff.
        def decision(lines):
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
                f.write("\n".join(lines))
                f.flush()
                stdin = json.dumps({"tool_input": {"command": "cd ../other && git commit -m x"},
                                    "transcript_path": f.name, "cwd": "/nonexistent"})
                out = io.StringIO()
                with mock.patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(out):
                    main()
            return out.getvalue()

        readme = use("Write", file_path="../other/README.md")
        self.assertIn("humanizer", decision([readme, STAT]))
        self.assertEqual("", decision([readme, use("Skill", skill="humanizer"), STAT]))


if __name__ == "__main__":
    unittest.main()
