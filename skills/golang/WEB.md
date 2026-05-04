# Go Embedded Web UI Conventions

Satellite of `SKILL.md`. Read this when the project has a `serve` subcommand,
embeds a browser UI, or otherwise serves HTTP for its own UI — see the
conditional-loading rule in SKILL.md.

Some CLI tools benefit from a `serve` command that launches a local web UI —
for browsing data at a glance, sharing with non-terminal users, or when the
dataset is better suited to a grid/card layout than a terminal table. The key
principle: the web UI ships inside the binary. No external files, no npm, no
build step for the frontend.

## Embedding static files

Use `go:embed` to bake HTML/CSS/JS into the binary:

```go
package web

import "embed"

//go:embed static/index.html
var indexHTML []byte
```

Keep the frontend as a single `index.html` file with inline CSS and JS. This
keeps embedding trivial and avoids needing a static file server for multiple
assets. For anything beyond a simple dashboard, a single HTML file with vanilla
JS is still preferable to introducing a JS build pipeline.

## HTTP routing

Implement `http.Handler` directly — no framework needed. A switch on
`r.URL.Path` (or `r.URL.Path` + `r.Method` for REST-ish APIs) is fine:

```go
type Server struct {
    db *db.DB
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    switch {
    case r.URL.Path == "/" || r.URL.Path == "/index.html":
        w.Header().Set("Content-Type", "text/html")
        w.Write(indexHTML)
    case r.URL.Path == "/api/items" && r.Method == http.MethodGet:
        s.handleListItems(w, r)
    case r.URL.Path == "/api/items" && r.Method == http.MethodPost:
        s.handleCreateItem(w, r)
    default:
        http.NotFound(w, r)
    }
}
```

## JSON API conventions

- Request bodies: JSON (`json.NewDecoder(r.Body)`)
- Responses: JSON with `Content-Type: application/json`
- Query parameters for filtering/searching (`r.URL.Query().Get("q")`)
- Error responses: appropriate HTTP status codes (400, 404, 409) with a JSON
  body: `{"error": "message"}`
- No CORS headers needed — the frontend is served from the same origin

## The `serve` command

Add it as a subcommand with an optional port flag (default 8080):

```go
case "serve":
    fs := flag.NewFlagSet("serve", flag.ContinueOnError)
    port := fs.String("port", "8080", "port to listen on")
    fs.Parse(args)
    srv := &web.Server{DB: database}
    fmt.Printf("Listening on http://localhost:%s\n", *port)
    http.ListenAndServe(":"+*port, srv)
```
