---
name: changelog
description: >
  Propose CHANGELOG.md updates by analysing git tags and diffs. Uses Keep a Changelog
  format. Detects undocumented releases, reads actual code changes (not just commit
  messages), and outputs a proposed entry for review. Works with any language.
allowed-tools: "Read,Glob,Grep,Bash(git tag:*),Bash(git log:*),Bash(git diff:*),Bash(git show:*)"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# Changelog Skill

Generate and maintain a CHANGELOG.md following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## Format Reference

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-03-15
### Added
- New feature description

### Changed
- Modified behaviour description

### Fixed
- Bug fix description

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
```

### Categories (use only those that apply)
- **Added** — new features or capabilities
- **Changed** — changes to existing functionality
- **Deprecated** — features that will be removed in future
- **Removed** — features that have been removed
- **Fixed** — bug fixes
- **Security** — vulnerability fixes

## Workflow

### Step 1: Gather Context

1. **Read CHANGELOG.md** if it exists. Extract the most recent documented version.
2. **List git tags** ordered by creation date:
   ```bash
   git tag --sort=creatordate
   ```
3. **Identify undocumented releases**: compare the tag list against the changelog. Any tags newer than the last documented version are candidates.

### Step 2: Handle Multiple Undocumented Tags

If there are multiple undocumented tags, tell the user:

> "There are N undocumented releases since [last version]: [list]. Would you like me to do all of them, just the latest, or specific ones?"

Wait for the user's choice before proceeding.

### Step 3: Analyse Each Release

For each tag range (`<previous-tag>..<target-tag>`):

1. **Get the commit log** (as hints — do NOT rely solely on these):
   ```bash
   git log --oneline <prev>..<tag>
   ```

2. **Get the diff stat** to understand scope:
   ```bash
   git diff --stat <prev>..<tag>
   ```

3. **Read the actual diffs** for key files. Focus on source code, not generated files or vendored dependencies. Use `--stat` output to identify which files changed significantly, then read those diffs:
   ```bash
   git diff <prev>..<tag> -- '*.go' '*.py' '*.php' '*.js' '*.ts' '*.rs'
   ```
   For large diffs, focus on the files with the most changes first. Skip test files for categorisation purposes (though a major test addition might indicate a new feature).

4. **Categorise changes** into Added / Changed / Fixed / Removed / Deprecated / Security. Use your judgement:
   - New functions, commands, CLI flags, API endpoints → **Added**
   - Modified behaviour, refactored internals, changed defaults → **Changed**
   - Bug fixes (look for conditional fixes, error handling, edge cases) → **Fixed**
   - Deleted features, removed flags or commands → **Removed**
   - Security patches, dependency updates for CVEs → **Security**

   When commit messages are unhelpful (e.g. "WIP", "fix", "stuff"), lean entirely on the diff content. Describe *what changed for the user*, not implementation details.

### Step 4: Propose the Entry

Output the proposed changelog entry as a fenced code block. Do NOT write it to the file — the user will review first.

If this is a **bootstrap** (no CHANGELOG.md exists):
- Create the full file structure with header and links
- Only write detailed entries for the tag range the user chose
- List older tags as placeholder entries with no details:
  ```markdown
  ## [0.0.9] - 2026-02-20
  ```

If this is an **incremental update** (CHANGELOG.md already exists):
- Output only the new section(s) to be inserted after `## [Unreleased]`
- Include updated comparison links for the bottom of the file

### Step 5: Check for Unreleased Changes

After proposing documented releases, check if there are commits after the latest tag:
```bash
git log --oneline <latest-tag>..HEAD
```

If there are, mention it: "There are also N commits since [latest tag] that haven't been tagged yet. Want me to add an [Unreleased] section?"

## Guidelines

- Write entries from the **user's perspective**, not the developer's. "Added `--tree` flag for hierarchical list display" not "Implemented renderTree function in format.go".
- Keep entries concise — one line per change, no paragraphs.
- Group related small changes into a single entry where sensible.
- If a release is clearly a patch (only fixes), say so briefly.
- Include the release date from the tag: `git tag -l --format='%(creatordate:short)' <tag>`
- For comparison links at the bottom, detect the repository URL from `git remote get-url origin` or the README.
- British English spelling (behaviour, colour, organisation, etc).
