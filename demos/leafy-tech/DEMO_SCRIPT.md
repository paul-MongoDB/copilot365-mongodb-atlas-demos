# 15-minute demo: "The Willow Bend quote"

**Audience:** technical audiences. They want to know how it works, not only what it does.

**The one thing they should leave with:** one chat can query live Atlas data and read Teams and
OneDrive together, using the signed-in user's permissions, with no Atlas synchronization into the Microsoft 365 search index and no custom app.

## Simple to advanced, one chat

| Kind of query | Prompt | What Atlas has to do |
|---|---|---|
| Simple lookup | Prompts 1a, 1b | Read one product's stock |
| Filter and sort | Prompt 2 (optional) | Find customers with no security spend and rank them |
| Aggregation pipeline | Prompt 3 | Unwind devices, filter by date, group and total by customer, sort |
| Vector search | Prompt 4 | Match a nurse's words to product descriptions by meaning |

Copilot picks the query at run time, so say what the question needs, not what you saw it run.

## The story

Leafy Tech is a fictional IT reseller. You are its Sales Director. Nina, an account manager, has
drafted a quote for 500 clinical laptops for Willow Bend Health, and it needs the Sales Director's sign-off
before Friday. The catalog, stock, customers and quotes live in **Atlas**. The team's notes live
in **Teams**. The policy, rebate rules and customer contract live in **OneDrive**.

### What the Sales Director has to do to sign off

Nina posted quote Q-2026-4471 in Teams: 500 laptops with docks, warranty and imaging, at 14% off
every line. Any quote over $500,000 needs the Sales Director's sign-off before it goes to the
customer, so it can't go out until the Sales Director approves it. To approve it, the Sales Director has to confirm five
things:

| What the Sales Director must confirm | The rule | Where the answer is | Prompt |
|---|---|---|---|
| We can ship all 500 | Available stock must cover the quantity quoted | Atlas | 1a, 1b |
| It's the right product | It has to meet what the nurses asked for | Teams, Atlas | 4 |
| The price and terms are right | The contract sets 10% off and a 4-year warranty. Services stay at list price | OneDrive, Atlas | 5 |
| The deal makes money | Gross margin must be at least 15%, with no exceptions | OneDrive, Atlas | 5 |
| The rebate is protected | The Fabrikam deal registration must be approved before the quote goes out | Atlas, Teams, OneDrive | 5 |

### How the Sales Director uses the system

Without Copilot, the Sales Director opens the quote system, the inventory screen, the contract, the discount
policy, the rebate rules and the Teams channel, then works out the margin himself. In this demo
he stays in one Copilot chat and asks plain questions. Copilot reads Atlas, Teams and OneDrive
with the Sales Director's own permissions and shows the source for each fact.

Copilot doesn't approve anything. It only reads the data, and the Sales Director makes the decision:

1. **The Sales Director checks the quote in Copilot.** The stock is covered once the truck lands. The draft
   fails on price, warranty, the dock and margin, and the deal isn't registered.
2. **The Sales Director sends it back to Nina.** He doesn't sign the draft, because $930,950 at 14.1% is under
   the 15% floor. Copilot can draft his Teams reply, and the Sales Director reviews and sends it.
3. **Nina fixes it.** The quote changes to 10% off, the G2 dock, the 4-year warranty and imaging at
   list price. The new total is $1,003,500 at 18.3%. Nina also gets the deal registration filed,
   which takes one business day to approve.
4. **The Sales Director signs off.** Once the corrected quote has its registration ID, the Sales Director approves it and it
   goes to Willow Bend by Friday.

Say it in 20 seconds: "Nina can't send this quote without my sign-off. Before I sign, I have to
know we can ship it, it's the right product, it matches the contract, it makes money and the
rebate is safe. Those answers live in three places. I'm going to ask Copilot for all of them from
one chat, and then I'll make the call."

## Timeline

| Clock | Beat | What they see |
|---|---|---|
| 0:00 | Prompts 1a, 1b: live stock | 320 becomes 500 in the next answer |
| 2:00 | How it's wired | The path of one question, and the five setup steps |
| 5:00 | Prompt 2: cross-sell (optional) | Who buys hardware but no security |
| 6:00 | Prompt 3: warranties ending | An aggregation over 300 customers, from one sentence |
| 8:00 | Prompt 4: meaning search | A nurse's words become a product, with no shared keywords |
| 9:30 | Under the hood | The index, the document, the query |
| 10:30 | Prompt 5: the quote | Six problems across three systems, with the math |
| 13:00 | Close and questions | |

If you run long, skip Prompt 2.

## Setup on stage

- Copilot Chat, **one new conversation**. In Copilot's model picker, choose a named model, not
  Auto. Auto did not call the connector in our tests. Use **Opus 5.5**, with **6.1 sol** as the
  backup. Rehearse with the model you will present on.
- In Settings, Sources, confirm the Atlas connection is still signed in.
- `stage/prompts.txt` open. Paste the prompts; don't type them.
- A terminal at the project root, with the font enlarged.
- [SETUP_ORIENTATION.md](../../SETUP_ORIENTATION.md) open for the wiring section at 2:00.
- A recording of your own dry run, in case Copilot stalls. The repo does not include one.
- Stock is back to 320. Run this if you rehearsed since the last reset:

  ```bash
  .venv/bin/python demos/leafy-tech/scripts/live_insert.py --undo
  ```

---

## 0:00 Prompts 1a and 1b: live stock (simple lookup)

Open with no slides and no setup. Say: "I'm the sales director at a reseller. One of my account
managers has a quote for 500 laptops, about a million dollars, and it needs my sign-off. Let's
start with the simplest question there is, then make them harder. Can we ship them?"

```text
How many MedBook 14 Clinical laptops can we ship right now? Show each warehouse with on hand, reserved and available, then the total available.
```

What comes back: **320 available**. Dallas has 240 on hand, but 100 are reserved. Say: "That's a
simple lookup: one product, one read. We need 500. We're 180 short, but a truck is due at Chicago
this week."

In the terminal:

```bash
.venv/bin/python demos/leafy-tech/scripts/live_insert.py
```

```text
Check again. How many can we ship right now?
```

What comes back: **500 available**, Chicago now 330.

If Copilot repeats the old number:

```text
Query the catalog again right now.
```

Say: "No sync job and no reindex. Copilot asked Atlas again, and Atlas answered with what's
true now."

## 2:00 How it's wired

Say: "So how did that work?" Then walk through [SETUP_ORIENTATION.md](../../SETUP_ORIENTATION.md):
the path of one question, then the five setup steps.

Say: "What you just saw ran through that path, and so does everything else today. Atlas is queried at question time rather than synchronized into Microsoft 365's search index.
Requested results are returned to Copilot, bounded by my Atlas roles and the organization access mode."

## 5:00 Prompt 2: cross-sell (filter and sort, optional)

```text
Which healthcare customers spent the most with us in the last 12 months but bought no security products? Show the top five: customer, account manager and spend.
```

What comes back: Copper Crossing Family Clinics first, at $1,235,175.

Say: "One step harder: a filter and a sort across 300 customers."

## 6:00 Prompt 3: warranties ending (aggregation pipeline)

```text
Which customers have the most device warranties running out between November 1, 2026 and January 31, 2027? Show the top 10: customer, industry, account manager, devices expiring and spend in the last 12 months.
```

What comes back: Willow Bend Health first with **640 devices**, then Ironwood Heights Law Group
with 254.

Say: "Harder again: an aggregation pipeline. Answering it means opening the device array inside each
customer, keeping the warranties in the date range, adding them up per customer and ranking
them. We didn't write a report for it, and it's a call list for the sales team."

To show the steps, run this in the terminal. It prints the pipeline and its result:

```bash
.venv/bin/python demos/leafy-tech/scripts/demo_queries.py --pipeline
```

To show Copilot's own query, try this prompt. It is optional, so rehearse it first:

```text
Show me the exact query you ran for that answer.
```

## 8:00 Prompt 4: meaning search (vector search)

Say: "Before I sign: did Nina quote the right laptop? The nurses told her what they need."

```text
Nina has a hospital customer who described what their nurses need in their own words. Find out what they said, then match that description to the product descriptions in our catalog by meaning. Show the three closest products with a one-line reason each. Keep it under 80 words.
```

What comes back: **Fabrikam MedBook 14 Clinical** first, the laptop Nina quoted, then the MedTab 11
and the CareView 22. Copilot read Nina's notes, then matched them against 332 products in Atlas.

If Copilot answers with no search, or searches by keyword:

```text
Using semantic search on the product descriptions, which product is closest in meaning to what the nurses said?
```

Say: "The hardest kind: there's nothing to filter on. That's vector search. The nurse said
'harsh cleaning chemicals' and 'knocked off the cart.' The catalog says 'disinfectant wipes' and
'drop-tested.' A keyword search misses that. Vector search matches on meaning."

## 9:30 Under the hood

In the terminal:

```bash
.venv/bin/python demos/leafy-tech/scripts/demo_queries.py --hood
```

It prints three things. Point at each:

1. **The index.** "This is the whole thing. `autoEmbed` tells Atlas to embed the description
   with Voyage AI. We wrote no embedding code."
2. **The document.** "No vector in it. And stock lives inside the product, so one read gets
   everything."
3. **The query.** "Plain English goes straight into `$vectorSearch`, which is why an MCP tool
   call can pass the user's words through."

## 10:30 Prompt 5: the quote

Say: "Now the real job. Today this is an hour across six tools. I'm adding one column to show
where each fact came from."

```text
Nina needs my sign-off on the Willow Bend quote. Show one table with Line, Product, Problem and Source columns. For Source, say Atlas, Teams or OneDrive, and name the document. Then give the draft and corrected totals with margin, the rebate at stake, and who approves it. Keep it short.
```

Don't read it aloud. Paste it. You've already said what the extra column is for.

If the answer skips a source or the table comes back messy, use this longer version:

```text
Nina asked me to sign off the Willow Bend quote before it goes out Friday. Using the quote, our product catalog, the discount policy, the Fabrikam rebate rules, Willow Bend's contract and what the team has said: what's wrong with it? Show one table with Line, Product, Problem and Source columns. Source means quote, catalog, policy, rebate rules, contract or team notes. Then give the draft and corrected quote totals with gross margin, the rebate at stake, and who approves it. Keep it short.
```

What comes back:

| Problem | Where the rule lives |
|---|---|
| 14% discount, but the contract fixes 10% | OneDrive contract |
| Margin 14.1%, under the 15% floor | OneDrive policy, Atlas cost |
| G1 dock is end of life and won't fit the G2 carts | Atlas catalog, Omar's Teams note |
| 3-year warranty, but the contract requires 4 | OneDrive contract |
| Imaging was discounted, but services stay at list | OneDrive policy |
| No deal registration, so $27,000 of rebate at risk | Atlas quote, OneDrive rebate rules, Grace's Teams note |

Draft: **$930,950 at 14.1%**. Corrected: **$1,003,500 at 18.3%**, plus the $27,000 rebate if
the deal is registered first. The Sales Director approves it, because it is over $500,000.

Point at the table. Say: "Read down the Source column: Atlas, Teams and OneDrive, in one answer.
The price went up $72,550 and the quote got safer. Stock isn't on this list, because the truck
we just landed fixed it. That's the live data feeding the decision."

Then give the decision. Say: "So I'm not signing this draft. It goes back to Nina with these
fixes. Once the corrected quote has its deal registration, I'll sign it. Copilot did the
checking. The decision is still mine."

Optional, if you have time. Rehearse it first:

```text
Draft my Teams reply to Nina with the corrected quote and what she needs to do before Friday.
```

## 13:00 Close

Say: "You saw a simple lookup, an aggregation pipeline and a vector search, all from plain
English in one chat. Three things to take away. The data stayed in Atlas. Copilot used my
permissions, not a service account with the keys to everything. And the setup was a settings
change, an index and a sign-in, not an application. Any customer with data in Atlas can start
there."

---

## If something goes wrong

- **Copilot says it needs a connection.** Check the model picker, then Settings, Sources. Atlas
  ends a connection after 7 days of inactivity, or 30 days from the grant. If it still can't
  connect, put this at the front of the prompt, with your own project and cluster, then paste
  your prompt after it:

  ```text
  In the Atlas project '<your-project>', cluster <your-cluster>, database leafy_tech,
  ```

- **Copilot cites the channel export, not Teams.** That's expected if Teams hasn't indexed the
  posts. Say: "Teams content goes through Microsoft 365's index, which takes time. Atlas doesn't,
  and you just saw the difference."
- **Copilot stalls.** Switch to the recording of your own dry run.

## Things to know about the data

- All names are fictional. The vendors use Microsoft's sample brands (Fabrikam, Wingtip, Litware,
  Proseware, Adatum).
- Copilot may count the problems differently. Say "several problems", and check the totals.
- Scale: 332 products, 300 customers, 3,101 orders, 61 quotes.

## After the demo

```bash
.venv/bin/python demos/leafy-tech/scripts/live_insert.py --undo
```
