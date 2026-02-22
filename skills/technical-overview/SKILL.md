---
name: technical-overview
description: |
  Generate a TECHNICAL_OVERVIEW.md file for any codebase. Automatically detects the tech stack, explores models/routes/services, and produces a concise reference document that helps future AI sessions (or humans) quickly understand the project without re-exploring. Use when starting work on an existing project, onboarding to a new codebase, or creating documentation for your team. Works with Laravel, Rails, Django, Node/Express, and other common stacks.
---

# Technical Overview Generator

Generate a concise `TECHNICAL_OVERVIEW.md` file that captures the essential information needed to understand and work with a codebase.

## Purpose

This document helps future AI sessions (and humans) quickly orient themselves without re-exploring the entire codebase. It should be:
- **Concise**: 100-200 lines max
- **Actionable**: Where to look, not exhaustive documentation
- **Current**: Include a "Last updated" date

## Process

### 1. Detect the Stack

Check for framework indicators:

| File | Indicates |
|------|-----------|
| `composer.json` | PHP (Laravel, Symfony) |
| `package.json` | Node.js / JavaScript |
| `Gemfile` | Ruby (Rails) |
| `requirements.txt` / `pyproject.toml` | Python (Django, Flask) |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

Extract key dependencies and versions from these files.

### 2. Check the README

Read `README.md` (or `README.rst`, etc.) and assess:
- Does it have a clear one-sentence description of what the app does?
- Or is it boilerplate/empty?

**If boilerplate or unclear**: Ask the user:
> "What does this application do in one sentence?"

### 3. Explore the Codebase

Adapt exploration based on detected stack:

#### Laravel/PHP
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

#### Rails/Ruby
- `app/models/` - ActiveRecord models
- `app/controllers/` - Controllers
- `config/routes.rb` - Routes
- `app/services/` - Service objects
- `db/schema.rb` - Database schema

#### Django/Python
- `*/models.py` - Django models
- `*/views.py` - Views
- `*/urls.py` - URL routing
- `*/services.py` or `*/utils.py` - Business logic

#### Node/Express
- `src/models/` or `models/` - Data models
- `src/routes/` or `routes/` - Route handlers
- `src/services/` or `services/` - Business logic
- `src/middleware/` - Custom middleware

### 4. Identify Key Patterns

Look for:
- **Authorization model**: Roles, permissions, policies, middleware
- **Custom conventions**: Non-standard patterns, blade directives, decorators
- **Feature flags**: Config-based feature toggles
- **Business logic locations**: Where the "interesting" code lives
- **Testing patterns**: Test structure, factories, fixtures

### 5. Generate the Document

Use this template structure:

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

See the `examples/` directory for sample outputs from different frameworks.
