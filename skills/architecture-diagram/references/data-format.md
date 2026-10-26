# Diagram data format

The diagram is one JSON document. `scripts/build.py` checks it and embeds it in
the page; the page lays out and draws every view itself, so the data holds no
coordinates, sizes or colours.

A complete worked example lives in `examples/room-bookings.json` (a small
office admin app, three levels deep, with one flagged problem).

## Top level

```json
{
  "title": "Room Bookings",
  "summary": "Two or three plain sentences: what the app is for and who uses it.",
  "view": { "nodes": [], "edges": [] }
}
```

- `title`: the app's name as its users know it. Shown in the header.
- `summary`: shown in the side panel on the overview.
- `view`: the overview (top level) view.

## Views

A view is a set of boxes (`nodes`) and arrows (`edges`). Any node may carry its
own `view`, which is what the reader sees after clicking that box. Views nest
as deep as the app needs.

```json
{ "nodes": [ ... ], "edges": [ ... ] }
```

Optional: `"direction": "RIGHT"` or `"DOWN"` pins the layout direction. Leave it
out. By default the page lays each view out both ways and picks whichever fits
the reader's screen better. Pinning it makes small screens worse.

## Nodes

```json
{
  "id": "bookings",
  "label": "Room bookings",
  "kind": "process",
  "tech": "Large rooms need approval",
  "description": "Staff pick a room and a time. Most bookings are confirmed straight away.",
  "view": { "nodes": [ ... ], "edges": [ ... ] }
}
```

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Unique within its view. Letters, digits, hyphens. Must not start with `^`. |
| `label` | yes | Short name shown in the box. What users see on screen, not the code name. |
| `kind` | yes | One of the kinds below. |
| `description` | strongly advised | One to three plain sentences, shown in the side panel and read out by screen readers. |
| `tech` | no | A short second line in the box: "Every morning", "Large rooms only", "Web app". Keep it to a few words. |
| `view` | no | The view inside this box. Its presence makes the box clickable, drawn with stacked edges. |
| `issue` | no | A confirmed problem with this part, in one or two plain sentences. The box gets a red outline and a "!" badge, the panel shows it under "Known issue", and every enclosing box gets a small "!" so the reader can follow the trail down. |

### Kinds

| Kind | Drawn as | Use for |
|---|---|---|
| `person` | dark pill | People or teams, by role: "Staff", "Facilities team". Never named individuals. |
| `process` | white box | Parts of the system that do something. Most boxes. |
| `store` | cylinder | Somewhere data is kept: a database, a queue, stored files. |
| `external` | grey dashed box | Systems outside the app that it talks to: sign-on, mail server, a payments service, an AI provider. |

Bots, AI agents and CI pipelines: use `external` when they sit outside the app
and call into it (a Claude skill on someone's laptop, a CI job), and `process`
when they are part of the app itself (an AI step inside a pipeline).

## Edges

```json
{ "from": "catalogue", "to": "bookings", "label": "what can be booked" }
```

- `from` and `to` are node ids in the same view.
- `label` is optional but usually worth having: say what flows, in plain words
  ("confirmation email", "daily booking list"), not how ("HTTP POST", "event").
- Arrows point the way the thing flows. A two-way exchange is two edges.

### Pointing outside the view: `^id`

Inside a nested view, an edge end written as `^id` refers to a node in an
enclosing view: the nearest ancestor view that has a node with that id. The
page draws it as a faint dashed stub labelled with that node's name, and
clicking the stub jumps to the view where it lives.

```json
{ "from": "^staff", "to": "requested", "label": "room and time" }
```

Use stubs to keep the reader oriented: show where the inputs come from and
where the outputs go. Only add the ones that matter; every stub is another box.

## Checks

`python3 scripts/build.py --check data.json` reports:

- problems (the build refuses): missing ids or labels, duplicate ids in a view,
  unknown kinds, edges whose ends do not resolve, an empty `issue`;
- warnings (the build continues): nodes without a description, edges with an
  empty label, views with more than nine boxes.
