# Go TUI Conventions (Bubble Tea / Charm)

Satellite of `SKILL.md`. Read this when the project uses (or is about to use)
the Charmbracelet stack — see the conditional-loading rule in SKILL.md.

For interactive terminal UIs, use the Charmbracelet stack.

## Dependencies

```
github.com/charmbracelet/bubbletea    # TUI framework (Elm architecture)
github.com/charmbracelet/lipgloss     # Styling
github.com/charmbracelet/huh          # Forms (input, textarea, select)
github.com/charmbracelet/bubbles      # Widgets (table, etc.) — as needed
```

Use `huh` whenever the TUI needs user input beyond single keypresses (adding
items, editing fields, etc.). It handles focus, validation, and tab-navigation
so you don't have to.

## Model structure

Single model struct, mode-based dispatch:

```go
type mode int

const (
    modeTable mode = iota
    modeAdd
    modeEdit
    modeConfirmDelete
    modeFilter
)

type model struct {
    mode    mode
    store   *Store
    items   []Item
    cursor  int
    status  string    // Transient feedback ("Item added.", "Error: ...")
    err     string    // Fatal error (shown instead of UI)
    filter  string    // Current search/filter text
    form    *huh.Form // Active form (nil when not in form mode)
    // ... mode-specific state
}
```

## Keyboard navigation — think vim

The goal is always: in and out, done. Single-key actions for core functions, no
modifier combos required. Cursor keys work, but power users shouldn't need them.

**Standard keybindings to follow where applicable:**
- `q` / `ctrl+c` — quit
- `j` / `k` / `↑` / `↓` — navigate list
- `/` — search/filter mode (incremental, like vim)
- `1`-`9` — jump directly to item by index
- `a` — add new item
- `e` / `Enter` — edit selected item
- `d` — mark done / toggle completion
- `x` — delete (with confirmation)
- `Esc` — cancel current mode, return to main view

Not every app needs all of these. But when a function maps to one of these keys,
use the standard binding. Consistency across tools is the point.

## Styling

Define lipgloss styles as package-level variables. Reuse across the View function:

```go
var (
    styleTitle  = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205"))
    styleSubtle = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
    styleError  = lipgloss.NewStyle().Foreground(lipgloss.Color("196"))
)
```

For a real palette (Nord, Catppuccin, Gruvbox, etc.) see the **Theming** section
below — semantic aliases beat hex codes scattered through the View.

## View rendering
- Use `strings.Builder` for efficient rendering.
- Check `m.err` first — early return if in error state.
- Status/feedback messages are transient — clear on next keypress.

## Multi-column layouts — avoid the lipgloss Width() footgun

When building side-by-side panes (e.g. a list column + preview column), do
**not** nest styled strings inside a block that has `Width()` set:

```go
// BROKEN: lipgloss miscounts visible width of the nested styles
// and wraps the row, eating a visible line.
row := "▸ " + styleSubtle.Render(date) + " " + label
leftBox := lipgloss.NewStyle().Width(leftWidth).Render(row)
```

The inner `styleSubtle.Render` emits ANSI resets that confuse the outer
`Width()`'s visible-width calculation. It decides the row is over-budget and
wraps it, which renders as a blank leading line that looks like your content
has disappeared.

Instead, pre-pad each row to its exact visible width yourself, then join the
columns with `lipgloss.JoinHorizontal`:

```go
func padToWidth(s string, w int) string {
    vw := lipgloss.Width(s)
    if vw >= w {
        return s
    }
    return s + strings.Repeat(" ", w-vw)
}

// Build each column as pre-padded lines, then join — no outer Width() wrap.
leftCol  := strings.Join(leftLines, "\n")
rightCol := strings.Join(rightLines, "\n")
view := lipgloss.JoinHorizontal(lipgloss.Top, leftCol, " │ ", rightCol)
```

`lipgloss.Width(s)` is ANSI-aware and measures correctly, so use it for the
visible-width check. The outer layout is then just text, and JoinHorizontal
aligns by the tallest block.

## Shelling out to $EDITOR or other external programs

When the TUI needs to suspend itself and hand the terminal over to another
program (an editor, `less`, `git diff`, etc.), use `tea.ExecProcess`. It
releases the alt-screen, runs the command inheriting stdin/stdout/stderr, then
resumes the TUI and fires a completion message:

```go
type editorFinishedMsg struct{ err error }

func openEditorCmd(path string) tea.Cmd {
    editor := os.Getenv("EDITOR")
    if editor == "" {
        editor = "vi"
    }
    c := exec.Command(editor, path)
    return tea.ExecProcess(c, func(err error) tea.Msg {
        return editorFinishedMsg{err: err}
    })
}
```

In your `Update`, handle `editorFinishedMsg` to reload whatever the editor
might have changed (e.g. re-read the file from disk, refresh a list). Don't
try to run the editor inline with `exec.Command(...).Run()` — the alt-screen
and bubbletea input handling will fight you.

---

## Theming

The Charm stack has no global "set theme" call — each component you use
(bubbles widgets, huh forms, custom lipgloss styles in your own View) needs
its styles overridden individually. The trick is to do that override-work
once, against a small set of semantic aliases, not against raw hex codes
scattered through the code.

### Pattern: three layers

Define a `theme` package with:

1. **Raw palette** — the named colours from whatever scheme you use
   (Nord0..Nord15, Catppuccin's mantle/crust/etc., Gruvbox's bg0..fg4).
2. **Semantic aliases** — `Accent`, `Success`, `Warning`, `Error`, `Bg`,
   `Fg`, `FgMuted`. Your app uses these. Switching from Nord to Gruvbox is
   then a one-file change to the alias mapping.
3. **Common styles** — `Title`, `Selected`, `Normal`, `Faint`, `Border`
   built from the semantic aliases.

### Ready-to-copy Nord templates

Two template files ship with this skill:

- `templates/theme/nord.go` — full Nord palette, semantic aliases, common
  lipgloss styles.
- `templates/theme/nord_huh.go` — a `huh.Theme` builder (`theme.NordHuh()`)
  that themes forms to match.

Copy them into a `theme/` package in your project. Then in views:

```go
import "myapp/internal/theme"

s := theme.Title.Render("My App")
// ...
err := huh.NewForm(group).WithTheme(theme.NordHuh()).Run()
```

### Per-component overrides

For bubbles widgets, find each component's `Styles` struct or `DefaultStyles()`
function and assign your themed styles in:

```go
l := list.New(items, list.NewDefaultDelegate(), 0, 0)
l.Styles.Title = theme.Title
l.Styles.HelpStyle = theme.Faint

d := list.NewDefaultDelegate()
d.Styles.SelectedTitle = theme.Selected
l.SetDelegate(d)
```

This is mostly copy-paste boilerplate per component — write it once when you
reach for a new widget.

### Light/dark adaptive

For a single theme that works in both light and dark terminals, use
`lipgloss.AdaptiveColor` for the semantic aliases:

```go
Accent = lipgloss.AdaptiveColor{Light: "#5e81ac", Dark: "#88c0d0"}
```

Lip Gloss picks the right value based on the detected terminal background.

### Contrast tip

Bold foreground on a coloured background can wash out in some terminals
(notably `Selected = Foreground(Bg).Background(Accent).Bold(true)` with a
light-blue accent). Eyeball the result in your real terminal before settling
— if it looks soft, drop `.Bold(true)` or pick a darker accent.
