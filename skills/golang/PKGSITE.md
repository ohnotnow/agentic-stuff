# pkg.go.dev API (v1beta)

The official pkg.go.dev API, launched May 2026, exposes the same metadata that
backs the pkg.go.dev website as a stateless, GET-only JSON service. Useful when
you need to answer questions like "what's the latest version of X?", "does this
module have known vulnerabilities?", "what does this package export?", or "who
imports this?" — without scraping HTML or shelling out to `go list -m`.

There are two ways in:

1. **`pkgsite-cli`** — the official reference client. Reach for this first.
   Covers the common questions in one-liners.
2. **Raw HTTP** — the underlying JSON API. Use when you need something the CLI
   doesn't cover yet (notably `/vulns`), structured output for further
   processing, or you're embedding lookups inside a Go program.

- **Base URL:** `https://pkg.go.dev/v1beta`
- **Interactive reference:** <https://pkg.go.dev/v1beta/api>
- **OpenAPI spec:** <https://pkg.go.dev/v1beta/openapi.yaml>
- **Reference client source:** [`pkgsite-cli`](https://github.com/golang/pkgsite/tree/master/cmd/internal/pkgsite-cli)

No authentication is required and no rate limits are documented — treat it as
a public best-effort service.

---

## Prefer `pkgsite-cli` for quick lookups

The user has `pkgsite-cli` installed at `~/go/bin/pkgsite-cli` (usually on
`PATH` via `~/go/bin`). If it's missing on another machine:

```bash
go install golang.org/x/pkgsite/cmd/internal/pkgsite-cli@latest
```

It currently exposes three commands — `package`, `module`, `search` — with
flags that cover most of the API. More are promised in future releases.

```bash
# Search the index
pkgsite-cli search uuid

# Inspect a package
pkgsite-cli package github.com/google/go-cmp/cmp

# Reverse dependencies (who imports this?)
pkgsite-cli package -imported-by github.com/google/go-cmp/cmp

# Exported symbols
pkgsite-cli package -symbols github.com/google/go-cmp/cmp

# Module info
pkgsite-cli module github.com/google/go-cmp

# Tagged versions of a module
pkgsite-cli module -versions github.com/google/go-cmp

# Versions + packages in one shot
pkgsite-cli module -packages -versions github.com/google/go-cmp
```

Run `pkgsite-cli <command> -h` for the full flag list on each subcommand.

**Caveats:**
- **No `vulns` command yet.** For vulnerability lookups you must hit
  `/v1beta/vulns/{path}` directly (or use `govulncheck` against a local
  module, which is better when you have the source).
- The **wire format is stable; the CLI flag surface is explicitly not yet
  stable.** If you script around `pkgsite-cli` in CI, pin the version or
  prefer raw HTTP.

---

## Raw API — when to drop down

Use the JSON API directly when you need:
- **Vulnerabilities** (`/v1beta/vulns/{path}`) — the CLI doesn't expose this.
- **Structured JSON output** to pipe into `jq` or parse in code (the CLI is
  designed for human reading).
- **Pagination, filtering, or version pinning** at fine grain — the `?filter=`
  regex and `?token=` pagination aren't surfaced via CLI flags.
- **In-process calls** from a Go program — just call `net/http` rather than
  shelling out to a CLI whose flags may change.

### Endpoints at a glance

| Endpoint | Returns |
|----------|---------|
| `/v1beta/package/{path}` | Metadata for a single package |
| `/v1beta/module/{path}` | Metadata for a module |
| `/v1beta/versions/{path}` | Tagged versions (and up to 10 recent pseudo-versions) of a module |
| `/v1beta/packages/{path}` | All packages contained in a module |
| `/v1beta/search?q={query}` | Search results (matches path or synopsis) |
| `/v1beta/symbols/{path}` | Symbols declared by a package |
| `/v1beta/imported-by/{path}` | Paths of packages that import this one (excludes same-module imports) |
| `/v1beta/vulns/{path}` | Known vulnerabilities (sourced from <https://vuln.go.dev>) |

### Common query parameters

Most endpoints accept some subset of these — see the
[interactive reference](https://pkg.go.dev/v1beta/api) for the exact set per
endpoint.

| Param | Type | Notes |
|-------|------|-------|
| `module` | string | Module path, for disambiguation (see below) |
| `version` | string | Semver (`v1.2.3`), `latest`, or branch (`master`/`main`). Defaults to latest tagged |
| `goos` / `goarch` | string | Build context for docs/symbols (e.g. `linux`, `amd64`) |
| `limit` | int | Max items in a paginated response |
| `token` | string | Pagination cursor — pass the previous response's `nextPageToken` |
| `filter` | string | Regex matched against the result set. **Must be percent-encoded.** Use `url.QueryEscape` from Go |

Endpoint-specific extras:

- `/package/{path}` — `doc` (`text`/`html`/`md`/`markdown`), `examples` (bool),
  `imports` (bool), `licenses` (bool). Documentation is only returned when
  `doc` is set.
- `/module/{path}` — `licenses` (bool), `readme` (bool).
- `/search` — `symbol` (further restrict matches to packages exporting a
  symbol matching this string).

### Pagination

List endpoints return a paginated envelope:

```json
{
  "items": [ ... ],
  "total": 1234,
  "nextPageToken": "opaque-string-or-empty"
}
```

Loop until `nextPageToken` is empty, passing the previous token as `?token=...`
on each follow-up. Don't try to interpret the token — it's opaque.

### Error responses

```json
{
  "code": 400,
  "message": "ambiguous path",
  "fixes": ["specify ?module=example.com/a"]
}
```

The `fixes` array is usually the most useful field — it often tells you the
exact query parameter to add. Surface it in any client you build instead of
collapsing the error to a plain string.

### Path ambiguity ("precision over convenience")

Unlike the website, the API will not guess which module a package belongs to.
If `example.com/a/b/c` could live in either module `example.com/a` or
`example.com/a/b`, the response is an error with a `candidates` list of the
possible module paths.

To resolve, **reissue the same request with a `?module=` parameter** pointing
at one of the candidates — don't change the path. The website silently picks
the longest match; the API refuses to.

```bash
# Ambiguous → error with candidates
curl -s "https://pkg.go.dev/v1beta/package/example.com/a/b/c"

# Disambiguated
curl -s "https://pkg.go.dev/v1beta/package/example.com/a/b/c?module=example.com/a/b"
```

### Headline response shapes

**Package** (`/package/{path}`):
```json
{
  "modulePath": "string",
  "version": "string",
  "isLatest": true,
  "isStandardLibrary": false,
  "goos": "all",
  "goarch": "all",
  "path": "string",
  "name": "string",
  "synopsis": "string",
  "isRedistributable": true
}
```

**Module** (`/module/{path}`):
```json
{
  "path": "string",
  "version": "string",
  "commitTime": "RFC3339 timestamp",
  "isLatest": true,
  "isRedistributable": true,
  "isStandardLibrary": false,
  "hasGoMod": true,
  "repoUrl": "string"
}
```

**Versions** (`/versions/{path}`) — paginated `ModuleVersion` items including
`version`, `commitTime`, `latestVersion`, `deprecated`, `deprecationReason`,
`retracted`, `retractionReason`. Check `deprecated`/`retracted` before
recommending an upgrade target — neither is shown on the website's version
selector.

**Symbols** (`/symbols/{path}`):
```json
{
  "modulePath": "string",
  "version": "string",
  "symbols": {
    "items": [
      { "name": "...", "kind": "Type|Function|Method|Constant|Variable|Field",
        "synopsis": "...", "parent": "..." }
    ],
    "total": 42
  }
}
```

**Imported-by** (`/imported-by/{path}`) — `importedBy.items` is a flat list of
package paths. Same-module importers are excluded.

**Vulnerabilities** (`/vulns/{path}`) — paginated items of
`{ "id": "GO-YYYY-NNNN", "details": "..." }`. Treat this as a complement to
`govulncheck`, not a replacement — `govulncheck` knows your actual call graph,
this only knows the module.

For the full shape of every endpoint, the
[interactive reference](https://pkg.go.dev/v1beta/api) and the
[OpenAPI spec](https://pkg.go.dev/v1beta/openapi.yaml) are authoritative —
don't guess fields.

### Worked HTTP examples

```bash
# Latest version of a module
curl -s https://pkg.go.dev/v1beta/module/golang.org/x/time | jq '.version'

# Three most recent versions, with deprecated/retracted flags
curl -s "https://pkg.go.dev/v1beta/versions/golang.org/x/time?limit=3" \
  | jq '.items[] | {version, deprecated, retracted}'

# Look up a package at a branch
curl -s "https://pkg.go.dev/v1beta/package/github.com/google/go-cmp/cmp?version=master" \
  | jq '{path, version}'

# Search, restricted to packages exporting a matching symbol
curl -s "https://pkg.go.dev/v1beta/search?q=uuid&symbol=NewV4" | jq '.items[0]'

# Importers under .io/ TLDs (filter must be percent-encoded)
curl -s "https://pkg.go.dev/v1beta/imported-by/golang.org/x/time/rate?limit=10&filter=%5E.%2A%5C.io%2F"

# Vulnerabilities for a module — not available via pkgsite-cli
curl -s https://pkg.go.dev/v1beta/vulns/golang.org/x/image | jq '.items[].id'
```

---

## When to reach for any of this

Good fits:
- Resolving the **latest tagged version** before updating `go.mod`, especially
  when you also want to check `deprecated`/`retracted` flags.
- Checking **known vulnerabilities** as part of a review pass — complements
  `govulncheck` rather than replacing it.
- Listing a package's **exported symbols** to judge API surface before taking
  on a dependency.
- Finding **who imports** a package — useful for impact estimates before a
  breaking change in a published library.
- Disambiguating a path's owning module without cloning anything.

Less good fits:
- Anything that needs the *local* module graph (`go list -m all`, replaces,
  vendored mods) — pkg.go.dev only knows the public module proxy.
- High-volume bulk queries — no documented batch endpoint or rate limit, so be
  polite (cache, sleep between requests).

---

## Calling the API from Go

Nothing exotic — `net/http` + `encoding/json`. Sketch including error and
candidate handling:

```go
type PackageInfo struct {
    ModulePath        string `json:"modulePath"`
    Version           string `json:"version"`
    IsLatest          bool   `json:"isLatest"`
    Path              string `json:"path"`
    Name              string `json:"name"`
    Synopsis          string `json:"synopsis"`
    IsRedistributable bool   `json:"isRedistributable"`
}

type APIError struct {
    Code       int      `json:"code"`
    Message    string   `json:"message"`
    Fixes      []string `json:"fixes"`
    Candidates []string `json:"candidates,omitempty"`
}

func (e *APIError) Error() string { return e.Message }

func fetchPackage(ctx context.Context, path string) (*PackageInfo, error) {
    u := "https://pkg.go.dev/v1beta/package/" + path
    req, _ := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    if resp.StatusCode != http.StatusOK {
        var apiErr APIError
        _ = json.NewDecoder(resp.Body).Decode(&apiErr)
        return nil, &apiErr
    }
    var info PackageInfo
    if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
        return nil, err
    }
    return &info, nil
}
```

Don't `url.PathEscape` the module path as a whole — slashes are meaningful. If
a path segment genuinely needs escaping (rare), escape only that segment. Do
use `url.QueryEscape` on `filter=` regexes.
