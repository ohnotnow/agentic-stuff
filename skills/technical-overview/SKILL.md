---
name: technical-overview
description: |
  Generate a TECHNICAL_OVERVIEW.md file for any codebase. Automatically detects the tech stack, explores models/routes/services, and produces a concise reference document that helps future AI sessions (or humans) quickly understand the project without re-exploring. Use when starting work on an existing project, onboarding to a new codebase, or creating documentation for your team.
---

# Technical Overview Generator

Generate a concise `TECHNICAL_OVERVIEW.md` file that captures the essential information needed to understand and work with a codebase.

## Purpose

This document helps future AI sessions (and humans) quickly orient themselves without re-exploring the entire codebase. It should be:
- **Concise**: 100-200 lines max
- **Actionable**: Where to look, not exhaustive documentation
- **Current**: Include a "Last updated" date

## Process

### 1. Detect the stack

Read the manifest files (`composer.json`, `package.json`, `go.mod`, `pyproject.toml` and so on) and note the language, framework and key dependency versions.

### 2. Check the README

Read `README.md` (or `README.rst`, etc.) and assess:
- Does it have a clear one-sentence description of what the app does?
- Or is it boilerplate/empty?

**If boilerplate or unclear**: Ask the user:
> "What does this application do in one sentence?"

### 3. Explore the codebase

Find where the app-specific code lives: entry points, the data model, how requests or commands are routed, business logic, configuration and tests. Skip framework boilerplate.

For Laravel, check these:
- `app/Models/*.php` - Domain models and relationships
- `app/Http/Controllers/` - Entry points
- `app/Livewire/` or `app/Http/Livewire/` - Livewire components
- `routes/web.php`, `routes/api.php` - Route definitions
- `app/Services/` - Business logic
- `app/Enums/` - Enumerations
- `app/Providers/AppServiceProvider.php` - Custom setup (Blade directives, etc.)
- `bootstrap/app.php` - Middleware aliases (Laravel 11+)
- `config/` - Custom config files (ignore standard Laravel ones)
- `database/factories/` - Factory states for testing

### 4. Identify Key Patterns

Look for:
- **Authorization model**: Roles, permissions, policies, middleware
- **Custom conventions**: Non-standard patterns, blade directives, decorators
- **Feature flags**: Config-based feature toggles
- **Business logic locations**: Where the "interesting" code lives
- **Testing patterns**: Test structure, factories, fixtures

### 5. Generate the Document

Use this structure as a menu, not a form: keep the sections that fit the project and leave out the rest. For a CLI or TUI, for instance, swap Routes for commands and flags, Authorization for whatever access model it has (often none), and Domain Model for storage (database schema, file formats) and configuration.

```markdown
# Technical Overview

Last updated: YYYY-MM-DD

## What This Is

[One sentence from README or user]

## Stack

- [Language] [Version] / [Framework] [Version]
- [Key packages with versions]

## Directory Structure

```
[Only app-specific directories, not framework boilerplate]
[Annotate what lives where]
```

## Domain Model

```
[ASCII diagram of model relationships]
[Use arrows: → for belongs-to, ←→ for many-to-many]
```

### Key Model Fields

[Only the important fields, not every column]

### Enums

[List enums with their values and helper methods]

## Authorization

[Table of roles and how they're determined]

### [Framework-specific auth patterns]

[Middleware, directives, policies, decorators, etc.]

## Routes Overview

### Web Routes

[Table: Route | Handler | Access level]

### API Routes (if applicable)

[Table: Endpoint | Auth required]

## Key Business Logic

[Table: Location | Purpose]

## Testing

- Framework: [Test framework]
- Pattern: [How tests are structured]
- Factories/Fixtures: [Notable states or helpers]
- Run: [Command to run tests]

## Feature Flags

[List any config-based feature toggles]

## Local Development

[Key commands for local setup]
```

## Important Notes

- **Don't over-document**: This is orientation, not full docs
- **Skip obvious framework boilerplate**: Focus on custom/app-specific code
- **Relationships matter most**: The domain model section is often the most valuable
- **Include the date**: So readers know if it might be stale
- **Ask when uncertain**: If README is unclear, ask the user for the one-liner

## Example Output

See `examples/laravel-livewire-example.md` for one sample output. It shows the expected shape and depth; it is not a template to copy for other stacks.
