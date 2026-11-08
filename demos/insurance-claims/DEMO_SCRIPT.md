# 10-minute demo: "Monday morning at Contoso Mutual"

**The one thing the audience should leave with:** Copilot can now reason over a customer's live
system of record in Atlas together with Work IQ (Teams, OneDrive), in one conversation.
That works with one federated connector, with no data copied and no custom app. It answers
the question every Copilot customer asks: "but can it see our data?"

## Why this is new (say it in 30 seconds, don't put it on a slide)

Copilot already reasons over email, chats and files through Work IQ. But the data a business
runs on, such as claims, orders and policies, lives in operational databases. Bringing that
data in has meant indexing a copy with a synced connector, or building a Copilot Studio
agent with an API in front of the database. Both work, but both are projects. The MongoDB
federated connector lets Copilot query Atlas live, at the moment the question is asked,
with Work IQ in the same answer. That is what you're about to see.

This audience built the products in the other options. Present the federated connector as
completing the picture, never as replacing synced connectors or Copilot Studio.

## The story

Paul manages a claims team at Contoso Mutual, a fictional home insurer. On Monday morning
one of his team flags a $41,850 water damage claim from the Brennan family, who have two
small kids and no kitchen. Paul has to settle it. The claim lives in **Atlas**. The
inspector's findings live in **Teams**. The policy and claims rules live in **OneDrive**. While deciding it, Copilot
uncovers a contractor that has told the same story on seven claims, and that Contoso has
already paid $97,950.

## Timeline

| Clock | Beat | The wow |
|---|---|---|
| 0:00 | Opening: the old way (slide 9) | 45 minutes, 5 apps, a 2-day wait |
| 0:45 | Prompt 1: the claim and the team | The record and the team disagree, side by side |
| 2:15 | Prompt 2: the contractors | Copilot finds the fraud pattern |
| 4:15 | Prompt 3: same story, different words | A claim that never says "ceiling" is found |
| 5:45 | Live insert + Prompt 4 | A claim from 30 seconds ago is in the answer |
| 6:45 | Prompt 5: the decision | Every number from a different system, with sources |
| 9:15 | Close (slide 10) | Old way vs today, and what it means for Copilot |

Copilot answers that call the connector take time. Time each one in your dry run. If the
dry run goes past 9:30, drop the optional closer and shorten what you say while Prompt 5
runs. Don't drop a prompt.

## Setup on stage

- Optional: `stage/stopwatch.html` in a browser tab. It has an opening screen, a running
  clock and a closing screen.
- Browser tab 2: Copilot Chat with the MongoDB Atlas source switched on, in **one new
  conversation** for the whole demo. New chats start on **Auto**, which failed to reach the
  database. Switch the model picker to **6.1 sol** before the first prompt.
- `stage/prompts.txt` open. Paste the prompts; don't type them. They name no database,
  project or cluster, on purpose: a real user wouldn't. `stage/prompts-explicit.txt` is the
  backup with names, for a prompt that fails.
- A terminal at the project root, for the live insert (the connection string loads from `.env`).
- A screen recording of a good dry run, ready in case Copilot stalls on stage.
- `live_insert.py --undo` has been run since the last rehearsal.

---

## 0:00 Opening (45 seconds)

Show slide 9. It lists the six steps Paul goes through today.

Say: "This is how a manager works through one insurance claim today. Five apps, 45 minutes,
and two days waiting on a report. The data that matters most, the claims themselves, sits in
a database Copilot has never been able to see. Let's do it differently."

Then give the 30-second "Why this is new" explanation above. Switch to Copilot. (If you
use the clock, press **Space** in `stopwatch.html` now.)

## 0:45 Prompt 1: the claim and the team

```text
Pull up claim CLM-2026-10482 and check what my team has said about it. Does anything not add up? Keep it under 100 words.
```

What comes back:
- **Atlas:** Brennan family, Plano. Under review. LeafyDry Restoration's estimate is
  $41,850, and Contoso has set aside $35,500 for it.
- **Team notes** (Teams, or the channel export in OneDrive): Jordan, the field inspector, priced the repair at $32,500: $16,300 for the
  burst pipe, $6,800 for mold and $9,400 for floor damage from a slow leak that is months
  old. The family signed an assignment of benefits with LeafyDry the night of the damage.
  That is a form that hands the insurance payment to the contractor. Maya flagged it as
  urgent: two kids under five, no kitchen.
- **The mismatch:** $9,350, or 28.8% over Contoso's pricing guide.
- **A caveat to expect.** If Teams is not indexed, the answer ends with "verified through the
  channel export, not live Teams". Say "the team's notes", and don't claim live Teams.
  Copilot's answer is about 100 words, so it fits on screen. A timed run (2026-11-02, GPT-6.1 Sol)
  took about 4 minutes of Copilot time for all five prompts, so there are about 6 minutes left to talk.

Say: "The database says one thing and the team says another. Before today, nobody put
those side by side, because they live in different systems."

## 2:15 Prompt 2: the discovery

```text
Look at our water damage claims since August 1 that used a contractor. Is anything unusual about the contractors? Compare them on number of claims, average percent above our pricing guide estimate, assignments of benefits, and how much we've already paid. Show a small table sorted by average above guide, highest first, and one sentence on what stands out.
```

What comes back: **LeafyDry Restoration**. It has 7 claims, averages **36.7% over** the
pricing guide, and has **7 of 7** with same-night assignments of benefits. Contoso has
**already paid $97,950** on its three closed claims. Every other contractor is at 7.5%
over or less.

Say: "I didn't write a report. Atlas grouped every claim by contractor and did the math
where the data lives. And we've already paid this contractor almost $98,000."

## 4:15 Prompt 3: same story, different words

```text
Find other claims whose descriptions are most similar in meaning to the Brennan claim: homeowner away, water coming through a ceiling under an upstairs bathroom, and a restoration company on site right away recommending a full tear-out. Rank them by similarity. List only the close matches: claim number, city, contractor and similarity score, then one sentence on what they have in common.
```

What comes back: the six other LeafyDry claims (the Brennan claim itself is excluded), from
Frisco, McKinney, Allen and Plano, with similarity scores of about 0.83 to 0.88, and one closing
sentence: same story, same contractor. Lower-scoring hail and roofing claims are filtered out. Point at **CLM-2026-10323 in Allen**: "my house sitter called about water coming out of the
light fixture in the den."

Say: "Search these claims for the word 'ceiling' and you get 49 hits, mostly hail damage.
You'd also miss this one, because she never wrote 'ceiling'. Vector search matches what
people mean. Atlas builds that meaning index itself, so there's no pipeline to build."

## 5:45 Live: a new claim arrives

**First, ask with nothing inserted.** Paste:

```text
Have any new LeafyDry Restoration claims come in today?
```

What comes back: none today. The newest LeafyDry claim is from October 25. Say: "Nothing new
today. Now watch." (Tested 2026-11-02: passes.)

**Then insert.** Say: "A claim just came in while we were talking." In the terminal:

```bash
.venv/bin/python demos/insurance-claims/scripts/live_insert.py
```

Wait for `inserted CLM-2026-10531`. On Atlas it also waits until vector search can see the
claim, usually a few seconds. Then, in the same chat:

```text
Check again. Have any new LeafyDry Restoration claims come in today?
```

If Copilot just repeats "none", it reused its earlier answer. The "check again" wording passed in
testing, so you likely won't need this, but if it happens ask:

```text
Query the claims system again right now.
```

What comes back: **CLM-2026-10531**, the Ryan and Katie Holloway family in McKinney, reported minutes ago.
LeafyDry's estimate is $42,600, which is 37.9% over the guide. "Water dripping through the
ceiling fan in the game room, right under the kids' bathroom. A crew from LeafyDry pulled up
within the hour."

Say: "A minute ago the answer was none. That claim didn't exist. There's no sync and no overnight copy. Copilot
asked Atlas, and Atlas answered with what's true right now."

## 6:45 Prompt 5: the decision

```text
I need to settle the Brennan claim today. Using the claim and policy records, Jordan's findings, and our homeowners policy and claims handling guidelines: what do we pay, what do we deny and why, does it need a fraud investigation, and who approves it? Show the math in one table with Item, Amount, Decision and Source columns. Name the source as claim record, team notes, policy or guidelines. Leave out living expenses. Then answer the investigation and approver questions in two lines.
```

What comes back:

| Item | Amount | Decision | Source |
|---|---|---|---|
| Burst damage | $16,300 | Pay | Jordan in **Teams**; covered under the homeowners policy in **OneDrive** |
| Mold | $6,800 | Pay **$5,000** | $5,000 mold limit, homeowners policy in **OneDrive** |
| Floor damage from a slow leak | $9,400 | **Deny** | Leaks lasting over 14 days are excluded, homeowners policy in **OneDrive** |
| Deductible | -$2,500 | | Policy record in **Atlas** |
| **Pay now** | **$18,800** | | |

Copilot should also say:
- **It goes to the special investigations unit (SIU), the team that checks for fraud.**
  Four red flags apply and two make it mandatory: the contractor is on the watch list, the
  estimate is 28.8% over guide, it's one of 8 LeafyDry claims (counting the live one) with
  the same story, and the assignment of benefits was signed the night of the damage.
- **Paul approves.** $18,800 is within Maya's authority, but claims sent to the special
  investigations unit need the team lead. Pay the undisputed amount now and don't hold it for the investigation.
- **If it reads closely:** offer the family a $150-a-day meal allowance because they have
  no kitchen, and lower the $35,500 set aside for the claim.

The answer is one table with Item, Amount, Decision and Source columns, then two lines for
the fraud investigation and the approver. Each source cell can name several systems (for example "claim record;
team notes; guidelines"). Don't claim one system per row. Point at the Source column. Say: "Every number came from a different
system: the database, a colleague's message, the policy, the guidelines. That's the 45
minutes from the opening, in one answer, with receipts."

**Optional closer** (only if the clock shows under 8:30):

```text
Draft my Teams reply to Maya approving the undisputed amount and listing what she needs to do for the Brennan family this week.
```

## 9:15 Close (45 seconds)

Switch to slide 10: the old way next to today, and the three things they saw.

Say: "Under ten minutes, against 45 and a two-day wait. A decision with sources, a fraud
pattern worth $98,000, and a family that hears from us today.

This is Copilot reaching the system of record: the data the business
actually runs on, live, reasoned over together with Work IQ. Any joint customer running
Atlas, on Azure or elsewhere, can turn this on with a connector and an index. It's not a
custom build. That makes Copilot more valuable in exactly the conversations where the
customer asks, 'but can it see our data?' Now it can."

After the session, run:

```bash
.venv/bin/python demos/insurance-claims/scripts/live_insert.py --undo
```

---

## Q&A prompts (have these ready)

The audience will ask "can it do X?" These answer the most likely questions live.

**"Can it handle analytics, not just lookups?"** (Tested 2026-11-02: returned the expected numbers)

```text
For the October hailstorm, CAT-2026-17, break down the number of claims, the total money set aside for open claims, and the total paid by city. Show a small table sorted by claims, highest first.
```

Expected: 110 claims. Irving leads with 24 claims and $297,500 set aside for open claims, then
Frisco 19, Garland 17, Dallas 15, Plano 14, McKinney 11, Allen 10.

**"Can it join data across collections and documents?"**

```text
Priya has two sewer backup claims on Shady Elm Ct in Irving. Check each policy's endorsements and our water backup endorsement document. Is each one covered, and for how much?
```

Expected:
- **Grace Thompson, CLM-2026-10407.** Her policy has no water backup endorsement (an
  add-on that covers sewer backups), so the damage is excluded. Deny.
- **The Parks, CLM-2026-10408.** Their policy has the add-on (form HO-WB-10), so they're
  covered up to $10,000.

Same street, same storm, and one field on the policy record decides it.

**"Is there a revenue angle?"**

```text
How many sewer backup claims have we denied this year because the policy had no water backup endorsement, and how much was claimed? What would the endorsement have cost?
```

Expected: 8 claims and $103,850 claimed. The endorsement costs $45 to $140 a year. That's an
upsell list for agents.

**"Can it figure out what matters on its own?"** (riskier, so test it in the dry run first)

```text
What needs my attention this morning?
```

A good answer leads with the Brennan escalation from Teams and the open LeafyDry claims in
Atlas.

---

## If something goes wrong

- **A prompt takes more than 60 seconds.** Talk over it using the "Why this is new" points.
  If it fails, switch to the recording for that beat.
- **Copilot can't reach the database** ("needs a connection", wrong Atlas project, or a
  "no" that turns out wrong). First check the model picker is not on Auto. Then re-ask that
  prompt from `stage/prompts-explicit.txt`.
- **Prompt 2 is vague.** Use this version, which names the exact comparison:

  ```text
  For water damage claims since August 1 that have a contractor, compare the contractors: number of claims, average estimate, average percent above our pricing guide estimate, how many had an assignment of benefits, and how much we have already paid.
  ```

- **Prompt 3 runs keyword searches.** Use the "semantic search" version:

  ```text
  Using semantic search on the claim descriptions, find other claims that tell the same story as the Brennan claim: homeowner away, water coming through a ceiling under an upstairs bathroom, and a restoration company on site right away recommending a full tear-out. List only the close matches: claim number, city, contractor and similarity score, then one sentence on what they have in common.
  ```

  If it still does a text match, name the index:

  ```text
  Use the claims_semantic vector search index on loss_description.
  ```

  To prove which search ran, ask this and look for `claims_semantic`:

  ```text
  Which query did you run? Show the exact query.
  ```

- **Prompt 4 misses the new claim.** Check the terminal printed `inserted`. If Copilot repeats
  "none", ask the first line below. If it still misses it, ask the second.

  ```text
  Query the claims system again right now.
  ```

  ```text
  Show me claim CLM-2026-10531.
  ```
- **Prompt 5 is thin or skips a source.** Run it in the **Researcher** agent, which
  Microsoft lists as supporting federated connectors. It's slower, so use it only as a
  fallback.
- **The Teams posts aren't found.** On 2026-11-02 they were not indexed after several hours.
  The OneDrive file `DFW Property Claims channel export.docx` (built into `fallback/`) holds
  the same five posts, and the prompts find it with no change. Say "my team's notes", not
  "the Teams channel", if a source comes up.

## Before you present

- Confirm how the connector signs in to Atlas. If it passes through each user's own
  identity, say so; the audience will ask about governance and admin control. If it uses one
  shared database user, don't claim per-user permissions.
- Tested on 2026-11-02 on an M10 cluster, model 6.1 sol:
  Prompts 1, 2, 3 and 5 returned the expected numbers, and Prompt 3 ran a real vector search
  on `claims_semantic`. Prompt 4 and the Q&A prompts also passed in 6.1 sol.
- Copilot answers are long. Prompt 5 now asks for one table and two lines. Time each answer.
- Do a full timed dry run in one chat, then run `live_insert.py --undo`.

---

## Appendix: full expected answers

**Prompt 2: contractor comparison** (before the live insert)

| Contractor | Claims | Avg estimate | Avg % over guide | Assignments of benefits | Already paid |
|---|---|---|---|---|---|
| **LeafyDry Restoration LLC** | **7** | **$37,864** | **+36.7%** | **7** | **$97,950** |
| Lone Star Restoration | 2 | $8,250 | +7.5% | 0 | $0 |
| Metroplex Mitigation Services | 8 | $15,525 | +6.7% | 0 | $18,100 |
| Trinity Dry-Out Co. | 3 | $11,417 | +4.8% | 0 | $17,700 |
| Bluebonnet Water Mitigation | 7 | $20,479 | -1.6% | 1 | $52,000 |
| Prairie Home Restoration | 2 | $24,400 | -2.2% | 0 | $43,800 |

After the live insert, LeafyDry shows 8 claims, a $38,456 average, +36.8% and 8 assignments of benefits.

**Prompt 3: the seven LeafyDry claims** (Copilot returns six, because "other claims" excludes the Brennan row)

| Claim | City | Insured | How the claimant said it |
|---|---|---|---|
| CLM-2026-10288 | Frisco | Whitfield | "Got back from a work trip and the living room ceiling was sagging..." |
| CLM-2026-10308 | McKinney | Keller | "at the lake for Labor Day... big brown bulge" |
| CLM-2026-10323 | Allen | Hartman | "water coming out of the light fixture in the den" |
| CLM-2026-10333 | Plano | Lindqvist | "back from a weekend in Austin... family room ceiling had collapsed" |
| CLM-2026-10343 | Frisco | Mullen | "after a few days away... stains spreading across the kitchen ceiling" |
| CLM-2026-10482 | Plano | Brennan | "away at my sister's for the weekend..." |
| CLM-2026-10524 | Plano | Pruitt | "out of town visiting the grandkids... caved in over the breakfast nook" |

**Prompt 5: the four fraud red flags and where each comes from**

1. LeafyDry is on the Vendor Watch List (OneDrive vendor list, added 2026-10-01).
2. The estimate is 28.8% over the pricing guide: $41,850 against $32,500 (Atlas and Teams).
   The threshold is 25%.
3. It's one of seven LeafyDry claims since Aug 23 with the same story, eight after the live
   insert (Atlas aggregation and vector search). The threshold is three in 90 days.
4. The assignment of benefits was signed on the day of the damage, before the claim was
   reported (Teams and the Atlas notes).

The guidelines are in OneDrive, section 6: two flags make a referral mandatory, every
payment on a claim sent to the special investigations unit needs Team Lead approval, and
the undisputed amount is paid within 5 business days.
