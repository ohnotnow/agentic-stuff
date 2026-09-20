---
name: mac-migration
description: Plan and script a developer's move from an old Mac to a new one over the LAN - survey the home directory by name and size (never by content), sort it into copy / rebuild / self-syncs / reinstall, and produce a re-runnable rsync script that skips the gigabytes of caches. Use when the user says they are getting a new Mac, asks what to copy over, wants a migration or transfer script, or asks "what will I miss?". Also covers the non-file bits (Homebrew, uv tools, Docker volumes, DB data) and the Apple openrsync traps. Sibling to mac-disk-hunter (finding space) and homebrew-spring-clean.
---

# Mac Migration

A playbook for moving a developer from one Mac to another, keeping the old one around. The goal is a script the user can leave running over the LAN while they do the manual installs (Office, Teams, the App Store stuff), and a short list of things that are *not* files and need doing by hand.

The user is a competent Unix person with years of accumulated cruft: several language toolchains, ML model caches, Docker, three editors, two terminal emulators, and dotfiles they wrote in 2014. Assume competence. The value you add is the triage and the traps, not an explanation of `rsync -a`.

Migration Assistant exists and is the right answer for a non-developer. For a developer it drags every cache, every dead virtualenv and every Intel-era binary across. The user has asked you precisely because they want the opposite: "the stuff I probably care about, minus the trash".

## Rule one: survey by name and size, never by content

Dotfiles are where the API keys live. `~/.bashrc`, `~/.zshrc`, `~/.config/*/config.yml`, `~/.netrc`, `~/.composer/auth.json`, an Obsidian note called "API keys" - all of it. You do not need to read a single one of them to decide whether it gets copied. A file's *name*, *size* and *location* are enough.

So: `ls`, `du -sh`, `fd`, `stat`. Never `cat`, `head`, `grep -r` for keys, or "let me just check what's in here". If you find yourself about to open a dotfile, stop - the answer to "copy it?" is almost always yes for anything small and hand-written, and the user can prune the list afterwards.

The transcript is logged to disk. A secret that lands in it is a secret the user has to rotate.

## The survey

Run these in order. Total time on a busy 250 GB home directory: a few minutes.

```bash
cd ~
ls -la ~ | awk '{print $1, $5, $NF}'                    # everything at top level, incl. dotfiles
du -sh -- .[a-z]* * 2>/dev/null | sort -h               # sized, smallest to largest
du -sh Documents/* Library/* "Library/Application Support"/* Library/Containers/* 2>/dev/null | sort -h | tail -25
du -sh .cache/* .local/share/* .npm/* go/* .config/* 2>/dev/null | sort -h | tail -20
```

Then census the junk inside the code tree - this is where most of the bulk hides:

```bash
fd -H -t d '^(node_modules|vendor|\.venv|venv|target|\.git|dist|build|__pycache__|\.next)$' ~/Documents/code --max-depth 4 \
  -x du -sk {} 2>/dev/null \
  | awk '{n=split($2,a,"/"); s[a[n]]+=$1} END{for(k in s) printf "%.1fG %s\n", s[k]/1048576, k}' | sort -rn
```

Note `--max-depth 4` misses deeply nested virtualenvs; the rsync dry run later counts them properly. `du` on macOS is BSD: `-I pattern` masks a name everywhere, which is handy for the cross-check below. There is no `--exclude`.

`ncdu` may be installed (2.x is parallel and much faster on a big tree); `ncdu -o file` for non-interactive output. Nice, not required.

## The triage

Sort every top-level item into exactly one bucket. Sizes below are one real machine in 2026, to calibrate expectations, not targets.

**Copy - actual state, irreplaceable or annoying to recreate**

- Code tree (`~/Documents/code`, `~/code`, `~/src`, `~/Projects`), *minus the junk dirs*. Keep `.git`. Typically 30 GB raw, under 8 GB after excludes.
- `~/Desktop`, `~/Documents` (the rest), loose files sitting in `~` itself (there are always some: logs, mp3s, "test.txt"), `~/bin`.
- Shell dotfiles and their helpers: `.bashrc .bash_profile .profile .zshrc .zprofile .vimrc .vim .tmux.conf .gitconfig .gitignore_global .inputrc .fzf.*`, shell completion scripts, `.aspell.*`.
- Shell histories (`.bash_history .zsh_history .mysql_history .psql_history .php_history .sqlite_history .python_history .rediscli_history .lesshst`). Cheap and people miss them.
- `~/.config` whole (editor, terminal, `gh`, `glab`, `uv`, `karabiner`, `raycast` ...). Exclude `*/Cache/` and `*/cache/` inside it.
- `~/.ssh`, `~/.gnupg`, `~/.aws`, `~/.azure`, `~/.kube`, `~/.docker/{config.json,daemon.json,contexts}`, `~/.composer/auth.json`, `~/.lando/config*` (not the rest of `.lando`).
- AI tool state: `~/.claude` (minus `security/`, `session-env/`, `file-history/`), `~/.claude.json`, `~/.codex` (minus `cache/ log/ sessions/ tmp/`), `~/.gemini`, `~/.copilot`.
- `~/Library/Fonts`. Developers forget this one every time and then wonder why their terminal looks wrong.
- Firefox profile, if they use Firefox: `Library/Application Support/Firefox`, excluding `cache2/`, `startupCache/`, `Crash Reports/`. 10 GB is normal and fine on a LAN. Firefox must be quit during the copy, and on the new Mac `about:profiles` may be needed to select the copied profile. Firefox Sync (a Mozilla account, never a Google sign-in) covers bookmarks, history, logins, tabs, add-ons and most prefs, but *not* add-on settings and data, container definitions, site permissions or the full session, so copy the profile and treat Sync as the backup. Chrome and Safari sync via account; skip.
- `~/Library/Preferences/<terminal>.plist` for iTerm2 (`com.googlecode.iterm2.plist`), Ghostty (`com.mitchellh.ghostty.plist`), Warp, kitty if not in `.config`.
- Selected `~/Library/Application Support`: `obsidian`, `com.raycast.macos`, anything the user names. Not the editors (see below).

**Optional - real data, big, ask**

- `~/Pictures ~/Music ~/Movies ~/Downloads`. Offer as a flag, default off.
- Local database data. Ask first: for most developers it is throwaway seeded test data and the answer is "don't bother". If it matters, DBngin keeps MySQL/Postgres under `Library/Application Support/com.tinyapp.DBngin/Engines/` (copies arm64 to arm64 *with the engine stopped* and the same engine version on the target); Homebrew databases live under `/opt/homebrew/var/{mysql,postgresql@N}` and a `mysqldump` / `pg_dumpall` is safer than copying files.
- Docker volumes. The Docker VM disk (`Library/Containers/com.docker.docker`, 50 GB+) is useless to copy. If a named volume holds data they care about, export it on the old box:
  ```bash
  docker volume ls
  docker run --rm -v VOLNAME:/v -v "$PWD":/b alpine tar czf /b/VOLNAME.tgz -C /v .
  ```
  Lando/Sail/Herd projects usually rebuild their databases from seeders or a dump anyway; ask.

**Rebuilds itself - skip, and say why so the user trusts the omission**

- `~/.cache` (uv, huggingface, pip, puppeteer, phpactor, codex-runtimes): often 30 GB+. Models re-download on first use.
- `~/.npm/_cacache`, `~/.composer/cache`, `~/.cargo/registry`, `~/go/pkg`, `~/.bun/install/cache`, `~/.local/share/uv` (managed Pythons and the tool venvs), `~/.local/share/nvim` (plugins).
- Inside code: `.venv venv node_modules vendor target dist build __pycache__ .next .pytest_cache .mypy_cache .ruff_cache .phpunit.cache`, Laravel `storage/logs storage/framework/{cache,sessions,views} bootstrap/cache`.
- `~/Library/Caches`, `~/Library/Logs`, `Library/Application Support/Caches`.

**Syncs itself - skip**

- Dropbox, Google Drive (`Library/CloudStorage`), iCloud (`Library/Mobile Documents`), OneDrive.
- `~/Library/Mail` (re-add the accounts), Messages, Photos library if in iCloud.
- Editor app support (`Code`, `Cursor`, `Zed`, `JetBrains`) - settings sync via account; the dirs are mostly extension binaries and caches. Copy `~/.config/nvim`, `~/.vscode/extensions` list at most.
- Claude desktop, Slack, Teams, Zoom, Discord app support. Log in again.

**Reinstall for the new CPU - skip**

- `~/go/bin`, `~/.local/bin` (usually symlinks into `.local/share` anyway), `~/.cargo/bin`, `~/.lando/{bin,plugins}`, `~/.bun/bin`, anything under `~/Applications` that is not an app the user made.
- Even arm64 to arm64, a fresh install gets a native build for the new chip and drops the odd Rosetta straggler.

**Not files at all - the by-hand list**

```bash
brew bundle dump --file=~/Brewfile        # only records what you asked for; deps come along on `brew bundle`
brew leaves --installed-on-request        # if they want to read the list first
uv tool list                              # re-run `uv tool install X` for each
pipx list; npm ls -g --depth=0; cargo install --list; go version   # whichever apply
docker volume ls                          # see above
```

The Brewfile lands in `~` so the script carries it over. On the new Mac: enable Remote Login (System Settings > General > Sharing) before running anything, install Homebrew, `brew bundle`, then re-auth `gh`, `glab`, `aws`, `az`, `1Password`, and let 1Password/keychain-style tools sync rather than copying `~/Library/Keychains` (do not copy Keychains).

## The script

Ship a re-runnable script, dry run by default, that pushes *from the old Mac to the new one* over ssh. Pushing is the right direction: the old machine has the tooling, and the new one only needs sshd on. A template lives beside this file: `migrate-template.sh`. Regenerate its include list for the machine in front of you; the exclude list is largely universal.

Design points that matter:

- `--files-from=<list>` with paths relative to `$HOME` and `./` as the source: one list defines the whole transfer and directory structure is preserved.
- Never `--delete`. The old Mac stays intact, the script is additive, re-running is safe.
- `DO_IT=1` to copy, otherwise `--dry-run --stats`. Feature flags (`WITH_MEDIA=1`) for the optional buckets.
- Loose files in `~` come from `find "$HOME" -maxdepth 1 -type f`, filtered.
- Accept a local directory as the target so the script can be dry-run tested without the new Mac existing yet. (Two days before delivery is exactly when people write this script.)

## Apple's rsync is openrsync - the traps

`rsync --version` on macOS 15+ says `openrsync: protocol version 29`. It is not GNU rsync and it bit in three ways, all verified:

1. **A missing `--files-from` entry silently truncates the transfer.** One `stat: No such file or directory` warning and the file list stops there; the dry run reported 1 GB where the answer was 11 GB. Filter the list through `[ -e "$f" ]` before handing it to rsync, and print what was dropped.
2. **`--files-from` does not imply recursion.** Pass `-r` explicitly alongside `-a`. (GNU has the same rule, so it costs nothing.)
3. **No `--info=progress2`, no `--itemize-changes`.** `--progress`, `--partial`, `--stats`, `--exclude-from`, `--files-from` all work. Keep `--progress` out of dry runs; with a quarter of a million files the output is unreadable.

`brew install rsync` on both ends and `--rsync-path=/opt/homebrew/bin/rsync` if the user wants the GNU niceties. Not required.

Exclude patterns behave as in GNU: a trailing `/` matches directories only, a pattern without `/` matches by basename anywhere. Verified `build/` excludes `project/build/` and nothing else.

## Verify before quoting a number

The dry-run total is the headline the user acts on, so cross-check it once with an independent tool:

```bash
du -sh -I .venv -I venv -I node_modules -I vendor -I build -I dist -I target -I __pycache__ ~/Documents/code
```

If the two disagree by more than a few percent, something in the list or excludes is over-matching or (see trap 1) the list got truncated. Bisect by feeding a single project dir through `--files-from` with one exclude at a time; a small project (under 1 GB) makes each probe a few seconds instead of minutes.

A real number from one machine: 240 GB home, 22 GB in the default transfer (10 GB of that the Firefox profile), 33 GB with media.

## How to report back

Lead with the script path, the three invocations, and the headline size. Then, short and bulleted:

- what is copied,
- what is skipped and *why* (rebuilds / syncs / reinstall), so the omission reads as a decision, not a gap,
- the by-hand list,
- a secrets note: name the copied files that hold tokens by design (`.ssh`, `.gnupg`, `.aws`, `gh`/`glab` config, `auth.json`, `.netrc`, any note the survey turned up by *title*) so the user can prune or re-auth. Say you did not open any of them.
- the judgement calls you made on their behalf (that `temp/` dir, the 80 MB folder of thumbnails you could not identify).

Do not write the exclude list into the user's head as gospel. Their friend's machine is not their machine.
