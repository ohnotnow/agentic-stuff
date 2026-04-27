---
name: practical-laravel-api
description: Conventions for designing practical, consumer-friendly JSON APIs in Laravel with Sanctum. Use when adding or changing endpoints under routes/api.php or app/Http/Controllers/Api/, when reviewing an existing API for consistency, or when aligning multiple Laravel API apps on a shared shape. Optimised for non-developer consumers (Power BI, Excel, AI agents holding tokens) rather than strict OpenAPI compliance — the goal is "obvious from the response", not "minimal payload".
---

# Practical Laravel API

How we like our JSON APIs to look. Principles first, then the rules, then what we don't do, then the testing and docs setup that holds it all together.

The audience for these APIs is **not** other developers building polished SDKs. It's:

- **Power BI / Excel users** building their own reports, who can write a query but won't read OpenAPI specs.
- **Admins / managers** asking AI agents (with a Sanctum token) questions like "how many of our staff are on site this week, and how does that compare to last week?".
- Occasional internal scripts.

If a developer has to write five extra lines to use one of these APIs, that's fine — they'll figure it out. The optimisation target is the non-developer consumer.

---

## Principles

> Get these right and most of the rules fall out naturally.

### 1. Self-describing over compact

A response should be readable on its own. A consumer should not need a second lookup to interpret what they got back. That means returning labels alongside codes, slugs alongside IDs, and giving every section a meaningful name. The cost is a few extra bytes; the benefit is that PowerBI binds straight to the field and an AI agent can answer the user's question without a translation step.

### 2. Loud failure on bad input

If a consumer sends an unknown filter, a malformed date, or asks for a field that doesn't exist — return a `400` with a message that names the offender *and* lists what is allowed. Silent acceptance is the worst-case behaviour: the consumer gets confidently-wrong data and never knows. Loud failure makes the API self-teaching — an AI agent can read the error and self-correct on the next call.

### 3. Stable across environments

Slugs, not auto-increment IDs. Date strings, not datetimes. Named keys, not array positions. The thing a consumer writes today should still work after a database reseed in staging.

### 4. Match the role, not the token

Pick role-based gates over token-ability juggling for cross-cutting access ("can this user see manager-level reports?"). Token abilities are good for finely scoped third-party tokens, but most internal API consumers are humans minting their own token from their profile page — they shouldn't have to know they need to tick `view:team-plans` before it'll work.

### 5. The OpenAPI spec is generated, not maintained

Use Scramble (or similar) to generate the spec from the controllers. Hand-maintained API docs rot within a sprint. What you *do* maintain by hand is a short conventions doc (`API.md`) explaining the patterns, not the field-by-field reference.

---

## The Rules

### Always wrap responses in named keys

Every response is a JSON object with a meaningful top-level key. Never return a bare array.

```json
// Yes
{ "entries": [ ... ], "date_range": { "start": "...", "end": "..." } }

// No
[ {...}, {...}, {...} ]
```

Why: PowerBI binds to a named property. Agents can walk the response without guessing structure. Versioning is easier — adding a sibling key is backwards-compatible.

### Codes and labels both come back

Anywhere there's an enum, status, or referenced model, return both the machine value *and* the human label.

```json
{
  "availability_status": 2,
  "availability_status_label": "On site",
  "category": "support",
  "category_label": "Support",
  "location": "rankine",
  "location_label": "Rankine"
}
```

Filter and write using the code. Display using the label. This eliminates the consumer's translation table entirely.

### Slugs, not IDs, for public references

Auto-increment integer IDs are an internal detail. They differ across environments, they're meaningless to humans, and they're easy to confuse. Slugs (`rankine`, `vpn-service`) are stable, human-typeable, and survive reseeds. Add a `slug` column to any model that's referenced from the public API.

If you must include the ID for some reason (e.g. a JS client needs it), name it explicitly (`location_id`) and put the slug next to it.

### Dates are date-only strings, `YYYY-MM-DD`

For date-only concepts (a plan entry, a working day, a holiday), serialise as `YYYY-MM-DD` strings. Never as ISO datetimes — they invite timezone confusion and PowerBI mis-parses them.

```json
{ "entry_date": "2026-04-22", "date_range": { "start": "2026-04-20", "end": "2026-05-01" } }
```

Add a regex test guarding the format on each endpoint. Cheap insurance.

### Filtering: `?filter[name]=value`, allow-list, loud failure

Use Spatie's QueryBuilder for query-string filtering. Declare every allowed filter explicitly:

```php
QueryBuilder::for(PlanEntry::query())
    ->allowedFilters([
        AllowedFilter::exact('availability_status'),
        AllowedFilter::callback('location_slug', fn ($q, $v) => $q->whereHas('location', fn ($qq) => $qq->where('slug', $v))),
    ])
    ->get();
```

Spatie raises an `InvalidFilterQuery` (which becomes a `400`) for any filter not on the list, with a message naming the offender and listing allowed filters. That error message is the API's documentation, surfaced exactly when the consumer needs it.

For the `from`/`to` date pair (which doesn't actually filter at the DB level — it bounds the response window) use `AllowedFilter::callback('from', fn () => null)` so it's allow-listed without doing anything to the query.

### Date windows: paired, ISO, capped

If your endpoint returns time-series data, accept `filter[from]` and `filter[to]` together. Pull the parsing into a trait:

```php
// app/Http/Controllers/Api/Concerns/ParsesDateWindowFilter.php
trait ParsesDateWindowFilter
{
    private int $maxWindowDays = 62;

    private function parseDateWindow(Request $request): array
    {
        $from = $request->input('filter.from');
        $to = $request->input('filter.to');

        if ($from === null && $to === null) return [null, null];

        abort_if($from === null || $to === null, 400, 'filter[from] and filter[to] must be provided together.');
        abort_if(!preg_match('/^\d{4}-\d{2}-\d{2}$/', $from) || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $to), 400, 'filter[from] and filter[to] must be ISO dates (YYYY-MM-DD).');

        $fromDate = Carbon::parse($from);
        $toDate = Carbon::parse($to);
        abort_if($fromDate->gt($toDate), 400, 'filter[from] must be on or before filter[to].');
        abort_if($fromDate->diffInDays($toDate) > $this->maxWindowDays, 400, 'Date range is too large (max '.$this->maxWindowDays.' days).');

        return [$from, $to];
    }
}
```

Pick a sensible default window (next ten weekdays, current month, etc.) so most consumers never have to specify one. Cap the maximum span — 62 days is a good starting point — to stop accidental "give me everything" requests.

### Sparse fieldsets where it makes sense: `?fields[entries]=a,b,c`

For list endpoints with many fields per row, allow consumers to ask for a subset:

```
GET /api/v1/plan?fields[entries]=entry_date,location,note
```

Reject unknown fields with a `400`. PowerBI users get smaller payloads; agents get to probe what fields exist by trying.

### `scope` field on every report response

If the data returned varies by role (admin sees everyone, manager sees their team), include a `scope` field telling the consumer what slice they got: `"all"`, `"team"`, `"own"`. For reports that are role-independent, return `"global"` rather than omitting the field — generic adapters love "the field is always there".

This is critical for AI agents answering numerical questions honestly. "How many staff are on site?" has a very different answer at `scope=team` versus `scope=all`.

### Auth: Sanctum + role gates

Authentication via Sanctum personal access tokens, minted by the user from their profile page. Authorisation via Laravel gates that check the user's role on the model:

```php
// AppServiceProvider::boot()
Gate::define('accessManagerApi', fn (User $user) => $user->isAdmin() || $user->isManager());
```

```php
// routes/api.php
Route::middleware('auth:sanctum')->prefix('v1')->group(function () {
    Route::get('/plan', [PlanController::class, 'myPlan']);
    Route::prefix('reports')->middleware('can:accessManagerApi')->group(function () {
        Route::get('/team', [ReportController::class, 'team']);
    });
});
```

Use token abilities only when you genuinely need finely scoped third-party tokens (e.g. a partner integration that should only read, never write). For internal humans-with-tokens, role gates are the right level of granularity.

### Versioning: `/api/v1` prefix from day one

Even if you only have one version, prefix it. Adding `/v2` later is trivial; adding any prefix to existing un-prefixed routes is a breaking change.

### Loud 4xx, helpful messages

- `400` — bad query parameters (filter, fieldset, date window). Body has a `message` naming what was wrong.
- `401` — missing/invalid token.
- `403` — authenticated but role-blocked.
- `404` — record missing or not yours. Use `findOrFail` and per-action ownership checks.
- `422` — validation error on a write. Use Form Requests; Laravel's standard envelope is fine.

Don't return a `200` with `{"error": "..."}` in the body. The status code is part of the contract.

---

## Documentation

### Generated spec at `/docs/api`

Use [Scramble](https://scramble.dedoc.co/) to generate an OpenAPI spec from your controllers. It picks up route definitions, return types, and `#[QueryParameter]` attributes. Mount the docs UI behind a gate — internal staff can browse it, randoms can't:

```php
// AppServiceProvider::boot()
Gate::define('viewApiDocs', fn (?User $user = null) => optional($user)->is_admin);
```

### `#[QueryParameter]` attributes on every handler

Every query parameter (filters, fieldsets, date windows) gets a `#[QueryParameter]` attribute on the controller method, with a description written for a human and a realistic `example`. Scramble surfaces these in the spec.

```php
#[QueryParameter('filter[location_slug]', description: 'Only return entries at this location (e.g. "rankine").', type: 'string', example: 'rankine')]
#[QueryParameter('filter[from]', description: 'Start of a custom date window (YYYY-MM-DD). Must be paired with filter[to].', type: 'string', example: '2026-04-20')]
public function myPlan(Request $request): JsonResponse { ... }
```

The descriptions are part of the API. Write them like you'd write a sentence to a colleague, not like XML.

### `API.md` for the conventions, not the reference

Maintain a short `API.md` at the repo root covering:

- Auth (how to mint a token, where to put it).
- The endpoint overview as a small table.
- The conventions (envelope shape, code+label, slugs, dates, scope, filter style, error model).
- Two or three real curl examples.
- A pointer to `/docs/api` for the field-level reference.

Aim for under 200 lines. Anything longer rots; anything shorter forces consumers to read the generated spec.

---

## Testing

### Golden-master tests for response shapes

For any endpoint whose exact JSON shape matters, capture a fixture and assert against it:

```php
test('coverage report golden master — empty scenario', function () {
    $admin = User::factory()->create(['is_admin' => true]);
    Sanctum::actingAs($admin);

    $response = $this->getJson('/api/v1/reports/coverage');
    $response->assertOk();

    $fixture = base_path('tests/fixtures/coverage-report-empty.json');
    if (! file_exists($fixture)) {
        file_put_contents($fixture, json_encode($response->json(), JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)."\n");
    }
    $response->assertExactJson(json_decode(file_get_contents($fixture), true));
});
```

Self-bootstrapping: the first run writes the fixture; subsequent runs assert against it. To regenerate after an intentional change, delete the file and re-run.

### Tests that guard each convention

For every API, have at least one test for each of:

- **Date format**: regex-check every date field is `YYYY-MM-DD`.
- **Unknown filter rejection**: send `?filter[wibble]=foo`, assert `400`, assert the error names allowed filters.
- **Unknown field rejection**: send `?fields[entries]=note,not_a_real_field`, assert `400`.
- **Paired date window**: send only `filter[from]`, assert `400`.
- **Date window cap**: send a year-long range, assert `400`.
- **Auth**: unauthenticated → `401`; wrong-role → `403`; not-yours → `404`.
- **Scope field**: assert presence on every report endpoint.

These are cheap to write and catch regressions you wouldn't otherwise notice.

### Test the docs route loads

One feature test per app:

```php
test('api docs page loads for admins', function () {
    $admin = User::factory()->create(['is_admin' => true]);
    $this->actingAs($admin)->get('/docs/api')->assertOk();
});
```

If Scramble fails to generate the spec (e.g. a controller method has a malformed PHPDoc) the page returns 500. This test catches that before consumers do.

---

## What we don't do

A short list of patterns to actively reject when you see them in PRs:

- **Top-level arrays.** `return response()->json($entries)` — wrap it.
- **IDs without slugs.** Returning `"location_id": 7` with no slug means the consumer needs a separate lookup.
- **Codes without labels.** Returning `"status": 2` with no `status_label` forces every consumer to maintain its own translation.
- **Datetimes for date-only fields.** `"entry_date": "2026-04-22T00:00:00.000000Z"` is a trap.
- **Silent acceptance of unknown filters.** If `filter[wibble]=foo` does nothing, the consumer never finds out their query was wrong.
- **Hand-maintained reference docs.** They will rot. Keep `/docs/api` generated from code; keep `API.md` for conventions only.
- **Inline middleware ability strings without a role fallback.** `->middleware('ability:view:all-plans')` blocks legitimate admin tokens that don't happen to have that ability ticked. Prefer role gates.
- **Returning `200` with an error body.** Use the right status code.
- **Custom validation messages.** Laravel's defaults are fine. Custom messages drift from rules and confuse agents that have learnt the standard format.
- **A `count` field next to a list of things.** Consumers can count the array. It's just another field to keep in sync.

---

## When you're starting from scratch

For a brand-new API in a Laravel app:

1. `composer require dedoc/scramble spatie/laravel-query-builder`
2. Add a `Gate::define('viewApiDocs', ...)` in `AppServiceProvider`.
3. Add `RestrictedDocsAccess::class` to the Scramble middleware in `config/scramble.php`.
4. Create `app/Http/Controllers/Api/Concerns/ParsesDateWindowFilter.php` (see above).
5. Set up `routes/api.php` with `Route::middleware('auth:sanctum')->prefix('v1')->group(...)`.
6. Build the first controller. Wire up `#[QueryParameter]` attributes as you go.
7. Write the first golden-master test before adding more endpoints.
8. Write `API.md` early — even just the conventions section. It forces you to commit to them.

## When you're aligning an existing API

1. Read the controllers. List which conventions are already followed and which aren't.
2. Pick the lowest-risk inconsistencies first (adding a `slug` field next to an `id` is additive; restructuring a response is breaking).
3. Add golden-master tests *before* changing shapes — that's how you catch the diff.
4. Fix the inconsistencies in small commits, one convention at a time.
5. Update `API.md` and the Scramble attributes as you go.
6. Don't try to do it all in one PR.
