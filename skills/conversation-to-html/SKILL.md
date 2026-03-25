---
name: conversation-to-html
description: "Convert a Claude Code or Codex CLI session into a beautiful, shareable single HTML file for presentations and workshops. Supports both Claude Code and OpenAI Codex CLI session logs. Use when the user wants to showcase, export, present, or share a coding agent conversation as HTML. Also triggers on: 'conversation to html', 'export session', 'share this conversation', 'make a transcript', 'session to html', 'presentation from session', 'showcase conversation', 'codex session', or any request to turn a Claude Code or Codex session into a shareable format. Should be used proactively when the user mentions workshops, demos, or sharing coding agent conversations."
---

# Conversation to HTML

Convert Claude Code or Codex CLI sessions into polished, branded HTML transcripts for sharing and presentations.

## Workflow

### 1. Find the session

The user may provide:
- **Nothing** (default): find the latest *completed* session for the current project
- **A session ID**: use that specific session
- **A file path**: use that JSONL file directly

#### Default: discover the latest session

Claude Code stores sessions at `~/.claude/projects/{encoded-path}/`. The encoded path replaces `/` with `-` in the absolute CWD path.

To find sessions, run:

```bash
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --list-sessions
```

This lists all sessions for the current project, sorted by most recent first. The current in-progress session is included — it's fine to convert it.

If the user wants a specific session, use `--session-id UUID` with `--discover`.

### 2. Confirm with the user

Briefly tell the user:
- Which session was found (show the slug, date, and message count)
- Ask for a title (suggest one based on the project name or session content)

### 3. Generate the HTML

When `--title` is provided and no explicit `-o` is given, the script automatically generates a filename from the title as a filesystem-safe slug with today's date appended (e.g. `--title "Chat About Lovely Cats"` produces `chat-about-lovely-cats-2026-03-25.html`). You do not need to pass `-o` unless the user wants a specific path.

```bash
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --discover \
  --format html \
  --timestamps \
  --title "Your Title Here"
```

Or with a specific session:

```bash
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --discover \
  --session-id "SESSION_UUID" \
  --format html \
  --timestamps \
  --title "Your Title Here"
```

Or with a direct file path:

```bash
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  /path/to/session.jsonl \
  --format html \
  --timestamps \
  --title "Your Title Here"
```

### 4. Verify the output

```bash
head -n 40 conversation.html
```

Check:
- Title is correct
- No system prompts, CLAUDE.md content, or tool calls leaked through
- Messages are in the right order
- User and assistant roles are correct

### 5. Tell the user

Report where the file was written and its message count. Suggest they open it in a browser to preview.

## Output features

The generated HTML includes:
- Hero section with session metadata (date, duration, model, message count)
- Chat-bubble layout (user messages right-aligned in blue, assistant left-aligned in white)
- Avatar icons (person for user, star for assistant)
- Syntax-highlighted code blocks via Prism.js (requires internet for CDN; degrades gracefully offline)
- Floating message navigation panel (bottom-right button)
- Smooth reveal animations (capped at message 20 to avoid long delays)
- Responsive layout for mobile and desktop
- Print-friendly styling with page-break protection
- Noto Sans typography from Google Fonts

## Codex CLI sessions

For Codex sessions, add `--source codex` to all commands. Codex stores sessions at `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (not organised by project).

```bash
# List Codex sessions
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --source codex --list-sessions

# Generate HTML from latest Codex session
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --source codex \
  --discover \
  --format html \
  --timestamps \
  --title "Codex Session"
```

You can also pass a specific Codex JSONL file directly (with `--source codex` to use the correct parser):

```bash
python3 ~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py \
  --source codex \
  ~/.codex/sessions/2026/03/24/rollout-*.jsonl \
  --format html \
  --timestamps \
  --title "Codex Session"
```

The `--session-id` flag does substring matching for Codex, so you can use a partial UUID.

## Script location

The rendering script lives at:
`~/.claude/skills/conversation-to-html/scripts/extract_chat_markdown.py`
