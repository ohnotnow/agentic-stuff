---
name: laravel-cloud
description: House gotchas and demo-app patterns for Laravel Cloud on top of the official CLI skill. Use ALONGSIDE the official 'deploying-laravel-cloud' skill (installed via `cloud skills:install`) whenever deploying or managing Laravel Cloud apps. Triggers on "cloud deploy", "cloud ship", "teardown", "push to cloud", or any Laravel Cloud work.
---

# Laravel Cloud: the reality layer

The official `deploying-laravel-cloud` skill (install/update with `cloud skills:install`) covers the generic mechanics: command discovery, flag combos, deploy-then-monitor, subagent delegation. Read it first and follow it. THIS skill is the house layer: verified foot-guns, demo-app patterns, and the secret-handling split between agent and human. If the official skill and this one disagree on mechanics, suspect CLI drift and re-verify with `cloud <command> -h`.

Everything below was verified live against cloud CLI v0.5.0 on 2026-08-13, except entries stamped with a later date. If you are on a much newer CLI, re-verify a gotcha before relying on it, and delete anything upstream has fixed.

## House demo-app pattern

Demo apps are disposable: seeded data, wiped on every deploy.

1. `cloud ship --name=<repo-name> --database-preset=dev -n` (postgres18 default). Ship streams clean JSON status lines and returns app id, environment id, and the vanity URL. The auto-triggered first build fails on Flux auth - expected and harmless.
2. Env vars (append is safe for new keys): `SSO_ENABLED=false`, `SCOUT_DRIVER=database`, and `APP_URL=<vanity url>` - Cloud only pre-sets APP_KEY, it does NOT set APP_URL.
3. Build command: set by the USER via the `flux-cloud-build` shell function (below), never by the agent - it carries Flux credentials.
4. Deploy command (agent-settable, credential-free): `php artisan migrate:fresh --force && php artisan db:seed --force --class=TestDataSeeder`.
5. `cloud deploy -n`, expect streaming JSON ending in `deployment.succeeded` plus the URL. For long deploys or post-hoc digging: `cloud deploy --no-wait` then `cloud deploy:monitor -n` (delegate to a subagent - logs can be long).
6. Verify from outside: curl the login page (200) and any API/auth endpoints for their expected status codes.
7. Teardown: `cloud application:delete <name-or-id> -n --force` (confirm with the user first), then `cloud database-cluster:delete` if the cluster lingers, then remove `.cloud/` locally.

## The secret-handling split

Agents must never run commands whose text embeds secret values (transcripts are logged; permission classifiers rightly block them). The split that works:

- USER runs anything carrying `$FLUX_USERNAME` / `$FLUX_LICENSE_KEY` - via the shell function below, in a real terminal.
- AGENT runs everything else: env vars with non-secret values, deploy commands, deploys, verification.

### The flux-cloud-build function (user's bashrc)

```bash
# Set a Laravel Cloud environment's build command for a Flux Pro project.
# Usage: flux-cloud-build [environment] [extra-build-steps]
flux-cloud-build() {
    local env="${1:-production}"
    local extra="${2:-}"

    if [ -z "$FLUX_USERNAME" ] || [ -z "$FLUX_LICENSE_KEY" ]; then
        echo "flux-cloud-build: FLUX_USERNAME / FLUX_LICENSE_KEY not set" >&2
        return 1
    fi

    local build="composer config http-basic.composer.fluxui.dev"
    build="$build $FLUX_USERNAME $FLUX_LICENSE_KEY"
    build="$build && composer install"
    build="$build && npm install --no-audit"
    build="$build && npm run build"
    if [ -n "$extra" ]; then
        build="$build && $extra"
    fi

    local out
    if out=$(cloud environment:update "$env" --build-command="$build" -n --force --fields=id 2>&1); then
        echo "Updated build command for '$env'"
    else
        echo "Failed to update '$env':" >&2
        echo "$out" >&2
        return 1
    fi
}
```

Design notes, each learned the hard way: short concatenated lines because TUI-wrapped pastes smuggle newlines into long string literals (see foot-gun 5); output captured and shown only on failure because `-n --force` echoes the full resource JSON including the credential-bearing build command; `--fields=id` slims any echo that escapes; the `extra` arg is for project-specific build steps (NOTE: the old example, `php artisan passport:keys --force`, is SUPERSEDED - see "Stable Passport keys" below; keys in the build rotate every deploy and log every OAuth client out).

When the agent needs the build command changed, it asks the user to run this function rather than printing a long command to copy (TUI wrapping mangles pasted long commands - and a mangled paste can store broken config that only surfaces at the next build).

## Stable Passport keys (verified live 2026-08-15, devnotes)

Passport apps must NOT run `passport:keys --force` in the build command - it mints a new keypair every deploy, invalidating every issued token, so all OAuth/MCP clients re-authenticate after every push. The pattern that works:

1. USER generates a keypair locally into a temp dir (keeps dev keys untouched, values never near a transcript): `openssl genrsa -out oauth-private.key 4096 && openssl rsa -in oauth-private.key -pubout -out oauth-public.key`.
2. USER pastes each file's full PEM (multiline, BEGIN/END included) into the Secrets Manager as project-scoped secrets `PASSPORT_PRIVATE_KEY` and `PASSPORT_PUBLIC_KEY`, then deletes the temp files. Passport's vendor config reads exactly those env names at runtime and ignores the key files when they are set - no published config needed.
3. Build command carries no passport:keys step; deploy command is plain `php artisan migrate --force` (migrate:fresh would still wipe the oauth_clients table and force re-auth regardless of stable keys - BOTH halves matter).

Proof of the pattern: an MCP client authenticated before a redeploy answered immediately after it, no 401, database intact. Multiline PEM secrets survive to runtime env intact.

## Foot-gun ledger (verified v0.5.0, 2026-08-13 unless stamped otherwise)

1. **Multiple API tokens brick everything, including the fix.** Every command fails with "Multiple API tokens found. Set organization_id...". `repo:config` fails the same way, so it cannot repair the state it complains about. Fix: user, in a real terminal, `cloud auth:token --list` then `--remove` down to one token. With a single token, commands resolve the app from the git remote without any `.cloud/config.json`.
2. **No TTY means prompts render NOTHING.** Interactive commands (auth:token pickers, repo:config) exit 0 with zero output when run without a terminal. Silence is not success; it is Laravel Prompts finding no TTY. Anything interactive goes to the user's real terminal.
3. **`cloud ship` still does not write `.cloud/config.json`.** Also: `repo:config` only offers EXISTING applications - there is no "this is a new app" path. New app = `ship`; linking an existing app = `repo:config`.
4. **Plain environment variables are runtime-only.** They become the app's `.env`; they are NOT present during builds. `COMPOSER_AUTH` as an env VAR does NOT authenticate builds (verified: 59 packages resolved, then flux-pro 401). Secrets-Manager SECRETS are different - they DO reach builds (see foot-gun 12). The legacy pattern for private packages is `composer config http-basic...` inside the build command; corollary: the stored buildCommand field then holds credentials in PLAIN TEXT and is not masked (env var values ARE masked as ***** unless --show-sensitive). Never fetch or print buildCommand; use `--fields` to avoid it.
5. **Build commands execute line-by-line from a generated script.** A literal newline inside your command string becomes a separate shell command ("--no-audit: command not found" after npm ran without it). Newlines arrive via TUI-wrapped pastes into shell string literals. Hence the short-line function style.
6. **npm 11 rejects `--audit false`.** Use `--no-audit`. (The old space-separated boolean form worked on older npm.)
7. **Deploy-command filesystem writes are DISCARDED.** Docs are explicit: "changes made to the filesystem by deploy commands will not be persisted". Anything writing files the app needs at runtime (passport:keys, storage:link) belongs in the BUILD command, which bakes into the image. Deploy commands = migrations/seeds only. Symptom of getting it wrong: 500s from missing files that "were definitely created".
8. **`--fields=` works on update/create commands too**, not just get/list - use it to slim the confirm echo, and always on resources whose JSON carries secrets.
9. **environment:variables `--action` semantics are only partly verified**: `append` adds new keys (verified). `set` vs `replace` semantics (upsert vs replace-all) are UNVERIFIED - test before trusting, especially `replace`, and note the command's primary description is now "replace all variables from a file".
10. **New environments default to PHP 8.5 / Node 24.** Check composer platform constraints and the pdo_sqlsrv-on-8.5 caveat if relevant.
11. **Push-to-deploy defaults ON** (`usesPushToDeploy: true`). Every push to the branch auto-deploys - which for demo apps still on migrate:fresh means the data is wiped by a README typo push. Warn demo testers; consider it when timing pushes. (The old "keys rotate in build" half of this warning is solved by the Stable Passport keys pattern above.)
12. **Secrets Manager works, both directions (verified 2026-08-15).** Project-scoped secrets reach BUILD time (Flux composer credentials now live there for devnotes) and RUNTIME env (Passport PEM keys, multiline values intact). This likely obsoletes the credential-embedding `composer config http-basic` line in flux-cloud-build - `COMPOSER_AUTH` as a SECRET (not env var - see foot-gun 4) is the thing to try on the next new app. That specific combination is still UNVERIFIED; how the Flux creds are wired into the devnotes build via secrets is the working reference.
13. **Masked-by-default JSON.** `--show-sensitive` exists on most read commands; without it env var values print as *****. The old "application:list leaks all env vars in plain text" warning is fixed - but buildCommand is not treated as sensitive (see 4).

## Prerequisites

- `cloud` CLI installed and authenticated, EXACTLY ONE API token (see foot-gun 1)
- Current directory is a git repo whose remote is connected to Laravel Cloud
- For Flux projects: `FLUX_USERNAME` and `FLUX_LICENSE_KEY` in the user's shell env, and the `flux-cloud-build` function in their bashrc
- `.cloud/` in .gitignore
