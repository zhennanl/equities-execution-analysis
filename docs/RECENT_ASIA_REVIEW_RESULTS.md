# Most Recent Completed Asia Index Reviews — Complete Per-Market Scan

*Revised 2026-07-28 (v2). v1 covered only the markets we had graded
backtests for; this version scans EVERY Asian market and writes "None"
explicitly where the provider reported no changes — absence of change
is information (it was our own review of v1 that caught the gap).
MSCI results parsed directly from MSCI's official public change list
PDF; FTSE from LSEG/FTSE notices.*

---

## MSCI May 2026 SAIR — ALL Asia-Pacific markets (ann May 12, eff close May 29)

Source: [MSCI Global Standard Indexes public list, Geneva May 12 2026](https://app2.msci.com/eqb/gimi/stdindex/MSCI_May26_STPublicList.pdf) — parsed in full.

| Market | Adds | Deletions |
|---|---|---|
| **China** | **22** (incl. Full Truck Alliance ADR, RemeGen, Sichuan Biokin, COSCO Shipping Energy H + 18 more A/H names) | **24** (incl. China State Construction, China Literature, Meitu, NetEase Cloud Music, Goodix, Weigao H + 18 more) |
| **Japan** | 3 (Furukawa Electric, Mitsui Kinzoku, Resonac) | **14** (Japan Airlines, M3, Oracle Japan, Sysmex, Shimadzu, Sekisui Chemical, Sony Financial, Toyota Industries, ZOZO, Tokyu, TIS, MonotaRO, Matsukiyo, Tsuruha) |
| **Taiwan** | 1 (MPI Corp) | 7 (Asia Cement, Catcher, China Airlines, Compal, Far Eastern New Century, THSR, Teco) — index 83→77 |
| **India** | 5 (Adani Energy Solutions, Federal Bank, Indian Bank, Multi Commodity Exchange, National Aluminium) | 4 (Hyundai Motor India, Jubilant Foodworks, Kalyan Jewellers, Rail Vikas Nigam) |
| **Korea** | None | 3 (Hanjin KAL, HD Hyundai Marine Solution, SK Biopharmaceuticals) |
| **Malaysia** | None | 6 (Axiata, MR DIY, Nestlé Malaysia, Petronas Dagangan, QL Resources, YTL Corp) |
| **Indonesia** | None | 6 (Amman Mineral, Barito Renewables, Chandra Asri, Dian Swastatika, Petrindo Jaya, Sumber Alfaria) |
| **Hong Kong** | None | 1 (Wharf Holdings) |
| **Philippines** | None | 1 (Jollibee Foods) |
| **Australia** | 1 (PLS Group) | None |
| **Singapore** | **None** | **None** (absent from MSCI's change summary = no changes) |
| **Thailand** | **None** | **None** (absent from summary = no changes) |

**Asia-Pacific totals: 32 adds, 66 deletions** — a strongly
deletion-skewed review, dominated by China's 24 and Japan's 14.

## FTSE June 2026 quarterlies — Asia indices

| Index | Result | Source |
|---|---|---|
| FTSE TWSE Taiwan 50 (eff Jun 18) | IN: GUC 3443, BizLink 3665, Nan Ya PCB 8046, Zhen Ding 4958; OUT: Compermed 6919, China Steel 2002, Formosa Plastics 1301, Hotai 2207; reserve list: Compeq, Innolux, Kinsus, WinWay, WT Micro | [FTSE notice Jun 5](https://research.ftserussell.com/products/index-notices/home/getnotice/?id=2620903) |
| FTSE China A50 (eff open Jun 22) | IN: GigaDevice, Montage, Dongshan Precision, Victory Giant, Weichai; OUT: CSCEC, Foshan Haitian, Haier Smart Home, Ping An Bank, Mindray | [LSEG press release](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-china-index-series-quarterly-review-q2-2026) |
| Straits Times Index (eff Jun 22) | **No constituent changes**; reserve list refreshed (First Resources, Keppel REIT, Olam, Sheng Siong, Suntec REIT) | [LSEG](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/straits-times-index-quarterly-review-june-2026), [SGX notice](https://links.sgx.com/1.0.0/corporate-announcements/QJLW41WE5X03WW82/891418_20260604%20Straits%20Times%20Index%20STI%20quarterly%20review_June%202026.pdf) |
| FTSE Bursa Malaysia KLCI (semi-annual) | **One constituent change** per LSEG (name not verified here — see source; a January PREVIEW article circulating a 3-name swap is speculation, not results) | [LSEG](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-bursa-malaysia-klci-june-2026-semi-annual-review) |
| FTSE SET (Thailand) | **Not verified** — no results notice located in this scan; treat as unknown, not as "no change" | — |
| FTSE ST Index Series (broader SG family) | Reviewed Jun 4 (changes in the smaller ST indices; STI itself unchanged) | [FTSE notice](https://research.ftserussell.com/products/index-notices/home/getnotice/?id=2620886) |

## What the complete scan adds to the picture

1. **The review was far bigger than our tracked slice**: we measured
   TW/KR execution behavior in depth, but China (46 total changes) and
   Japan (17) carried most of the Asia flow. Coverage priority for the
   universe build-out follows directly: China and Japan first.
2. **The deletion skew was real in May** — 66 deletions vs 32 adds
   across Asia, with Indonesia (0/6) and Malaysia (0/6) purely
   deletion-side. This is prior support for the Aug QIR skew screen
   (Indonesia/China deletion-skewed), which will be graded Aug 12.
3. **"None" rows matter**: Singapore and Thailand had zero MSCI
   changes and STI had zero FTSE changes — a desk telling clients
   "your SG book has no index event this cycle" is providing real
   information, and a scan that omits quiet markets can't say it.
4. **Migration mechanism confirmed at scale**: the deletions appear
   simultaneously as Small Cap ADDITIONS in
   [MSCI's Small Cap list](https://app2.msci.com/eqb/gimi/smallcap/MSCI_May26_SCPublicList.pdf)
   — the segment-migration netting our flow model should incorporate.

## Measured execution behavior (our graded markets, unchanged from v1)

MSCI TW deletions: T-multiples median 16x (THSR 38x), −4.3% front-run,
78% of volume on T, arb→tracker handoff 8/8. FTSE TW50: ~5x multiples,
$2.95B simulated turnover w/ 27% reweight leg validated on TSMC's real
−7.27M-share print. A50: futures/creations pre-funding, small cash
prints. Grading: MSCI deletions 10/10 (TW 7/7, KR 3/3); FTSE adds 9/9;
rank deletes LOW-tagged watch zone. Korea/press sources:
[Seoul Economic Daily](https://en.sedaily.com/finance/2026/05/13/msci-removes-hanjin-kal-hd-hyundai-marine-solution-sk),
[Focus Taiwan](https://focustaiwan.tw/business/202605130009),
[MSCI press release](https://www.msci.com/eqb/pressreleases/archive/MSCI_May26_QIRPR.pdf),
[TWSE notice](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69dbea9fd019e202abe0101d9.pdf).
In-repo graded analyses: docs/case_studies/.
