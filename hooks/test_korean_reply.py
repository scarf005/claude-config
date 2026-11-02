import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from korean_reply import is_english

HOOK = Path(__file__).with_name("korean_reply.py")
STICKER = "/home/scarf/사진/corn/에리콘 DX/025.png"
ENGLISH = f"""Partly. The tests cover appended payloads and unrelated bytes. They don't test a real foreign file renamed to `.mo`, such as an ELF, a shell script or a ZIP.

**Covered**
- **Appended payload:** `MZ payload` after a valid catalog fails (`test_trailing_bytes_fail`).

**Not covered**
- **Foreign file types:** the code rejects them through the magic-number check, but no test feeds one.
- **Polyglot files:** a `.mo` that is also valid as another format.

I can add tests for the foreign-header, hostile-offset and polyglot cases.

{STICKER}"""
KOREAN = f"""찾아봤는데 `parse_mo`는 `test_trailing_bytes_fail`에서 MZ payload 뒤 바이트를 거부한다요.
`validate_mo.py`의 `validate` 함수가 magic number와 offset table을 검사한다요.

{STICKER}"""


def run_hook(transcript, last=None):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d, "t.jsonl")
        path.write_text("".join(json.dumps(e) + "\n" for e in transcript), encoding="utf-8")
        event = {"transcript_path": str(path), "stop_hook_active": False}
        if last is not None:
            event["last_assistant_message"] = last
        return subprocess.run([sys.executable, "-B", str(HOOK)], input=json.dumps(event),
                              capture_output=True, text=True, check=True).stdout


def user(text):
    return {"type": "user", "message": {"content": text}}


def assistant(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


class IsEnglish(unittest.TestCase):
    def test_english_reply_with_hangul_sticker_path_is_english(self):
        self.assertTrue(is_english(ENGLISH))

    def test_korean_reply_with_sticker_path_is_korean(self):
        self.assertFalse(is_english(KOREAN))

    def test_korean_reply_with_many_identifiers_is_korean(self):
        self.assertFalse(is_english("`foo_bar`, `baz_qux`, `parse_mo`, `validate` 함수를 고쳤다요."))


class Main(unittest.TestCase):
    def test_blocks_last_assistant_message_missing_from_transcript(self):
        self.assertIn('"block"', run_hook([user("q")], last=ENGLISH))

    def test_blocks_english_reply_in_transcript(self):
        self.assertIn('"block"', run_hook([user("q"), assistant(ENGLISH)]))

    def test_passes_korean_last_assistant_message(self):
        self.assertEqual(run_hook([user("q"), assistant(KOREAN)], last=KOREAN), "")


if __name__ == "__main__":
    unittest.main()
