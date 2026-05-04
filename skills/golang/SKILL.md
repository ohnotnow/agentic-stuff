---
name: golang-user-conventions
description: >
  Users conventions and patterns for Go CLI/TUI projects. Use when working on a Go
  project
allowed-tools: "Read,Write,Edit,Bash,Glob,Grep"
version: "0.4.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# Go CLI/TUI Project Conventions

Standards for building small, focused Go tools — single self-contained binaries
that are easy to share and cross-compile. These are opinionated defaults, not
laws. Scale up or down based on the project.

## Conditional sections

This skill is split across files. SKILL.md (this file) covers conventions that
apply to any Go CLI. Two satellite files cover situational topics — only read
them when relevant:

- **`TUI.md`** — Bubble Tea, lipgloss, huh, theming, the `Width()` footgun,
  shelling out to `$EDITOR`.
  Read when: `go.mod` imports `github.com/charmbracelet/...`, **or** the user's
  request mentions a TUI / Bubble Tea / interactive terminal UI / list / form /
  picker, **or** you're starting a new project and the user has described
  something interactive.
- **`WEB.md`** — embedded web UI conventions (`serve` subcommand, `go:embed`,
  `http.Handler` patterns, JSON API).
  Read when: the project has a `serve` subcommand or imports `net/http` for
  serving (not just fetching), **or** the user's request mentions a web
  dashboard, browser UI, or `serve` command.

Don't load these defensively — the savings only work if you actually skip
them when they don't apply. If a session shifts direction (a CLI gains a TUI,
a tool grows a `serve` command), pull the satellite file in mid-session.

Reusable code lives under `templates/` (e.g. `templates/theme/nord.go` for
Nord-themed lipgloss + huh styles) and is referenced from the satellite that
covers it.

## Project Layout

Choose the simplest layout that fits the project's complexity:

### Single file (`main.go` only)
For scripts-with-a-GUI. Under ~400 lines, no real domain logic, mostly glue
between config/OS/UI. Example: a music shuffler, a quick file picker.

### Flat `package main`, multiple files
When you have distinct concerns (storage, domain types, UI) but they're tightly
coupled and nobody will import the code as a library. Split by concern:

```
myapp/
  main.go       # Entrypoint, arg parsing, wiring
  store.go      # Database access, queries, migrations
  types.go      # Domain types, enums, validation
  ui.go         # Bubble Tea model, update, view
  *_test.go     # Tests alongside source
  go.mod
```

This is the default for most projects.

### `internal/<name>/` package
When the tool has 5+ source files, subcommands, a public-facing contract (JSON
API, stable exit codes, documented ID format), or genuinely separable concerns.
The `internal/` boundary prevents accidental imports.

```
myapp/
  main.go                  # Thin: flag extraction, open DB, dispatch
  internal/myapp/
    app.go                 # Command router, handlers
    store.go               # DB access, schema, migrations
    migrate.go             # Migration definitions
    types.go               # Domain types, validation
    config.go              # Config detection, defaults
    format.go              # Output formatting
  main_test.go             # Integration tests
  go.mod
```

### Multiple distinct domains under `internal/`
When the project has genuinely separate domains (not just layers of one domain),
use separate packages under `internal/`. For example, a tool that fetches RSS
feeds, stores data, and serves a web UI has three distinct domains:

```
myapp/
  main.go                  # Entrypoint, wiring
  internal/
    db/db.go               # Storage layer
    models/models.go       # Shared data types
    youtube/               # External API integration
      youtube.go
      rss.go
      fetch.go
    web/                   # Embedded web UI
      server.go
      static/index.html
  go.mod
```

This is appropriate when each package has its own distinct responsibility and
the packages communicate through the shared models. Don't flatten genuinely
separate domains into a single package just for consistency.

**Heuristic:** if you're reaching for more than ~4 source files, or the tool has
subcommands, use `internal/`. Otherwise flat is fine.

---

## CLI Flag Parsing

Always use `flag.FlagSet` from the standard library for command-line flags. One
FlagSet per subcommand. Don't hand-roll argument parsing — it leads to
inconsistencies across projects and breaks down with boolean flags, `--flag=value`
syntax, or help text.

```go
func runAdd(args []string) error {
    fs := flag.NewFlagSet("add", flag.ContinueOnError)
    category := fs.String("category", "", "category name")
    fs.SetOutput(io.Discard) // Suppress default help output
    if err := fs.Parse(args); err != nil {
        return err
    }
    // fs.Args() returns remaining positional arguments
    url := fs.Arg(0)
    // ...
}
```

For tools with subcommands, dispatch on `os.Args[1]` (or the first positional
arg) then pass the remaining args to the subcommand's FlagSet. No need for
cobra or other frameworks — `flag.FlagSet` per subcommand is sufficient for
focused tools.

---

## SQLite

When a project needs persistent storage, use SQLite.

### Dependencies
- Always `modernc.org/sqlite` — pure Go, no CGo, cross-compiles cleanly.
- Import as `_ "modernc.org/sqlite"` with `database/sql` for the driver.

### Opening the database
Set these pragmas on every connection immediately after opening:

```go
db.ExecContext(ctx, "PRAGMA foreign_keys = ON")
db.ExecContext(ctx, "PRAGMA busy_timeout = 5000")
db.ExecContext(ctx, "PRAGMA journal_mode = WAL")
```

For in-memory databases (tests), limit to a single connection to keep the DB
alive across queries:

```go
db.SetMaxOpenConns(1)
```

### Schema and migrations
Always use a `schema_version` table and numbered, forward-only migrations. Users
may skip releases, so each migration must be independently applicable — just
apply all versions newer than the current one.

**schema_version table:**
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, 0);
```

**Migration structure:**
```go
type migration struct {
    version     int
    description string
    apply       func(ctx context.Context, tx *sql.Tx) error
}

var migrations = []migration{
    {1, "baseline schema", func(ctx context.Context, tx *sql.Tx) error {
        _, err := tx.ExecContext(ctx, `CREATE TABLE ...`)
        return err
    }},
    // Append new migrations here. Never modify existing ones.
}
```

**Applying migrations:**
```go
func runMigrations(ctx context.Context, db *sql.DB) error {
    var current int
    db.QueryRowContext(ctx, "SELECT version FROM schema_version WHERE id = 1").Scan(&current)

    for _, m := range migrations {
        if m.version <= current {
            continue
        }
        tx, _ := db.BeginTx(ctx, nil)
        if err := m.apply(ctx, tx); err != nil {
            tx.Rollback()
            return fmt.Errorf("migration %d (%s): %w", m.version, m.description, err)
        }
        tx.ExecContext(ctx, "UPDATE schema_version SET version = ? WHERE id = 1", m.version)
        tx.Commit()
    }
    return nil
}
```

**Scale the migration complexity to the project:**
- Personal tools: simple `ALTER TABLE ADD COLUMN` is fine.
- Distributed tools with critical data: use backup/drop/recreate when SQLite
  can't alter constraints in place (e.g. changing CHECK constraints).

### DB path conventions
- **Project-scoped tools** (like an issue tracker): store the DB in the current
  directory, gitignore it.
- **User-facing tools**: store in `~/.config/<toolname>/` using
  `os.UserConfigDir()`.

---

## Configuration

- **Project-scoped tools** (end user is an agent or the tool is per-repo):
  DB-hosted config, single-row table with `CHECK (id = 1)`.
- **User-facing tools**: YAML config in `~/.config/<toolname>/config.yaml`.
  Always ship a `.example` file. Use `gopkg.in/yaml.v3`. Provide sensible
  defaults so the tool works without any config file.

---

## Error Handling

### CLI tools with structured output (JSON)
Use a typed error with code, message, and exit code:

```go
type CLIError struct {
    Code     string // "validation", "not_found", "usage", "internal"
    Message  string
    ExitCode int    // 64=usage, 65=validation, 66=not_found, 1=internal
}
```

Output errors as JSON: `{"error": {"code": "...", "message": "..."}}`.

### TUI apps
Plain `error` returns from store/logic layers. In the UI, set `m.status` to a
short human-readable message. No logging frameworks.

---

## Testing

- **Stdlib `testing` only.** No testify, no ginkgo.
- **Always test the store layer and domain logic.**
- **TUI rendering tests are optional** (read: skip them).
- Use `:memory:` SQLite with a helper:

```go
func newTestStore(t *testing.T) *Store {
    t.Helper()
    s, err := NewStoreWithPath(":memory:")
    if err != nil {
        t.Fatalf("create test store: %v", err)
    }
    t.Cleanup(func() { s.Close() })
    return s
}
```

- Use `t.Helper()` on all test helpers.
- Use `t.Cleanup()` for teardown instead of manual defer.
- Use `t.Run("subtest name", ...)` to organise related assertions.
- Test that migrations apply cleanly on a fresh database.

---

## Shell Completion (for richer CLIs)

For tools with multiple subcommands, flags, and user-facing IDs, offer a
`completion` subcommand that prints a bash or zsh completion script. This is
the standard pattern used by kubectl, gh, docker, etc. — the binary generates
its own completion script.

**Only worth adding when** the tool has enough commands/flags/IDs that tab
completion genuinely saves time. A simple TUI app with no subcommands doesn't
need it.

### How it works

1. Register `completion` as a command that **does not need the database** (so it
   works before any init/setup).
2. The command prints a shell script to stdout. The user sources it:
   ```bash
   eval "$(mytool completion bash)"          # in .bashrc
   mytool completion zsh > ~/.zsh/completions/_mytool  # for zsh
   ```
3. **Generate the script from the command registry** — build the command names,
   flags, and subcommands programmatically so completions never drift out of
   sync with the actual CLI.

### Key patterns

**Static completions** — command names, flag names, enum values (statuses,
types, priorities) are baked into the script at generation time:

```go
func generateBashCompletion() string {
    cmdNames := strings.Join(CommandNames(), " ")
    // Build per-command flag cases from the registry...
    return fmt.Sprintf(`_mytool_completions() {
    local commands="%s"
    # ...
}
complete -F _mytool_completions mytool
`, cmdNames)
}
```

**Dynamic completions** — for user data like issue IDs, the generated script
calls the tool at tab-time to fetch live values:

```bash
# Inside the generated completion script:
ids=$(mytool list --all 2>/dev/null | grep -o '"id": *"[^"]*"' | sed 's/"id": *"//;s/"//')
COMPREPLY=($(compgen -W "${ids}" -- "${cur}"))
```

This is what makes `mytool show f<tab>` expand to the full ID — it runs
`mytool list` in the background and offers matching IDs.

**Zsh gets richer output** — use `_describe` for command descriptions and
`_arguments` for flag documentation. Bash uses `compgen -W` for simple word
matching.

### When to offer it

Ask whether completion would be useful when the project has:
- Multiple subcommands (5+)
- Flags with enumerated values
- User-facing IDs or names that benefit from tab-expansion

For simpler tools, skip it entirely.

---

## Build

Single self-contained binary. No CGo.

```bash
go build -o <name> .
go test ./...
```

Cross-compile with standard `GOOS`/`GOARCH`:
```bash
GOOS=linux GOARCH=amd64 go build -o <name>-linux .
GOOS=darwin GOARCH=arm64 go build -o <name>-macos .
GOOS=windows GOARCH=amd64 go build -o <name>.exe .
```

---

## Out of Scope

This skill does not cover:
- Standalone web services / HTTP APIs (embedded web UIs for CLI tools are covered in WEB.md)
- Multi-package library design
- Anything requiring CGo
- JS build pipelines or frontend frameworks (keep embedded UIs as vanilla HTML/JS)
- Complex build pipelines (goreleaser, etc.)
