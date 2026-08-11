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
| 3 | Predict Changes | 1:30 | The rulebook end to end, and a per-name probability |
| 4 | Daily Data | 1:00 | The print is one day; venues differ |
| 5 | **Taiwan Case Study** | **7:00** | **The close is the venue. Here's the order.** |
| 6 | Agentic Workflow | 1:00 | Fetcher, Analyst, Author, Reviewer — three of four built |
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
> And the buying isn't a view. A tracker buys the name because
> its benchmark now contains it. That's forced demand rather than
> fundamental demand, and it behaves differently — it's
> price-insensitive, and it turns up on a known date.
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
> call for August — announcement on the 12th, effective at the
> close on the 31st.

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
> can follow the chain yourself, end to end.

**[Step 4.]**

> Then each candidate against the cutoff and its buffers. The
> buffer matters more than the cutoff. MSCI doesn't add you when
> you cross the line, they add you when you clear it by a margin,
> and that's what makes any of this predictable.

**[Step 5 — the call.]**

> Last step is the call, and it's a probability per name rather
> than a yes or no. Under the hood it's twenty thousand simulated
> reviews. The rule itself is sharp — what gets shaken is the two
> inputs I can't observe: where the cutoff lands inside MSCI's own
> five percent band, and which of the ten pricing dates they
> strike it on.
>
> Four names are in reach. Three clear the bar by enough that the
> simulation barely wavers — better than 95. Phison sits closer
> in, at 65. And on the other side there's a border deletion
> hanging over the floor at 36.
>
> What that number doesn't price is MSCI's discretion — they can
> flex the count, and there's a liquidity screen I take as passed.
> I'd rather volunteer that than be caught by it.

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

## 5.2 · The two sides of the trade

**[The diagram — parties left and right, the auction in the
middle.]**

> One page of framing, because it tells you what to measure.
>
> On one side, the trackers. Their demand is three numbers
> multiplied: the probability of the change, the weight gap — what
> the index will assign minus what they hold — and the money
> tracking the index. They consume liquidity at the close, because
> printing in the benchmark is zero tracking error by definition.
>
> On the other side, whoever supplies it — prop desks, hedge
> funds, index-rebalance pods. They accumulate inventory
> beforehand and provide liquidity into that same auction.
>
> Probability came from the page before. Weight I rebuild. The
> money tracking the index is the hard number, and it gets its own
> section at the end. Everything in between is about the venue
> where the two sides meet.

## 5.3 · Where the volume actually prints

> This is the finding everything else sits on.
>
> On a normal day, a Taiwanese stock puts about nine and a half
> percent of its volume through the closing auction. On its index
> effective day, 79 percent.
>
> That changes what you're even trading. Most of the day's
> business goes through one call at half past one. If you're
> working that order, the continuous session barely matters.

## 5.4 · The same thing, through the session

> Here's the intraday shape. Normal days build gradually. Index
> days sit flat all afternoon and then hit a wall at the close.
> There's nowhere quiet to hide the trade.

## 5.5 · What the close costs — and where I corrected myself

> So what does it cost you? Measured against the day's VWAP,
> minus six basis points. Which sounds great, and I didn't
> believe it.
>
> If the auction is 79 percent of the day's volume, it's also 79
> percent of the day's VWAP. I was comparing the close against a
> benchmark that mostly is the close. It was always going to come
> out near zero.
>
> So I rebuilt it — the jump from the last continuous price into
> the auction print, where the auction's own volume isn't inside
> the benchmark. That reads about minus 25 basis points on
> additions.
>
> And the two versions reconcile: minus six divided by the one
> minus 79 percent the benchmark has left is roughly the direct
> number. That's how I know I found the right explanation rather
> than a convenient one.

## 5.6 · How much the close can absorb

> Now the bigger sample. Different instrument, deeper history —
> eleven years of the exchange's own auction file, 2,815 sessions.
>
> On an index day the typical impact is still close to zero. But
> the spread around it is three to five times wider than the same
> name's ordinary auctions, and nine prints in ten still land
> inside about one point eight percent.
>
> So the fair reading is that the close is cheap on average and
> a lot less predictable when an index trade is in it. That's a
> sizing input, not a price forecast.

## 5.7 · Foreign flow on the day itself

> Taiwan publishes daily foreign buying and selling per stock, so
> you can see the print land.
>
> I scaled each event day by that stock's own normal foreign
> activity. On the effective day, additions take about three
> times a normal day's net buying. Deletions are sharper — five
> times normal selling, and they keep bleeding at almost twice
> normal for two weeks after. Outside the effective day, both
> sides sit inside the noise.
>
> One caveat I'd volunteer: that file nets all foreign accounts
> against each other, so if foreign prop is providing liquidity to
> foreign trackers, these multiples understate the gross index
> flow.

## 5.8 · Has anyone bought them already?

> So is the market already positioned this time?
>
> A typical confirmed addition drifts up seven percent against
> the market before the announcement, on real foreign buying. The
> three adds I can see in the flow file sit below their peer
> median instead — the fourth trades on the TPEx and isn't in the
> file at all. The depository's weekly census of large holders
> shows nothing unusual either. And Nanya has drifted 17.6
> percent the wrong way.
>
> Price and flow together are pricing this at roughly zero, and
> the rule says better than 95. That gap is the thesis. It cuts
> both ways and I'd say so — less crowding to unwind, but also
> nobody agreeing with me yet.

## 5.9 · How big is the order

> Last big section, and the one you'd actually use. Weight I
> build. Liquidity I've just spent five minutes on. What's left is
> the money tracking the index, and that's where the time went.
>
> The number this project started with was USD 180 billion, which
> someone had typed into a script years ago as a proxy with
> nothing behind it. I threw it out.

**[Open the mandate dropdown.]**

> There are four pools of money that have to buy, and most people
> only think of the first. Index ETFs. Index mutual funds.
> Institutional passive mandates — a pension fund handing
> BlackRock twenty billion to track MSCI World, which sits in no
> ticker anyone can look up. And then benchmark-aware active
> managers, who technically don't have to buy, but a manager
> holding none of a new one-percent constituent is running a
> minus-one-percent active bet by standing still.
>
> I can reach the first three. Let me show you how.
>
> First, the ETFs I can actually name — the Taiwan exposure
> sitting inside emerging-market and global trackers, plus the
> funds on the MSCI Taiwan indexes themselves. That last group
> was missing from the earlier version, and it shouldn't have
> been, because a new constituent goes into those at the same
> review. Call it 45 billion.
>
> Second, the indexed money that isn't an ETF. Separate accounts,
> index mutual funds, pension mandates. MSCI is a public company,
> so it reports the fee revenue it earns on that money to the SEC
> every quarter. And on the last earnings call, management put a
> size on the pool itself: about five trillion dollars.
>
> Five trillion against two point eight trillion of ETF money.
> So for every dollar sitting in an MSCI-linked ETF, there's
> about a dollar seventy-seven of mandate money with no ticker
> on it. Apply that ratio to the Taiwan ETFs I just named.
>
> Add the two together and you land at USD 125 billion.

**[Only if pressed — but have it ready.]**

> The fee revenue is my check on the five trillion. Fifty-six
> million a quarter on five trillion of assets is about 0.45
> basis points, a fifth of what MSCI earns on ETFs. That's the
> right shape — mandates negotiate their fees down — so the two
> disclosures agree with each other.
>
> One assumption, and I'll say it before you do: the five
> trillion spans every MSCI index, so I'm assuming the mandate
> mix looks like the ETF mix. If you don't want that assumption,
> invert the fee revenue at the ETF rate instead and you get a
> hard floor of sixty billion. The ranking of the names doesn't
> move either way. And the fourth pool, benchmark-aware active,
> is still missing from both numbers entirely.

**[Back to the bars.]**

> Run that through and the four names need somewhere between half
> a day's volume and one and a half days' — all arriving in an
> auction that usually handles a tenth of the day. Phison is the
> tightest print, just under a day and a half of its own volume,
> and it's also the least certain add, at 65. Those two facts
> belong in the same sentence.
>
> And the table underneath carries the full working per name:
> weight, dollars, shares, divided by that name's own ADV. Nothing
> on this page is asserted. It's arithmetic you can check while
> I'm talking.

## 5.10 · The deletion, and the borrow check

> The border deletion gets its own check, because the trade there
> is a short, and a short needs borrow.
>
> Taiwan publishes securities-lending balances daily. Caliway's
> sits at nine and a half million shares — the 18th percentile of
> its own covered history, and down about twelve percent over the
> last month. Nobody's building a borrow into this.
>
> Caveat: that file only sees the lending channel. Margin shorts
> and synthetic shorts are invisible, so this is the absence of
> evidence, not proof of absence.

## 5.11 · The result that didn't work

> One more, and I'd rather volunteer it than be caught by it.
>
> I tested a handful of rules for whether any of this predicts
> direction. Fitted them on the older events, scored them on the
> newer ones. Nothing survived. The best of them is weak, and it's
> the best of several tries, so it's weaker than it looks.
>
> That's a null result and I've written it up as one. It's the
> reason this site sizes the trade instead of forecasting the
> price.
>
> Although here's what I'd say in my own defence, and it's the
> more interesting version. None of the things I tested was the
> ratio that actually matters — forced flow over available
> liquidity. I couldn't build it historically, because per-event
> index weights need a point-in-time float stack going back a
> decade and I only rebuilt the recent ones. Two of the features
> that did come back significant are crude proxies for it: how
> liquid the name is, and how many other names are competing for
> the same day.
>
> So it's less "nothing works" than "I tested what I could build,
> and the thing worth testing needs data I don't have." That's a
> specific ask, not a shrug.

---

# 6 · Agentic AI Workflow

*60 seconds.*

> Last page. Everything on this site is generated by a script with
> a named input and a checked output, which is most of what you
> need to make it run itself.

**[The loop.]**

> Four agents. A Fetcher that retrieves what TWSE publishes in the
> evening — the daily net buying by investor type, the lending
> balances. An Analyst that reruns the framework on the new data
> and gives its own read of the market colour. An Author that
> writes the report, every line pointing back at the source. And a
> Reviewer that reads the draft against those files — if a number
> doesn't match, or the reasoning is flawed, it goes back for a
> rerun rather than out the door.

**[The timeline.]**

> On the clock it's an evening's work: files land, the framework
> recalculates, the draft flags anything unusual, the review
> either passes it or kicks it to a human, and it's sitting there
> at seven in the morning.

**[Not on the page — say it.]**

> Where it actually stands: three of the four are built. The
> fetching, the analysis and the reporting exist today; the
> reviewer is the one I'd finish first.
>
> Because that's the box that matters. Fetch, compute and write
> gives you a publishing machine. What makes it research is that
> the last one can stop the note.

---

# Close

*15 seconds. Four sentences, then stop talking.*

> So, to pull it together. In Taiwan the close is where an index
> day happens — cheap on average, three to five times less
> predictable with an index order in it. Four additions and a
> border deletion are live for August, and neither the flow file
> nor the depository shows anyone positioned yet. And the order
> behind them is half a day to a day and a half of each name's
> volume, priced off MSCI's own disclosures line by line.
>
> Happy to dig into any of it.

---

# If they ask

**"How much do I trust your float numbers?"**
> Not as much as MSCI's, and that's what the band is for. Names
> that land inside it I flag as coin-flips rather than calls.

**"That AUM figure is a guess."**
> It's MSCI's own numbers, multiplied. The ETF side is summed
> fund by fund from published assets. The multiplier is the five
> trillion MSCI disclosed against its own ETF pool, and the fee
> revenue checks it. One assumption in the chain, the mandate
> mix, and I flag it. If you'd rather have the number with no
> assumption at all, the fee inversion gives sixty billion, and
> the names rank the same.

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

**"Is Nanya really better than 95?"**
> That's the rule applied to my best inputs, with the two I can't
> observe simulated. What it doesn't include is MSCI's
> discretion — the count flex, the liquidity screen. I could fake
> a haircut for that, but I'd rather show the clean number and
> name what's outside it.

**"Would you trade it?"**
> I'd size it, not direct it. The order is a known fraction of a
> known day, it lands in a venue I've measured, and I'd execute in
> the close — printing in the benchmark is zero tracking error by
> definition. Working the session only helps if you're right about
> direction, and nothing I found predicts direction.

**"What would you do with a terminal?"**
> Four things, roughly in order of value. Licensed index files, so
> free float is real and the weight stops being an estimate.
> Mandate data, which retires the one assumption in the AUM
> chain. Holdings data on benchmark-aware active funds, which is
> the one pool of forced buying I can't see at all. And a borrow
> book, so I can watch crowding form instead of reading about it a
> week later.
>
> With the first of those I could finally build the feature I
> actually want to test — expected forced flow over available
> liquidity, per event, back a decade.
