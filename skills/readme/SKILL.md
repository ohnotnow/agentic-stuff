---
name: readme
description: |
  Generate a GitHub-style README.md for the current project by reading the actual codebase. Use when the user asks to "generate a readme", "write a readme", "document this project", "create a readme", or invokes /readme. Also callable from the github-create skill.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - Agent
  - AskUserQuestion
---

# README generator

Generate an accurate, human-sounding README.md by reading the actual codebase. Every claim in the README should be verifiable from the code.

## Workflow

### Step 1: Check for existing README

Look for `README.md` in the project root.

- **No README exists**: proceed to step 2.
- **README exists but is boilerplate**: offer to replace it. Detect boilerplate by checking for these phrases:
  - "Laravel is a web application framework"
  - "This README would normally document"
  - "This project was bootstrapped with"
  - "This template provides a minimal setup"
  - Or: file is under 5 lines with only a heading and no real content
- **README exists and looks genuine**: ask the user what they want — regenerate from scratch, update specific sections, or leave it alone.

### Step 2: Read style guidelines

Check for `assets/guidelines.md` in this skill's directory (`~/.claude/skills/readme/assets/guidelines.md`).

If the file exists and has content, read it and follow its guidance. The guidelines file takes priority over the defaults in this skill. It is the main customisation point for teams and individuals — they can add their own conventions without editing this SKILL.md.

### Step 3: Detect project type

Check for manifest files to identify the stack:

| File | Stack |
|------|-------|
| `composer.json` + `artisan` | Laravel |
| `composer.json` | PHP |
| `pyproject.toml` or `requirements.txt` | Python |
| `package.json` + `next.config.*` | Next.js |
| `package.json` + `nuxt.config.*` | Nuxt |
| `package.json` | Node.js |
| `Gemfile` + `config/routes.rb` | Rails |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

Check from most specific to least specific (e.g. check for Laravel before generic PHP).

### Step 4: Read the codebase

Read the project to understand what it actually does. Work in this order:

1. **Manifest file** (`package.json`, `pyproject.toml`, `composer.json`, `Cargo.toml`, `go.mod`, etc.) — extract project name, description, dependencies, scripts/commands, version.
2. **Entry points** — `main.*`, `index.*`, `app.*`, `src/index.*`, CLI definitions, route files.
3. **Key directories** — scan `src/`, `app/`, `lib/`, `cmd/` to understand the project structure. Read 5-10 key files at most. Do not attempt to read the entire codebase.
4. **Infrastructure markers** — check for Dockerfile, `.github/workflows/`, `.gitlab-ci.yml`, `.env.example`, Makefile, `docker-compose.yml`.
5. **Licence file** — check if `LICENCE`, `LICENSE`, or `LICENSE.md` exists.
6. **Git repository** — check if the project is a git repository. If so try and establish the github URL for clone/install guidelines.

### Step 5: Ask the user (only if needed)

If the one-line project description is not clear from the manifest or code, ask the user:

> "What does this project do in one sentence?"

Ideally ask zero questions. Only ask if you genuinely cannot infer the purpose.

### Step 6: Write the README

Write the complete README.md to the project root as a single file.

#### Sections to include

**Always include:**

- **Project name** — from the manifest or directory name
- **One-line description** — what the project is, in one sentence
- **What it does** — 2-4 factual sentences explaining what the project does, grounded in actual code
- **Getting started** — prerequisites and setup commands, tailored to the detected stack (see the stack guidance table below)

**Include only when there is real content to put in them:**

- **Usage / examples** — only if there are CLI entry points, API routes, or obvious usage patterns in the code
- **Configuration** — only if the project has meaningful environment variables or config files beyond framework defaults
- **Development** — only if there are test commands, linting, or build steps worth documenting
- **API reference** — only for libraries or packages with a public API
- **Deployment** — only if there is a Dockerfile, CI config, or deploy script
- **Licence** — only if a licence file exists in the project

**Never include empty sections or sections with placeholder content.** If there is nothing real to say, leave the section out entirely.

#### Stack-specific getting started defaults

| Stack | Prerequisites | Setup | Run |
|-------|--------------|-------|-----|
| Laravel | PHP 8.x, Composer (Lando if `.lando.yml` present) | `lando start` or `composer install` | `php artisan serve` |
| Python | Python 3.x, uv (if pyproject.toml uses uv) | `uv sync` | `uv run ...` |
| Node | Node 18+, npm/yarn/pnpm (detect from lockfile) | `npm install` | `npm start` / `npm run dev` |
| Go | Go 1.21+ | `go mod download` | `go run .` |
| Rust | Rust/Cargo | `cargo build` | `cargo run` |

Always prefer actual commands found in the project over these defaults. Read the manifest's scripts section, Makefile targets, or pyproject.toml scripts to find the real commands.

### Step 7: Pick a tone

Before running the humaniser, decide whether the project suits a `natural` or `professional` tone.

**Signals for `natural`** (personal, opinionated, first-person friendly):
- Single author, hobby or experimental project
- Playful or informal project name
- No `CONTRIBUTING.md`, no CI config, no corporate package namespace
- README audience is likely the author or casual users

**Signals for `professional`** (clear, measured, third-person):
- Multiple contributors or team-owned
- Has `CONTRIBUTING.md`, code of conduct, or formal issue templates
- Corporate or organisational package namespace
- Library or framework intended for external consumers
- CI/CD pipelines, release workflows, semantic versioning

**When it's ambiguous** — for example a well-structured Laravel app that could be either a personal experiment or a work project — ask the user:

> "This looks like it could be a personal project or something more formal. Should the README sound casual and personal, or more professional?"

Most of the time this question won't fire. Only ask when the signals genuinely point both ways.

### Step 8: Run the humaniser agent

Check if `~/.claude/agents/humaniser.md` exists. If it does, spawn it as a sub-agent using the Agent tool, pointing it at the README.md file you just wrote and telling it to use the tone chosen in step 7. The humaniser agent runs with fresh context (no memory of writing the README) and does an editorial pass to remove AI writing patterns.

If the agent file does not exist, skip this step silently.

## Writing rules

Follow these rules when writing the README. They are guardrails against common AI writing patterns.

- Use sentence case for headings (not Title Case Every Word)
- No emojis and no badges unless the user specifically asks for them
- No "serves as", "stands as", "functions as" — just use "is"
- No significance inflation — avoid "pivotal", "crucial", "vibrant", "vital", "key"
- No promotional language — avoid "groundbreaking", "stunning", "seamless", "powerful"
- No rule-of-three lists (don't force ideas into groups of three)
- No em dashes — use commas or full stops instead
- No generic positive conclusions ("the future looks bright", "exciting times ahead")
- No boldface-header bullet lists (e.g. "**Speed:** faster builds" — just write prose or plain lists)
- Be specific and factual — every claim should be verifiable from the code you read
- Vary sentence length naturally — not every sentence needs to be the same structure
- If something is not known from the code, leave it out rather than hedging or guessing
- No AI vocabulary words: Additionally, delve, enhance, foster, garner, landscape, tapestry, testament, underscore, valuable, vibrant, showcase, interplay, intricate
- No synonym cycling — if you said "the project" once, you can say "the project" again instead of "the tool", "the system", "the application"
- No "not only X but also Y" constructions
- No curly quotes — use straight quotes

These rules catch the worst offenders. The humaniser agent (step 7) does a more thorough editorial pass.

## Integration with github-create

When called from the github-create skill, this skill generates the README, picks a tone (step 7), and runs the humaniser agent, then returns. It does not handle licence creation, repository description, or any git operations — github-create manages those separately.

## The guidelines file

The `assets/guidelines.md` file is the main customisation point for this skill. If you share this skill with a team, each person can edit `guidelines.md` to match their conventions without touching SKILL.md.

Examples of what might go in `guidelines.md`:

- "We always use Python 3.14+ and `uv` rather than `pip`"
- "Include a 'Contributing' section in every README"
- "Our projects are internal tools — skip the licence section"
- "Always mention that we use Docker for local development"
- "Our READMEs should be concise — no more than 80 lines"
