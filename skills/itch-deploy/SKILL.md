---
name: itch-deploy
description: Upload a game to itch.io with butler or set up its CI deploy. Use when asked to publish, upload or deploy to itch.io, when a workflow needs BUTLER_API_KEY, or when `butler push` or `butler status` fails.
---

# itch.io deploy

Account `scarf005`, web channel `html5`. Check a game with `butler status scarf005/<game>`.

1. Set the CI secret with `~/.local/bin/setup-itch.io.rk [OWNER/REPO]`. It sets `BUTLER_API_KEY` through `gh` for the current or named repository, and replaces any value there.
2. The script asks for the key at a hidden terminal prompt and refuses other input. The key for `butler` is in `~/.config/itch/butler_creds`; never print it. A new key comes from https://itch.io/user/settings/api-keys.
3. Upload from this machine with `butler push <dir> scarf005/<game>:html5 --userversion <version>`. The directory holds `index.html` at its root.
4. In CI, copy the `itch-publish` step from `~/repo/head-full-of-flowers/.github/workflows/deploy.yml`.

`invalid game` from `butler` means the page does not exist. `butler` and the script cannot create a page. The user creates it at https://itch.io/game/new with kind HTML; a draft accepts uploads.
