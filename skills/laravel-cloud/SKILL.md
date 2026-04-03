---
name: laravel-cloud
description: Deploy and manage Laravel Cloud demo applications via the `cloud` CLI. Use when the user asks to deploy, create, update, or tear down a Laravel Cloud app. Triggers on keywords like "cloud deploy", "cloud ship", "teardown", "cloud teardown", "ship it", "push to cloud", or any reference to managing Laravel Cloud applications or environments.
---

# Laravel Cloud Demo Manager

Manage the full lifecycle of Laravel Cloud demo applications: create, deploy, and teardown.

## Prerequisites

- The `cloud` CLI must be installed and authenticated (`cloud auth`)
- The current directory must be a git repository with a remote
- For Flux UI projects: `FLUX_USERNAME` and `FLUX_LICENSE_KEY` must be set in the local shell environment

### Finding the `cloud` CLI

The `cloud` binary may not be on the default PATH. If `which cloud` fails, check these common locations:

```bash
find /usr/local/bin /opt/homebrew/bin "$HOME/.composer/vendor/bin" "$HOME/.config/composer/vendor/bin" "$HOME/bin" "$HOME/.local/bin" -name "cloud" -type f 2>/dev/null
```

Use the full path for all subsequent commands if needed (e.g. `~/.composer/vendor/bin/cloud`).

## Workflows

### 1. Create & Deploy New Demo

Use when the user wants to ship a new demo app to Laravel Cloud.

**Step 1: Determine app status**

First, check for `.cloud/config.json` in the project root:

- **If it exists**: read the `application_id` and verify with `cloud application:get <application_id> --json`. If valid, the app already exists — skip to workflow 2 (Deploy Update).
- **If it does not exist**: the app may still exist on Cloud (e.g. created via the web UI). Ask the user:
  - "Is this a brand new app, or does it already exist on Laravel Cloud (e.g. created via the web UI)?"
  - If **already exists**: link manually (see "Linking an Existing App" below), then skip to workflow 2 (Deploy Update).
  - If **brand new**: continue with step 2 below.

**Step 2: Verify Flux credentials (if needed)**

If the project uses Flux UI (check `composer.json` for `livewire/flux`), verify that `FLUX_USERNAME` and `FLUX_LICENSE_KEY` are set in the local environment:

```bash
echo "FLUX_USERNAME=${FLUX_USERNAME:-(not set)}" && echo "FLUX_LICENSE_KEY=${FLUX_LICENSE_KEY:-(not set)}"
```

If either is missing, warn the user and stop. Never hardcode credentials in the skill or commit them.

**Step 3: Ensure `.cloud/` is gitignored**

Check if `.cloud/` or `.cloud` appears in `.gitignore`. If not, offer to append it. The directory contains machine-specific IDs (application_id, organization_id) — not secrets, but not useful to commit.

**Step 4: Create the app (without deploying yet)**

Derive the app name from the git repository name (the repo slug, e.g. `my-amazing-app`).

```bash
cloud ship --name=<repo-name> --database=postgres --database-preset=dev --json
```

This creates the application, a production environment, and a serverless Postgres database. **Important:** `cloud ship` automatically triggers an initial build using default commands. This initial build will almost certainly fail (missing Flux credentials, wrong build commands, etc.) — this is expected and harmless. Wait for it to complete before proceeding.

**Step 5: Set environment variables**

Now that the app and environment exist, configure them *before* deploying again.

```bash
cloud environment:variables --action=set --key=SSO_ENABLED --value=false --force
```

**Step 6: Set custom build and deploy commands**

Build the build command string by reading `FLUX_USERNAME` and `FLUX_LICENSE_KEY` from the local shell environment and interpolating their values. If the project does not use Flux UI, omit the `composer config` line.

For Flux UI projects, the build command is:

```
composer config http-basic.composer.fluxui.dev <FLUX_USERNAME_VALUE> <FLUX_LICENSE_KEY_VALUE> && composer install && npm install --audit false && npm run build
```

For non-Flux projects:

```
composer install && npm install --audit false && npm run build
```

The deploy command is always:

```
php artisan migrate:fresh --force && php artisan db:seed --force --class=TestDataSeeder
```

Apply both with:

```bash
cloud environment:update --build-command="<build_command>" --deploy-command="<deploy_command>" --force
```

**Step 7: Deploy**

Now that environment variables and build/deploy commands are configured, trigger the actual deploy:

```bash
cloud deploy 2>&1
```

Run in the background (`run_in_background: true`) with a timeout of 600000ms (10 minutes) — fresh deploys can take several minutes. The `cloud deploy` output is extremely noisy (ASCII art banner, animated spinners producing thousands of lines). The `--no-ansi`, `-q`, and `--silent` flags do not help — `--no-ansi` still outputs the art, and `-q`/`--silent` suppress everything including the final URL. Just let it run in the background and check the result when done.

After completion, check the result by grepping the output for the final JSON status line:

```bash
grep '"status":"deployment' <output_file> | tail -1
```

This avoids wading through thousands of spinner lines. A successful deploy ends with `"status":"deployment.succeeded"` and includes the URL. Also use `cloud application:get --json` to confirm the app status.

### 2. Deploy Update

Use when the app already exists on Laravel Cloud and the user wants to push changes.

**Step 1: Verify app is linked**

Check `.cloud/config.json` exists and contains a valid `application_id`. If missing:

- Ask the user whether they want to create a new app (workflow 1) or link to an existing one.
- To link an existing app, follow the "Linking an Existing App" procedure below.

**Step 2: Deploy**

```bash
cloud deploy 2>&1
```

Run in the background (`run_in_background: true`) with a timeout of 600000ms (10 minutes). The output is extremely noisy — see workflow 1, step 7 for details on why flags don't help. `cloud deploy` always triggers a full redeploy even if nothing has changed.

After completion, tell the user and use `cloud application:get --json` to confirm status.

### 3. Teardown Demo

Use when the user wants to completely remove a demo app and its resources.

**Step 1: Confirm with the user**

Always ask for explicit confirmation before tearing down. Show the app name and warn that this will delete the application and all associated resources (database, environment, etc.).

**Step 2: Delete the application**

```bash
cloud application:delete <application_name_or_id> --force
```

If the database cluster needs separate deletion:

```bash
cloud database-cluster:delete <cluster_name_or_id> --force
```

**Step 3: Clean up local config**

```bash
rm -f .cloud/config.json
```

Confirm teardown is complete.

## Linking an Existing App

The `cloud repo:config` command is currently broken (LazyCollection bug). Use this workaround instead:

1. List all apps to find the right one:

```bash
cloud application:list --json
```

**Security note:** this output includes all environment variables in plain text (API keys, etc.). Do not pipe it anywhere persistent or log it.

2. Match the app by `repositoryFullName` against the current git remote. Extract the `id` and the organisation ID from the output.

3. Create `.cloud/config.json` manually:

```json
{
    "organization_id": "<org-id>",
    "application_id": "<app-id>"
}
```

4. Verify the link:

```bash
cloud application:get <app-id> --json
```

5. Ensure `.cloud/` is in `.gitignore` (see workflow 1, step 3).

## Important Notes

- The deploy command always runs `migrate:fresh` — this is intentional for demo apps as data is disposable seed data.
- `cloud deploy` always triggers a full redeploy — there is no "already up-to-date" short circuit.
- Flux credentials are interpolated into the build command at creation time. If credentials change, re-run `environment:update` with the new build command.
- The `cloud` CLI resolves the target app/environment from `.cloud/config.json` and the git remote automatically.
- Use `cloud environment:logs` to debug deployment issues.
- Use `cloud application:list --json` to see all apps across the organisation. **Caution:** this output includes environment variables in plain text — do not log or pipe it anywhere persistent.
- The `cloud` CLI is very new and has known bugs (e.g. `repo:config` LazyCollection error). If a command fails unexpectedly, check if a workaround exists in this skill before giving up.

## Known CLI Issues (as of v0.1.15)

### `{"message":"Required."}` on every command

**Symptom:** Every non-interactive CLI command (`application:list`, `environment:variables`, `deploy`, etc.) fails with `{"message":"Required."}` and no further explanation.

**Cause:** The `organization_id` is missing from `.cloud/config.json`. The CLI needs it for all API calls but gives no indication that this is what's missing. The `cloud auth` command does not save it, and `cloud ship` does not always create the config file.

**Fix:** You need to get the organisation ID. If `application:list` also fails (chicken-and-egg), the user must run the command interactively in their terminal to select the org and see the output. Then look for the org ID in the app details (format: `org-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

Ensure `.cloud/config.json` contains **both** fields:

```json
{
    "organization_id": "org-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "application_id": "app-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

Once the `organization_id` is present, non-interactive commands work normally.

### `cloud auth` creates duplicate organisations

Each run of `cloud auth` may create a new organisation with the same name. This is a known quirk — it doesn't cause problems but is confusing when listing apps. The user may need to select the correct org interactively.

### App created via web UI not linked locally

If the user created the app through the Laravel Cloud web UI rather than `cloud ship`, there will be no `.cloud/config.json`. Use `cloud application:get <app-id>` interactively to get the org ID and app ID, then create the config file manually (see "Linking an Existing App" above).
