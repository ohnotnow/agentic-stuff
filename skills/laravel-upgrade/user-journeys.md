# Walking the app as its users

> **Draft v1.** Learned on the same upgrade as `SKILL.md` (November 2026): an
> exam-paper workflow app with four kinds of user (admin, setter, moderator,
> external examiner), a Vue 2 front end with Livewire 3 forms, files on an
> encrypted disk, queued mail through Horizon. The walkthrough took about an
> hour and found the one real regression of the whole upgrade, which a green
> suite of 222 tests had missed. Nothing here has been tried on a second app
> yet, so update it when one agrees or disagrees.

The test suite proves the code does what the tests say. This proves the app
still does what its users need, on the real cache, queue, mail and storage.
Do it after section 3's other checks, on the upgraded branch, in the dev
environment.

Load the `playwright-cli` and `playwright-cli-quirks` skills first.

## 1. Find out who the users are, from the code

Don't guess roles from the UI: a role you never log in as is a role you never
test. Read:

- **Seeders** (`database/seeders/`, often a `TestDataSeeder`): the seeded
  logins and their passwords, and how users are attached to things. Check the
  user's own convention for local admin logins too.
- **Policies and gates** (`app/Policies/`, `Gate::define` in the service
  providers): what each kind of user may do.
- **Role flags**: `is_admin` columns, pivot flags (`is_setter`,
  `is_moderator`...), admin middleware on route groups.
- **Routes**: `lando artisan route:list`, grouped by middleware. Every POST is
  an action somebody takes.
- **How each user logs in.** Not everyone has a password. On the original app
  externals got a signed login link by email, so their journey started in
  mailhog.

Check the local database has data before you start
(`lando artisan tinker --execute '...'` with a few counts). If it's empty, ask
before reseeding: the developer may have test data they care about.

## 2. Draft the journeys, then let the developer refine them

Write each journey as a plain sentence naming the user and the outcome:
"the moderator signs off the paper and uploads corrections", not "test
PaperController@store". Group them by user. Include for each kind of user:

- the everyday job (the thing they log in to do),
- every file they upload or download, in each file type that matters,
- every email the journey should send,
- the different categories or stages the app has (on the original app: main
  and resit papers, and a workflow from first draft to print-ready).

For admins, add the reports and every filter on them, exports, impersonation
(start and stop), and any "create a new period/term/year" action.

Show the list to the developer **before driving anything**. They know which
corners are special cases to skip, which features are already known to be
broken, and which part of the upgrade worries them (on the original app: file
type icons that a front-end change might have broken). Their answers change
the list.

Ask which destructive actions you may run (delete, disable, "clear all",
copying data into a new year). Local data is still somebody's test data.

## 3. Walk the workflow in order

Run one named browser session per user (`playwright-cli -s=setter open ...`)
so each keeps its own login, and walk the workflow in the order it happens
in real life. On the original app: setter, then moderator, then external,
then admin. Each stage creates the data the next one needs, and by the time
you reach the admin reports there is a course at every stage to look at.

Pick one clean record (a course nobody has touched) for the main walk, so
what you see is what you did.

Use the site the way a person would: click the button, choose from the
dropdown, pick the date in the picker. Posting straight to the endpoint
skips exactly the front-end code the upgrade may have broken. Fall back to
`fetch()` from the page only for checks a person can't do (status codes,
headers, bytes).

## 4. Check results properly

"The page loaded" isn't a result. For each step, read something back:

- **Saved forms:** reload the page and read the values, or read the row with
  tinker.
- **Status flags and badges:** read the flag from the database, and check the
  badge on the list page and the report.
- **Downloads:** fetch from the page and compare the byte length with the
  original file, and the first bytes (`%PDF-`, `PK` for Office files and zips).
  Look at the headers too; on the original app every download came back as
  `text/html`.
- **Spreadsheet exports:** open them (`uv run --with openpyxl python -I -c
  ...`) and read a row for the record you walked. Hand-rolled XML regexes skip
  empty cells and shift the columns, so don't use one.
- **Zips:** `unzip -l`.
- **Emails:** read subject and recipient from mailhog's API after each step
  that should send one. Queued mail takes a few seconds through Horizon.
- **Icons and layout:** a screenshot of the list, read as an image.
- **Console errors** after each page: `playwright-cli console error`.
- **Server-side warnings:** Laravel Debugbar's Messages tab, if installed,
  shows deprecations that the log config sends nowhere. Read it from the
  page: fetch the URL, take the `phpdebugbar-id` header, then fetch
  `/_debugbar/open?op=get&id=<id>`.

## 5. Check what people must not be able to do

- **An unrelated user.** Impersonate (or log in as) a user with no link to
  the record you walked. From their page, `fetch()` every route the journeys
  used: view, upload, comment, download, delete, the admin pages. Expect 403
  on each. On the original app this proved that the controller authorisation
  attributes Shift had added actually worked. Any 200 is a finding; check
  whether it changed data, and put it back.
- **A logged-out visitor.** `curl -s -o /dev/null -w '%{http_code}
  %{redirect_url}\n'` against `/`, the home page and a deep link like a
  record page. Expect a redirect to the login page. On the original app every
  one returned an empty 401: Laravel 11+ only redirects guests if told where
  to, and an unslimmed app with its old Kernel never tells it. Anyone
  following a link from a notification email after their session expired
  would have seen a blank page. This was found by accident, so it's a named
  step now. The fix was one line in `AppServiceProvider::boot()`:
  `AuthenticationException::redirectUsing(fn () => route('login'));`, plus a
  feature test that a guest is redirected and a JSON request still gets 401.

## 6. Sort regressions from things that were always like that

Before reporting a finding, look at the same code on the pre-upgrade branch
(`git show master:path/to/file`). Most findings on the original app predated
the upgrade: an unguarded approval endpoint, mislabelled report columns, a
wrong download header.

- **Regression:** report it first, with the fix and a test, and ask before
  changing code.
- **Pre-existing:** don't fix it in the upgrade branch. Collect them into one
  triage note (in `ant`, or whatever the project uses) with the file, how you
  confirmed it, and what you only guessed. The developer decides later.

Also look out for things that fail only because of the dev environment (on
the original app, a PDF service that isn't reachable from the dev machine).
Say so, and don't count them as findings.

## 7. Report and tidy up

Lead with regressions. Then what was walked and worked, briefly, by user.
Then the pre-existing findings. Then what wasn't covered, and why. Say what
test data you left behind and how to reset it.

Close every browser session, then check the process table
(`playwright-cli-quirks` has the commands).
