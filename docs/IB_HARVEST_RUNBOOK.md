# IB Harvest Runbook — click-by-click (Windows)

*Session 9i. Goal: 5-minute TWSE bars, years deep, via your own
Interactive Brokers account. Total time ~15 min of clicking + ~35
min of unattended fetching. Everything runs on YOUR computer.*

---

## Step 0 — Install Trader Workstation (skip if already installed)

If you only use the IBKR mobile app / web portal, you need the
desktop platform (the API lives in it):

1. Browser -> **interactivebrokers.com** (or .com.hk) -> top menu
   **Trading** -> **Platforms** -> **Trader Workstation (TWS)** ->
   **Download** for Windows.
2. Run the installer, launch **Trader Workstation**, log in with
   your normal IBKR username/password (choose **Live** account;
   complete two-factor on your phone if prompted).
3. Leave TWS open and logged in for everything below.

*(Alternative: "IB Gateway" is a lighter no-GUI version — same
download page. If you use Gateway, its ports are 4001/4002; the
script tries all ports automatically.)*

## Step 1 — Enable the API in TWS (2 minutes)

1. In TWS, top-left menu: **File -> Global Configuration...**
   (on some versions it is **Edit -> Global Configuration...**).
2. In the left-hand tree of the window that opens: click **API**,
   then **Settings** under it.
3. On the right side:
   - TICK the checkbox **"Enable ActiveX and Socket Clients"**.
   - You may LEAVE **"Read-Only API"** ticked — we only read
     historical data; read-only is the safer setting.
   - Look at **"Socket port"** — just note the number (7496 for
     live TWS, 7497 for paper; no need to change it — the script
     tries all standard ports).
4. Click **OK**. If Windows Firewall pops up asking to allow TWS
   network access, click **Allow**.
5. Keep TWS running and logged in.

## Step 2 — Check / add the Taiwan market-data subscription (5 min)

1. In a browser: **interactivebrokers.com -> Log In -> Client
   Portal** (this is the website, separate from TWS).
2. Click the **person/head icon** in the top-right -> **Settings**.
3. Under **Account Settings**, find the **Trading** section ->
   click **Market Data Subscriptions** (sometimes shown with a gear
   icon; on newer layouts: Settings -> Account Settings -> scroll
   to "Market Data Subscriptions" -> click the **gear/Configure**).
4. You'll see Current subscriptions and an **Available** list
   grouped by region. Open **Asia-Pacific** (or type "Taiwan" in
   the search box).
5. If you see a **Taiwan Stock Exchange** entry: tick it ->
   **Continue/Save** -> it shows the monthly fee (a few USD) and
   activates within minutes. (You can return to this same page to
   UNSUBSCRIBE after the harvest — billing is monthly.)
6. If Taiwan does NOT appear in the list for your account: don't
   stop — go to Step 3 anyway; the `verify` step also tries
   DELAYED data, which sometimes serves historical bars without a
   subscription. The verify output will tell us definitively.
7. If you subscribed: restart TWS once (log out, log back in) so
   the entitlement loads.

## Step 3 — Run the three commands (PowerShell)

Open **PowerShell** (Start menu -> type "powershell" -> Enter),
then paste these lines one at a time:

```powershell
cd C:\Users\Bill\Downloads\execution_analytics
python --version        # any Python 3.10+ is fine; if this errors,
                        # install from python.org first (tick
                        # "Add python.exe to PATH" in the installer)
pip install ib_async
python scripts\ib_harvest.py verify
```

**Reading the verify output** (TWS must be open and logged in):
- `connected on port 7496` (or similar) -> TWS API is reachable.
- `VERIFY OK — proceed to fetch` -> everything works; continue.
- `LIVE: ...error...` then `DELAYED: 53 bars ...` + VERIFY OK ->
  works via delayed data, no subscription needed; continue.
- `No TW historical data served` -> your account can't get TWSE
  data at any tier; stop here and tell me — we fall back to the
  FinMind sponsor route.
- `No TWS/Gateway reachable` -> TWS isn't running, or Step 1's
  checkbox isn't ticked, or Firewall blocked it.

Then the harvest (leave the window open; ~35 minutes; safe to
interrupt and rerun — it resumes where it stopped):

```powershell
python scripts\ib_harvest.py fetch
```

And the decisive check (instant, offline):

```powershell
python scripts\ib_harvest.py sanity
```

**Reading sanity**: a table of per-name ratios (IB bar-sum vs
official TWSE daily volume on print days).
- ratios ~ **1.00** -> IB bars INCLUDE the closing auction — best
  possible outcome; IB supersedes every other source.
- ratios ~ **0.3-0.9** -> continuous-only (like TV) — still a big
  win (5m, years deep) and the derived-auction method applies.
- ratios ~ **0.001** or ~**1000** -> the lots-vs-shares unit factor
  needs flipping — one-line fix on my side.

## Step 4 — Hand back to me

Paste me the `verify` output and the first ~10 lines of `sanity`.
I take it from there: unit fix if needed, wire ib_bars.json into
the three execution studies, rerun everything at 5-minute
resolution across 2022-2026, and (if you want) unsubscribe
reminder for the market data.
