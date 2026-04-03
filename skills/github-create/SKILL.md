---
name: github-create
description: |
  Create a new GitHub repository from the current local project, push code, and handle finishing touches (README, LICENSE, description). Use when the user wants to publish a local project to GitHub for the first time. Triggers on: "github-create", "create a repo", "push this to github", "put this on github", "create a github repo", "let's make a repo", or any request to publish a local project to GitHub as a new repository.
---

# GitHub Create

Create a new GitHub repository from the current local project with all the finishing touches.

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

Check if a `LICENSE` file exists in the project root.

If no LICENSE exists:

1. Gather candidate names for attribution:
   - Check the user's memory files for a stored license attribution name.
   - Run `git config user.name` for their git identity.
   - Extract the GitHub username or org name from the repo URL (the owner portion of `owner/repo`).
2. **If a stored name is found in memory**: Ask with a light touch: "Shall I add an MIT License attributed to **[Name]**? (Or would you prefer a different name for this one?)"
3. **If no stored name is found**: Present all the candidate names found (git config name, GitHub username/org) and ask which to use. Offer to remember the choice for future projects.

Use the template at `assets/MIT-LICENSE-TEMPLATE`, replacing `{{YEAR}}` with the current year and `{{AUTHOR}}` with the confirmed name.

If a LICENSE already exists, skip this step.

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

### Step 9: Commit and push finishing touches

Stage any new files created (README.md, LICENSE, .github/workflows/release.yml) and commit:

```bash
git add README.md LICENSE .github/  # only files that were created/modified
git commit -m "chore: add project documentation"
git push origin HEAD
```

If any git command is denied by the user's permissions, list the files that need committing and provide the commands for the user to run themselves. Then carry on with any remaining non-git steps. Do not retry denied commands or try to work around the restriction.

### Step 10: Done

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
