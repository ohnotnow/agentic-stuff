---
name: shell-function
description: >
  Create a shell function or alias tailored to the user's current shell (bash, zsh, fish, etc).
  Generates portable, idiomatic code for the detected shell. Use when the user asks for a
  shell function, alias, helper, shortcut, or one-liner they want to keep. Triggers: 'shell
  function', 'alias', 'make me a command', 'add to my shell', 'bash function', 'zsh function',
  'fish function', or any request to create a reusable shell command.
allowed-tools: "Bash(echo $SHELL:*),Bash(echo $0:*),Bash(which *),Bash(command -v *),Bash(grep -n agentrc *),Bash(bash -n *),Bash(zsh -n *),Bash(fish -n *),AskUserQuestion"
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

### Step 5: Offer to install

After the user has approved the function, offer to install it.

Keep functions in a file of the skill's own, never in the user's main shell config: `~/.bash_agentrc` for bash, `~/.zsh_agentrc` for zsh. Main config files often hold API keys and tokens, so don't read them; the only thing to check there is whether they source the agent file. Fish needs none of this: write the function to `~/.config/fish/functions/<name>.fish`.

1. **Check the name is free.** Ask the user's real shell what the name means now, printing only its kind (never a function body, which can contain an inline token):
   - bash: `bash -ic 'type -t <name>'`
   - zsh: `zsh -ic 'whence -w <name>'`
   - fish: `fish -c 'type -t <name>'`

   `-i` makes bash and zsh load the user's config, which the agent's own shell doesn't. If anything prints (an alias, function, builtin or program on the PATH), tell the user what the name already is and suggest another.

2. **Create the agent file** if it doesn't exist, starting with:
   ```bash
   # Shell functions and aliases added by an AI coding agent.
   # Never put API keys, tokens or passwords in this file: agents read it.
   ```

3. **Add the function.** If the agent file already has content, back it up (`cp ~/.zsh_agentrc ~/.zsh_agentrc.backup.$(date +%Y%m%d%H%M%S)`). Append the function between marker comments:
   ```bash
   # --- Added by shell-function skill YYYY-MM-DD ---
   the_function_here() {
       ...
   }
   # --- End shell-function addition ---
   ```
   Then syntax-check the file: `bash -n ~/.bash_agentrc`, `zsh -n ~/.zsh_agentrc`, or `fish -n ~/.config/fish/functions/<name>.fish`. If the check fails, restore the backup and show the user the error.

4. **Check the main config sources the agent file:** `grep -n agentrc ~/.zshrc` (for bash, check `~/.bashrc` and, on macOS, `~/.bash_profile`). If nothing prints, show the user this line to add themselves:
   ```bash
   [ -f ~/.zsh_agentrc ] && source ~/.zsh_agentrc
   ```
   Don't edit the main config yourself.

5. Tell the user to open a new terminal or `source` the agent file.

### If the user declines installation

Show them how to use it manually: paste the function into their terminal for this session, or add it to their shell config themselves.

## Safety rules

- Never write to, or read, the user's main shell config. The only check there is the `grep` for the source line.
- Back up the agent file before changing it, syntax-check it afterwards, and restore the backup if the check fails.
- If the agent file is in a state you don't understand, don't modify it: show the user what to paste instead.
