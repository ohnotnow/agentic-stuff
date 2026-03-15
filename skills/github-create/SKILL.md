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

## Workflow

### Step 1: Verify Environment

Check prerequisites:

```bash
gh auth status
git rev-parse --is-inside-work-tree
git log --oneline -1
```

If not in a git repo, offer to run `git init` and create an initial commit.

If there are uncommitted changes, warn the user and ask whether to commit them first or proceed as-is.

### Step 2: Detect Project Type

Check for framework indicators to inform README generation and .gitignore review:

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

Note the detected stack for later use in README generation.

### Step 3: Gather Details

Ask the user these questions (suggest sensible defaults):

1. **Repository name** - Suggest the current directory name. Accept or override.
2. **Organisation** - Run `gh api user/memberships/orgs --jq '.[].organization.login'` to list available orgs. Present the options plus "personal account". If only one org exists, still ask (do not assume).
3. **Visibility** - Public or private? Default: public.

### Step 4: Create Repository and Push

Build the `gh repo create` command based on answers:

```bash
# Personal account
gh repo create <repo-name> --public --source . --remote=origin --push

# Organisation
gh repo create <org>/<repo-name> --public --source . --remote=origin --push
```

If `origin` remote already exists, warn and ask the user whether to overwrite it or abort.

Extract the repository URL from the output for use in later steps.

### Step 5: Handle README

Assess the current README situation:

1. **No README.md exists** - Check if a `/readme` skill is available. If it is, tell the user: "There's no README yet. You could run `/readme` to generate a detailed one, or I can create a basic one now. Which do you prefer?" If no `/readme` skill exists, offer to create a basic one.
2. **README.md exists but is framework boilerplate** - Detect boilerplate by checking for telltale phrases:
   - Laravel: "Laravel is a web application framework"
   - Rails: "This README would normally document"
   - Django: "Django project"
   - Create React App: "This project was bootstrapped with"
   - Vite: "This template provides a minimal setup"
   - Generic: File is under 5 lines or contains only a heading with no real content
   If boilerplate is detected, offer the same choice as above (dedicated skill or basic README).
3. **README.md exists and looks genuine** - Skip. Do not offer to overwrite.

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

1. Check the user's memory files for a stored license attribution name. 
2. **If a name is found**: Ask with a light touch: "Shall I add an MIT License attributed to **[Name]**? (Or would you prefer a different name for this one?)"
3. **If no name is found**: Check the git config for the users git name and email. Ask: "Would you like me to add an MIT License? If so, what name should it be attributed to?" Offer the names from git and also to remember the name for future projects.

Use the template at `assets/MIT-LICENSE-TEMPLATE`, replacing `{{YEAR}}` with the current year and `{{AUTHOR}}` with the confirmed name.

If a LICENSE already exists, skip this step.

### Step 7: Generate Description

Write a concise repository description (under 100 characters, no emoji, no special characters) based on understanding of the project. This should be a single plain-English sentence summarising what the project does.

### Step 8: Commit and Push Finishing Touches

Stage any new files created (README.md, LICENSE) and commit:

```bash
git add README.md LICENSE  # only files that were created/modified
git commit -m "chore: add project documentation"
git push origin HEAD
```

Then set the repository description (do not skip this step):

```bash
gh repo edit <repo-url> -d "Very short description of the project"
```

### Step 9: Done

Report the repository URL and confirm everything is set up. Keep it brief.

## Important Notes

- Always confirm the organisation and visibility before creating the repo. Creating in the wrong org is a pain to fix.
- Never force-push or overwrite existing remotes without explicit user consent.
- If `gh repo create` fails (e.g. name taken), report the error and ask the user for an alternative name.
- The `resources/readme-style.md` file is optional user customisation for README style preferences. If it does not exist, use sensible defaults.
