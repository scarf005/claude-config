import unittest

from rm_guard import violation


class RmGuardTest(unittest.TestCase):
    def test_denies_rm_in_heredocs_remote_shells_and_wrappers(self):
        # Bash(rm:*) let the first command run: rm sat in a heredoc for the remote shell.
        for cmd in ["timeout 30 ssh phone bash <<'EOF'\nx > $TMPDIR/d.txt; rm -f $TMPDIR/d.txt\nEOF",
                    "ssh phone 'rm -rf ~/x'", "bash -c \"rm a\"", "sh -c 'cd /tmp && rm a'",
                    "find . -name x | xargs rm", "sudo rm /etc/x", "timeout 5 rm a", "/bin/rm a",
                    "\\rm a", "echo $(rm a)", "env FOO=1 rm a"]:
            self.assertIsNotNone(violation(cmd), cmd)

    def test_allows_rm_as_text_or_inside_other_command_names(self):
        for cmd in ["git rm --cached x", "tmp-rm /tmp/x", "rg -n 'rm' f", "gio trash x",
                    "echo 'do not use rm here'", "rmdir empty", "npm run rm-cache", "ls ~/rm",
                    "rg -n 'mv|rm)' f", "jq 'test(\"gio|rm\")'"]:
            self.assertIsNone(violation(cmd), cmd)


if __name__ == "__main__":
    unittest.main()
