---
name: shell-function
description: >
  Create a shell function or alias tailored to the user's current shell (bash, zsh, fish, etc).
  Generates portable, idiomatic code for the detected shell. Use when the user asks for a
  shell function, alias, helper, shortcut, or one-liner they want to keep. Triggers: 'shell
  function', 'alias', 'make me a command', 'add to my shell', 'bash function', 'zsh function',
  'fish function', or any request to create a reusable shell command.
allowed-tools: "Read,Bash(echo $SHELL:*),Bash(echo $0:*),Bash(which *),Bash(command -v *),AskUserQuestion"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# Shell Function Skill

Create shell functions and aliases that are idiomatic for the user's current shell.

## Workflow

### Step 1: Detect the Shell

The environment info tells you the user's shell. But confirm it:

```bash
echo $SHELL
```

Map the result:
- `/bin/bash` or `/usr/bin/bash` → **bash**
- `/bin/zsh` or `/usr/bin/zsh` → **zsh**
- `/usr/bin/fish` or `/opt/homebrew/bin/fish` → **fish**
- `/bin/sh` → **POSIX sh** (keep it minimal)
- Other → ask the user

### Step 2: Understand the Request

Ask clarifying questions only if the request is genuinely ambiguous. Most of the time you can infer:
- What the function should do
- What arguments it needs
- A sensible name (suggest one, let the user override)

### Step 3: Write the Function

Write idiomatic code for the detected shell. Key differences to remember:

**bash / zsh** (mostly compatible):
```bash
function_name() {
    # body
}
```

**fish**:
```fish
function function_name --description "Short description"
    # body
end
```

**POSIX sh**:
```sh
function_name() {
    # body — no bashisms
}
```

Guidelines:
- Prefer functions over aliases for anything with arguments or logic.
- Use simple aliases only for trivial remappings (`alias ll='ls -la'`).
- Include a brief comment at the top explaining what it does.
- Handle missing dependencies gracefully (e.g. check `command -v ffprobe` before using it).
- Quote variables properly. Unquoted variables are bugs.
- Use `local` for variables in bash/zsh. Use `set -l` in fish.
- If the function needs external tools, mention them so the user knows what to install.

### Step 4: Present the Function

Show the function in a fenced code block with the correct language tag (`bash`, `zsh`, `fish`, `sh`).

Briefly explain:
- What it does
- Usage example(s)
- Any dependencies (external tools needed)
- How to add it to the users shell config

### Step 5: Offer to Install

After the user has seen and approved the function, offer to add it to their shell config.

**This is the most dangerous part. Be extremely careful.**

Say something like:

> Want me to add this to your shell config (`~/.bashrc` / `~/.zshrc` / `~/.config/fish/functions/`)? I'll create a timestamped backup first.  But this is a potentially risky operation if something goes wrong with the file edit.

If they say yes:

1. **Identify the correct config file**:
   - bash → `~/.bashrc` (Linux) or `~/.bash_profile` (macOS — but check if `.bashrc` is sourced from `.bash_profile` first)
   - zsh → `~/.zshrc`
   - fish → `~/.config/fish/functions/{function_name}.fish` (fish uses one-function-per-file)

2. **Read the config file first** to check:
   - Does a function/alias with this name already exist? If so, warn the user and ask.
   - Is the file suspiciously large or complex? If so, warn the user.

3. **Create a backup**:
   ```bash
   cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d%H%M%S)
   ```

4. **Append the function** with clear markers:
   ```bash
   # --- Added by Claude (shell-function skill) $(date +%Y-%m-%d) ---
   the_function_here() {
       ...
   }
   # --- End Claude addition ---
   ```

5. **Verify the result** by reading the file back and checking it parses:
   ```bash
   bash -n ~/.bashrc    # syntax check for bash
   zsh -n ~/.zshrc      # syntax check for zsh
   fish -n ~/.config/fish/functions/name.fish  # syntax check for fish
   ```

6. **If the syntax check fails**: immediately restore the backup, show the user the error, and apologise. Do NOT leave a broken config file.

7. Tell the user to `source ~/.zshrc` (or equivalent) or open a new terminal.

### If the User Declines Installation

Just show them the manual steps again:
> To use this, add the function to your `~/.zshrc` and run `source ~/.zshrc`, or paste it directly into your terminal to use it for this session only.

## Safety Rules

- NEVER overwrite a config file. Only append.
- ALWAYS back up before modifying.
- ALWAYS syntax-check after modifying.
- ALWAYS restore from backup if syntax check fails.
- If in ANY doubt about the config file state, do not modify it — just show the user what to paste.
- For fish, prefer the `~/.config/fish/functions/` directory (auto-loaded, no sourcing needed, easy to remove).
