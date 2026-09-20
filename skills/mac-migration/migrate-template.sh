#!/bin/bash
# TEMPLATE - regenerate the LIST block for the machine in front of you (see SKILL.md).
# Push "the stuff you probably care about" from this Mac to the new one over the LAN.
# Run ON THE OLD MAC.  Needs Remote Login (System Settings > General > Sharing) on the new Mac.
#
#   migrate-to-new-mac.sh user@new-mac.local          # dry run (default)
#   DO_IT=1 migrate-to-new-mac.sh user@new-mac.local  # actually copy
#   WITH_MEDIA=1 ...                             # also Pictures/Music/Movies/Downloads
#
# Firefox profile is included: QUIT FIREFOX before a real copy.
#
# Safe to re-run: rsync only sends what changed.  Nothing is ever deleted on the target.
set -eu

DEST="${1:?usage: $0 user@host}"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# ---- what to copy (paths relative to $HOME) -------------------------------------
cat > "$SCRATCH/files" <<'LIST'
Documents
Desktop
bin
.bashrc
.bash_profile
.profile
.zshrc
.vimrc
.vim
.tmux.conf
.gitconfig
.git-completion.bash
.fzf.bash
.fzf.zsh
.aspell.en.pws
.aspell.en.prepl
.config
.ssh
.gnupg
.aws
.azure
.kube
.lando/config.yml
.lando/config
.claude
.claude.json
.codex
.gemini
.copilot
.composer/auth.json
.composer/config.json
.docker/config.json
.docker/daemon.json
.docker/contexts
.mutt
.local/state
.bash_history
.mysql_history
.php_history
.sqlite_history
.python_history
.rediscli_history
Library/Fonts
Library/Preferences/com.googlecode.iterm2.plist
Library/Preferences/com.mitchellh.ghostty.plist
Library/Application Support/obsidian
Library/Application Support/com.raycast.macos
Library/Application Support/Firefox
LIST

# loose files sitting directly in ~ (mp3s, logs, pdfs, odd scripts) - small enough, keep the lot
find "$HOME" -maxdepth 1 -type f ! -name '.DS_Store' ! -name '.*.backup*' ! -name '.claude.json.backup' \
  ! -name '*.lock' ! -name '.CFUserTextEncoding' \
  -exec basename {} \; >> "$SCRATCH/files"

if [ -n "${WITH_MEDIA:-}" ]; then
  printf '%s\n' Pictures Music Movies Downloads >> "$SCRATCH/files"
fi

# ---- what NOT to copy, wherever it appears --------------------------------------
cat > "$SCRATCH/exclude" <<'EX'
.DS_Store
.venv/
venv/
node_modules/
vendor/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.phpunit.cache/
.phpunit.result.cache
target/
dist/
build/
.next/
.nuxt/
storage/logs/
storage/framework/cache/
storage/framework/sessions/
storage/framework/views/
bootstrap/cache/
.lando/logs/
.claude/security/
.claude/session-env/
.claude/file-history/
.claude/skills_and_agents.tgz
.codex/cache/
.codex/log/
.codex/sessions/
.codex/tmp/
.config/*/Cache/
.config/*/cache/
.config/uv/cache/
Library/Application Support/Firefox/Crash Reports/
cache2/
startupCache/
*.log
*.pyc
*.o
EX

# openrsync (Apple's rsync) aborts the whole run on a missing --files-from entry, so drop them
grep -v '^$' "$SCRATCH/files" | while IFS= read -r f; do
  [ -e "$f" ] && printf '%s\n' "$f" || echo "   (skipping, not found: $f)" >&2
done > "$SCRATCH/files.ok"

# remote target gets a trailing colon; a plain local path is handy for testing
case "$DEST" in *:*|*@*) TARGET="$DEST:" ;; *) TARGET="$DEST" ;; esac

RSYNC_OPTS=(-a -r -h --partial --files-from="$SCRATCH/files.ok" --exclude-from="$SCRATCH/exclude")
if [ -n "${DO_IT:-}" ]; then RSYNC_OPTS+=(--progress); else RSYNC_OPTS+=(--dry-run --stats); fi

cd "$HOME"
echo "==> $( [ -n "${DO_IT:-}" ] && echo COPYING || echo DRY RUN ) $HOME -> $TARGET"
rsync "${RSYNC_OPTS[@]}" ./ "$TARGET"
