---
name: mac-disk-hunter
description: Track down where disk space has gone on macOS — System Data, Time Machine local snapshots, dev caches (uv, npm, pnpm, Homebrew, Docker, Xcode DerivedData), ML model caches (huggingface, ollama), and the usual hiding places in `~/Library` and `~/.cache`. Use whenever the user says they're low on disk space, the Mac is full, "System Data is huge", "where's my disk space gone", asks to clean up cruft, find big files/folders, free up space, mentions a startup disk warning, or asks about the `mole` / `mo` cleaner. Surveys first, suggests second — never deletes without explicit confirmation. The disk-space counterpart to the mac-triage skill (which covers RAM/CPU).
---

# Mac Disk Hunter

A checklist for finding where the disk space has gone on a developer's Mac. The user is an old-school Unix admin who accumulates cruft from many languages and toolchains (uv, npm, pnpm, Homebrew, Docker, Xcode, huggingface, ollama, etc.), plus the usual macOS-specific hiding places (Time Machine local snapshots, purgeable space, "System Data"). Assume competence; the unfamiliar bit is *which corner of macOS the bytes are hiding in this time*.

The user has `ncdu` available which is interactive by default - use `ncdu -o <file>` (or `-o -` to pipe) for non-interactive output. Write any capture file to your session scratchpad if the harness gives you one; /tmp otherwise. Use `du -sh` for quick targeted spot-checks.

**Check the ncdu version first** with `ncdu --version`:

- **ncdu 2.x** (Zig rewrite, 2021+) has parallel scanning — noticeably faster than `du` on big trees, especially on an NVMe SSD where `stat()` latency dominates. Prefer it for broad sweeps like `$HOME`.
- **ncdu 1.x** is single-threaded, same as `du` — no speed advantage. If you spot a 1.x install, mention in passing that `brew upgrade ncdu` will get them the threaded version. Don't make a fuss; it's a footnote, not a blocker.

## Optional tooling: check, mention, move on

Check what's on hand before starting: `command -v ncdu mo jq`. Nothing here is required - the core flow runs on built-ins (`df`, `du`, `tmutil`, `docker system df`) - but note the preferred Step 3 survey pipes ncdu into `jq`, so if either half is missing, go straight to the `du` fallback rather than improvising. If a nice-to-have is missing, spend one passing line on it ("`brew install ncdu mole` would make this faster next time") and carry on with the fallbacks. Do not make installing things step one: the disk is full, and "download more software" is a comedy opening move. The right moment to pitch installs properly is the wrap-up (see How to report back).

## The mental model (APFS in Linux terms)

| macOS / APFS | Linux-ish equivalent | Notes |
|---|---|---|
| **Sealed system volume** (`/`) | Read-only `/usr` partition | Always near-full and unchangeable. **Ignore its size.** Real user data lives on `/System/Volumes/Data`. |
| **Data volume** (`/System/Volumes/Data`) | `/home` + `/var` + everything else | This is the one that fills up. `df -h` shows it under the same mount as `/`. |
| **Purgeable space** | tmpfs / reclaimable cache | macOS may count evictable caches and old snapshots as "free" to apps, so `df` can flatter by tens of GB. Older macOS exposed a "Purgeable" figure via `diskutil info`; newer versions (verified absent on macOS 26 / Darwin 25) expose it nowhere in the CLI, not even `system_profiler SPStorageDataType`. If Step 1 shows no Purgeable line, it is not obtainable: say so and move on. |
| **"System Data"** in Finder's About This Mac | Catch-all bucket | Whatever Finder couldn't classify. **Almost always Time Machine local snapshots, caches, or `~/Library`** — not actually the OS. The phrase "System Data is huge" is the user repeating Finder's misleading label. |
| **Local Time Machine snapshots** | LVM snapshots, but invisible | APFS keeps hourly snapshots locally even if you have no Time Machine drive attached. Each can be many GB. `tmutil listlocalsnapshots /`. |
| **APFS containers vs volumes** | LVM VG / LV | All system volumes share one container's free space. `diskutil apfs list` shows the layout. |

## The golden rule

**Never auto-delete.**

Disk space is shared system state. A wrong `rm -rf` on `~/Library/Containers` or a Homebrew cellar is a long afternoon of recovery. The flow is always:

1. Find where it went (read-only).
2. Present a ranked list to the user with safe-vs-careful annotations.
3. Only if they specifically ask you to clean it up - run the cleanup commands.

Even "obviously safe" things like `~/.cache/uv` get a confirmation. The cost of asking is small. The cost of wiping a dev's signing keys, simulator state, or auth tokens is not.

## The diagnostic flow

Run in this order. Each step narrows the search.

### Step 1 — What does the disk actually look like?

```bash
df -h / /System/Volumes/Data
diskutil info /System/Volumes/Data | grep -E "Used Space|Free Space|Purgeable"
```

Read the **data volume** line, not `/`. The diskutil labels on current macOS are `Volume Used Space` and `Container Free Space`: Used is per-volume, Free is per-container (all volumes share one container's pool), which is why the grep needs both patterns. Note up to three numbers:

- **Used**: what's actually on disk.
- **Avail**: what `df` thinks is free (often optimistic).
- **Purgeable**: the gap between "free" and "really free", *if reported*. On newer macOS (verified on macOS 26 / Darwin 25) no Purgeable line appears at all, and no other CLI reports it either. If it's absent, tell the user plainly: purgeable isn't exposed on this OS version, so the `df` number is the real number. Then move on; don't hunt for a figure the CLI cannot produce.

If purgeable IS reported and huge (say 30 GB against "0 bytes free"), the system is technically fine, but still worth hunting: purgeable rarely shrinks on its own at the speed you'd like.

### Step 2 — Check Time Machine local snapshots (the silent killer)

This is the single most-forgotten cause. **Always check it, even if the user says they have no Time Machine drive.** APFS keeps local snapshots regardless.

```bash
tmutil listlocalsnapshots /
```

The listing mixes two kinds of entry: hourly `com.apple.TimeMachine.*` snapshots and occasional `com.apple.os.update-*` ones left by macOS updates. Count only the TimeMachine kind (`tmutil listlocalsnapshots / | grep -c com.apple.TimeMachine`; the raw listing also includes a header line, so grep rather than counting lines), and read the dates, not just the count. The normal shape is roughly one snapshot per hour covering the last 24 hours: that is stock APFS behaviour and is NOT a finding, however many there are. The signal is count AND age together: snapshots older than about 24 to 48 hours, or gaps suggesting thinning has stalled, mean GB are probably pinned. Mention any os.update entries but leave them alone; how `thinlocalsnapshots` treats them is unverified.

There's no built-in command to show snapshot sizes individually, but a usable estimate exists: take the data volume's Used figure and subtract everything `du` can see live (the `$HOME` total plus the outside-`$HOME` sweep, both from Step 3). The residual approximates snapshot bulk. Three practicalities, learned in the field:

- Use `df`'s Used column as the minuend and keep everything in GiB. diskutil's figure is decimal GB, about 7 percent adrift, which is easily enough to swallow the answer.
- The Step 3 survey prints a top-20 list, not a total. Capture the ncdu scan to a file and query it twice; Step 3 ships the total-producing jq alongside the ranked one.
- Present the result as an upper bound, not a measurement: `du` cannot read TCC-protected paths (see the Step 4 warnings), and every GB it cannot see lands in the residual.

Each snapshot pins all changes since the previous one, so a busy dev day can plausibly pin several GB.

To thin them (only with user confirmation):

```bash
# Reclaim up to ~1 TB of snapshot space at maximum urgency. The trailing 4 is an
# urgency level (1-4), NOT a snapshot count: there is no "keep N snapshots" mode,
# and at urgency 4 this may thin every snapshot.
sudo tmutil thinlocalsnapshots / 999999999999 4

# Or nuke a specific one:
sudo tmutil deletelocalsnapshots <snapshot-date>
```

Note: `thinlocalsnapshots` needs `sudo`. Warn the user before running.

### The mole scout (if installed)

[mole](https://github.com/tw93/mole) (`brew install mole`, binary `mo`) is a well-regarded open-source cleaner from homebrew-core - genuinely safe-by-default, not part of the "free up your Mac!" scamware family. Its dry-run automates most of Steps 3 and 4 in one pass and covers corners the hotspot table doesn't: orphaned caches from uninstalled apps, old Electron app versions, stale login items. If `mo` is on the PATH, run the scout here, then use the manual surveys to fill in what it ignores.

```bash
# Output is heavy with ANSI colour and spinner animation.
# NO_COLOR=1 strips the colour codes; redirecting keeps the spinner frames out of the capture.
# The scan takes several minutes on a full disk: raise your command timeout,
# or a killed mo looks like mole being broken. $SCRATCH = your session
# scratchpad, or /tmp failing that:
NO_COLOR=1 mo clean --dry-run > "$SCRATCH/mole-scan.txt" 2>/dev/null
```

(System caches need sudo for a full preview - `sudo -v && NO_COLOR=1 mo clean --dry-run ...` - but ask the user first, as ever with sudo.)

The scan file is a short category summary (a couple of hundred lines) - read it whole. The itemised receipt lands in `~/.config/mole/clean-list.txt` and is thousands of lines of paths: do NOT read it wholesale, just pull the big-ticket entries:

```bash
grep GB ~/.config/mole/clean-list.txt
```

That typically returns a dozen lines accounting for most of the reclaimable total. mole's header also prints a "Free space" figure that should agree with diskutil's Container Free Space from Step 1: a free sanity check that both tools are reading the same volume.

Rules of engagement:

- **Dry-run only, ever.** A bare `mo clean` deletes thousands of files in one pass. If the user wants mole to do the actual cleaning, they run it themselves after reviewing; point them at the whitelist (`~/.config/mole/whitelist`, managed via `mo clean --whitelist`) for anything to protect first.
- **`mo purge` is the sharp one** - it strips build artefacts (`node_modules`, `target/`, `vendor/`) across whole source trees. Never suggest it casually; regenerating a working tree's dependencies mid-project is not "free" to its owner.
- **mole lists cleanable cruft, not disk usage.** It will not surface a bulging `~/Movies`, VM disk images, or any user data, and it reports Time Machine snapshots and Docker without touching them. Steps 1 and 2 and the surveys below still matter.

Its default whitelist already shields the expensive-to-regenerate caches (huggingface, ollama models, iCloud `Mobile Documents`) - same philosophy as this skill.

### Step 3 — Top-level survey of `$HOME`

This is the workhorse. Get a ranked list of top-level directories under `$HOME` (including dotfiles, which is where most caches hide).

**If ncdu 2.x is available**, prefer it — the parallel scan is markedly faster on a full `$HOME`:

```bash
# Capture once (several minutes on a full disk: raise your command timeout),
# then query the file as often as you like. $SCRATCH = your session
# scratchpad, or /tmp failing that:
ncdu -o "$SCRATCH/home.json" -x ~ 2>/dev/null

# Ranked top-level list:
jq -r '
  .[3][1:][]
  | if type == "array"
    then [.[0].name, ([.. | objects | .dsize? // 0] | add)]
    else [.name, (.dsize? // 0)]
    end
  | "\(.[1] / 1024 / 1024 / 1024 | . * 100 | floor / 100) GB  \(.[0])"
' "$SCRATCH/home.json" | sort -rn | head -20

# Grand total (GiB) - the number the Step 2 snapshot estimate needs.
# NB the spaces in "? // 0" are load-bearing: "?//" is a different operator in jq 1.6+.
jq -r '[.[3][1:][] | if type=="array" then ([.. | objects | .dsize? // 0] | add) else (.dsize? // 0) end] | add / 1024 / 1024 / 1024 | floor' "$SCRATCH/home.json"
```

**Otherwise (or on ncdu 1.x)**, the bulletproof `du` one-liner still works fine:

```bash
du -sh ~/* ~/.[!.]* 2>/dev/null | sort -h | tail -20
```

The `~/.[!.]*` glob catches dotfiles without matching `~/.` and `~/..`. `sort -h` sorts human-readable sizes correctly.

For a **deeper interactive exploration** of a specific subtree the user wants to drill into, the same ncdu-to-`jq` pipeline works on any path:

```bash
ncdu -o - -x ~/Library 2>/dev/null | jq -r '
  .[3][1:][]
  | if type == "array"
    then [.[0].name, ([.. | objects | .dsize? // 0] | add)]
    else [.name, (.dsize? // 0)]
    end
  | "\(.[1] / 1024 / 1024 / 1024 | . * 100 | floor / 100) GB  \(.[0])"
' | sort -rn | head -20
```

(That walks ncdu's nested format, sums `dsize` recursively per top-level child, and converts to GB. Adjust the path as needed.)

Don't drop the user into ncdu's interactive TUI — they want answers in the conversation, not a curses session.

**Then sweep outside `$HOME`.** On a dev Mac a quarter or more of the used space can live there, and nothing above sees it:

```bash
du -sh -x /Applications /Library /opt/homebrew /usr/local /Users/Shared /private/var 2>/dev/null | sort -h
```

(`2>/dev/null` is fine here, unlike the Step 4 batch: these directories always exist, so the errors are just permission noise, not evidence.) `/Applications` alone can be tens of GB and appears in no cache table. For APFS-aware readers: `/Applications` and friends are firmlinks, and `du -x` does traverse them (verified), so they count. The list is not exhaustive - `/private/tmp`, `/Volumes` and other users' homes are omitted; add them if the numbers still refuse to add up. `du` undercounts unreadable corners out here (ordinary permissions and TCC both), which is fine for ranking; just remember it when these numbers feed the Step 2 snapshot estimate. Sum the `$HOME` total plus this sweep and compare against `df`'s Used figure: a large residual usually means snapshots (see Step 2).

The top of the survey list almost always points at one of the **Known Hotspots** below. Don't go deeper yet — first check whether the offender is one of the well-known ones, because there's usually a *proper* command to clean it (e.g. `docker system prune` rather than `rm -rf`).

### Step 4 — Walk the Known Hotspots

Run the batch below to size every common hotspot in one pass; absent paths identify themselves on stderr. Build a ranked summary from the output. **Don't read the contents** — you only need sizes.

```bash
# Batch-check the common dev caches in one go. Leave stderr visible: a
# "No such file or directory" line is evidence (tool not installed), and
# silencing it makes "absent" indistinguishable from "empty".
du -sh \
  ~/.cache/huggingface \
  ~/.cache/uv \
  ~/.cache/pip \
  ~/Library/Caches/pip \
  ~/.cache/pre-commit \
  ~/.npm \
  ~/Library/pnpm/store \
  ~/.cargo/registry \
  ~/.cargo/git \
  ~/go/pkg/mod \
  ~/Library/Caches/Homebrew \
  ~/Library/Developer/Xcode/DerivedData \
  ~/Library/Developer/CoreSimulator \
  ~/Library/Caches \
  ~/Library/Logs \
  ~/.Trash \
  ~/Downloads \
  | sort -h
```

Three warnings about the output. First, stderr carries two very different signals: "No such file or directory" means the tool isn't installed, while "Operation not permitted" means the path exists but is TCC-protected (macOS privacy gates: `~/.Trash`, Safari's caches, assorted `com.apple.*` directories). TCC is not a permissions problem and sudo does NOT get past it; only granting the terminal Full Disk Access does. Report TCC-blocked paths as "exists, size unknown", never as absent, and treat any figure whose tree contains them (`~/Library/Caches`, say) as a floor. Second, the list contains parent-and-child pairs (`~/Library/Caches` contains the Homebrew and pip caches), so never total the output as printed: report non-overlapping numbers. Third, `/private/var/log` is deliberately not in the batch - non-sudo `du` mostly can't read it; it stays in the hotspot table for awareness only.

Then Docker: two commands, and always run both, because they answer different questions. (The `du` is the one sanctioned exception to the Containers row below.)

```bash
docker system df                                     # inside the VM: what pruning could free
du -sh ~/Library/Containers/com.docker.docker/Data   # on the host: what Docker actually costs
```

Do NOT silence stderr on the docker command: a half-up daemon fails loudly and usefully (500s from the socket, API version complaints), and `2>/dev/null` turns "Docker is broken" into "Docker: nothing to report". If the daemon won't answer you still have the host-side `du` figure; a broken daemon also blocks pruning, so the order is restart or update Docker Desktop first, prune second.

`Docker.raw` in that directory is sparse: `du` shows real allocation, `ls -lh` shows apparent size, and they can differ by tens of GB. Quote the `du` figure as what Docker costs the host, and `docker system df`'s reclaimable figure as what pruning frees inside the VM. The two are not interchangeable: freed space inside the VM returns to the host via TRIM on modern Docker Desktop, but slowly and not always fully (believed, not verified by this skill's authors), so warn the user that `df` may not move much straight after a prune. The guaranteed full reclaim is Docker Desktop's "reset to factory defaults", which loses every container, image and volume. Never hand-delete `Docker.raw`.

And Ollama, if installed:

```bash
du -sh ~/.ollama/models 2>/dev/null
```

### Step 5 - When the biggest thing isn't in the table

The table below covers the classifiable cruft. Sooner or later the survey's top entry is something it doesn't: `~/Library/Application Support` at 50+ GB, a bulging `~/Documents/code`, some app's private hoard. The method is the same one level down:

```bash
du -sh -x <the-big-directory>/* 2>/dev/null | sort -h | tail -10
```

Report what you find by name and size even when none of it is agent-deletable: a 13 GB app-data directory is worth the user knowing about, and the app's own settings are the way in. For source trees, the node_modules row in the table already has the find command. The rule stands: name it, size it, let the user decide. "It's big but not in my table" is not a finding, it's a shrug.

## The Known Hotspots

Memorise these. Most "where did my disk go?" answers live in this table.

| Path / Tool | Typical size | Safe to nuke? | Cleanup command |
|---|---|---|---|
| **Time Machine local snapshots** | 0–50+ GB | ✅ Yes (after confirmation) | `sudo tmutil thinlocalsnapshots / 999999999999 4` |
| **`~/Library/Developer/Xcode/DerivedData`** | 0–30 GB | ✅ Always safe — rebuilds on next compile | `rm -rf ~/Library/Developer/Xcode/DerivedData/*` |
| **Old iOS Simulators** | 0–20 GB | ✅ Yes — keeps current ones | `xcrun simctl delete unavailable` |
| **`~/Library/Developer/Xcode/iOS DeviceSupport`** | 0–10 GB per OS version | ⚠️ Careful — needed to debug those iOS versions; old ones safe to delete | `rm -rf <specific-version-folder>` |
| **Docker images / volumes / build cache** (`~/Library/Containers/com.docker.docker/Data`) | 5-80 GB | ⚠️ Mostly safe: `prune` only removes unused, but the daemon must be healthy first | `docker system prune -a --volumes` (warn: also removes stopped containers' volumes) |
| **`~/.cache/huggingface`** | 1–100+ GB | ⚠️ Re-downloads on next use; check the user actually doesn't need offline | `rm -rf ~/.cache/huggingface/hub` (or `huggingface-cli delete-cache` for interactive) |
| **`~/.ollama/models`** | 5–80 GB per model | ⚠️ Each model is GBs and slow to redownload — let the user pick | `ollama list`, then `ollama rm <model>` |
| **`~/.cache/uv`** | 1–10 GB | ✅ Yes — uv repopulates | `uv cache prune` (preferred) or `uv cache clean` |
| **`~/Library/Caches/pip`** (macOS default; `~/.cache/pip` if XDG is set - `pip3 cache dir` settles it) | 1-5 GB | ✅ Yes | `pip cache purge` |
| **`~/.npm`** | 0.5-10 GB | ✅ Yes (cache only, not `node_modules`) | `npm cache clean --force` (an EACCES about root-owned files is ancient sudo-npm cruft; the clean still removes nearly everything, and `sudo chown -R $(id -u):$(id -g) ~/.npm` clears the crumbs) |
| **`~/Library/pnpm/store`** | 1–20 GB | ⚠️ Shared store across projects — `prune` is safe | `pnpm store prune` |
| **`~/Library/Caches/Homebrew`** | 1–10 GB | ✅ Yes — re-downloads on next install | `brew cleanup -s` (and `brew autoremove`) |
| **`~/.cache/pre-commit`** | 0.5–5 GB | ✅ Yes — rebuilds | `pre-commit clean && pre-commit gc` |
| **`~/.cargo/registry` + `~/.cargo/git`** | 1–10 GB | ✅ Yes | `cargo cache --autoclean` if installed, else `rm -rf ~/.cargo/registry/cache` |
| **`~/go/pkg/mod`** | 1–10 GB | ✅ Yes | `go clean -modcache` (deletes everything; will redownload) |
| **Stray `node_modules` across projects** | 0.5 GB × N projects | ⚠️ Per-project — only safe if user isn't actively working on it | Find: `find ~/code -name node_modules -type d -prune -exec du -sh {} +` |
| **`~/Library/Caches/*`** (general) | 1–20 GB total | ⚠️ Mostly safe but app-specific (Slack, Discord, browsers, IDEs) | Spot-check biggest offenders first; most apps recreate on launch |
| **`~/Library/Logs`** | 0.5–5 GB | ✅ Mostly safe — keep last week | `find ~/Library/Logs -type f -mtime +30 -delete` |
| **`/private/var/log`** | 0.5–5 GB | ⚠️ System logs — don't blindly delete; let macOS rotate | `sudo log erase --ttl` (the flag takes no argument; drops only expired TTL content) if really needed |
| **`~/.Trash`** | 0-big; unsizable without Full Disk Access (TCC blocks `du`) | ✅ Yes | Empty via Finder; terminal `rm` hits the same TCC wall as `du` |
| **`~/Downloads`** | 0–huge | ⚠️ User content — list big ones, let them choose | `find ~/Downloads -size +100M -exec ls -lh {} \;` |
| **Old `.dmg` / `.pkg` installers in Downloads** | 0.5–5 GB each | ✅ Usually yes (keep what's needed) | `find ~/Downloads -name "*.dmg" -o -name "*.pkg"` |
| **`~/Library/Containers`** | varies | ❌ **Don't touch**: app data, settings, sandboxed user files. One exception: Docker's data lives here, see the Docker row | Use the app's own settings to clear data, or remove only after uninstalling the app |
| **`~/Library/Application Support`** | varies | ❌ **Don't touch wholesale**: app data, profiles, browser bookmarks live here | Size the subdirs (Step 5) and report; clear only via each app's own settings |
| **Browser profiles (Firefox, Chrome)** | 1–10 GB | ❌ Don't delete — that's their bookmarks, history, extensions | If a profile cache is huge, use the browser's "clear cache" UI |

## Action priority (least destructive first)

Always work top-down. Re-measure after each step, with one APFS caveat that makes a fool of the measurement: **`df` barely moves when you delete things.** Every deleted byte stays pinned by the local snapshots until they expire (roughly 24 hours) or are thinned. Verified in the field: a 70 GB cleanup left `df` showing one GB LESS free afterwards, because a fresh hourly snapshot had just pinned the lot. Measure success by the directories you emptied, tell the user the `df` payoff arrives within a day, and if they want the space immediately, thin snapshots AFTER the bulk deletions.

1. **Thin Time Machine local snapshots.** Often the single biggest win and entirely macOS-managed (low risk to user data). Worth re-running as the final step too, to release what the snapshots pinned while you were deleting.
2. **Run the per-tool prune commands** (`brew cleanup -s`, `docker system prune`, `uv cache prune`, etc.). These are *designed* to be safe — they only remove what the tool considers unused.
3. **Clear `DerivedData` and unavailable simulators.** Pure rebuild artefacts. Always safe.
4. **Empty Trash.** Trivially reversible up to the moment you empty it.
5. **Trim ML model caches** (huggingface, ollama) only after listing them and letting the user pick which to keep. These are *expensive* to re-download.
6. **Delete old log files** (>30 days).
7. **Hunt big files in `~/Downloads` and `~/Movies`** — these are user content, never delete without an explicit per-file OK.
8. **Reboot.** Last resort, but a reboot does free purgeable space and clears `/private/var/folders` tmp cruft. Worth knowing it exists; don't lead with it.

## How to report back

Structure the summary like this:

1. **Headline number** — e.g., "32 GB locked in Time Machine local snapshots; another 18 GB in Docker images you haven't used in months."
2. **Ranked table** — biggest offenders first, with size and safe-to-nuke classification (✅ / ⚠️ / ❌). Numbers, not prose.
3. **Suggested cleanup actions, in priority order** — paste the exact commands but **don't run them yet**.
4. **Total reclaimable estimate** — "Looks like ~60 GB easily recoverable, another ~20 GB if you're willing to lose the local huggingface cache."
5. **Wait for the user to say "yes, do X and Y"** before running anything destructive.
6. **For next time** - if mole or ncdu 2.x were missing during the hunt, close with the one-line install suggestion (`brew install mole ncdu`). The user has just watched the manual version of what those tools automate; this is the natural "while it's in mind" moment. If everything was already installed, skip this item entirely rather than reporting that there is nothing to report.

Unit discipline: mole reports decimal GB while `du` and the ncdu pipeline report GiB, so the same npm cache can read "45.02GB" from one and "42G" from the other. That 7 percent gap is unit mixing, not an error. Convert everything to one unit (GiB) for the report and say so.

Keep it tight, a bit wry. The user has been deleting files since before APFS existed; they don't need a lecture, just a map.

## A final note

The two questions worth asking yourself before suggesting any deletion:

1. **Is this regenerable?** (caches, build artefacts, downloadable models — yes; user data, app state, signing keys — no)
2. **What's the cost of regenerating it?** (a `brew install` is seconds; a 70 GB LLM is hours and possibly bandwidth)

When in doubt: list it, don't delete it. The user can always run `rm` themselves.

## See also

- **mac-triage** — for sluggishness / RAM / CPU issues. Different problem, different skill.
