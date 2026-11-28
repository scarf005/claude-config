import os
import tempfile
import unittest

from banned_words import added, final_reply_problem


class BannedWordsTest(unittest.TestCase):
    def test_new_gate_word_in_edit_is_denied(self):
        """An edit that names a subcommand `gate` adds the word; the same text in old_string adds nothing."""
        edit = {"tool_name": "Edit", "tool_input": {"old_string": "x", "new_string": "run `term-capture.py gate`"}}
        self.assertIsNotNone(added(edit))
        same = {"tool_name": "Edit", "tool_input": {"old_string": "the gate", "new_string": "the gate."}}
        self.assertIsNone(added(same))

    def test_gated_and_gating_are_denied(self):
        for word in ("gated", "Gates", "gating"):
            self.assertIsNotNone(added({"tool_name": "Write", "tool_input": {"file_path": "/n/x.md", "content": word}}))

    def test_identifiers_joined_by_underscore_pass(self):
        """`commit_gate.py` and terrain `t_gate_metal` are one word each, so they do not match."""
        text = "see commit_gate.py and t_gate_metal, aggregate, gateway"
        self.assertIsNone(added({"tool_name": "Write", "tool_input": {"file_path": "/n/x.py", "content": text}}))

    def test_write_counts_against_the_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a.md")
            with open(path, "w") as f:
                f.write("Mandatory gates run first.")
            keep = {"tool_name": "Write", "tool_input": {"file_path": path, "content": "Mandatory gates run first!"}}
            self.assertIsNone(added(keep))
            more = {"tool_name": "Write", "tool_input": {"file_path": path, "content": "gates and a gate"}}
            self.assertIsNotNone(added(more))

    def test_commit_and_pr_text_is_checked_other_commands_are_not(self):
        bash = lambda command: {"tool_name": "Bash", "tool_input": {"command": command}}
        self.assertIsNotNone(added(bash("git commit -m 'feat: add a size gate'")))
        self.assertIsNotNone(added(bash("gh pr create -R o/r --title 'gate captures'")))
        self.assertIsNone(added(bash("rg -n gate src/")))

    def test_final_reply_with_the_word_is_blocked(self):
        self.assertIsNotNone(final_reply_problem(["`gate`(재인코딩 판정)은 개인 repo에 둬요."]))
        self.assertIsNone(final_reply_problem(["commit_gate.py 훅이 막았어요."]))


if __name__ == "__main__":
    unittest.main()
