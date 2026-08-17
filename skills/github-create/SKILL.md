---
name: github-create
description: |
  Create a new GitHub repository from the current local project, push code, and handle finishing touches (README, LICENSE, description). Use when the user wants to publish a local project to GitHub for the first time. Triggers on: "github-create", "create a repo", "push this to github", "put this on github", "create a github repo", "let's make a repo", or any request to publish a local project to GitHub as a new repository.
---

# GitHub Create

Create a new GitHub repository from the current local project with all the finishing touches.

## Key concerns

This skill creates **public, permanent artifacts**. Once pushed, content is effectively un-deletable - even amended or force-pushed content lingers in GitHub's object store for ~90 days, may be cached in search indexes, and may have been cloned by anyone watching. Treat every name and string going into a public repo as a one-way commitment.

**Two failure modes to guard against above the rest:**

1. **Identity leaks in the LICENSE** - joining the user's real name (from `userEmail` context, an email-to-name inference, `git config user.name` if unconfirmed, or tool output like `sentry auth whoami`) to a public handle in immutable git history. This is the single worst step this skill can take. **Step 5 is the procedure - never skip the memory lookup, never derive a name from email or tool output, always confirm before writing.**
2. **Private-project leaks in the README or code** - internal codenames, hostnames, project slugs, real issue IDs, or org names from the user's other work, surfacing in a public artifact. **Step 8 (Pre-commit leak scan) is non-skippable** and must run before any commit, even if the user has already reviewed the files.

Both failure modes arise from acting *unilaterally* on identity decisions. The corrective: show diffs before committing, run the leak scan before pushing, ask the user when in doubt. The cost of one extra question is always less than the cost of one preventable leak.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- `git` initialised in the current directory
- Current directory has at least one commit

## Constrained wrappers: agent-commit and agent-github

Some users have the `agent-commit` and `agent-github` wrapper commands installed. They are narrow, agent-friendly routes: `agent-commit` commits only explicitly named files with a validated message, `agent-github` can only create and initially push one new repository, and both use a preview-then-token confirmation so nothing happens on the first invocation. Check for them early:

```bash
command -v agent-commit agent-github
```

- **Both found**: use them for the commit and publish steps below.
- **Not found**: mention it once, in passing - something like "No agent-commit/agent-github commands found - falling back to raw git/gh" - then use the native commands shown in each step. Do not pitch them or suggest installing anything. (They come from https://github.com/ohnotnow/agent-commit - only bring that up if the user asks what the commands are.)
- **One found**: use whichever is available for its step and fall back for the other.

On the native path, respect the user's git permissions. If `git add` or `git commit` is denied, tell the user what files need committing and give them the commands to run themselves. Do not retry denied commands or work around the restriction. Never use `git push --force`, `git reset`, or any destructive git operation on either path.

## Workflow

### Step 1: Verify environment

Check prerequisites and wrapper availability:

```bash
gh auth status
git rev-parse --is-inside-work-tree
git log --oneline -1
command -v agent-commit agent-github
```

If not in a git repo, offer to run `git init` and create an initial commit.

If there are uncommitted changes or untracked files, warn the user and ask how they want them handled (commit them, `.gitignore` them, or move them aside). This matters most on the wrapper path: `agent-github` refuses to publish unless the working tree is completely clean, untracked files included.

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

1. **Repository name** - suggest the current directory name. Accept or override.
2. **Owner** - with the wrapper, run `agent-github owners` to list the authenticated account and its organisations. Natively, run `gh api user/memberships/orgs --jq '.[].organization.login'` and present the options plus "personal account". If only one org exists, still ask (do not assume).
3. **Visibility** - public or private? Default: public.

With the owner and name settled, the repository URL is known before the repo exists: `https://github.com/<owner>/<repo>`, clone URL `https://github.com/<owner>/<repo>.git`. Use these when writing the README so clone instructions are copy/paste-able.

### Step 4: Handle README

Assess the current README situation:

1. **No README.md exists** - check if a `/readme` skill is available. If it is, tell the user: "There's no README yet. You could run `/readme` to generate a detailed one, or I can create a basic one now. Which do you prefer?" If no `/readme` skill exists, offer to create a basic one.
2. **README.md exists but is framework boilerplate** - detect boilerplate by checking for telltale phrases:
   - Laravel: "Laravel is a web application framework"
   - Rails: "This README would normally document"
   - Django: "Django project"
   - Create React App: "This project was bootstrapped with"
   - Vite: "This template provides a minimal setup"
   - Generic: file is under 5 lines or contains only a heading with no real content
   If boilerplate is detected, offer the same choice as above (dedicated skill or basic README).
3. **README.md exists and looks genuine** - skip. Do not offer to overwrite.

**Basic README generation**: If creating a basic README (no dedicated skill), use session context and project analysis to write a concise, accurate README covering:
- Project name and one-line description
- What it does (2-3 sentences)
- Prerequisites and quick start (adapted to detected stack), using the constructed clone URL from Step 3
- Usage examples if obvious from the code
- License reference if a LICENSE will exist

If the user has an `assets/readme-style.md` file in the skill directory, read it and follow its style guidance.

Do NOT include generic filler, badges, or sections with no real content.

After writing the readme, if the `/readme` skill was used, the humaniser agent runs automatically as part of that skill. If you created a basic readme manually instead, spawn the humaniser agent (from `~/.claude/agents/humaniser.md`) for an editorial pass, if available.

### Step 5: Handle LICENSE

Check if a `LICENSE` file exists in the project root. If one already exists, skip this step.

If no LICENSE exists, the attribution name must be determined carefully - this is the single highest-stakes string in the repo (see Key concerns at the top of this skill).

#### 5a. Search user-memories first, with broad queries

A single narrow search query will miss memories phrased differently from the words you'd reach for. Run **at least all of these** queries against `mcp__user-memories__search` before doing anything else:

- `attribution copyright license`
- `name` (bare term - broad sweep catches unexpectedly relevant entries)
- `MIT LICENSE` (or whichever licence applies)
- The GitHub repo owner from Step 3 (e.g. the user's GitHub handle or org slug)

If any memory speaks to attribution preference for this user's repos, **use it without re-confirming** unless the situation is ambiguous (e.g. a memory says "use `<handle>` for personal repos, ask for org repos" and this is an org repo). Memory exists to encode standing preferences - re-asking when memory has already answered wastes the user's time and signals you don't trust your own records.

#### 5b. Forbidden inference sources

Never derive the LICENSE attribution name from any of these:

- The `userEmail` field in the conversation's system context (e.g. `jane.doe@example.com` becoming "Jane Doe")
- Any other email-to-name inference, including the local part of email addresses
- Tool output that may surface a real name: `sentry auth whoami`, `gcloud auth list`, `aws sts get-caller-identity`, `gh api user`, IDE telemetry, git history of *other* repos
- "Sounds right from session context" - if you can't name the exact authoritative source, ask the user

These sources are forbidden because they often surface a real name when the user publishes under a handle, and joining the two in a public LICENSE is a doxxing event that cannot be undone.

#### 5c. Allowed candidate sources, when memory has nothing

If the memory search returned nothing relevant, gather candidates from these allowed sources only:

- `git config user.name`
- The GitHub username or org name from the repo target (the owner portion of `owner/repo`)

Then **ask the user explicitly** which to use, listing all candidates verbatim. Example:

> "I don't have a stored attribution preference for this repo. Candidates: `git config user.name` says **`<value>`**, and the GitHub owner is **`<value>`**. Which should go in the LICENSE? (Or something else?)"

Wait for the user's response before writing the file. Offer to save the choice via `mcp__user-memories__remember` so future projects don't ask again.

#### 5d. Write the file

Use the template at `assets/MIT-LICENSE-TEMPLATE`, replacing `{{YEAR}}` with the current year and `{{AUTHOR}}` with the confirmed name. Do **not** add any other identifying string (no email, no URL, no organisation reference) unless the user asked for it.

### Step 6: Go release workflow

**Only for Go projects** (detected by `go.mod` in step 2).

Check if `.github/workflows/` already contains a release workflow. If not, offer to create one:

> "This is a Go project. Want me to add a GitHub Actions workflow that builds cross-platform binaries and attaches them to a release when you push a version tag (e.g. `v1.0.0`)?"

If the user accepts, create `.github/workflows/release.yml` using the template at `assets/go-release-workflow.yml`. Read the template and adapt the binary output name to match the repository name (replace the placeholder).

If the user declines or the project is not Go, skip this step.

### Step 7: Security policy

If a `SECURITY.md` already exists in the project root, skip this step. Likewise if the `moat-repo-fixer` skill is available - it handles the security policy along with broader repo hardening after publish (Step 11).

Otherwise, offer to add one now from the template at `assets/SECURITY.md` so it ships with the initial push. The template directs reporters to GitHub's private vulnerability reporting and deliberately names no person and no email address - adding a contact email is the same identity decision as the LICENSE name, so only add one if the user explicitly asks (the Step 5 rules apply).

The Security-tab route the template describes needs private vulnerability reporting enabled on the repo, which is off by default - Step 11 covers enabling it after publish.

### Step 8: Pre-commit leak scan (non-skippable)

Before staging anything, grep the files that are about to be committed for identifying strings tied to the user. This step is **non-skippable**, even when the user has already reviewed the files themselves - content generated during the session may contain leaks they didn't notice and you wrote in. The cost of a false positive (asking the user about a string) is far less than the cost of leaking real data into a public repo's permanent history.

#### 8a. Build the scan pattern

Assemble identifying strings from:

- **Email domain** of the `userEmail` context line (e.g. if `userEmail: jane.doe@acme.co.uk`, scan for `acme.co.uk` and `acme`).
- **Real-name fragments** - first name, last name, full name - if these have appeared anywhere in the session (in tool output, system context, or earlier messages).
- **The user's other GitHub orgs** from the owner listing gathered in Step 3. These shouldn't appear in a personal repo unless attribution is intended.
- **Internal-looking hostnames** - anything matching `*.<email-domain>`, `*.internal.*`, `*.corp.*`, or hostnames that came up during the session.
- **Real project slugs, codenames, issue IDs** - anything from real Sentry/Jira/Linear/GitHub data the user shared while building the project (e.g. issue IDs like `PROJ-123`, codenames like `cronmon`, table names like `internal_widgets`).

Construct a single case-insensitive grep:

```bash
grep -rniE 'pattern1|pattern2|pattern3|...' --include="*.md" --include="*.txt" --include="*.json" --include="*.yml" --include="*.yaml" .
```

Include all text-format extensions present in the repo. **Do not** rely on `--include="*.md"` alone - leaks can land in config files, code, and templates too.

#### 8b. Triage hits with the user

For each hit, show the file, line number, and the surrounding context. For each, ask the user one of:

- **Scrub it**: replace with a generic placeholder (`myapp`, `acme-corp`, `example.com`). Show the proposed replacement before applying.
- **Keep it**: the user confirms the string is intentional (e.g. crediting a real contributor by name, referencing a genuinely public project).
- **Cut the surrounding content**: sometimes the sentence/bullet/example as a whole doesn't earn its space once the identifying detail is removed.

**Do not auto-scrub.** Even when a replacement seems obvious, the user might want a different placeholder, or the hit might be a false positive worth keeping. Wait for explicit per-hit confirmation.

#### 8c. Re-scan after fixes

If any scrubbing was applied, re-run the grep to confirm zero remaining hits. Only proceed to commit when the scan is clean.

### Step 9: Commit the finishing touches

**Show the diff to the user before committing** - this is especially important after a leak scan, when content has been edited.

With `agent-commit`, name every file individually (it refuses directories, `.`, and `-a`/`-A`):

```bash
agent-commit -m "chore: add project documentation" README.md LICENSE SECURITY.md .github/workflows/release.yml
```

It prints a preview and an eight-character token; repeat the identical command with `--yes <token>` to make the commit. The first message line must be Conventional Commits shaped (`type(scope): summary`), and AI-attribution footers ("Generated with...", "Co-Authored-By...") are refused - do not add them. For a multi-line message, write it to a file and pass `-m @/path/to/message.txt`.

Native fallback (no push yet - there is no remote until Step 10):

```bash
git diff            # show the user before committing
git add README.md LICENSE SECURITY.md .github/workflows/release.yml
git commit -m "chore: add project documentation"
```

If a native git command is denied by the user's permissions, list the files that need committing and provide the commands for the user to run themselves, then carry on once they have.

### Step 10: Create the repository and push

First compose the repository description: a single plain-English sentence summarising what the project does, under 100 characters, no emoji or special characters.

With `agent-github`:

```bash
agent-github publish \
  --repo <owner>/<repo> \
  --public \
  --description "Very short description of the project"
```

It prints a preview (account, exact target, visibility, branch, commit and file counts) and a token. Show the preview to the user and confirm the owner and visibility before repeating the identical command with `--yes <token>`. `agent-github` refuses if any remote already exists or the working tree isn't clean - resolve those with the user rather than working around them.

Native fallback:

```bash
gh repo create <owner>/<repo> --public --source . --remote=origin --push
gh repo edit <owner>/<repo> -d "Very short description of the project"
```

If `origin` already exists on the native path, this probably isn't a first-time publish - warn the user and ask before touching anything.

If creation fails because the name is taken, ask the user for an alternative name, update any URLs already written into the README to match, and commit that fix before retrying.

### Step 11: Repo hardening

If you have the `moat-repo-fixer` skill - offer to invoke it.  It helps apply best practices and protections against supply-chain attacks to GitHub repositories.

If moat isn't available and a `SECURITY.md` was added in Step 7, enable private vulnerability reporting so the Security-tab route it describes actually works. It is off by default, and it is a public-repo feature - skip this if the repo was published private:

```bash
gh api -X PUT repos/<owner>/<repo>/private-vulnerability-reporting
```

If that command is denied, tell the user they can enable it themselves in the repo's Settings under Code security, or run the command above.

### Step 12: Done

Report the repository URL and confirm everything is set up. Keep it brief.

If a Go release workflow was added, remind the user how to trigger it:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Important notes

- Always confirm the owner and visibility before publishing. Creating in the wrong org is a pain to fix.
- Never force-push or overwrite existing remotes without explicit user consent.
- The README is written before the repo exists, from the URL constructed in Step 3. If the repo name changes at publish time, update the README URLs to match and commit the fix.
- The `assets/readme-style.md` file is optional user customisation for README style preferences. If it does not exist or is empty, use sensible defaults.
