---
name: audience-credibility
description: Defensive credibility check for deliverables (reports, dashboards, demos, presentations, web pages, marketing copy) aimed at a real human audience — especially when those readers have local context (a city, an institution, a profession) that lets them spot inaccurate or implausible details. Use this skill BEFORE generating the deliverable when it will mention specific places, buildings, organisations, distances, demographics, or named personas. ALSO use it as a final review pass on any visual or copy output before delivery, to catch design and copywriting tropes that have become recognisable "this came from an LLM" tells. Trigger reliably when the user mentions creating something for "my colleagues", "an audience", "a demo", "a presentation", "to share with stakeholders", or any output that needs to look credible and not AI-generated. Also trigger when the user names a specific institution, city, or audience their work is for. Especially important for demos meant to demonstrate AI capability — where one credibility slip undermines the whole point of the demo.
---

# Audience credibility

When you generate user-facing deliverables — reports, dashboards, demos, presentations, web pages — the audience's threshold for *dismissing* the work as "AI slop" is much lower than their threshold for being *impressed* by it. One verifiable inaccuracy, or one recognisable design trope, is enough to cost you the entire room.

This is especially painful when the deliverable is meant to *demonstrate* what AI can do. A demo undermined by an "obviously AI-generated" tell becomes evidence for the eye-roll, not against it.

This skill is a defensive check you run before delivery. It has two pillars.

## Pillar 1 — Ground the named entities

Before committing to any specific named entity in the deliverable, verify it. The audience for a localised deliverable has local knowledge you don't. If you guess at a distance, a building name, or a neighbourhood demographic and get it wrong, the rest of your work is read through that lens.

### What counts as a named entity

- **Places**: cities, neighbourhoods, streets, transport routes, distances between points
- **Institutions**: organisations, departments, named buildings, named programmes
- **Demographics**: who actually lives in a neighbourhood, who works in a job, what they earn, what they can afford
- **Dates and historical facts**: when something was built, who designed it, what era it represents
- **Personas**: a fictional persona's job title, salary band, housing situation, commute, family setup

### The check (do this before writing the deliverable)

1. **List the named entities** you're about to commit to. Even if a detail feels minor, list it.

2. **Verify each one** by web search, local-knowledge file, or asking the user. Two minutes of verification beats half an hour of post-hoc correction.

3. **For personas, also check socioeconomic plausibility.** A plausible-sounding placename can still be wrong for the persona. Picking a gentrified neighbourhood for a low-paid worker fails the local sniff test even though the geography is fine. Ask "would this person actually live here? Could they afford it? Would they really commute this way?"

4. **Cite verifiable claims** so the audience can validate them. A clickable source on the load-bearing facts buys trust for the rest of the report by extension.

5. **State estimates as estimates** with reasoning, rather than as confident numbers. "We've used 280 kWh/m²/yr for this 1969 building, above the CIBSE typical of 215 because of the era's thermal envelope" is much stronger than just stating 280 as fact.

If you're not sure about a detail, ask the user — they almost always know. "Where would a typical X actually live in Y?" is a five-second question that prevents the credibility-destroying mistake.

### Watch out for the over-correction failure mode

When the user catches one wrong detail, the temptation is to fix that exact detail in isolation rather than re-examine the underlying assumption.

Example from real life: told "Partick is not 4 miles from Gilmorehill", the wrong fix is to look up Partick's actual distance and update the number. The right fix is to ask why Partick was picked at all — and discover that the user wanted a 4-mile commute (which is realistic for the persona's salary), and Partick was the wrong neighbourhood, not the wrong distance.

When corrected, ask: "what was the assumption behind this choice, and is *that* what's wrong?"

## Pillar 2 — Avoid the current AI tells

Certain visual and copy patterns have become recognisable "this came out of an LLM" markers. They're not wrong on their own — many were good design choices once — but they've been overused enough that they now carry an "AI slop" connotation for an attentive audience.

Before delivering visual output, audit it against `references/current-ai-tells.md`. Remove or rework anything that matches.

The tells list changes over time as the design vocabulary shifts. Treat it as a living document — update it when you notice a new pattern becoming a tell, or when an old tell becomes neutral again. The reference file is dated at the bottom so the next reader knows how stale it is.

### A note on craft

The goal isn't to avoid *good design*. Many of the tells were genuinely good ideas at one point. The goal is to avoid the specific overused implementations that have become flags. Where a tell has a good underlying idea, the reference file suggests an alternative that achieves the same goal differently.

### Watch out for defending the trope

When a tell is pointed out, the temptation is to rationalise it as "good design" or "it's just a coloured stripe, what's the harm?" The point is not whether the design choice is defensible in isolation — it's whether it pattern-matches to a tell that the audience will spot. The reference file overrules personal taste here.

## When to run the check

| Moment | Pillar | What to do |
|---|---|---|
| Just after the user briefs you, before you write anything | Pillar 1 | List named entities. Verify or ask. |
| When you're picking a fictional persona's details | Pillar 1 | Sanity-check socioeconomic plausibility. |
| When the user corrects one detail | Pillar 1 | Ask whether the underlying assumption is wrong, not just the surface detail. |
| Just before delivery, on any visual output | Pillar 2 | Audit against `references/current-ai-tells.md`. |
| Just before delivery, on any prose output | Pillar 2 | Same audit, focused on the copy section of the reference. |

For both pillars, brevity matters more than thoroughness — a five-minute check that catches the obvious problems beats a 30-minute check the model skips because it feels expensive.

## What success looks like

A deliverable an attentive audience member could not, on a quick read or scan, point to and say "that's wrong" or "that's an AI-ism". Substance untouched, credibility preserved. The audience can then engage with the actual content rather than dismissing it on cosmetic grounds.

## Localising this skill

This skill ships with a generic AI-tells list and generic guidance on named-entity verification. To get the most out of it, layer your own context on top:

- **Add a local-knowledge note** for places/institutions you regularly produce work about. Even a one-paragraph "this is what's in this city" note for the LLM helps.
- **Update the AI-tells reference** as you spot new tells in the wild, and prune ones that have become neutral.
- **Add domain-specific verification rules** if you work in a regulated or technical field where there are standard places to verify (e.g. companies house, official statistics, regulatory registers).

The point is not to follow this skill verbatim — the point is to have *some* skill that catches credibility gaps before they reach an audience.
