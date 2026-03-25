#!/usr/bin/env python3
"""Extract a user/assistant transcript from Claude Code session JSONL files.

Supports direct file input, session discovery by project path, and listing
available sessions. Outputs Markdown or a self-contained branded HTML file.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class Message:
    role: str
    text: str
    timestamp: str | None = None


@dataclass
class SessionInfo:
    path: Path
    session_id: str
    modified: float
    slug: str | None = None
    timestamp: str | None = None
    cwd: str | None = None
    message_count: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a user/assistant transcript from a Claude Code session JSONL file."
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        help="Path to the Claude Code session JSONL file (optional when using --discover)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write the transcript. Defaults to <input>.<md|html> based on format.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "html"),
        default="markdown",
        help="Output format to generate.",
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Include timestamps in each transcript section header.",
    )
    parser.add_argument(
        "--title",
        help="Override the top-level title.",
    )
    # Session discovery arguments
    parser.add_argument(
        "--discover",
        nargs="?",
        const=".",
        metavar="PROJECT_PATH",
        help="Find the latest session for a project path (defaults to CWD).",
    )
    parser.add_argument(
        "--list-sessions",
        nargs="?",
        const=".",
        metavar="PROJECT_PATH",
        help="List available sessions for a project path and exit.",
    )
    parser.add_argument(
        "--session-id",
        help="Select a specific session by UUID when using --discover.",
    )
    parser.add_argument(
        "--exclude-session",
        help="Exclude a session by UUID (e.g. to skip the current in-progress session).",
    )
    parser.add_argument(
        "--source",
        choices=("claude", "codex"),
        default="claude",
        help="Session source: 'claude' for Claude Code, 'codex' for OpenAI Codex CLI.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Session discovery
# ---------------------------------------------------------------------------

def encode_project_path(project_path: str) -> str:
    """Encode a project path to the Claude Code directory name format."""
    return project_path.rstrip("/").replace("/", "-")


def discover_sessions(project_path: str, exclude_session: str | None = None) -> list[SessionInfo]:
    """Find all session JSONL files for a project."""
    encoded = encode_project_path(os.path.abspath(project_path))
    sessions_dir = Path.home() / ".claude" / "projects" / encoded

    if not sessions_dir.exists():
        return []

    sessions: list[SessionInfo] = []
    for f in sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        session_id = f.stem
        if exclude_session and session_id == exclude_session:
            continue

        info = SessionInfo(
            path=f,
            session_id=session_id,
            modified=f.stat().st_mtime,
        )

        # Peek at the file for metadata and message count
        try:
            with f.open("r", encoding="utf-8") as handle:
                msg_count = 0
                for i, line in enumerate(handle):
                    if i > 50:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("slug") and not info.slug:
                        info.slug = record["slug"]
                    if record.get("timestamp") and not info.timestamp:
                        info.timestamp = record["timestamp"]
                    if record.get("cwd") and not info.cwd:
                        info.cwd = record["cwd"]
                    if record.get("type") in ("user", "assistant"):
                        msg_count += 1
                # Count remaining messages
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") in ("user", "assistant"):
                            msg_count += 1
                    except json.JSONDecodeError:
                        continue
                info.message_count = msg_count
        except OSError:
            pass

        sessions.append(info)

    return sessions


def format_session_list(sessions: list[SessionInfo]) -> str:
    """Format session list for display."""
    if not sessions:
        return "No sessions found."

    lines = []
    for i, s in enumerate(sessions):
        ts = ""
        if s.timestamp:
            try:
                dt = datetime.fromisoformat(s.timestamp.replace("Z", "+00:00"))
                ts = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                ts = s.timestamp[:16] if s.timestamp else ""

        slug_str = f"  slug: {s.slug}" if s.slug else ""
        latest = " (latest)" if i == 0 else ""
        lines.append(
            f"  {s.session_id}  {ts}  ~{s.message_count} msgs{slug_str}{latest}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Codex session discovery
# ---------------------------------------------------------------------------

def discover_codex_sessions(exclude_session: str | None = None) -> list[SessionInfo]:
    """Find all Codex CLI session JSONL files.

    Codex stores sessions at ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
    Unlike Claude Code, sessions are not organised by project.
    """
    sessions_root = Path.home() / ".codex" / "sessions"
    if not sessions_root.exists():
        return []

    sessions: list[SessionInfo] = []
    for f in sorted(sessions_root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        # Extract session ID from filename like rollout-2026-03-24T14-34-37-UUID.jsonl
        stem = f.stem
        session_id = stem  # use full stem as ID since it includes timestamp

        if exclude_session and exclude_session in session_id:
            continue

        info = SessionInfo(
            path=f,
            session_id=session_id,
            modified=f.stat().st_mtime,
        )

        # Peek for metadata
        try:
            with f.open("r", encoding="utf-8") as handle:
                msg_count = 0
                for i, line in enumerate(handle):
                    if i > 80:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("type") == "session_meta":
                        payload = record.get("payload", {})
                        if not info.timestamp:
                            info.timestamp = payload.get("timestamp")
                        if not info.cwd:
                            info.cwd = payload.get("cwd")
                    if record.get("timestamp") and not info.timestamp:
                        info.timestamp = record["timestamp"]
                    if record.get("type") == "response_item":
                        p = record.get("payload", {})
                        if p.get("type") == "message" and p.get("role") in ("user", "assistant"):
                            msg_count += 1
                # Count remaining
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "response_item":
                            p = record.get("payload", {})
                            if p.get("type") == "message" and p.get("role") in ("user", "assistant"):
                                msg_count += 1
                    except json.JSONDecodeError:
                        continue
                info.message_count = msg_count
        except OSError:
            pass

        sessions.append(info)

    return sessions


def extract_codex_session_metadata(records: list[dict]) -> dict:
    """Extract metadata from Codex session records."""
    meta: dict = {}
    for record in records[:20]:
        if record.get("type") == "session_meta":
            payload = record.get("payload", {})
            if payload.get("cwd") and "cwd" not in meta:
                meta["cwd"] = payload["cwd"]
            if payload.get("cli_version") and "version" not in meta:
                meta["version"] = payload["cli_version"]
            if payload.get("model_provider") and "model" not in meta:
                meta["model"] = payload["model_provider"]
    # Use the first actual message timestamp as the base
    for record in records:
        if record.get("type") == "response_item":
            p = record.get("payload", {})
            if p.get("type") == "message" and p.get("role") in ("user", "assistant") and record.get("timestamp"):
                meta["first_timestamp"] = record["timestamp"]
                break
    for record in reversed(records[-20:]):
        ts = record.get("timestamp")
        if ts:
            meta["last_timestamp"] = ts
            break
    meta["source"] = "codex"
    return meta


def _is_codex_system_content(text: str) -> bool:
    """Check if text is Codex system/environment boilerplate."""
    prefix_markers = (
        "<environment_context>",
        "<permissions instructions>",
        "<permissions",
        "<sandbox_environment>",
        "<custom_instructions>",
        # AGENTS.md / skill instructions injected by the harness
        "# AGENTS.md instructions for",
        "AGENTS.md instructions for",
    )
    # Harness warnings that appear as user messages
    substring_markers = (
        "Warning: apply_patch was requested via exec_command",
    )
    stripped = text.strip()
    if any(stripped.startswith(m) for m in prefix_markers):
        return True
    if any(m in stripped for m in substring_markers):
        return True
    return False


def extract_codex_messages(records: list[dict]) -> list[Message]:
    """Extract user and assistant messages from Codex session records.

    Codex uses type=response_item with payload.type=message.
    User content is in input_text blocks, assistant content in output_text blocks.
    Skip developer messages and system/environment context.
    """
    messages: list[Message] = []

    for record in records:
        if record.get("type") != "response_item":
            continue

        payload = record.get("payload", {})
        if payload.get("type") != "message":
            continue

        role = payload.get("role")
        if role not in ("user", "assistant"):
            continue

        timestamp = record.get("timestamp")
        content = payload.get("content") or []

        if role == "user":
            parts = []
            for block in content:
                if block.get("type") == "input_text":
                    text = (block.get("text") or "").strip()
                    if text and not _is_codex_system_content(text):
                        parts.append(text)
            text = "\n\n".join(parts).strip()
            if not text:
                continue
            messages.append(Message(role="User", text=text, timestamp=timestamp))

        elif role == "assistant":
            parts = []
            for block in content:
                if block.get("type") == "output_text":
                    text = (block.get("text") or "").strip()
                    if text:
                        parts.append(text)
            text = "\n\n".join(parts).strip()
            if not text:
                continue
            messages.append(Message(role="Assistant", text=text, timestamp=timestamp))

    return messages


# ---------------------------------------------------------------------------
# JSONL parsing and message extraction
# ---------------------------------------------------------------------------

def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc


def extract_session_metadata(records: list[dict]) -> dict:
    """Extract useful metadata from session records."""
    meta: dict = {}
    for record in records[:20]:
        if record.get("slug") and "slug" not in meta:
            meta["slug"] = record["slug"]
        if record.get("cwd") and "cwd" not in meta:
            meta["cwd"] = record["cwd"]
        if record.get("version") and "version" not in meta:
            meta["version"] = record["version"]
        if record.get("message", {}).get("model") and "model" not in meta:
            meta["model"] = record["message"]["model"]
    # Use the first actual message timestamp as the base (not preamble records)
    for record in records:
        if record.get("type") in ("user", "assistant") and record.get("timestamp"):
            meta["first_timestamp"] = record["timestamp"]
            break
    # Find last timestamp
    for record in reversed(records[-20:]):
        if record.get("timestamp"):
            meta["last_timestamp"] = record["timestamp"]
            break
    return meta


def extract_messages(records: Iterable[dict]) -> list[Message]:
    """Extract user and assistant messages from Claude Code session records."""
    messages: list[Message] = []

    for record in records:
        record_type = record.get("type")
        if record_type not in ("user", "assistant"):
            continue

        message = record.get("message") or {}
        content = message.get("content")
        timestamp = record.get("timestamp")

        if record_type == "user":
            if not isinstance(content, str):
                continue
            text = content.strip()
            if not text:
                continue
            messages.append(Message(role="User", text=text, timestamp=timestamp))

        elif record_type == "assistant":
            if not isinstance(content, list):
                continue
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = (block.get("text") or "").strip()
                    if t:
                        parts.append(t)
            text = "\n\n".join(parts).strip()
            if not text:
                continue
            messages.append(Message(role="Assistant", text=text, timestamp=timestamp))

    return messages


# ---------------------------------------------------------------------------
# Timestamp formatting
# ---------------------------------------------------------------------------

def format_timestamp(ts: str | None, base_ts: str | None = None) -> str:
    """Format an ISO timestamp as elapsed time from base_ts (e.g. '00:00', '03:42').

    If base_ts is not provided, falls back to absolute HH:MM.
    """
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if base_ts:
            base_dt = datetime.fromisoformat(base_ts.replace("Z", "+00:00"))
            elapsed = dt - base_dt
            total_seconds = max(0, int(elapsed.total_seconds()))
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        local_dt = dt.astimezone()
        return local_dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return ts[:16] if ts else ""


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (lowercase, hyphens, no special chars)."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def format_date(ts: str | None) -> str:
    """Format an ISO timestamp into a readable date string."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%A %d %B %Y")
    except (ValueError, TypeError):
        return ""


def format_duration(first_ts: str | None, last_ts: str | None) -> str:
    """Calculate duration between two ISO timestamps."""
    if not first_ts or not last_ts:
        return ""
    try:
        dt1 = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        delta = dt2 - dt1
        minutes = int(delta.total_seconds() / 60)
        if minutes < 1:
            return "< 1 min"
        elif minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m" if mins else f"{hours}h"
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(
    messages: list[Message],
    source_file: Path,
    include_timestamps: bool,
    title: str | None,
) -> str:
    title = title or "Session Transcript"
    lines = [
        f"# {title}",
        "",
        f"Source: `{source_file.name}`",
        f"Messages: {len(messages)}",
        "",
        "---",
        "",
    ]

    base_ts = messages[0].timestamp if messages else None
    for message in messages:
        header = f"## {message.role}"
        if include_timestamps and message.timestamp:
            header = f"{header} ({format_timestamp(message.timestamp, base_ts)})"
        lines.append(header)
        lines.append("")
        lines.append(message.text.rstrip())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

USER_AVATAR_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round" stroke-linejoin="round" class="avatar-icon">'
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
    '<circle cx="12" cy="7" r="4"/></svg>'
)

ASSISTANT_AVATAR_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"'
    ' stroke-linecap="round" stroke-linejoin="round" class="avatar-icon">'
    '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77'
    ' 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
)


def format_inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: (
            f'<a href="{html.escape(m.group(2), quote=True)}">'
            f"{html.escape(m.group(1))}</a>"
        ),
        escaped,
    )
    escaped = re.sub(
        r"`([^`]+)`",
        lambda m: f"<code>{m.group(1)}</code>",
        escaped,
    )
    escaped = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda m: f"<strong>{m.group(1)}</strong>",
        escaped,
    )
    return escaped


def render_message_html(text: str) -> str:
    lines = text.splitlines()
    chunks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    in_code = False
    code_lines: list[str] = []
    code_language = ""

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            body = "<br>\n".join(format_inline_markdown(line) for line in paragraph_lines)
            chunks.append(f"<p>{body}</p>")
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{format_inline_markdown(item)}</li>" for item in list_items)
            chunks.append(f"<ul>{items}</ul>")
            list_items = []

    def flush_code() -> None:
        nonlocal code_lines, code_language
        if code_lines:
            lang_class = f"language-{html.escape(code_language, quote=True)}" if code_language else "language-none"
            code_body = html.escape("\n".join(code_lines))
            chunks.append(f'<pre><code class="{lang_class}">{code_body}</code></pre>')
            code_lines = []
            code_language = ""

    for line in lines:
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_language = line[3:].strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
            continue

        if re.match(r"^\d+\.\s", stripped):
            flush_paragraph()
            list_items.append(re.sub(r"^\d+\.\s+", "", stripped))
            continue

        flush_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code:
        flush_code()

    return "\n".join(chunks)


def render_html(
    messages: list[Message],
    source_file: Path,
    include_timestamps: bool,
    title: str | None,
    metadata: dict | None = None,
) -> str:
    meta = metadata or {}
    page_title = html.escape(title or "Session Transcript")
    source_name = html.escape(source_file.name)
    session_date = format_date(meta.get("first_timestamp"))
    duration = format_duration(meta.get("first_timestamp"), meta.get("last_timestamp"))
    model_name = html.escape(meta.get("model", ""))
    is_codex = meta.get("source") == "codex"
    eyebrow_label = "Codex CLI Session" if is_codex else "Claude Code Session"
    footer_label = "Generated from a Codex CLI session log" if is_codex else "Generated from a Claude Code session log"

    # Build transcript items
    base_ts = meta.get("first_timestamp") or (messages[0].timestamp if messages else None)
    transcript_items = []
    for index, message in enumerate(messages, start=1):
        role_slug = message.role.lower()
        avatar = ASSISTANT_AVATAR_SVG if role_slug == "assistant" else USER_AVATAR_SVG

        bubble_meta_parts = [html.escape(message.role)]
        if include_timestamps and message.timestamp:
            bubble_meta_parts.append(format_timestamp(message.timestamp, base_ts))
        bubble_meta_parts.append(f"#{index:02d}")
        meta_str = " &middot; ".join(bubble_meta_parts)

        anim_index = min(index, 20)

        transcript_items.append(
            "\n".join(
                [
                    f'<article id="msg-{index:02d}" class="message message--{role_slug}" style="--message-index: {anim_index};">',
                    '  <div class="message__chrome">',
                    f'    <div class="message__meta"><span class="message__avatar">{avatar}</span>{meta_str}</div>',
                    f'    <div class="message__bubble">{render_message_html(message.text)}</div>',
                    "  </div>",
                    "</article>",
                ]
            )
        )

    transcript_html = "\n".join(transcript_items)

    # Build jump navigation
    nav_items = []
    for index, message in enumerate(messages, start=1):
        role_slug = message.role.lower()
        preview = message.text[:60].replace("\n", " ")
        if len(message.text) > 60:
            preview += "..."
        nav_items.append(
            f'<a href="#msg-{index:02d}" class="nav__item nav__item--{role_slug}">'
            f'<span class="nav__num">#{index:02d}</span> '
            f'<span class="nav__role">{html.escape(message.role)}</span>'
            f'<span class="nav__preview">{html.escape(preview)}</span></a>'
        )
    nav_html = "\n".join(nav_items)

    # Build stats pills
    stats = [f"Messages: {len(messages)}"]
    if session_date:
        stats.insert(0, session_date)
    if duration:
        stats.append(f"Duration: {duration}")
    if model_name:
        stats.append(model_name)
    stats_html = "".join(f'<div class="hero__stat">{html.escape(s)}</div>' for s in stats)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    :root {{
      --uofg-university-blue: #011451;
      --uofg-dark-blue: #005398;
      --uofg-blue-80: #344374;
      --uofg-blue-60: #677297;
      --uofg-blue-40: #99A1B9;
      --uofg-blue-20: #CCD0DC;
      --uofg-blue-10: #E6E7EE;
      --uofg-light-grey-1: #F5F5F5;
      --uofg-light-grey-2: #E6E6E6;
      --uofg-light-grey-3: #CCCCCC;
      --uofg-mid-grey-2: #999999;
      --uofg-dark-grey-3: #323232;
      --uofg-highlight: #FFDD00;
      --uofg-white: #FFFFFF;
      --uofg-lavender: #5B4D94;
      --radius-card: 28px;
      --radius-bubble: 22px;
      --shadow-soft: 0 18px 40px rgba(1, 20, 81, 0.12);
      --shadow-bubble: 0 10px 24px rgba(1, 20, 81, 0.08);
      --page-width: 1120px;
    }}

    * {{ box-sizing: border-box; }}
    html {{ color-scheme: light; scroll-behavior: smooth; }}

    body {{
      margin: 0;
      font-family: "Noto Sans", system-ui, sans-serif;
      color: var(--uofg-dark-grey-3);
      background:
        radial-gradient(ellipse at 10% 0%, rgba(91, 77, 148, 0.08), transparent 40%),
        radial-gradient(circle at 90% 20%, rgba(0, 83, 152, 0.10), transparent 35%),
        linear-gradient(180deg, #f8f9fc 0%, #eef2f7 100%);
      min-height: 100vh;
    }}

    a {{ color: var(--uofg-dark-blue); }}
    a:focus-visible {{ outline: 3px solid var(--uofg-highlight); outline-offset: 2px; }}

    .page {{
      width: min(calc(100% - 48px), var(--page-width));
      margin: 0 auto;
      padding: 32px 0 56px;
    }}

    /* --- Hero --- */
    .hero {{
      position: relative;
      overflow: hidden;
      border-radius: var(--radius-card);
      padding: 36px 32px 32px;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent 50%),
        linear-gradient(135deg, var(--uofg-university-blue) 0%, #02236a 48%, var(--uofg-dark-blue) 100%);
      color: var(--uofg-white);
      box-shadow: var(--shadow-soft);
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -8% -36% auto;
      width: 340px; height: 340px;
      border-radius: 50%;
      background: rgba(255, 221, 0, 0.14);
      filter: blur(6px);
      pointer-events: none;
    }}
    .hero::before {{
      content: "";
      position: absolute;
      top: -20%; left: -10%;
      width: 280px; height: 280px;
      border-radius: 50%;
      background: rgba(91, 77, 148, 0.18);
      filter: blur(40px);
      pointer-events: none;
    }}
    .hero__eyebrow {{
      display: inline-flex; align-items: center; gap: 10px;
      margin-bottom: 16px;
      font-size: 0.85rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase;
      position: relative;
    }}
    .hero__eyebrow::before {{
      content: "";
      width: 12px; height: 12px; border-radius: 999px;
      background: var(--uofg-highlight);
      box-shadow: 0 0 0 6px rgba(255, 221, 0, 0.18);
    }}
    .hero h1 {{
      max-width: 16ch; margin: 0;
      font-size: clamp(2.1rem, 5vw, 3.9rem);
      line-height: 0.95; letter-spacing: -0.04em;
      position: relative;
    }}
    .hero__stats {{
      display: flex; flex-wrap: wrap; gap: 12px;
      margin-top: 24px; position: relative;
    }}
    .hero__stat {{
      padding: 10px 14px;
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(10px);
      font-size: 0.88rem;
    }}

    /* --- Jump navigation --- */
    .nav-toggle {{
      position: fixed; bottom: 24px; right: 24px; z-index: 100;
      width: 48px; height: 48px; border-radius: 50%; border: none;
      background: var(--uofg-dark-blue); color: var(--uofg-white);
      box-shadow: 0 6px 20px rgba(1, 20, 81, 0.25);
      cursor: pointer; font-size: 1.2rem;
      display: flex; align-items: center; justify-content: center;
      transition: transform 150ms ease, background 150ms ease;
    }}
    .nav-toggle:hover {{ background: var(--uofg-university-blue); transform: scale(1.08); }}
    .nav-toggle:focus-visible {{ outline: 3px solid var(--uofg-highlight); outline-offset: 2px; }}

    .nav-panel {{
      position: fixed; bottom: 84px; right: 24px; z-index: 99;
      width: 320px; max-height: 50vh; overflow-y: auto;
      border-radius: 16px; background: var(--uofg-white);
      box-shadow: 0 12px 40px rgba(1, 20, 81, 0.18);
      border: 1px solid var(--uofg-blue-10);
      padding: 12px;
      display: none; opacity: 0; transform: translateY(8px);
      transition: opacity 200ms ease, transform 200ms ease;
    }}
    .nav-panel.open {{ display: block; opacity: 1; transform: translateY(0); }}
    .nav__item {{
      display: flex; align-items: baseline; gap: 8px;
      padding: 8px 10px; border-radius: 8px;
      text-decoration: none; color: var(--uofg-dark-grey-3);
      font-size: 0.82rem; line-height: 1.4;
      transition: background 100ms ease;
    }}
    .nav__item:hover {{ background: var(--uofg-blue-10); }}
    .nav__num {{ font-weight: 700; font-size: 0.72rem; color: var(--uofg-blue-60); flex-shrink: 0; }}
    .nav__role {{ font-weight: 600; flex-shrink: 0; }}
    .nav__item--user .nav__role {{ color: var(--uofg-dark-blue); }}
    .nav__item--assistant .nav__role {{ color: var(--uofg-lavender); }}
    .nav__preview {{ color: var(--uofg-mid-grey-2); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }}

    /* --- Transcript --- */
    .transcript {{
      margin-top: 28px;
      padding: 28px 18px 40px;
      border-radius: var(--radius-card);
      background: rgba(255, 255, 255, 0.72);
      box-shadow: var(--shadow-soft);
      backdrop-filter: blur(16px);
    }}
    .transcript__inner {{ display: flex; flex-direction: column; gap: 18px; }}

    /* --- Messages --- */
    .message {{
      display: flex; width: 100%;
      opacity: 0; transform: translateY(12px);
      animation: reveal 420ms ease forwards;
      animation-delay: calc(var(--message-index) * 22ms);
      page-break-inside: avoid;
    }}
    .message--assistant {{ justify-content: flex-start; }}
    .message--user {{ justify-content: flex-end; }}
    .message__chrome {{ max-width: min(82ch, 88%); }}
    .message__meta {{
      display: flex; align-items: center; gap: 6px;
      margin: 0 14px 8px;
      font-size: 0.76rem; font-weight: 700;
      letter-spacing: 0.04em; text-transform: uppercase;
      color: var(--uofg-mid-grey-2);
    }}
    .message__avatar {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
    }}
    .message--user .message__avatar {{ color: var(--uofg-dark-blue); }}
    .message--assistant .message__avatar {{ color: var(--uofg-lavender); }}
    .avatar-icon {{ width: 16px; height: 16px; }}

    .message__bubble {{
      position: relative;
      padding: 18px 20px;
      border-radius: var(--radius-bubble);
      box-shadow: var(--shadow-bubble);
      line-height: 1.72;
    }}
    .message--assistant .message__bubble {{
      background: linear-gradient(180deg, #ffffff 0%, #f6f8fb 100%);
      border-top-left-radius: 8px;
      border: 1px solid rgba(1, 20, 81, 0.08);
    }}
    .message--user .message__bubble {{
      background: linear-gradient(135deg, var(--uofg-dark-blue) 0%, var(--uofg-university-blue) 100%);
      color: var(--uofg-white);
      border-top-right-radius: 8px;
    }}
    .message__bubble p:first-child,
    .message__bubble ul:first-child,
    .message__bubble pre:first-child {{ margin-top: 0; }}
    .message__bubble p:last-child,
    .message__bubble ul:last-child,
    .message__bubble pre:last-child {{ margin-bottom: 0; }}
    .message__bubble p {{ margin: 0 0 1em; }}
    .message__bubble ul {{ margin: 0 0 1em; padding-left: 1.2em; }}
    .message__bubble li + li {{ margin-top: 0.45em; }}

    .message__bubble code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      font-size: 0.88em; padding: 0.15em 0.4em;
      border-radius: 8px; background: rgba(1, 20, 81, 0.08);
    }}
    .message--user .message__bubble code {{ background: rgba(255, 255, 255, 0.16); }}

    .message__bubble pre {{
      overflow-x: auto; margin: 1em 0;
      padding: 16px 18px; border-radius: 18px;
      background: #1d1f21; color: #c5c8c6;
    }}
    .message__bubble pre code {{
      display: block; padding: 0;
      background: transparent; color: inherit;
      white-space: pre; font-size: 0.85em;
    }}
    .message--user .message__bubble pre {{
      background: rgba(0, 0, 0, 0.35); color: #e8ecf0;
    }}
    .message--user .message__bubble a {{ color: #d7ebff; }}

    /* --- Footer --- */
    .footer {{
      padding: 22px 8px 0;
      font-size: 0.88rem; color: var(--uofg-mid-grey-2);
      text-align: center;
    }}

    @keyframes reveal {{
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* --- Responsive --- */
    @media (max-width: 720px) {{
      .page {{ width: min(calc(100% - 24px), var(--page-width)); padding-top: 16px; }}
      .hero, .transcript {{ padding-left: 18px; padding-right: 18px; }}
      .hero h1 {{ max-width: none; }}
      .message__chrome {{ max-width: 100%; }}
      .nav-panel {{ width: calc(100vw - 48px); right: 12px; bottom: 76px; }}
      .nav-toggle {{ right: 12px; bottom: 16px; }}
    }}

    /* --- Print --- */
    @media print {{
      body {{ background: #ffffff; }}
      .page {{ width: 100%; padding: 0; }}
      .hero, .transcript {{ box-shadow: none; background: #ffffff; border: 1px solid #d9dfeb; }}
      .message {{ opacity: 1; transform: none; animation: none; page-break-inside: avoid; }}
      .nav-toggle, .nav-panel {{ display: none !important; }}
    }}

    /* Prism overrides */
    .message__bubble pre[class*="language-"],
    .message__bubble code[class*="language-"] {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div class="hero__eyebrow">{eyebrow_label}</div>
      <h1>{page_title}</h1>
      <div class="hero__stats">
        {stats_html}
      </div>
    </header>

    <section class="transcript" aria-label="Conversation transcript">
      <div class="transcript__inner">
        {transcript_html}
      </div>
    </section>

    <footer class="footer">
      {footer_label} for internal sharing and demonstration use.
    </footer>
  </main>

  <button class="nav-toggle" aria-label="Toggle message navigation" onclick="document.querySelector('.nav-panel').classList.toggle('open')">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
  </button>
  <nav class="nav-panel" aria-label="Message navigation">
    {nav_html}
  </nav>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-php.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-css.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markup.min.js" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script>
    document.querySelectorAll('.nav__item').forEach(function(el) {{
      el.addEventListener('click', function() {{
        document.querySelector('.nav-panel').classList.remove('open');
      }});
    }});
    document.addEventListener('keydown', function(e) {{
      if (e.key === 'Escape') document.querySelector('.nav-panel').classList.remove('open');
    }});
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()

    is_codex = args.source == "codex"

    # Handle --list-sessions
    if args.list_sessions is not None:
        if is_codex:
            sessions = discover_codex_sessions(exclude_session=args.exclude_session)
        else:
            project_path = args.list_sessions
            sessions = discover_sessions(project_path, exclude_session=args.exclude_session)
        if not sessions:
            print("No sessions found.", file=sys.stderr)
            return 1
        print(format_session_list(sessions))
        return 0

    # Determine input file
    input_path = args.input

    if args.discover is not None:
        if is_codex:
            sessions = discover_codex_sessions(exclude_session=args.exclude_session)
        else:
            project_path = args.discover
            sessions = discover_sessions(project_path, exclude_session=args.exclude_session)
        if not sessions:
            print("No sessions found.", file=sys.stderr)
            return 1

        if args.session_id:
            match = [s for s in sessions if args.session_id in s.session_id]
            if not match:
                print(f"Session not found: {args.session_id}", file=sys.stderr)
                print("Available sessions:")
                print(format_session_list(sessions))
                return 1
            input_path = match[0].path
        else:
            input_path = sessions[0].path

        print(f"Using session: {input_path.stem}", file=sys.stderr)

    if input_path is None:
        print("Error: provide an input file or use --discover", file=sys.stderr)
        return 1

    output_suffix = ".html" if args.format == "html" else ".md"
    if args.output:
        output_path = args.output
    elif args.title:
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_path = Path(f"{slugify(args.title)}-{date_str}{output_suffix}")
    else:
        output_path = input_path.with_suffix(output_suffix)

    records = list(iter_jsonl(input_path))

    if is_codex:
        messages = extract_codex_messages(records)
    else:
        messages = extract_messages(records)

    if not messages:
        raise SystemExit(f"No transcript messages found in {input_path}")

    if args.format == "html":
        if is_codex:
            metadata = extract_codex_session_metadata(records)
        else:
            metadata = extract_session_metadata(records)
        rendered = render_html(
            messages,
            input_path,
            include_timestamps=args.timestamps,
            title=args.title,
            metadata=metadata,
        )
    else:
        rendered = render_markdown(
            messages,
            input_path,
            include_timestamps=args.timestamps,
            title=args.title,
        )

    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {len(messages)} messages to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
