# README guidelines

## General tone

Friendly, professional, not *too* formal.  Assume the audience is fairly technical, but keep the top-level overview of the project readable to regular users who might just be looking for a project that 'does that thing I need'.

We are UK-based, so use British English.

## Badges

No badges unless the user explicitly asks for them.  Keep the top of the README clean.

## Sections to include

Beyond the basics (project name, description, "What it does"), always try to include:

- **Prerequisites** — list the tools needed (e.g. Docker, lando, uv, bun) so people don't get stuck at step one
- **Getting started** — including environment setup (`.env` etc.)
- **Running tests** — include the relevant test command for the stack
- **Contributing** — a short section pointing people to clone/fork, install dependencies, and run the tests.  Nothing heavy — just enough to be welcoming.

## Deployment

Skip deployment sections.  Deployment is handled separately and varies too much between projects to be useful in a generic README.

## Licence

Our default license is MIT.  If there isn't a license file in the repo - offer to write one - ask for the users name/organisation so the attribution can be given (if you want brownie points - check the project github url, or git config name/email).

## Technical overview

Please check if there is a `TECHNICAL_OVERVIEW.md` file in the repo.  It's our convention to include a high-level overview of the project in a separate file, so that people who want to can delve a bit deeper but without having to dig through the whole codebase.  If there is *not* a technical overview and you have access to a 'technical overview' skill - you should mention it to the user - but don't invoke the skill or try and use it.  Just give a fyi when you finish up.

## Language/framework specifics

### Python

- Our projects always use `uv` rather than `pip` for installing dependencies.  As many python people aren't yet familiar with uv - please include a markdown-formatted link to the uv project at `https://docs.astral.sh/uv/`
- Assuming there is a pyproject.toml file, you can find the python version requirements there.
- If there *is* an old pip-style requirements.txt file, please mention old-style pip install instructions.

### PHP/Laravel

- We use `lando` to run our local development environment.  Check the `.lando.yml` file (if it exists) for any custom commands (we often have `lando mfs` as a shortcut to migrate / fresh / seed the development database).
- The `.env.example` in our repos is pre-configured for lando local development.  The typical quick-start is:
  1. `cp .env.example .env`
  2. `lando start`
  3. `lando mfs` (to migrate and seed the database)
- Our default seeder (`database/seeders/TestDataSeeder.php`) creates a test user: **admin2x** / **secret**.  Mention this in the README so people can log in straight away.
- Please mention a few regular lando commands to get people started (eg. `lando artisan`, `lando composer`, `lando npm`).
- If `livewire/flux-pro` is in the composer.json then people will need a FluxUI licence to use the full project.  FluxUI is by Caleb Porzio and its homepage is `https://fluxui.dev/`.

### Node / JavaScript

- We use [bun](https://bun.sh/) as both our runtime and package manager.  Use `bun install`, `bun run`, etc. rather than npm/yarn/pnpm.
- If there is a `package.json`, check the `scripts` section for the actual commands to document.

