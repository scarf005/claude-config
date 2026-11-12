# scan every commit and the tracked files for secrets
audit:
    go run github.com/zricethezav/gitleaks/v8@v8.30.0 git --redact --no-banner .

# run gitleaks on every commit
install-hooks:
    prek install

# patch the newest installed Claude Code now instead of waiting for the daily timer
patch-claude:
    systemctl --user start claude-patch.service
