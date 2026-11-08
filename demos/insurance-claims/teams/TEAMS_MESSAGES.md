# Teams messages to seed before the demo

Post these at least two days before the demo. Teams posts can take several hours or more
to become searchable in Copilot. Copilot only sees Teams content you have access to.

**Where:** create a team called **Contoso Claims (DEMO)** with a standard channel called
**DFW Property Claims**. Using a team you own keeps fictional claim chatter out of your
organization's real channels, and channel posts are easy to show on screen.

**What to paste:** each post's message is the quoted block under its heading. When you
paste it, drop the leading `>` from each line.

**Who posts:** each message names its sender. You have two options.

- **With colleagues (best):** add 2 or 3 colleagues to the team and ask each to paste
  their posts. Copilot will then attribute findings to the right person ("Jordan
  Reyes reported...").
- **Solo:** post everything yourself. Each post has a *Solo prefix* line under its
  sender. Paste that line first, without the quotation marks, then the message. For
  example, Post 1 starts with `Field notes from Jordan Reyes, inspection on Thu Oct 22:`.
  Copilot still finds the facts; it just attributes them to you.

**Paul** is the presenter, the Team Lead in the story. Post 2 is addressed to him and
he replies to it. If you present under another name, replace "Paul" in Post 2 and in
its reply line, then rebuild the fallback document as described below.

Teams stamps each post with the day you post it, so every message carries its own
dates in the text. Do not reword the dollar amounts. The expected answers in
`DEMO_SCRIPT.md` depend on them. If you edit any post, rerun
`.venv/bin/python demos/insurance-claims/scripts/build_documents.py` from the repo root:
it rebuilds the fallback channel export from this file.

---

## Post 1: field adjuster inspection (the critical one)

**From:** Jordan Reyes (Field Adjuster)
*Solo prefix: "Field notes from Jordan Reyes, inspection on Thu Oct 22:"*

> Inspection done on the Brennan water loss, CLM-2026-10482, 2214 Briar Hollow Ln, Plano (inspected Thursday Oct 22).
>
> Cause: the supply line to the upstairs hall toilet let go at the compression fitting. That part is sudden and accidental.
>
> My scope at the Contoso Pricing Guide:
> - Kitchen ceiling collapse, drywall, insulation, lower cabinets and countertop, all from the burst: $16,300
> - Mold remediation in the kitchen ceiling cavity, also from the burst: $6,800
> - Subfloor under the upstairs vanity: $9,400. This one is old damage. The plywood is black and delaminated, the shut-off valve has rust staining, and the moisture readings say it has been seeping for months, not days.
>
> Total at our pricing: $32,500. LeafyDry's estimate is $41,850.
>
> LeafyDry had the Brennans sign an assignment of benefits the night of the loss, before they called us. Photos and moisture map are in the claim file.

## Post 2: desk adjuster escalation

**From:** Maya Chen (Desk Adjuster)
*Solo prefix: "From Maya Chen, Oct 28:"*

> Paul, the Brennan claim (CLM-2026-10482) needs you. LeafyDry's number is $41,850, which is over my $25k authority, and I'm not comfortable paying it anyway. Rachel Brennan has called three times this week. They have two kids under five and haven't had a working kitchen since Sunday Oct 18. Can you review it and sign off on Monday?

**Reply from Paul (Team Lead), in the same thread:**

> Yes, first thing Monday. Hold any payment until then.

## Post 3: SIU heads-up

**From:** Dana Brooks (SIU Investigator)
*Solo prefix: "Heads-up from Dana Brooks in SIU, Oct 29:"*

> Heads up, team. LeafyDry Restoration went on the Vendor Watch List on Oct 1. I keep seeing their name on Collin County water losses with the same story: homeowner away for the weekend, a ceiling comes down under an upstairs bathroom, LeafyDry is on site within the hour, an AOB gets signed that night, and they recommend a full tear-out. If you have one open, don't pay more than the undisputed amount without telling me, and send me the AOB.

## Post 4: sewer backup setup (for the bonus prompt)

**From:** Priya Nair (Desk Adjuster)
*Solo prefix: "From Priya Nair, Oct 27:"*

> I've got two sewer backups on Shady Elm Ct in Irving from the storm night of Oct 15, Grace Thompson and the Parks. Same street, same damage, about the same dollars. Checking endorsements before I call either of them.

## Post 5: background noise (optional)

**From:** Marcus Bell (Senior Adjuster)
*Solo prefix: "From Marcus Bell, Oct 27:"*

> CAT-2026-17 update: the Houston field team arrives Wednesday to help with the hail backlog in Irving and Garland. Send me any hail claims over $25k that still need an inspection.
