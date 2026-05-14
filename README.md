# tsd-celltower — AT&T cell tower inquiry (Boulan Park, Troy MI)

Investigation into a newly-constructed AT&T cell tower near **Boulan Park** and
**Boulan Park Middle School** in Troy, MI: who owns the land it sits on, and how
it came to be permitted next to a school and a park.

This folder is a self-contained handoff — open it in Claude Code to continue.
**See `index.html` for a single-page slide-deck summary of everything below.**

---

## The question

A new AT&T cell tower was constructed at **42°34'18.3"N 83°10'40.2"W**
(decimal **42.57175, -83.17783**), inspected on site by the owner of this
inquiry. Goals: (1) identify the property owner, (2) understand why it was
allowed so close to a school and park.

## What's been established so far

**Location.** The coordinates fall on the **Boulan Park Middle School** parcel,
**3570 Northfield Pkwy**, Troy — off Crooks Rd between Big Beaver and Wattles.

**The fiber permit.** Troy's "Permits Issued" database (see sibling project
`cot-permits`) contains **Metro Act ROW permit PROW2023-347**, issued
**2023-10-05**, applicant **Jeff Davis** (a recurring AT&T fiber contractor):
> *"Directional bore and place 2" PC from the pole at Wattles and Northfield Pkwy
> south for approximately 1950'. Set 2 new hand holes in ROW. **To provide
> service to new proposed AT&T mobility cell site.**"*
This is the fiber backhaul for the tower. (Full Metro Act dataset snapshot:
`troy_permits_metro_act_2026-05-14_0750.xlsx` in this folder.)

**The parcel.** Oakland County **KEYPIN 2020100003** (= Troy parcel
88-20-20-100-003), 3570 Northfield Pkwy:
- **Tax-exempt** — assessed value $0, taxable value $0 → publicly owned,
  consistent with **Troy School District** land.
- Owner **mailing address: 4400 Livernois Rd, Troy** (likely TSD administration —
  unconfirmed; owner *names* are redacted in the county's public layer).

**Adjacent parcels (point-queried against the Oakland County GIS).** Three
parcels make up the Boulan Park area — see `boulan_parcels.html`:
- **2020100003** — Boulan Park Middle School, 15.97 ac — mailing 4400 Livernois
  Rd → **Troy School District** (the cell-tower parcel).
- **2020227037** — the athletic track, 5.75 ac — *same* mailing address,
  4400 Livernois Rd → **Troy School District** (separate KEYPIN, same campus).
- **2020226092** — Boulan Park proper, 47.14 ac — mailing 500 W Big Beaver Rd
  (Troy City Hall) → **City of Troy**.
All three are tax-exempt; ownership is inferred from the tax-mailing address
(owner *names* redacted in the public layer).

**The Board of Education approval.** ✅ **Found.** Every TSD Board meeting
2021-01-01 → present (150 meetings, 1,684 agenda items) was crawled — see
`crawl_board_meetings.py` / `board_meetings_2021plus.json`. The lease was
**approved 2021-06-15 as Resolution 21-064, on a 4–2 vote** (Yes: Anne,
Gottlieb, Philippart, Wilson; No: Hauff, Schmidt; Absent: Hammond). It was
introduced 2021-06-01 as "AT & T Cell Tower Proposal" (report only). The
resolution authorizes the Superintendent to negotiate and execute a ground
lease with **New Cingular Wireless PCS, LLC (AT&T)** for ~2,500 sq ft at the
north (wooded) end of the site. The 10-document June-15 packet is in
`celltower_docs/`. **The dollar terms are *not* in the public record** — the
resolution's "Attachment B (General Parameters of Lease Agreement)" was never
uploaded, and the financials were likely settled in the June-15 closed session.

**The lease revenue — traced through every public financial record, not found.**
The amount Troy School District receives does not appear in any public financial
document:
- **Check register, FY11–FY26** (sibling project `~/Downloads/tsd-checkregister/`)
  — 224,267 line items. AT&T appears 6,519 times but only as a *vendor being
  paid* (~$700K total, for phone/data service). A check register records
  disbursements only — it has no revenue side.
- **Monthly Treasurer's Reports** — all 64 (Nov 2020 → Feb 2026) located on
  BoardDocs; their "Financial Statements" PDF reports revenue only as fund-level
  aggregates (Local / State / Federal Sources), with no account-level detail.
- **ACFRs FY21–FY25** (in `~/Downloads/tsd-budget/boarddocs/`) — no mention of
  AT&T / Cingular / cell tower / antenna in any year; the District reports
  GASB 87 leases *only as a lessee*, never as a lessor. The one dedicated
  **Facility Rentals Fund (535)** — "moneys generated from the rental of various
  facilities" — showed **$117,508** of (mixed) rental revenue in FY22, then was
  **dropped from ACFR reporting FY23+**, folding facility-rental income into the
  General Fund's un-itemized "Local Sources."

→ The revenue is structurally invisible in public financial reporting; it can
only be obtained by FOIA (see Open threads).

**Legal-description verification.** The deed legal description —
`T2N R11E SEC 20, PART OF SE 1/4 OF NW 1/4, BEG ... 16 A` — was traced and
overlaid on the official county parcel (see `verify_parcel.py`):
- Traverse closes to **0.16 ft** (internally consistent).
- Area **16.00 ac** (description) vs **15.98 ac** (county) — match within 0.1%.
- Corners agree within **20–42 ft** (normal deed-vs-GIS digitizing variance).
- **The tower coordinates fall inside both polygons.** ✅ Confirmed: the tower
  is on parcel 2020100003 / 3570 Northfield Pkwy.

**Why it was (legally) allowed near a school/park.** Mostly federal preemption:
- **Telecommunications Act of 1996 §704** (47 U.S.C. §332(c)(7)) — localities
  **may not** deny/regulate a wireless facility based on RF-emission health
  concerns if it meets FCC limits.
- **FCC "shot clocks"** — must act within fixed deadlines or it's deemed granted.
- **Michigan wireless siting law** (MCL 125.3514) — collocations are by-right;
  new support structures get special-land-use review on a ~90-day clock.

## Files in this folder

| File | What it is |
|---|---|
| `index.html` | **Self-contained, single-page slide deck** summarizing the whole investigation — also the GitHub Pages entry point. Open in a browser; arrow keys / on-screen controls to navigate. |
| `verify_parcel.py` | Traces the metes-and-bounds legal description, fetches the official Oakland County parcel geometry, overlays them, checks the tower point. Run: `python3 verify_parcel.py` (needs `requests`). |
| `parcel_verification.html` | Interactive Leaflet map — legal description shaded orange, official parcel outlined blue, tower / Point-of-Beginning / Section-20 center marked. |
| `parcel_verification.geojson` | Same geometry as GeoJSON (load in QGIS / Google Earth / geojson.io). |
| `property_boundaries.html` | Polished Leaflet map of the middle-school parcel — official vs. deed-reconstructed boundary, layer toggles, scale bar. |
| `boulan_parcels.html` | Three-parcel map: middle school + athletic track (TSD) + Boulan Park (City of Troy), color-coded, with owner/KEYPIN/area popups. |
| `boulan_parcels.geojson` | The three parcel geometries + tower/probe points as GeoJSON. |
| `crawl_board_meetings.py` | Pulls **every** TSD Board of Education meeting since 2021-01-01 and scans all agenda items for tower keywords. Reuses the BoardDocs client from the sibling `tsd-budget` project. Run: `python3 crawl_board_meetings.py`. |
| `board_meetings_2021plus.json` | Full corpus: every meeting, every agenda item (150 meetings / 1,684 items). |
| `celltower_hits.json` | The 22 agenda items whose title/action matched tower keywords. |
| `celltower_docs/` | The June-15-2021 Board packet (resolution, lease presentation, site plan, RF-safety articles) + the June-15 regular-meeting minutes confirming the 4–2 vote. See `manifest.json` inside. |
| `troy_permits_metro_act_2026-05-14_0750.xlsx` | Snapshot of all Troy "ROW, METRO ACT" permits — the dataset that surfaced PROW2023-347. Regenerated canonically by the `cot-permits` scraper. |

## Open threads / next steps

1. **Confirm ownership.** Look up KEYPINs `2020100003` (middle school),
   `2020227037` (track) and `2020226092` (City park) at the Troy Parcel
   Information Center — <https://apps.troymi.gov/ParcelInformationCenter>
   (reCAPTCHA-gated, do it in a browser) — to de-redact the owner *names*.
2. **~~Find the board approval.~~ ✅ DONE** — Resolution 21-064, approved
   2021-06-15 on a 4–2 vote. See `crawl_board_meetings.py` and `celltower_docs/`.
   The remaining gap is the **money**: get the lease's dollar terms (next item).
3. **Get the lease revenue / terms — FOIA.** The dollar figure is *not* in any
   public record — not the resolution packet, not the minutes, not the FY11–FY26
   check register, not the 64 monthly Treasurer's Reports, not the FY21–FY25
   ACFRs (see "What's been established"). FOIA Troy School District for
   **(a)** the executed AT&T ground lease, **(b)** Attachment B to Resolution
   21-064, **(c)** the 2021-06-15 closed-session minutes (the BoardDocs
   closed-session file 404s), and — the sharpest single ask — **(d)** the
   general-ledger account history (FY21–FY26) for the revenue object code the
   AT&T lease posts to, which yields both the amount *and* the commencement date.
4. **FOIA targets (City side).** City of Troy: site plan, special-land-use /
   Planning Commission file, and the **building permit** for the AT&T cell
   structure (separate from the Metro Act fiber permit).
5. **Building permit.** When the `cot-permits` File 2 scrape (`troy_permits_all_other_*.xlsx`)
   finishes, grep it for the tower's *building* permit — AT&T applicant, parcel
   88-20-20-100-003, keywords `tower / monopole / cell / wireless / antenna`.

## Data sources & endpoints discovered

- **Troy permits API** — `https://apps.troymi.gov/PermitsIssued/Results`
  (params `PageNumber`, `PermitType`; needs a browser User-Agent). Scraped by
  the `cot-permits` project.
- **Oakland County parcel REST** — `https://gisservices.oakgov.com/arcgis/rest/services/Enterprise/EnterpriseOpenParcelDataMapService/MapServer/1`
  (layer "Tax Parcel Plus"; query by `KEYPIN`). Used by `verify_parcel.py`.
- **Troy Parcel Information Center** — `https://apps.troymi.gov/ParcelInformationCenter`
  (reCAPTCHA-gated; manual lookups only).
- **Troy public meetings / agendas** — `https://apps.troymi.gov/Meetings`
  (City Planning Commission & City Council records — the *city-side* approval).
- **TSD BoardDocs** — `https://go.boarddocs.com/mi/troysd/Board.nsf`
  (committee `A4EP6J588C05`; the *school-district-side* records). Tooling in
  `~/Downloads/tsd-budget/scripts/`.

## Related folders

- `~/Downloads/cot-permits/` — the Troy permits scraper (`scrape_permits.py`).
  A long full-database scrape may still be running; let it finish.
- `~/Downloads/tsd-budget/` — Troy School District budget project; its
  `scripts/` folder is the BoardDocs harvesting toolkit referenced above.
