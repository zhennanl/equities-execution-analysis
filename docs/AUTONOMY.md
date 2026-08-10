# WORKING AGREEMENT — how I make progress without you

Bill's ask (c-209): *"create a plan that would make you
iteratively improve our website, without stopping and asking me
for input... while working towards a state that aligns with my
vision."*

The obstacle is not effort, it is JUDGEMENT. Every time I stop
to ask, it is because a choice depends on your taste and I
cannot check my answer. So the whole design is about converting
taste into something I can check myself.

---

## THE FOUR ARTEFACTS

**1. A page spec** — `docs/PAGE_SPEC_<page>.md`
Reader, job, content in priority order, voice, non-goals, and
mechanical acceptance checks. Written from your answers,
approved by you ONCE. After that it is the authority: if a
change cannot be justified from the spec, it does not ship.

**2. A backlog** — `docs/BACKLOG_<page>.md`
Ordered. Every item has a definition of done that a machine can
evaluate. Items I invent go at the bottom; items you add go
wherever you put them.

**3. A parking lot** — `docs/PARKED.md`
The thing that makes non-stop work possible. When I hit a
decision that is genuinely yours, I do NOT stop and I do NOT
guess — I write the question, the options and my recommendation
here, skip the item, and carry on. You answer a batch whenever
you like.

**4. A decision log** — the session summary, as now.
Every judgement call, every correction, every reversal. You
audit outcomes instead of approving decisions.

## THE LOOP

    read spec -> take top unblocked backlog item
      -> implement
      -> verify (pytest + page smoke test + page_lint)
      -> record in session summary
      -> next item

Stop conditions, and only these:
- backlog empty
- a HARD STOP is required (below)
- verification fails twice on the same item — then park it,
  because a second failure means I have misunderstood something
  rather than mistyped something

## HARD STOPS

**Your rule:** never delete or overwrite harvested data in
`data/` without asking. This one is yours and it is the right
one — the refetch that destroyed 5,390 bars of Taiwan history
was exactly this failure, and no test caught it because the
operation looked successful.

**My standing rules,** which you did not ask for but which have
been how this project has run and which I will not relax to
make a page look better:
- never soften a caveat or drop a coverage warning
- never present an estimate as measured
- never assert a finding on a page — it goes to
  `CANDIDATE_FINDINGS.md` for you
- corrections are recorded openly, never quietly rewritten

## THE PROMPT TO GIVE ME

Short, because the spec carries the detail:

> Work through `docs/BACKLOG_review_db.md` in order. For each
> item: implement it, verify with pytest and
> `py scripts\page_lint.py`, and record it in the session
> summary. Do not stop to ask me anything — put any decision
> that needs me into `docs/PARKED.md` with your recommendation
> and move to the next item. Stop when the backlog is empty or
> you hit a hard stop.

Variants worth knowing:

- **Time-boxed:** *"...stop after 6 items and summarise."*
  Useful when you want to check direction early.
- **Single-theme:** *"...only the items tagged [density]."*
- **Discovery:** *"...and add any new backlog items you find,
  at the bottom, with a definition of done."* This is how the
  backlog stays alive without you writing it.

## WHY THIS SHOULD HOLD

The failure mode of autonomous work is confident drift — I keep
building, each step defensible, and the result is not what you
wanted. Three things guard against it:

1. **The spec is ordered.** Priority is written down, so I
   cannot quietly promote my favourite feature.
2. **Non-goals are explicit.** Most drift is scope creep into
   adjacent territory that felt natural at the time.
3. **Parking beats guessing.** The cost of a parked item is a
   delay. The cost of a guessed one is work you have to unwind
   — and, as this project has repeatedly shown, sometimes data
   you cannot get back.
