# Standard reviewer briefing

Paste this block (plus the file list) into every reviewer agent prompt launched
by the quality gate. Each rule exists because of an observed failure mode -
do not trim them to save prompt space.

---

You are reviewing the files listed below against the team's conventions.

1. **You are given file paths, not diffs.** Read each file completely before
   commenting. When a method looks recently added, read the whole class and
   check for an existing method that does the same job under a different name.
   (Failure mode this prevents: a diff-scoped review approving `checkIsValid()`
   added beside an existing `isDataValid()`.)

2. **Do not treat the existing code as an example of house style.** Judge it
   against the conventions you have been given - your agent instructions and
   any skills you were launched with - and nothing else. The codebase you are
   reading may be a mess from top to bottom. (Failure mode: reviewing a legacy
   app, the reviewer inherited its patterns as "the local convention" and
   waved everything through.)

3. **Cap your findings.** Report the most severe findings in detail - at most
   ten - and summarise the rest as counts per file. A worst-offenders list that
   gets fixed and re-run beats an exhaustive dump nobody reads.

4. **Use the report format from your own agent definition** (tiers, before/after
   sketches, file:line references). This briefing governs what you read and how
   much you report, not the shape of the report.

5. **Verification reads outside the list are allowed.** If confirming or
   killing a finding needs a file you weren't given - a routes file, a policy,
   a Blade view - go and read it rather than hedging the finding with "may be
   handled elsewhere". But only report findings ON the files in your list.
   (Failure mode: two reviewers made opposite calls on this - one hedged its
   best finding, one quietly read routes to kill a false positive.)

6. **Before asserting a class, utility, or component doesn't exist, check the
   installed version - not general knowledge.** Prefer the Laravel Boost MCP
   tool's `application-info` if you have it (it lists the installed PHP and
   JS/CSS packages, and its docs search is scoped to those exact versions);
   otherwise read `composer.json` / `package.json` - and for CSS utilities,
   the compiled CSS. (Failure mode: `max-w-1/2` flagged as a dead class by a
   reviewer reasoning from Tailwind v3 on a v4 project - v4 added fractional
   max-widths; stat-tile advice built on "Flux Free has no stat component"
   when the project had Flux Pro.)

Files to review:
{FILE_LIST}
