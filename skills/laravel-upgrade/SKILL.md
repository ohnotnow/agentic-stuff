---
name: laravel-upgrade
description: >
  Checks to run around a Laravel major-version upgrade, especially a Laravel
  Shift pull request, for the breakage that the upgrade guide and a green test
  suite both miss - Shift leaving the app half-slimmed or unresolvable, renamed
  and re-defaulted .env variables, cached objects that stop unserialising,
  tests that silently stop running, deprecations hidden during tests - plus
  what to put in the go-live notes. Use when upgrading Laravel (11 to 12, 12 to
  13, or older), reviewing or fixing a Shift PR, or moving an app to a newer
  PHP version.
allowed-tools: "Read,Bash,Glob,Grep"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# Laravel upgrade checks

> **Draft v1.** Learned on one real upgrade, November 2026: a long-lived app
> taken from Laravel 9 / PHP 8.1 to Laravel 13.40 / PHP 8.5.7. Laravel 10, 11
> and 12 were done by hand, Laravel 13 by Shift. The app had never been
> slimmed (it still had its HTTP and Console Kernels), used PHPUnit, Livewire 3,
> Horizon on Redis and Ziggy, and deployed with Deployer to a VM. Everything
> below happened on that app and was verified there. Nothing has been confirmed
> on a second app yet, so update this skill when one agrees or disagrees.

The official upgrade guide tells you what changed, and Shift's review tells
you what it did. This is the list of things that went wrong anyway, with a
check for each.

The lesson behind all of it: **green tests are not the finish line.** On that
app the suite was green while the schedule was empty, mail would have gone to
the log file, and every page returned a 500 in the browser.

Run composer, artisan and tests inside the project's dev container (lando, as
written here), never on the host. The host PHP is usually a different version.

## 0. Baseline, before changing anything

On the current branch, save these to the scratchpad so you can compare later:

- **Test count:** `lando test`. Note the tests, assertions and skipped. A
  lower count later means tests stopped running (see 1e), not that they were
  deleted.
- **Schedule:** `lando artisan schedule:list > schedule-before.txt`
- **Routes:** `lando artisan route:list > routes-before.txt`

Then work out the app's shape:

- `ls app/Http/Kernel.php app/Console/Kernel.php app/Exceptions/Handler.php`.
  If they exist, the app is unslimmed, and 1a is the first thing to check on
  any Shift PR.
- `rg -l '@test\b' tests` finds doc-comment test annotations (see 1e).
- `rg -n 'remember(Forever)?\(' app` finds cached values. Note any that cache a
  model, a collection or another object (see 1c).
- Look up the versions of phpunit, paratest, ziggy, horizon and predis in
  `composer.json`. Each has an entry below.

## 1. Fixing the Shift PR

### 1a. A half-slimmed bootstrap ignores the Kernels

- **Symptom:** lots of test errors like `Target class [api.token] does not
  exist`. That's a middleware alias that's no longer registered: 153 errors on
  the original app. `schedule:list` is empty, so the scheduled commands stop
  running and nothing complains.
- **Cause:** the Laravel 13 Shift replaced `bootstrap/app.php` with the slim
  `Application::configure()` version, but kept the Kernels, the exception
  Handler and RouteServiceProvider. The slim bootstrap never loads any of them.
- **Check:** `rg -n 'configure\(' bootstrap/app.php` matches while
  `app/Http/Kernel.php` still exists.
- **Fix:** either restore the previous bootstrap with
  `git show <commit before Shift>:bootstrap/app.php`, or slim the app properly
  by moving the middleware, schedule and exception handling into
  `bootstrap/app.php` and deleting the Kernels. Restoring is the quick route,
  and was right for an app due to retire. Ask the user which they want.
- **Verify:** `schedule:list` and `route:list` match the baseline, and the
  test count is back.

### 1b. Composer can't resolve after Shift

The Laravel 13 Shift raised `brianium/paratest` to ^7.9, which needs PHPUnit
12, but left `phpunit/phpunit` at ^11. Read composer's conflict output and
move the test tooling together: phpunit, paratest and collision. A PHPUnit
major bump brings 1e with it.

### 1c. `serializable_classes` breaks cached objects (Laravel 13)

Laravel 13's `config/cache.php` ships `'serializable_classes' => false`.
Anything cached as an object comes back as `__PHP_Incomplete_Class`.

- **Why tests miss it:** `phpunit.xml` uses the array cache store, and its
  config has `'serialize' => false`, so nothing gets unserialised.
- **Fix:** list the classes that are actually cached, for example
  `[\Illuminate\Database\Eloquent\Collection::class, \App\Models\Foo::class]`.
  Use the `remember` grep from section 0 to find them.
- **Verify** on the real cache store (Redis or file): load the page that reads
  the cached value twice. The first load fills the cache and the second reads
  it back.

### 1d. Old env names in test and CI config

The old names are ignored silently. On the original app, `CACHE_DRIVER` in
`phpunit.xml` was ignored, so the tests quietly used the `database` cache
store instead of `array`. Search for the old names everywhere, not only in
`.env`:

```
rg -n 'CACHE_DRIVER|MAIL_DRIVER|MAIL_ENCRYPTION|BROADCAST_DRIVER|DATABASE_URL' \
  phpunit*.xml .env.example .lando.yml .gitlab-ci.yml .github 2>/dev/null
```

The replacements are `CACHE_STORE`, `MAIL_MAILER`, `MAIL_SCHEME` (it's not a
straight rename: `smtps` for port 465, nothing for STARTTLS on 587),
`BROADCAST_CONNECTION` and `DB_URL`.

### 1e. PHPUnit 12 ignores `@test` doc-comments

A test method that is marked only with `/** @test */`, with no `test` prefix
on its name, silently stops running under PHPUnit 12. The only sign is a lower
test count.

Convert every annotation to `#[Test]` and add
`use PHPUnit\Framework\Attributes\Test;` to each file. On the original app this
was a mechanical swap of 226 annotations. If you can, do it while still on
PHPUnit 11, where the doc-comments at least show up as deprecations. Then
check the test count against the baseline.

### 1f. Shift's Vite scripts in a laravel-mix app

Shift added `composer run dev` and `composer run setup` scripts, which assume
Vite. It also added `concurrently` and `@laravel/multiplex` to `package.json`
without updating `package-lock.json`, so `npm ci` fails. On a laravel-mix app,
drop the scripts and the two packages, or ask the user.

## 2. `.env`: renamed variables and changed fallbacks

This is the most dangerous part, because nothing errors. Any variable
production doesn't set picks up the new default. On the original app, an
unset `MAIL_MAILER` would have sent every email to the log file.

Don't work from a remembered list. Diff every `env()` call in `config/`
between the two branches:

```
for ref in master HEAD; do
  git archive "$ref" config | tar -xOf - \
    | rg -o "env\('[A-Z0-9_]+'[^)]*\)" | sort -u > "env-$ref.txt"
done
diff env-master.txt env-HEAD.txt
```

The regex cuts off defaults that contain nested calls, for example
`Str::slug(...)`, so read the config file itself for those. An app that is
already on Laravel 11 or 12 config will show a much shorter diff than the
Laravel 9 one did. The diff tells you what's left; don't assume.

What the diff turned up from Laravel 9 to 13 config, to give a sense of the
stakes:

| Variable | If unset, now |
|---|---|
| `CACHE_STORE` (was `CACHE_DRIVER`) | `database`, which fails if there's no cache table |
| `SESSION_DRIVER` | `database`, so logins fail if there's no sessions table |
| `DB_CONNECTION` | `sqlite` |
| `MAIL_MAILER` (was `MAIL_DRIVER`) | `log`: **email silently stops** |
| `MAIL_HOST`, `MAIL_PORT` | `127.0.0.1` / `2525` |
| `REDIS_PREFIX` | the format changed (`name_database_` became `name-database-`), so **queued jobs** under the old prefix are stranded |
| `CACHE_PREFIX`, `SESSION_COOKIE` | the format changed: the cache starts empty and everyone is logged out once |

Ask the user to update the `.env` files: their local one, `.env.example`, and
production. Never edit a `.env` yourself. To try a value for a single command,
use a real environment variable, which takes priority over `.env`:
`lando ssh -c 'cd /app && CACHE_STORE=redis php artisan ...'`.

## 3. Verify beyond the test suite

- **Test count** matches the baseline.
- **Deprecations are hidden during tests.** Laravel drops them while tests are
  running unless `LOG_DEPRECATIONS_WHILE_TESTING=true` is set
  (`HandleExceptions.php`, around line 134, in 13.40), and the deprecations
  channel defaults to `null`. Run
  `lando ssh -c 'cd /app && LOG_DEPRECATIONS_CHANNEL=stderr LOG_DEPRECATIONS_WHILE_TESTING=true php artisan test'`.
  To prove it's working, add a throwaway test that calls
  `trigger_error('probe', E_USER_DEPRECATED)` and confirm the probe shows up
  before you trust "no deprecations".
- **Anything the tests fake needs a real run.** Check what `phpunit.xml` and
  the tests replace: an array cache, a sync or faked queue, faked mail and
  storage. On the original app the suite never touched Redis at all. So:
  - Do a browser click round as each role, with playwright-cli. Check the
    console is clean, and save at least one form of each kind.
  - Run each scheduled command by hand (`lando artisan <command>`), plus
    `schedule:list`.
  - Send one real queued email through the real worker (Horizon) and see it
    arrive in mailhog. Inside lando, its API is
    `http://<mailhog service name>/api/v2/messages`. If the app uses
    `Mail::later()` with random delays, wait for a specific subject, not just
    any message.
- **Stale compiled views** after a package renames its namespace. With Ziggy
  1 to 2 (`Tightenco\Ziggy` became `Tighten\Ziggy`), every page returned a 500,
  `Target class [Tightenco\Ziggy\BladeRouteGenerator] does not exist`, until
  `lando artisan view:clear`. Tests compile views fresh, so they never see it.
  Clear views after any `composer update` that moves namespaces, and add it to
  the deploy steps.
- **Restart long-running workers** (Horizon, `queue:work`) after
  `composer update`. They still have the old code loaded.

## 4. Moving to a newer PHP

- **Try it without touching the dev environment.** Copy the code to the
  scratchpad with `git archive HEAD | tar -x -C <scratch>/app`. Run
  `composer install` from the lock in a throwaway PHP container of the target
  version, then run the suite with deprecations showing (section 3). The tests
  skip Redis, so add a `redis:7-alpine` container on a docker network and
  exercise the cache, a lock and a queued job for real. Then move lando to
  the new version and repeat section 3.
- **Keep the lower bound in `composer.json`** (for example `"php": "^8.3"`) so
  the same lock installs on both versions. Production can then move PHP
  without forcing a code change at the same moment.
- **Extensions for the server:**
  `composer check-platform-reqs --lock --no-dev`.
- **Seen on PHP 8.5** (November 2026):
  - `predis/predis` 1.1.x works, but logs a deprecation on almost every call
    (Use of "static" in callables). `phpredis` is the config default, so check
    `config('database.redis.client')` on production before deciding whether
    to care.
  - Older packages log deprecations for implicitly nullable parameters and for
    `ArrayAccess` methods without `#[\ReturnTypeWillChange]`. They're harmless
    for now.
- **Rollback changes meaning.** Once the server's PHP has moved, the old
  release may not run on it, so `dep rollback` isn't a way back. Snapshot the
  VM first.

## 5. Composer refuses insecure versions

Composer 2.9+ won't resolve versions that have known security advisories. In
November 2026 that meant every Laravel release below 12.69. Stepping through
intermediate majors needed a temporary
`"config": {"policy": {"advisories": {"block": false}}}`. Remove it as soon
as you're on a patched release, and finish on a clean `composer audit`. An
upgrade that resolves straight to the latest major doesn't need it.

## 6. The go-live notes

The user deploys, often weeks later. Write them a go-live document, and ask
whether it belongs in the repo before you put it there. Include:

- **A snapshot of production's effective config**, taken on the current
  release before anything changes, so nobody has to guess what `.env` leaves
  unset:
  `php artisan tinker --execute="foreach (['cache.default','cache.prefix','session.driver','session.cookie','database.default','database.redis.client','database.redis.options.prefix','mail.default','mail.mailers.smtp.host','mail.mailers.smtp.port','queue.default'] as \$k) echo \$k.' = '.var_export(config(\$k), true).PHP_EOL;"`.
  None of those keys holds a secret. Never dump the whole config.
- **The `.env` table** from section 2, with what Laravel uses if each variable
  is unset. Setting the old prefix values explicitly keeps today's behaviour.
- **A quiet moment:** away from the scheduled run times, with the queue empty.
  Jobs waiting under a changed Redis prefix never run.
- **Views:** `view:clear` then `view:cache` in the new release. Check whether
  the deploy tool already runs `view:cache` (with Deployer: `dep tree deploy`).
  If you can't check, mark it unverified. Compiled views live in shared
  storage, so they outlive the release that made them.
- **`cache:clear`, with a caveat:** on Redis it flushes the whole cache
  database (`REDIS_CACHE_DB`). If that's the same number as `REDIS_DB`, it
  also wipes the queues and sessions, so suggest
  `cache:forget <key>` for the specific keys instead.
- **`horizon:terminate`**, and how the server supervises Horizon so it comes
  back.
- **After deploy:** `php artisan config:show <key>` for the same keys, compared
  with the snapshot. Laravel 9 has no `config:show`, so on an app coming from
  9 it only works on the new release.
- **A smoke test checklist**, and **rollback** (see section 4).

Mark anything you couldn't check as **unverified**, and say what would check
it.

## Upgrade guides

Both Laravel and Livewire have upgrade guides available to you in markdown format.  The URL's follow a predictable pattern for the version you are upgrading to.

- https://livewire.laravel.com/docs/4.x/upgrading.md
- https://laravel.com/framework/docs/13.x/upgrade.md

## Tooling rakes met along the way

- `lando ssh -c "..."` mangles nested double quotes. Keep the inner command
  single-quoted and simple.
- `php artisan tinker file.php` runs the file and then waits for input, which
  hangs the tool call. Use `tinker --execute="require 'file.php';"` instead.
- `vendor/` exists only inside the container, so IDE "undefined class"
  warnings on the host are noise. Read vendor files with `lando ssh -c 'cat
  /app/vendor/...'`.
- laravel-mix 6 fails to build on node 26 ("require is not defined in ES
  module scope"), but builds on node 22.
