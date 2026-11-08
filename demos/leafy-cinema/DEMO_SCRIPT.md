# 10-minute demo: "Friday night at Leafy Cinema"

**The one thing the audience should leave with:** Copilot can reason over a business's live
data in Atlas together with its Teams chat and OneDrive documents, in one conversation. It
uses one federated connector (a connector that queries Atlas when the question is asked),
with no data copied and no custom app. It answers the question every Copilot customer asks:
"but can it see our data?"

This demo is built on `sample_mflix`, the movie database that ships with Atlas. Everyone
knows movies, so nobody has to learn a business first. The same pattern works for any
product catalog, order system or customer list.

## Simple to advanced, one chat

| Kind of query | Prompt | What Atlas has to do |
|---|---|---|
| Simple lookup | Prompts 1a, 1b | Sort by last updated and return three films |
| Filter and sort | Prompt 2 | Apply four conditions to 21,000 films and rank them |
| Aggregation pipeline | Prompt 3 | Calculate a critic-audience gap per film, then rank on it |
| Vector search | Prompt 4 | Match a description to plots by meaning |

Copilot picks the query at run time, so say what the question needs, not what you saw it run.

## The story

Paul runs programming at Leafy Cinema, a fictional small-town theater. The General
Manager, Helen, has drafted the six films for the winter "Hidden Gems" series and signs the
license contracts on Friday. Paul has to check her list. The film catalog lives in
**Atlas**. The team's chatter lives in **Teams**. The series rules, the license price list
and last year's lineup live in **OneDrive**.

## Timeline

| Clock | Beat | The wow |
|---|---|---|
| 0:00 | Prompts 1a, 1b: live insert | A film added 30 seconds ago is in the answer |
| 1:30 | Prompt 2: hidden gems | 21,000 films searched, ten answers, in seconds |
| 3:00 | Prompt 3: critics vs audiences | "Spy Kids: critics 93%, audiences 45%" |
| 4:15 | Prompt 4: the half-remembered movie | A customer's vague description becomes a title |
| 5:15 | The old way | Five places to look, an hour of tab hopping |
| 6:00 | Prompt 5: check the lineup | Five rule breaks, found across three systems |
| 9:00 | Close | What it means for Copilot |

If the clock is past 8:30 after Prompt 5, skip the optional closer. Keep Prompt 3: it is the
aggregation example.

## Setup on stage

- Copilot Chat with the MongoDB Atlas source on, **one new conversation** for the whole demo.
  New chats start on Auto. In Copilot's model picker, choose a named model, not Auto. Auto did
  not call the connector in our tests. We rehearsed this demo on **6.1 sol**. Rehearse with the
  model you will present on.
- `stage/prompts.txt` open. Paste the prompts; don't type them.
- A terminal at the project root for the live insert (the connection string loads from `.env`).
- A recording of your own dry run, in case Copilot stalls. The repo does not include one.
- The film from your last rehearsal is removed. If you rehearsed since you last ran it, run:

  ```bash
  .venv/bin/python demos/leafy-cinema/scripts/live_insert.py --undo
  ```

---

## 0:00 Prompts 1a and 1b: a new film arrives (simple lookup)

Open with no slides and no setup. Say: "I run programming at a small cinema. Let's start with the
simplest question there is, then make them harder."

**First, ask with nothing inserted.** Paste:

```text
What are the three most recently updated films in our movie catalog? Show title, year and last updated.
```

What comes back: three films last updated in September 2015 (Drinking Buddies, Va Savoir (Who
Knows?), A Town Like Alice). Say: "Nothing new in years. Now watch."

**Then insert.** Say: "A distributor just uploaded a film." In the terminal:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py
```

Wait for `vector search sees it`. Then, in the same chat:

```text
Check again. What are the three most recently updated films in our movie catalog?
```

What comes back: **The Projectionist of Marigold Falls** (2015): a documentary about the last
projectionist in a small-town cinema, 98% from 62 critics, 3,100 IMDb votes, 92 minutes, PG.
If Copilot repeats the old list, ask:

```text
Query the catalog again right now.
```

If you have time, ask this. Copilot should say yes:

```text
Would it qualify for our Hidden Gems series?
```

Say: "We're starting simple: a lookup. A minute ago the newest film was from 2015. There's no sync
and no overnight copy. Copilot asked Atlas, and Atlas answered with what's true right now."

## 1:30 Prompt 2: hidden gems (filter and sort)

```text
Which movies do critics love that hardly anyone has seen? I mean a critic score of 95% or higher from at least 40 critic reviews, and under 15,000 IMDb votes. Movies only, no TV series. Show the 10 with the most critic reviews: title, year, runtime, rating, critic score, critic reviews and votes.
```

What comes back: the top ten. Copilot doesn't state the total, so don't quote one. (112 films
qualify after the insert.) The ten are **13 Hours in a Warehouse** (98% from 267 critics, only
734 votes), Life Itself, Mr. Turner, Amy, Murderball, Spellbound, Shaun the Sheep Movie, Project
Nim, Winged Migration and Gloria.

Say: "One step harder: four conditions and a sort. I didn't export anything. Copilot asked Atlas,
and Atlas filtered 21,000 films and sorted them where the data lives. These are the movies
critics love and the public hasn't found."

## 3:00 Prompt 3: critics vs audiences (aggregation pipeline)

```text
Which movies did critics love but audiences didn't? Among movies with at least 40 critic reviews and at least 10,000 audience ratings, show the five with the biggest gap between the critic score and the audience score: title, year, critic score and audience score. Then one sentence on what you notice.
```

What comes back: **Spy Kids** (critics 93%, audiences 45%), Night Moves, Antz, Mr. Turner,
Stuart Little 2. Fifth place is a tie at 40 points, so Copilot may show Nurse Betty (critics 84%,
audiences 44%) instead of Stuart Little 2. Both are right.

Say: "Harder again: an aggregation. No field in the data holds this gap. It has to be calculated
for every film, then ranked. Critics gave Spy Kids 93%. Audiences gave it 45%."

For a technical room, follow with this prompt. It is optional, so rehearse it first:

```text
Show me the exact query you ran for that answer.
```

## 4:15 Prompt 4: the half-remembered movie (vector search)

```text
Dana at the box office has a customer who can't remember the name of a movie. Find out how the customer described it, then tell me which movie it is by matching that description to the plots in our movie catalog. Keep it under 60 words.
```

What comes back: **Wings of Desire (1987)**. Copilot read Dana's Teams post ("angels who watch over
a city... one of them wants to become human because he falls in love with a trapeze
artist"), then matched it to plots in Atlas.

Say: "The hardest kind: there's nothing to filter on. That's vector search. She never said the
title, or a single word from the plot summary. Atlas matched the meaning, not the words. Atlas
builds that meaning index itself, so there's no pipeline to build." (Behind the scenes: vector
search on `fullplot`, score 0.83. The next closest film scores 0.77.)

## 5:15 The old way (45 seconds)

Say: "Checking a film lineup today means five places. The catalog tool for runtimes and ratings.
Teams for what the team said. A Word file for the series rules. A spreadsheet for license
prices. A folder for last year's lineup. About an hour, and someone always misses something.
Let's ask Copilot instead."

## 6:00 Prompt 5: check the lineup

```text
Helen needs me to check her draft Hidden Gems lineup. Show one table with Film, Fee, Problem and Source columns. For Source, say Atlas, Teams or OneDrive, and name the document. Then give the total against the budget and three swaps that fix every problem and stay within budget. Keep it short.
```

Don't read it aloud. Paste it and say: "I'm adding one column to show where each fact came from."

Helen's draft, and what is wrong with it:

| Film | Year | Min | Rating | Fee | Problem (and where the rule lives) |
|---|---|---|---|---|---|
| Song of the Sea | 2014 | 93 | PG | $1,000 | none |
| '71 | 2014 | 99 | R | $1,000 | one of three R films |
| Murderball | 2005 | 88 | R | $850 | one of three R films |
| Leviathan | 2014 | 140 | R | $1,000 | 140 min is over the 125-minute limit (**Teams**); third R film (**guidelines**) |
| The Fog of War | 2003 | 95 | PG-13 | $850 | played last year (**OneDrive**, last year's lineups), even though Sam asked to bring it back (**Teams**) |
| Wings of Desire | 1987 | 128 | PG-13 | $650 | 128 min is over the limit (**Teams**) |
| **Total** | | | | **$5,350** | **$550 over the $4,800 budget** (Helen's post plus the rate card) |

Copilot's answer will vary. Check it against the five problems above. Its swaps must keep
the total under $4,800 and keep at least two non-English films. One valid fix is The Adventures
of Robin Hood (1938), The Rules of the Game (1939) and Belle de Jour (1967), which brings the
total to $4,350.

Point at the table. Say: "Read down the Source column. Every number came from a different place:
the runtimes and ratings from Atlas, the curfew from Walt in Teams, the rules from a Word
document, the prices from the rate card, last year's films from another file. That's the hour I
mentioned, in one answer, with receipts."

**Optional closer** (only if the clock shows under 8:30):

```text
Draft my Teams reply to Helen with the fixed lineup and the new total.
```

## 9:00 Close (45 seconds)

Say: "A simple lookup, an aggregation and a vector search, all from plain English in one chat. Under
ten minutes, against an hour of tab hopping. A film added a minute ago, a list of hidden gems
from 21,000 titles, a lost movie found from a vague description, and a lineup checked for
five problems across three systems.

The film catalog was a sample. Swap in your own orders, customers or tickets, and the
pattern is the same. Copilot reaches the data the business runs on, live, together with
Teams and OneDrive. One connector. No copy. No custom build. 'But can Copilot see our
data?' Now it can."

After the session, run:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py --undo
```

---

## Q&A prompts

Use these only if someone asks "can it do X?". They are optional, so rehearse them first.

Analytics across films. Expect Christopher Nolan (9 films, 8.34), Hayao Miyazaki (16 films, 8.07)
and Majid Majidi (8 films, 8.03):

```text
Which directors with at least six films since 1980 have the highest average IMDb rating? Show the top three with film count and average.
```

Location search. Expect two theaters in Minneapolis (0.4 and 0.7 miles), then Roseville (5.2 miles):

```text
Which movie theaters are closest to downtown Minneapolis? Show the three nearest and how far each is in miles.
```

Counting. Expect CA 169, TX 160, FL 111, NY 81, IL 70:

```text
Which five states have the most movie theaters in our theater list?
```

## If something goes wrong

- **A prompt takes more than 60 seconds.** Talk over it with the "same pattern for any
  catalog" point. If it fails, switch to your dry-run recording for that beat.
- **Copilot can't reach the database.** Check the model picker is not on Auto. Then put this at
  the front of the prompt, with your own project and cluster, then paste your prompt after it:

  ```text
  In the Atlas project '<your-project>', cluster <your-cluster>, database sample_mflix,
  ```

- **Prompt 1b misses the new film.** Check the terminal printed `vector search sees it`, then ask:

  ```text
  Show me the film "The Projectionist of Marigold Falls".
  ```

- **Prompt 4 matches the wrong movie.** Ask:

  ```text
  Using semantic search on the plots, which movie is closest in meaning to the customer's description?
  ```

- **Prompt 2 includes TV series or odd years.** The sample data has 232 TV series and a few
  rows whose year is text, not a number. Say "movies only" (already in the prompt).
- **Prompt 5 skips a source or the table is messy.** Use the longer version:

  ```text
  Helen asked me to check her draft Hidden Gems lineup before she signs the contracts. Using our movie catalog, the series guidelines, the license rate card, last year's lineups and what the team has said: what breaks the rules, and what does it cost against the budget? Show one table with Film, Year, Minutes, Rating, License fee and Problem columns. Name where each rule comes from: catalog, guidelines, rate card, last year's lineups or team notes. Then give the total against the budget and three swaps that fix every problem. Keep it short.
  ```

  Or name the missing source:

  ```text
  Also check last year's lineups.
  ```

  ```text
  Also check what Walt said about show length.
  ```

- **Teams posts aren't found.** Upload `fallback/Hidden Gems channel export.docx` to OneDrive.
  Copilot will say it used the channel export. Say "the team's notes".

## Things to know about the data

- `sample_mflix` has duplicate rows for a few films (Django Unchained, Guardians of the Galaxy,
  Food, Inc., The Secret World of Arrietty). None are in the lineup.
- There are two films titled Leviathan: 1989 (a sea-monster horror film) and 2014 (the Russian drama).
  Helen's post says "2014, the Russian drama" on purpose.
- The comments collection is placeholder text, so the demo doesn't use it.
- The data stops in 2015. That's why the series is "hidden gems", which age well.
- Prompt 2 asks for under 15,000 IMDb votes, while the series guidelines allow under 50,000. The
  tighter cut keeps the list to films almost nobody has seen, and every film it returns still
  meets the guidelines.

## Before you present

- Confirm how the connector signs in to Atlas. If it passes through each user's identity, say
  so, because the audience will ask about access control.
- Confirm the Atlas numbers:

  ```bash
  .venv/bin/python demos/leafy-cinema/scripts/demo_queries.py --check
  ```

- Run every prompt once in Copilot, in order, in one chat, on the model you will present on,
  and time them. Record your own dry run as a fallback.
- Stage Teams at least two days ahead, or upload the fallback export.
- Remove the film from your rehearsal:

  ```bash
  .venv/bin/python demos/leafy-cinema/scripts/live_insert.py --undo
  ```
