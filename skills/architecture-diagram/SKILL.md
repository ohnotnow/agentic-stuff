---
name: architecture-diagram
description: Make an interactive, zoomable architecture diagram of an application as a single self-contained HTML file, for non-technical managers who want to see how a system hangs together. The top view shows the app, its users and the outside systems it talks to; clicking a box zooms smoothly into what is inside it. Use this whenever the user asks for an architecture diagram, a system overview picture, "something to show management/the director", a visual of how an app works, or wants an existing architecture diagram brought up to date, for Laravel apps and small Go or Python tools alike, even if they do not say "interactive" or "HTML".
---

# Architecture diagram

The reader is a manager, not a developer. They want to see, at a glance, what an
application does, who uses it, what it talks to, and how its parts hang
together, then click into whichever part interests them. Everything here serves
that reader: plain words, a handful of boxes per view, and nothing claimed that
you have not checked. If the user says the audience is developers instead, ask
what they want to see; the advice below is tuned for managers.

The person asking you is busy too. They want the diagram, not a report about
it. Most of the apps you will meet are ordinary office and admin apps whose
purpose is obvious from the code; for those, ask the app's name if this is the
first diagram, then read, build, and tell them in a few lines. Keep every
message to the user short enough to take in at a glance: see "How to talk to
the user" below.

The deliverable is one HTML file (about 1.6 MB, because it embeds its layout
library and that library's licence) that opens by double-click and can be
emailed. It lives in the app's repository, by default at
`docs/architecture.html`. When online it loads the Noto Sans font from Google
Fonts, as the main website does; offline it falls back to Arial and works the
same.

You write only the content, as JSON. The renderer in `assets/template.html`
handles layout, zooming, colours, the side panel, keyboard use and small
screens, so do not hand-write HTML, coordinates or styling.

Keep working files in a scratch directory, written `$SCRATCH` below: your
session scratchpad if you have one, otherwise a temporary directory, never the
app's repo.

## Workflow

1. Check for an existing diagram, or ask the app's name
2. Read the app
3. Decide how to carve it up
4. Ask only if you must
5. Write the data
6. Build and report

### 1. Check for an existing diagram, or ask the app's name

Every built page embeds its data in a block marked `id="diagram-data"`, so
search the repo for that marker, leaving out this skill's own files and
vendored code, which contain it too:

```bash
rg -l 'id="diagram-data"' --glob '!.claude/**' --glob '!vendor/**' --glob '!node_modules/**'
```

If a diagram exists, start from it rather than from scratch. It carries
corrections the user has already made, such as what an obscure label means or
which features are retired, and those are expensive to rediscover:

```bash
python3 <skill-dir>/scripts/build.py --extract docs/architecture.html > "$SCRATCH"/architecture.json
```

Then update it to match the code, keeping the existing wording unless the code
now contradicts it. That wording is probably the user's own earlier answers, so
do not ask about it again.

If there is no diagram, this is a first build. If the request already names
the app, use that name and do not ask. Otherwise, before reading anything, ask
the user one question, what the people who use the app call it. Folder names,
package names and page titles are often a working name the app outgrew long
ago, and the code cannot tell you which. Offer what you can see as the guess
("The folder is called `roombook`. Is that what people call it?"), then wait.
The answer is the diagram's title and the name used in every description. An
existing diagram already carries the right name, so never ask it twice.

### 2. Read the app

Aim for understanding, not a code map. Read targeted excerpts rather than whole
files; a real app typically takes fifteen to thirty of them. If a guard in the
environment blocks a shell search (some block patterns containing words like
"export"), use your dedicated search tool instead.

Start with what people have already written down: a technical overview
(`TECHNICAL_OVERVIEW.md`, often made by the technical-overview skill) and the
README. They usually describe the pipeline, the outside systems and the moving
parts directly. Treat them as a head start, not the truth: docs go stale, and
where they disagree with the code, the code wins.

For a **Laravel** app, then:

- **The navigation** (the main layout or a navbar/sidebar Blade file). This is
  the best guide to the areas users think in, and to the labels they know.
- **The routes** (`routes/web.php` and any files it includes, `routes/api.php`)
  for completeness. Areas with routes but no navigation entry are probably
  retired or hidden. A menu item whose route refuses the people that menu is
  shown to is a problem (see "Problems" below).
- **Who can do what**: policies, route middleware, `@can` and custom Blade
  conditions (`Blade::if` in a service provider). These, more than the docs,
  tell you who the people on the diagram are and what each of them uses.
- **The user flags.** Before naming the people boxes, list every `is_*`
  column on the `User` model, its role helpers and scopes, and every
  `Blade::if`. Most of these apps have two booleans, `is_admin` and
  `is_staff`, with helpers such as `isStaff()` and often `isStudent()`, but
  some add more, and an extra flag can drive most of the permissions.
  `is_admin` means an admin of this app, not an IT or office
  administrator. `is_staff` means a member of staff in employment terms, which
  is how apps that also let students sign in tell the two apart. Name the
  people boxes by the role they play here, not "Administrators".
- **The app's own logic and settings**: `app/Services` and the app's own
  config file (`config/<appname>.php`), where rules such as who gets notified
  often live.
- **Behind the scenes**: the schedule (`routes/console.php` or
  `app/Console/Kernel.php`), `app/Jobs`, `app/Mail`, `app/Notifications`, and
  events with their listeners. Listeners are a good source of arrows: "when a
  booking is confirmed, the person who made it is emailed".
- **Outside systems**: `config/services.php`, `composer.json`, database
  connections and filesystem disks. Code that creates API tokens (Sanctum
  personal access tokens, API keys) is a sign that something outside reads the
  app's API. The mail and notification providers a fresh Laravel install lists
  in `config/services.php` (Postmark, SES, Resend, Slack) are usually unused
  defaults: do not chase each one, just draw only what you see being called.
- **What runs in production**: the deployment files (`docker-compose.yml`, or
  stack and compose files in folders such as `docker/` or `deploy/`). A queue
  worker or dashboard that the docs mention but production never starts is not
  part of the picture, and nor is a scheduler with nothing scheduled.

For a **Go or Python** tool: the entry points and subcommands (`cmd/`,
`main.go`, `pyproject.toml` scripts, the CLI definition), the pipeline from
input to output, outbound clients (HTTP, SMTP, SDKs) and where it stores data.

For **anything else**, ask the same questions of whatever is there: where does
it start, what goes in and what comes out, who uses it, what does it talk to,
and where does it keep things.

Leave out what is not the app: vendored third-party code, build output,
generated files, fixtures and demo data.

Two cautions, both learned the hard way:

- **A dependency or config entry is not proof of use.** Search for where an
  outside system is actually called before drawing it. A package can sit in
  `composer.json` with its only write call commented out.
- **Never open `.env` files** or anything else likely to hold secrets. Config
  files that read from the environment tell you what exists without exposing
  values.

### 3. Decide how to carve it up

- **Group by what the app does for people, not how it is built.** "Room
  bookings", "Kit loans", "Rooms and kit" make sense to a manager.
  "Controllers", "Models", "Livewire components" do not. Technical plumbing
  (database, queue, scheduler, stored files) goes into one "Behind the scenes"
  box.
- **Unpick permission-based menus.** Navigation groups things by who may see
  them, so an "Admin" menu is usually a mix of unrelated areas. Fold each item
  into the area it belongs to.
- **Use the labels users see on screen.** If the menu says "Kit loans" but the
  code says `EquipmentReservation`, the box says "Kit loans". Code names
  belong, at most, in a deeper level's `tech` line. When you group things that
  have no on-screen name of their own (the steps between reserving kit and
  returning it, say), give the group a plain name of your choosing.
- **Keep each view to about seven boxes, nine at most.** People and outside
  systems count: a top view with two kinds of user, the app and five outside
  systems is already eight. If there are more, group them. Never draw every
  screen: a box per screen is accurate and useless.
- **Let depth vary.** Most apps want three levels: the app in its world, its
  main areas, and what is inside the important ones. A pipeline may go a level
  or two deeper along its main path. Stop when the next level would just list
  screens, classes or files.
- **Draw pipelines as flows.** Stages left to right or top to bottom, with each
  stage zoomable into its own steps.
- **Lifecycles belong inside their box.** If one part of the app moves things
  through stages (a room booking going from requested to approved to
  confirmed), draw the stages inside that part's box. Make them the main view
  only when the whole app is that lifecycle.
- **Placing the awkward ones**:
  - Monitoring and plumbing (error tracking such as Sentry, queue dashboards
    such as Horizon) go in "Behind the scenes", with outside services drawn
    there as `external` boxes, with no arrow unless something real flows.
    The top view is for things users or the business depend on.
  - A group of people who only receive email, such as a committee, is a
    `person`, by role.
  - For bots, AI agents and CI jobs, see the note under the kinds in
    `references/data-format.md`.

### 4. Ask only if you must

Apart from the app's name on a first build (step 1), if you are confident what
the app is for and how it works, do not ask: go straight on and build. That is
the normal case.

Ask before building only when the answer would change the shape of the diagram
and the code cannot tell you: what the app is for at all, or whether a whole
area is still in use. Then send the shortest possible message (see "How to talk
to the user"): any problems first, then at most three one-line questions, each
with your best guess so the user can just say "yes". Then wait.

For smaller doubts, make the sensible guess, word that box's description
cautiously ("possibly no longer in use"), and carry on. You can raise it as one
of the three questions in your final report.

Sometimes nobody knows the answer: an acronym from an old specification that the
user cannot expand either, say. Keep the label exactly as written, say plainly
in the description that its meaning is not recorded ("named in the original
specification; what the letters stand for is not recorded"), and never invent
an expansion. A plausible guess presented as fact is the worst outcome here.
An expansion written down in the code or docs, such as in a comment or a
config file, counts as recorded: use it.

### 5. Write the data

Read `references/data-format.md` for the format, and look at
`examples/room-bookings.json` for a complete worked example. Write the JSON
to `$SCRATCH/architecture.json`. It ends up embedded in the HTML, and
`--extract` gets it back, so it does not need to live in the repo.

Writing for the reader:

- **Descriptions** are one to three sentences for a non-technical manager:
  what this part does and why it matters. Explain jargon or avoid it ("the
  VLE, the online learning system"). Every box should have one.
- **Arrow labels** say what flows, in plain words: "confirmation email",
  "daily booking list", "who is signing in". Not "POST /api/x" or "dispatches
  event".
- **Say what goes to each outside service.** For an API, remote storage or any
  other outside service, the description says what the app sends there and
  whether that is optional or off by default ("only if cloud backup is turned
  on"). The app's own database is a `store`, part of the app, and needs no
  such note.
- **Only claim what you checked.** If you could not confirm something, soften
  it ("possibly no longer in use") or leave it out. A confident wrong sentence
  in front of the director is worse than a vague right one.
- **Keep it free of exposure**: no hostnames, IP addresses, secrets, tokens,
  people's names, or institution and employer names. People appear as roles;
  services are described generically ("the single sign-on service", not the
  organisation's own name for it). The app's own name is fine.
- **Flag every problem with `issue`** on the one box where it goes wrong (see
  "Problems" below). You do not need permission first: the user sees it in
  your report and can ask you to take it off.
- **Say so if the app is not in use.** If the user tells you it is built but
  nobody uses it, or a part is retired, put that plainly in the summary or the
  relevant description.
- Use `^id` stubs in nested views to show where inputs come from and outputs go,
  so the reader stays oriented after zooming in. Boxes with no arrows are fine
  when nothing flows between them.

### 6. Build and report

```bash
python3 <skill-dir>/scripts/build.py "$SCRATCH"/architecture.json docs/architecture.html
```

The script checks the data first and refuses to build if anything is broken,
naming each problem. Fix them and rerun. Warnings (a crowded view, a missing
description) do not stop the build, but take them seriously.

If you have a browser tool, open the page and click into a box or two before
reporting. Run the browser tool from `$SCRATCH`, as some write snapshot files
into the current directory. The page draws itself a moment after it loads, so
if a snapshot shows an empty diagram, wait a second and take it again. Some
tools refuse `file://` pages; if so, serve the page's folder over HTTP on a
free port, on this machine only (`python3 -u -m http.server 0 --bind
127.0.0.1 --directory <folder>` picks a port and prints it), and stop the
server afterwards. Then report as below. Do not commit the file or otherwise
change git state unless asked.

The diagram is the file. Never publish it anywhere else (a hosted page, an
artifact, a gist, a shared drive) unless the user asks: it can show exactly
where an app is weak, and once published it may be cached or indexed.

## Problems

A problem is something outright wrong in the app: it breaks for users, or puts
people or data at risk. A menu that sends people to a page that refuses them,
an email that is configured but never sent, a page anyone can reach without
signing in. Problems are the most valuable thing you can find, so they always
come first in what you tell the user, and they go on the diagram as an `issue`,
worded for a manager: what goes wrong and who it affects, not which line of
code.

One problem gets one flag, even when it touches several boxes. Put it on the
part that is actually broken and name the other parts and the people affected
in the issue's text. The same flag on three boxes tells a manager three things
are broken when one is. For a menu that offers pages people cannot open, the
flag goes on the area those pages belong to (or most of them, if they are
spread out).

Not problems, so leave them out: things the user, a project note or a memory
says are deliberate; out-of-date docs; starter-kit leftovers; style or
code-quality opinions; anything you suspect but have not confirmed. When you
cannot tell whether a mismatch was meant, the file's history often settles it:
`git log -S` on the menu entry, say, can show a deliberate change that was only
half finished.

## How to talk to the user

Every message, whether a question before building or the report after it, takes
this shape and nothing more:

```markdown
**Problem:** The reminder email that should go out the day before a booking is
set up but never sent, because nothing schedules it. Flagged on the diagram.

Room Bookings lets staff book meeting rooms and borrow equipment, and emails
the facilities team a daily list of what is booked.

Diagram: /path/to/room-bookings/docs/architecture.html

1. Does anything still use the calendar feed? I've drawn it as possibly no
   longer in use.
```

1. **Problems**, if any, in bold at the top, one or two lines each.
2. **One sentence on what the app is**, saying only what you are sure of.
3. **The full path to the diagram** (left out if you are asking before
   building).
4. **At most three questions**, one line each, each with your guess.

That is the whole message. No list of files you read, no tour of what is in the
diagram (they can click it), no list of what you did not check, no other
findings. If the user wants more, they will ask.

## What the page already does

So you do not try to add it:

- lays out each view automatically, choosing the direction that best fits the
  screen;
- zooms smoothly into and out of boxes; breadcrumb, "Up a level (Esc)", the
  Escape key and the browser's back button all zoom out;
- shows each box's description, any issue and its connections in a side panel
  (below the diagram on narrow screens), and marks boxes with issues, and the
  boxes that contain them, with a "!";
- keeps text readable under browser zoom, scrolling a view that will not fit
  rather than shrinking it;
- supports the keyboard and screen readers;
- uses a fixed colour palette and Noto Sans, set in the template, the same for
  every app: do not restyle per diagram;
- carries the layout library's licence text, added by the build script.
