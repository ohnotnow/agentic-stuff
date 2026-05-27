---
name: github-create
description: |
  Create a new GitHub repository from the current local project, push code, and handle finishing touches (README, LICENSE, description). Use when the user wants to publish a local project to GitHub for the first time. Triggers on: "github-create", "create a repo", "push this to github", "put this on github", "create a github repo", "let's make a repo", or any request to publish a local project to GitHub as a new repository.
---

# GitHub Create

Create a new GitHub repository from the current local project with all the finishing touches.

## Key concerns

This skill creates **public, permanent artifacts**. Once pushed, content is effectively un-deletable — even amended or force-pushed content lingers in GitHub's object store for ~90 days, may be cached in search indexes, and may have been cloned by anyone watching. Treat every name and string going into a public repo as a one-way commitment.

**Two failure modes to guard against above the rest:**

1. **Identity leaks in the LICENSE** — joining the user's real name (from `userEmail` context, an email-to-name inference, `git config user.name` if unconfirmed, or tool output like `sentry auth whoami`) to a public handle in immutable git history. This is the single worst step this skill can take. **Step 6 is the procedure — never skip the memory lookup, never derive a name from email or tool output, always confirm before writing.**
2. **Private-project leaks in the README or code** — internal codenames, hostnames, project slugs, real issue IDs, or org names from the user's other work, surfacing in a public artifact. **Step 9 (Pre-commit leak scan) is non-skippable** and must run before any commit, even if the user has already reviewed the files.

Both failure modes arise from acting *unilaterally* on identity decisions. The corrective: show diffs before committing, run the leak scan before pushing, ask the user when in doubt. The cost of one extra question is always less than the cost of one preventable leak.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- `git` initialised in the current directory
- Current directory has at least one commit

## Git command restrictions

This skill uses `gh` CLI commands freely (repo create, repo edit, etc.) but must respect the user's git permissions. Many users restrict direct git commands (`git add`, `git commit`, `git push`) via their CLAUDE.md or permission settings.

**Rules:**
- Use `gh repo create --source . --push` for the initial push (this is a `gh` command, not a raw `git push`).
- For subsequent commits (README, LICENSE, etc.): attempt `git add` + `git commit` + `git push`. If any of these are denied, tell the user what files need committing and give them the commands to run themselves. Do not retry denied commands.
- Never use `git push --force`, `git reset`, or any destructive git operation.
- If the user has committed and pushed the files themselves, carry on with the remaining steps (description, etc.) without repeating the git operations.

## Workflow

### Step 1: Verify environment

Check prerequisites:

```bash
gh auth status
git rev-parse --is-inside-work-tree
git log --oneline -1
```

If not in a git repo, offer to run `git init` and create an initial commit.

If there are uncommitted changes, warn the user and ask whether to commit them first or proceed as-is.

### Step 2: Detect project type

Check for framework indicators to inform README generation, .gitignore review, and whether to offer a release workflow:

| File | Stack |
|------|-------|
| `composer.json` + `artisan` | Laravel |
| `composer.json` | PHP |
| `pyproject.toml` or `requirements.txt` | Python |
| `package.json` + `next.config.*` | Next.js |
| `package.json` + `nuxt.config.*` | Nuxt |
| `package.json` | Node.js / JavaScript |
| `Gemfile` + `config/routes.rb` | Rails |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `*.sh` (main files) | Shell script |

Note the detected stack for later use.

### Step 3: Gather details

Ask the user these questions (suggest sensible defaults):

1. **Repository name** — suggest the current directory name. Accept or override.
2. **Organisation** — run `gh api user/memberships/orgs --jq '.[].organization.login'` to list available orgs. Present the options plus "personal account". If only one org exists, still ask (do not assume).
3. **Visibility** — public or private? Default: public.

### Step 4: Create repository and push

Build the `gh repo create` command based on answers:

```bash
# Personal account
gh repo create <repo-name> --public --source . --remote=origin --push

# Organisation
gh repo create <org>/<repo-name> --public --source . --remote=origin --push
```

If `origin` remote already exists, warn and ask the user whether to overwrite it or abort.

Extract the repository URL from the output. This URL is needed for README clone instructions, so the repo must exist before generating the README.

### Step 5: Handle README

**Important:** This step comes after repo creation so that the README can include accurate clone URLs and release page links.

Assess the current README situation:

1. **No README.md exists** — check if a `/readme` skill is available. If it is, tell the user: "There's no README yet. You could run `/readme` to generate a detailed one, or I can create a basic one now. Which do you prefer?" If no `/readme` skill exists, offer to create a basic one.
2. **README.md exists but is framework boilerplate** — detect boilerplate by checking for telltale phrases:
   - Laravel: "Laravel is a web application framework"
   - Rails: "This README would normally document"
   - Django: "Django project"
   - Create React App: "This project was bootstrapped with"
   - Vite: "This template provides a minimal setup"
   - Generic: file is under 5 lines or contains only a heading with no real content
   If boilerplate is detected, offer the same choice as above (dedicated skill or basic README).
3. **README.md exists and looks genuine** — skip. Do not offer to overwrite.

**Basic README generation**: If creating a basic README (no dedicated skill), use session context and project analysis to write a concise, accurate README covering:
- Project name and one-line description
- What it does (2-3 sentences)
- Prerequisites and quick start (adapted to detected stack)
- Usage examples if obvious from the code
- License reference if LICENSE exists

If the user has a `resources/readme-style.md` file in the skill directory, read it and follow its style guidance.

Do NOT include generic filler, badges, or sections with no real content.

After writing the readme, if the `/readme` skill was used, the humaniser agent runs automatically as part of that skill. If you created a basic readme manually instead, spawn the humaniser agent (from `~/.claude/agents/humaniser.md`) for an editorial pass, if available.

### Step 6: Handle LICENSE

Check if a `LICENSE` file exists in the project root. If one already exists, skip this step.

If no LICENSE exists, the attribution name must be determined carefully — this is the single highest-stakes string in the repo (see Key concerns at the top of this skill).

#### 6a. Search user-memories first, with broad queries

A single narrow search query will miss memories phrased differently from the words you'd reach for. Run **at least all of these** queries against `mcp__user-memories__search` before doing anything else:

- `attribution copyright license`
- `name` (bare term — broad sweep catches unexpectedly relevant entries)
- `MIT LICENSE` (or whichever licence applies)
- The GitHub repo owner from Step 3 (e.g. the user's GitHub handle or org slug)

If any memory speaks to attribution preference for this user's repos, **use it without re-confirming** unless the situation is ambiguous (e.g. a memory says "use `<handle>` for personal repos, ask for org repos" and this is an org repo). Memory exists to encode standing preferences — re-asking when memory has already answered wastes the user's time and signals you don't trust your own records.

#### 6b. Forbidden inference sources

Never derive the LICENSE attribution name from any of these:

- The `userEmail` field in the conversation's system context (e.g. `jane.doe@example.com` → "Jane Doe")
- Any other email-to-name inference, including the local part of email addresses
- Tool output that may surface a real name: `sentry auth whoami`, `gcloud auth list`, `aws sts get-caller-identity`, `gh api user`, IDE telemetry, git history of *other* repos
- "Sounds right from session context" — if you can't name the exact authoritative source, ask the user

These sources are forbidden because they often surface a real name when the user publishes under a handle, and joining the two in a public LICENSE is a doxxing event that cannot be undone.

#### 6c. Allowed candidate sources, when memory has nothing

If the memory search returned nothing relevant, gather candidates from these allowed sources only:

- `git config user.name`
- The GitHub username or org name from the repo target (the owner portion of `owner/repo`)

Then **ask the user explicitly** which to use, listing all candidates verbatim. Example:

> "I don't have a stored attribution preference for this repo. Candidates: `git config user.name` says **`<value>`**, and the GitHub owner is **`<value>`**. Which should go in the LICENSE? (Or something else?)"

Wait for the user's response before writing the file. Offer to save the choice via `mcp__user-memories__remember` so future projects don't ask again.

#### 6d. Write the file

Use the template at `assets/MIT-LICENSE-TEMPLATE`, replacing `{{YEAR}}` with the current year and `{{AUTHOR}}` with the confirmed name. Do **not** add any other identifying string (no email, no URL, no organisation reference) unless the user asked for it.

### Step 7: Go release workflow

**Only for Go projects** (detected by `go.mod` in step 2).

Check if `.github/workflows/` already contains a release workflow. If not, offer to create one:

> "This is a Go project. Want me to add a GitHub Actions workflow that builds cross-platform binaries and attaches them to a release when you push a version tag (e.g. `v1.0.0`)?"

If the user accepts, create `.github/workflows/release.yml` using the template at `assets/go-release-workflow.yml`. Read the template and adapt the binary output name to match the repository name (replace the placeholder).

If the user declines or the project is not Go, skip this step.

### Step 8: Generate description

Write a concise repository description (under 100 characters, no emoji, no special characters) based on understanding of the project. This should be a single plain-English sentence summarising what the project does.

Set it immediately using `gh repo edit` (this is a `gh` command, not a git command, so it should not be blocked):

```bash
gh repo edit <repo-url> -d "Very short description of the project"
```

### Step 9: Pre-commit leak scan (non-skippable)

Before staging anything, grep the files that are about to be committed for identifying strings tied to the user. This step is **non-skippable**, even when the user has already reviewed the files themselves — content generated during the session may contain leaks they didn't notice and you wrote in. The cost of a false positive (asking the user about a string) is far less than the cost of leaking real data into a public repo's permanent history.

#### 9a. Build the scan pattern

Assemble identifying strings from:

- **Email domain** of the `userEmail` context line (e.g. if `userEmail: jane.doe@acme.co.uk`, scan for `acme.co.uk` and `acme`).
- **Real-name fragments** — first name, last name, full name — if these have appeared anywhere in the session (in tool output, system context, or earlier messages).
- **The user's other GitHub orgs** from `gh api user/memberships/orgs --jq '.[].organization.login'` (already gathered in Step 3). These shouldn't appear in a personal repo unless attribution is intended.
- **Internal-looking hostnames** — anything matching `*.<email-domain>`, `*.internal.*`, `*.corp.*`, or hostnames that came up during the session.
- **Real project slugs, codenames, issue IDs** — anything from real Sentry/Jira/Linear/GitHub data the user shared while building the project (e.g. issue IDs like `PROJ-123`, codenames like `cronmon`, table names like `internal_widgets`).

Construct a single case-insensitive grep:

```bash
grep -rniE 'pattern1|pattern2|pattern3|...' --include="*.md" --include="*.txt" --include="*.json" --include="*.yml" --include="*.yaml" .
```

Include all text-format extensions present in the repo. **Do not** rely on `--include="*.md"` alone — leaks can land in config files, code, and templates too.

#### 9b. Triage hits with the user

For each hit, show the file, line number, and the surrounding context. For each, ask the user one of:

- **Scrub it**: replace with a generic placeholder (`myapp`, `acme-corp`, `example.com`). Show the proposed replacement before applying.
- **Keep it**: the user confirms the string is intentional (e.g. crediting a real contributor by name, referencing a genuinely public project).
- **Cut the surrounding content**: sometimes the sentence/bullet/example as a whole doesn't earn its space once the identifying detail is removed.

**Do not auto-scrub.** Even when a replacement seems obvious, the user might want a different placeholder, or the hit might be a false positive worth keeping. Wait for explicit per-hit confirmation.

#### 9c. Re-scan after fixes

If any scrubbing was applied, re-run the grep to confirm zero remaining hits. Only proceed to commit when the scan is clean.

### Step 10: Commit and push finishing touches

Stage any new files created (README.md, LICENSE, .github/workflows/release.yml) and commit. **Show the diff to the user before committing** — this is especially important after a leak scan, when content has been edited.

```bash
git diff --staged   # or git diff if not yet staged — show the user before committing
git add README.md LICENSE .github/   # only files that were created/modified
git commit -m "chore: add project documentation"
git push origin HEAD
```

If any git command is denied by the user's permissions, list the files that need committing and provide the commands for the user to run themselves. Then carry on with any remaining non-git steps. Do not retry denied commands or try to work around the restriction.

### Step 11: Done

Report the repository URL and confirm everything is set up. Keep it brief.

If a Go release workflow was added, remind the user how to trigger it:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Important notes

- Always confirm the organisation and visibility before creating the repo. Creating in the wrong org is a pain to fix.
- Never force-push or overwrite existing remotes without explicit user consent.
- If `gh repo create` fails (e.g. name taken), report the error and ask the user for an alternative name.
- The `resources/readme-style.md` file is optional user customisation for README style preferences. If it does not exist, use sensible defaults.
- The repo must be created before generating the README, so that clone URLs and release page links are accurate.
