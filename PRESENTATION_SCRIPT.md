# Presentation Script — MSCI Index Review

**12 minutes, plus questions.** Audience is a program trading
desk, so assume they know the market cold and have a day already
running.

The idea is to show them a **tool**, not a paper. Most of the talk
is "here's what this page does and why you'd open it." Only the
case study gets numbers, and even there, only the handful that
carry the argument.

---

## The arc

| # | Page | Time | What they should take away |
| --- | --- | --- | --- |
| 0 | Opening | 0:20 | This is built for a dealer, not a PM |
| 1 | Start Here | 0:40 | The constraints, up front |
| 2 | Review Database | 0:45 | Every past change, searchable |
| 3 | Predict Changes | 1:30 | The rulebook, reproducible end to end |
| 4 | Daily Data | 1:00 | Cross-market context, and why I narrowed |
| 5 | **Taiwan Case Study** | **7:00** | **The close is the venue. Here's the order.** |
| 6 | Agentic Workflow | 1:00 | Most of this could run overnight |
| — | Close | 0:15 | Four sentences, then stop |

**Three rules for delivering it.**

Say what a page is for before you show it. People decide in a few
seconds whether to look up, and a chart on its own doesn't tell
them.

Say out loud that the first four pages are setup. It buys you
permission to move fast, and it tells them where the real content
is.

Raise your own weak points before anyone else does. They're all
on the site anyway, and naming them first turns a challenge into
a conversation.

**[Stage directions in brackets. Everything else is roughly what
you say.]**

---

# 0 · Opening

*20 seconds.*

> When MSCI adds a stock to an index, every fund tracking that
> index has to buy it, on a date that's published weeks ahead.
> What makes it interesting isn't that it happens. It's that
> everyone can see it coming.
>
> So I wasn't trying to work out whether the stock goes up. That's
> a PM's question. I wanted the dealer's version: how much has to
> trade, when does it show up, and where do you put it.
>
> The whole thing runs on free exchange files and a retail broker
> feed. No terminal. I'll show you where that hurts.

---

# 1 · Start Here

*40 seconds. Point at the route list, don't read it.*

> Four pages. Three of setup, then the analysis.

**[Analysis Limitations.]**

> I put the constraints first because they shape everything after
> them.
>
> The first one is that MSCI sells the constituent and free-float
> files, and I don't have them. So every weight here is rebuilt
> from public sources. If the float is off, the size cutoff lands
> in the wrong place, and then the prediction does too.
>
> The second is positioning data. No borrow book, no live short
> interest, no holdings feed. Anything I say about who's already
> in a name has to be assembled from what the exchange and the
> depository publish.

**[Why Taiwan.]**

> Two reasons I picked Taiwan for the deep dive. I did an
> index-rebalancing project on this market during an internship,
> so I'm carrying that forward. And Taiwan publishes an unusual
> amount for a market its size, free — daily buying and selling
> broken out by investor type, plus borrowing and lending
> balances.

---

# 2 · MSCI Index Review Database

*45 seconds. This page is a lookup tool. Show it working.*

> This is the event history, rebuilt from press releases and
> factsheets, because nobody publishes it in a form you can
> actually use.

**[Hover the map.]**

> Top section is the latest review across the region. Hover a
> market and you get its adds and deletes for that cycle.

**[Switch markets in section 2.]**

> Underneath, pick any market and you get its full history back to
> 2006. That's the sample everything later on is measured against.

**[Sections 3 to 5, quickly.]**

> Then current constituents sorted by weight and how long they've
> been in — which is really a deletion watchlist, since the small
> ones at the bottom are the ones with a buffer problem. And two
> search tools: one by company, one by review period. If someone
> asks whether a name has been in and out before, that's a
> ten-second answer.

---

# 3 · Predict MSCI Index Changes

*90 seconds. The credibility page. Slow down in the middle.*

> This walks MSCI's methodology one step at a time and ends with a
> call for August.

**[Steps 1 and 2, briskly.]**

> First the timeline, and why a passive fund has no choice about
> any of it. Then the eligibility screens. Most of the universe
> drops out here.

**[Step 3 — open one of the dropdowns.]**

> This is the step I'd want you to poke at. It works out where the
> size cutoff sits, starting from MSCI's own published reference
> and scaling it forward with a published index return.
>
> And every step has one of these dropdowns with the arithmetic
> in it. There isn't a number on this page I typed in by hand. You
> can follow the chain yourself, which is the point.

**[Step 4.]**

> Then each candidate against the cutoff and its buffers. The
> buffer matters more than the cutoff, honestly. MSCI doesn't add
> you when you cross the line, they add you when you clear it by a
> margin, and that's what makes any of this predictable.

**[Step 5.]**

> Last step is the call for August, with a confidence band rather
> than a yes or no. That band is the float problem from page one
> showing up again.

---

# 4 · Index Rebalance Daily Data

*60 seconds. Cross-market. This page has controls — use one.*

> One page of context before Taiwan. Twelve APAC markets, daily
> data.

**[Section 2.]**

> Return from announcement day onward. Roughly the shape you'd
> expect: a drift into the effective date, some of it handed back
> after.

**[Sections 3 and 4.]**

> This is the part a dealer cares about. Effective-day volume
> against a normal day, and notice the unit — it's a multiple of
> ADV, not a percentage. And look at the shape around the date.
> It's one day. It isn't a week of quiet accumulation.

**[Move the threshold slider in section 5.]**

> You can push the threshold up here and watch how much of the
> effect survives a stricter definition. It holds up better than I
> expected.

**[The transition. This buys the next seven minutes.]**

> Now, here's why I stopped and went one market deep. This panel
> puts twelve venues side by side, and they don't resolve their
> close the same way. Taiwan and Hong Kong run a real closing
> auction. Japan, Korea and Australia don't, not in the same
> sense. Average them together and you smooth away the exact thing
> worth looking at.

---

# 5 · Taiwan Case Study

*Seven minutes. Slow right down — everything so far was setup and
the room knows it.*

> This is the actual work. It builds outward from the venue: what
> the Taiwanese close does on an index day, how much it can
> swallow, whether anyone's already positioned, and how big the
> order sitting in front of us is.

## 5.1 · Ground rules

> Before any of it — the intraday work runs on 5-minute bars, and
> my broker's history for Taiwanese stocks doesn't go back very
> far. So these are recent-regime results and I'd rather say that
> now than have it come out later.
>
> Where I could get a longer history I used it. The auction
> section further down runs on eleven years of the exchange's own
> file.

## 5.2 · Where the volume actually prints

> This is the finding everything else sits on.
>
> A Taiwanese stock normally puts about a tenth of its daily
> volume through the closing auction. On its index effective day,
> it's closer to four fifths.
>
> That changes what you're even trading. Most of the day's
> business goes through one five-minute call. If you're working
> that order, the continuous session barely matters.

## 5.3 · The same thing, through the session

> Here's the intraday shape. Normal days build gradually. Index
> days sit flat all afternoon and then hit a wall at half past
> one. There's nowhere quiet to hide the trade.

## 5.4 · What the close costs — and where I corrected myself

> So what does it cost you? Measured against the day's VWAP,
> almost nothing. Which sounds great, and I didn't believe it.
>
> If the auction is four fifths of the day's volume, it's also
> four fifths of the day's VWAP. I was comparing the close against
> a benchmark that mostly is the close. It was always going to
> come out near zero.
>
> So I rebuilt it — the jump from the last continuous price into
> the auction print, where the auction's own volume isn't inside
> the benchmark. That gives a real number, and it's about five
> times bigger.
>
> The two versions reconcile arithmetically, which is how I know I
> found the right explanation rather than a convenient one.

## 5.5 · How much the close can absorb

> Now the bigger sample. Eleven years of the exchange's five-second
> auction file, every listed company.
>
> On an index day the typical impact is still close to zero. But
> the spread around it is three to five times wider than the same
> name's ordinary auctions.
>
> So the honest version isn't "the close is cheap." It's that the
> close is cheap on average and a lot less predictable when an
> index trade is in it. That's a sizing input. It isn't a view on
> price.

## 5.6 · Has anyone bought them already?

> Three names look likely to go in this month, so the obvious
> question is whether the market's already there.
>
> A typical addition draws real foreign buying in the weeks before
> the announcement. These three didn't — they sat below their
> peers, while foreigners were buying the peer group overall.
>
> Flow data only shows you trading, though, not holding. So I also
> pulled the depository's weekly census of custody accounts, which
> shows whether the large-holder bucket is growing. If passive
> money were building a position quietly, you'd see it there. It
> isn't showing up in either place.
>
> That cuts both ways and I'd say so. Less crowding to unwind, but
> also nobody agreeing with me yet.

## 5.7 · How big is the order

> Last section, and the one you'd actually use.
>
> Order size is index weight times tracking assets. Weight I can
> build. The tracking assets were the hard part, and that's where
> most of the time went.
>
> The number this project started with was USD 180 billion,
> which someone had typed into a script years ago as a proxy with
> nothing behind it. I threw it out.

**[Open the mandate dropdown.]**

> There are two pieces. First, the ETFs I can actually name — the
> Taiwan exposure sitting inside emerging-market and global
> trackers, plus the funds on the MSCI Taiwan indexes themselves.
> That last group was missing from the earlier version, and it
> shouldn't have been, because a new constituent goes into those
> at the same review.
>
> Second, and this is the part I like — the indexed money that has
> no ticker. Separate accounts, index mutual funds, pension
> mandates. MSCI is a public company, so it reports the fee
> revenue it earns on that money to the SEC every quarter. It just
> never reports the assets.
>
> But you can invert it. Take the fee revenue, divide by the fee
> rate MSCI earned on ETFs that same quarter, and you get the
> assets. It works out to at least a third of the ETF pool.
>
> Add the two together and you land at USD 60 billion.

**[Only if pressed — but have it ready.]**

> Every step in that errs low, which is the only reason I'll
> defend the number. Institutional mandates negotiate their index
> fees down, so pricing them at the ETF rate understates what's
> there. And I deliberately didn't scale up for the ETFs I
> couldn't enumerate, because a lot of them are single-country
> China and India funds that hold no Taiwan at all.

**[Back to the bars.]**

> Run that through and each of the three names needs somewhere
> between a quarter and a half of a normal day's volume — all
> arriving in an auction that usually handles a tenth of the day.
>
> And every name has its own dropdown with the full working:
> weight, dollars, shares, divided by that name's own ADV. Nothing
> on this page is asserted. It's arithmetic you can check while
> I'm talking.

## 5.8 · The result that didn't work

> One more, and I'd rather volunteer it.
>
> I tested a handful of rules for whether any of this predicts
> direction. Fitted them on the older events, scored them on the
> newer ones. Nothing survived. The best of them is weak, and it's
> the best of several tries, so it's weaker than it looks.
>
> That's a null result and I've written it up as one. It's the
> reason this site sizes the trade instead of forecasting the
> price. I'd rather give a desk a size I can defend than a view I
> can't.

---

# 6 · Agentic AI Workflow

*60 seconds.*

> Last page. Everything here is generated by a script with a named
> input and a checked output, which is most of what you need to
> make it run on its own.

**[The loop.]**

> Four steps. Something to fetch the exchange files when they
> publish in the evening. Something to rerun the analysis and tell
> you what actually changed. Something to draft the note in the
> desk's voice, with every line traceable to the file it came
> from. And then a checker that reads the draft back against those
> files and won't let anything through that it can't tie out.

**[The timeline.]**

> On the clock, it's an evening's work: files land, the framework
> reruns, the draft gets written and checked, and it's ready to go
> before the open.

**[Not on the page — say it.]**

> I'll be straight about where this actually stands. The
> harvesters, the analysis and the test suite all exist today. The
> scheduler, the writer and the checker don't. Three of the four
> boxes are real.
>
> And it's the fourth one that matters. Three agents that fetch,
> compute and write give you a publishing machine. What makes it
> research is that the last one can stop the note.

---

# Close

*15 seconds. Four sentences, then stop talking.*

> So, to pull it together. The close is where the trade happens,
> and most of an index day goes through it. It's cheap on average
> but a lot less predictable when there's an index order in the
> book. Nobody's pre-positioned these three names on either
> measure I could check. And the order is a meaningful slice of a
> normal day's volume, priced off a number I can source line by
> line.
>
> Happy to dig into any of it.

---

# If they ask

**"How much do I trust your float numbers?"**
> Not as much as MSCI's, and that's what the band is for. Names
> that land inside it I flag as coin-flips rather than calls.

**"That AUM figure is a guess."**
> It's a floor, and I can name every dollar in it. The ETF side is
> summed fund by fund from published assets. The rest comes off
> MSCI's own filings. Every approximation in it pushes the answer
> down, not up, and I'm happy to walk through them.

**"You're only covering part of the fund universe. Why not scale
up?"**
> Because what I'm missing isn't a smaller copy of what I have.
> A lot of it is single-country China, India and Korea funds that
> can't hold Taiwan at all. Scaling on coverage would credit
> Taiwan with money that's contractually barred from owning it.

**"Your intraday sample is small."**
> It is, which is why I state those results as a range rather than
> a point. When I needed a bigger sample I changed instrument —
> the auction work uses eleven years of exchange data, not the
> broker feed.

**"What would you do with a terminal?"**
> Three things. Real free float, which removes the band. A borrow
> book, so I can see crowding while it's forming instead of after.
> And deeper intraday history, which would let me test whether any
> of the auction behaviour is regime-specific.

**"Would you trade it?"**
> I'd size it, not direct it. The order is a known fraction of a
> known day, it lands in a venue I've measured, and I'd execute in
> the close — printing in the benchmark is zero tracking error by
> definition. Working the session only helps if you're right about
> direction, and nothing I found predicts direction.
