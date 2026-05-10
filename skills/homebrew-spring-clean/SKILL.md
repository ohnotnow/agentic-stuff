---
name: homebrew-spring-clean
description: Walk a developer through tidying up /opt/homebrew. Also use when hunting macOS disk space.
---

# Homebrew Spring Clean

A focused playbook for tidying `/opt/homebrew` (or `/usr/local` on Intel Macs). Sibling to **mac-disk-hunter** — if the question is broader than Homebrew (Time Machine snapshots, Xcode, ML caches, etc.), point the user there instead.

A Homebrew install grows like a barn loft: every `brew install <thing-for-a-throwaway-project>` from years past is still there, plus the deps it dragged in, plus old versions, plus build leftovers, plus `var/log/php-fpm.log` last written to in 2023. 18 GB is not unusual. 30 GB happens.

The user is a Unix-literate developer, often a PHP dev, often using `lando` or `herd` or `valet` *now* but with ghosts of the others still on disk. Treat them as competent — your job is to walk them through the tricksy bits, not lecture about `brew install`.

## The golden rule (same as mac-disk-hunter)

**Never auto-delete.** Always:

1. Survey (read-only).
2. Present a ranked table with size + safe-to-nuke classification.
3. Ask before each destructive step.
4. End with a before/after total.

The cost of asking is small. The cost of nuking the user's `azure-cli` because *you* didn't recognise it is a bad afternoon.

## The flow

### Step 0 — Where are we starting from?

```bash
du -sh /opt/homebrew 2>/dev/null
du -sh /opt/homebrew/* 2>/dev/null | sort -h
brew --version
```

Note the headline number — you'll quote the before/after at the end. The top-level breakdown almost always points at `Cellar`, `Caskroom`, `lib`, or `var` as the offender.

### Step 1 — The free-money round

Always start here. Zero risk, often reclaims 1–2 GB on its own.

#### Dry-run cleanup

```bash
brew cleanup -n 2>&1 | tail -30
```

Shows what `brew cleanup` would remove without doing it: old portable-ruby versions, stale `var/homebrew/tmp/.cellar/` build leftovers, multiple sub-versions of installed formulae. The total appears at the bottom (e.g. "would free approximately 1.2 GB").

We've seen ten old portable-ruby versions piled up under `/opt/homebrew/Library/Homebrew/vendor/portable-ruby/` on a single machine — 350 MB of pure cruft. Always check.

#### Stale logs in `var/log`

```bash
du -sh /opt/homebrew/var/log/* 2>/dev/null | sort -h
```

The classic offender is `php-fpm.log`. **Don't suggest deleting it without investigating.** PHP devs in particular — they've cycled through Herd / Valet / Lando over the years and may not remember whether anything still writes to it.

```bash
# Date range
head -3 /opt/homebrew/var/log/php-fpm.log
tail -3 /opt/homebrew/var/log/php-fpm.log
# Anything currently running?
pgrep -lf php-fpm
# Brew set to autostart it?
brew services list | grep -i php
```

The "safe to nuke" signal is: first/last entries years apart, no `php-fpm` process, no brew service set to start it. **Tell the user what you found** — "first entry Feb 2022, last entry Aug 2023, nothing running, nothing autostarted" — so they recognise the conclusion themselves. The "wait, *am* I still running fpm?" moment is the point.

If recent or active: leave it alone. Mention `truncate -s 0 <file>` as the option that doesn't break log rotation.

The same investigation applies to `nginx/access.log`, `nginx/error.log`, `mysql/<host>.err` etc — check the dates and whether the service is actually in use.

#### Run the cleanup

After the user OKs it:

```bash
brew cleanup -s          # -s also removes downloaded source archives
rm /opt/homebrew/var/log/php-fpm.log    # only if confirmed dead
```

### Step 2 — The leaves table

This is the heart of the spring-clean. Generate a sized table of every leaf (manually-installed formula) and walk through it with the user.

```bash
echo "=== Leaves with sizes (sorted) ==="
for f in $(brew leaves); do
  size=$(du -sh "/opt/homebrew/Cellar/$f" 2>/dev/null | awk '{print $1}')
  printf "%-8s %s\n" "$size" "$f"
done | sort -h
```

For every leaf the user might not recognise on sight, give a one-liner — don't make them open a browser to find out what `vault` is.

| Often-confusing names | What it actually is |
|---|---|
| `vault` | HashiCorp's secrets manager |
| `mactex` | Full LaTeX distribution (~5.6 GB cask!) |
| `dolt` | Git-style version control for SQL databases |
| `helix` | Modal text editor (Kakoune-inspired) |
| `pandoc` | Document format converter |
| `ghostscript` | PostScript / PDF interpreter |
| `poppler` | PDF rendering library |
| `aspell` | Spell checker (very common as a transitive dep) |
| `sphinx-doc` | Python documentation generator |
| `azure-cli` / `doctl` / `gh` / `glab` | CLIs for Azure / DigitalOcean / GitHub / GitLab |
| `boost` | C++ libraries (almost always a dep, rarely a leaf for normal users) |

For each leaf, ask: **"still using this?"** Don't assume. We've all installed something for a single afternoon's experiment three years ago. The user will surprise you with what they care about (we've seen `gcc` kept and `mactex` zapped in the same session).

#### Don't lump categories

Walk down the table. The user might keep `azure-cli` and `gcc` while ditching `mactex` and `dolt`. Each is a single named decision, not a category.

### Step 3 — Casks (the GUI app side)

```bash
du -sh /opt/homebrew/Caskroom/* 2>/dev/null | sort -h | tail -10
```

Casks are usually either small (a tiny menu-bar app) or huge (MacTeX, GIMP, etc.). The huge ones are usually the headline.

⚠️ **MacTeX (and other Apple-pkg-installed casks) need sudo internally.** `brew uninstall --cask mactex` triggers `sudo pkgutil --forget` under the bonnet. Claude **cannot** pass a password through, so the uninstall will fail with `sudo: a terminal is required to read the password`.

When suggesting these uninstalls, **explicitly tell the user upfront**:

> This one needs `sudo` internally — I can't run it from here. Please run `brew uninstall --cask mactex` in your own terminal, then come back when it's done.

Don't try and run it and hope for the best — you'll just get a half-uninstalled mess and a confused user.

### Step 4 — The autoremove dance (with footnotes)

```bash
brew autoremove --dry-run
```

`brew autoremove` removes formulae that *(a)* were installed as dependencies AND *(b)* are no longer needed by anything. Sounds simple. It isn't.

#### Footnote 1: `installed_on_request: true` blocks autoremove

If the user ever typed `brew install ghostscript` directly — even years ago, even if it was *also* pulled in as a dep at the time — Homebrew flags it `installed_on_request: true`, and `autoremove` will **not** touch it no matter how orphaned it becomes. This is the #1 reason autoremove returns "nothing to do" when there are obvious orphans sitting right there.

To find these stealth-orphans, check leaves with no users:

```bash
for f in $(brew leaves); do
  uses=$(brew uses --installed "$f" 2>/dev/null)
  if [ -z "$uses" ]; then
    size=$(du -sh "/opt/homebrew/Cellar/$f" 2>/dev/null | awk '{print $1}')
    echo "$size  $f"
  fi
done | sort -h
```

Present the orphan-leaves to the user. Many will be deliberate (their actively-used tools). The document-processing crowd (`ghostscript`, `poppler`, `sphinx-doc`, `pandoc`, `docutils`) often stand out as "I removed MacTeX months ago and these are the leftovers."

These need explicit `brew uninstall <name>` — autoremove won't help.

#### Footnote 2: Old kegs blocking everything

If a previous `brew uninstall` left old version directories behind in the Cellar (e.g. `Cellar/php@7.4/7.4.28` from 2022 with files brew couldn't `rm` without sudo), brew **still counts those as installed** for dependency calculations. So `aspell` won't autoremove because brew thinks `php@7.4` still needs it.

Spot the symptom: `brew uninstall foo` succeeds but you still see versioned subdirectories in `/opt/homebrew/Cellar/foo/`. Tell the user the exact command — they need to run it themselves:

```bash
sudo rm -rf /opt/homebrew/Cellar/php@7.4 /opt/homebrew/Cellar/php@8.0
```

Until those are gone, autoremove won't see the chain clearly.

#### Footnote 3: Targeted uninstalls unblock autoremove

Once you've done the targeted uninstalls (Step 2/3) and any phantom-keg cleanup, **re-run `brew autoremove`**. It will often now fire and sweep a chain of newly-orphaned deps.

We've seen one targeted `brew uninstall sphinx-doc` chain into autoremoving `python@3.11`, `openssl@1.1`, `nss`, `nspr`, `libidn`, `jbig2dec` — 110 MB of bonus reclaim that the first autoremove dry-run claimed wasn't there.

### Step 5 — Stale tap metadata (the "Skipping" warnings)

If `brew cleanup` outputs lots of `Warning: Skipping foo: most recent version X not installed` lines, the user's tap metadata is stale (often because they have `HOMEBREW_NO_AUTO_UPDATE=set` — a deliberate choice many devs make to avoid surprise upgrades during random `brew install` calls).

This blocks cleanup of old sub-versions of currently-installed formulae. The fix is one command:

```bash
brew update && brew cleanup -s
```

⚠️ **But this brings tap metadata up to date**, which the user may have been deliberately avoiding. Always ask first. If they want to stay frozen, the leftover ~150–200 MB of old sub-versions is a small price.

### Step 6 — Final accounting

```bash
du -sh /opt/homebrew
du -sh /opt/homebrew/Cellar /opt/homebrew/Caskroom /opt/homebrew/lib /opt/homebrew/var 2>/dev/null
```

Quote the before/after total. **"18 GB → 9.9 GB, eight gigs of museum exhibits gone."** A short before/after table by top-level dir is nice. A line of dry humour is fine — the user has earned a smile after a forty-minute disk-archaeology session.

## Known hotspots (quick reference)

| Path | Typical size | Notes |
|---|---|---|
| `/opt/homebrew/Caskroom/mactex` | 5.6 GB | Full LaTeX. Uninstall needs sudo. |
| `/opt/homebrew/Cellar/llvm` | 1.7 GB | Often a `rust` dep. Leave alone unless removing rust. |
| `/opt/homebrew/Cellar/php` | 250 MB+ | Old sub-versions; `brew cleanup` if metadata fresh. |
| `/opt/homebrew/Cellar/php@7.4`, `php@8.0` | 150 MB each | If from `shivammathur/php` tap, often abandoned. |
| `/opt/homebrew/Library/Homebrew/vendor/portable-ruby/` | 30 MB × N versions | `brew cleanup -s` sweeps. |
| `/opt/homebrew/var/homebrew/tmp/.cellar/` | 100 MB+ | Stale build leftovers — `brew cleanup -s`. |
| `/opt/homebrew/var/log/php-fpm.log` | 100 MB+ | **Investigate before deleting** (Step 1). |
| `/opt/homebrew/var/log/nginx/` | varies | Same — check whether nginx is still in use. |

## What NOT to touch

| Path | Why |
|---|---|
| `/opt/homebrew/var/postgres`, `mysql`, `redis`, `mongodb` | User data. Will silently delete database state. ❌ |
| `/opt/homebrew/etc/` | Hand-edited config for installed formulae (postgres confs, nginx confs, dnsmasq rules). ❌ |
| `~/Library/Caches/Homebrew` | Outside `/opt/homebrew`. Worth flagging but officially `mac-disk-hunter` territory. |

## Things that always need the user's terminal (sudo-gated)

State these clearly upfront whenever they come up — don't try and run them and hope:

- `brew uninstall --cask mactex` (and other casks installed via Apple `.pkg`)
- `sudo rm -rf /opt/homebrew/Cellar/<formula>/<old-version>` (phantom kegs from years ago)
- `sudo tmutil thinlocalsnapshots /` (out of scope but mention if Time Machine comes up)

## See also

- **mac-disk-hunter** — broader macOS disk-space hunting (Time Machine snapshots, Xcode DerivedData, ML caches, etc.). Refer there if the user's question goes wider than Homebrew.
