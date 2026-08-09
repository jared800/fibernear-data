# How each dataset actually gets here

Verified 2026-08-06 by `scripts/probe_sources.py` running on `ubuntu-latest`.
Result is committed at `data/source_probe.json` on every run.
Acquisition procedure for BDC **corrected 2026-08-07** — see the update below.

## Reachable from CI — automate freely

| Source | Status | Notes |
|---|---|---|
| `geo.fcc.gov/api/census/area` | **206**, 0.33s | lat/lon to census block. No key. Backs the address widget. |
| `opendata.fcc.gov` (Form 477) | **200**, 0.45s | 75.3M rows, 2014-2021, full SoQL. Public domain. |
| `www2.census.gov` Gazetteer | **206**, 0.17s | 32,333 places, 1.2 MB. Page inventory. |
| `www2.census.gov` ZCTA-Place crosswalk | **206**, 0.08s | 53,319 pairs, 9.8 MB. Solves BDC's missing ZIP dimension. |

⚠️ **Form 477 ends at June 2021.** It is 4.5 years stale against the current BDC
vintage and must never be mixed into the same figure, table or page.

## BDC: the download step was never necessary

The earlier version of this document said `broadbandmap.fcc.gov` was WAF-blocked
and that the Census Place archives had to be downloaded by hand every six months.
The first half is true and the second half is not.

**What is blocked:** `/nbm/map/api/*` from any datacenter IP — this container and
GitHub Actions both get a 403 from Akamai. `www.fcc.gov` and `data.fcc.gov` too.

**What works:** the same API, called from a page already open on that origin in a
normal browser. Nothing needs to touch disk, which also sidesteps the separate
problem that browser blob downloads were not landing in `~/Downloads` at all.

### The procedure (verified 2026-08-07, 20 markets extracted)

Open `https://broadbandmap.fcc.gov/data-download/nationwide-data`, then:

1. `GET /nbm/map/api/published/filing` — take the newest `process_uuid`.
   Dec 31 2025 is `16495d87-e2f6-49a8-96db-e50394a743e2`, files `D25_04aug2026`.
2. `GET /nbm/map/api/national_map_process/nbm_get_data_download/{uuid}/` — the file
   manifest, 10,613 entries. Filter
   `data_type === 'Fixed Broadband Summary by Geography Type - Census Place'`
   and read `state_fips` / `id`.
3. `GET /nbm/map/api/getNBMDataDownloadFile/{id}/1` — returns the zip as an
   ArrayBuffer (`PK\x03\x04`). One request per state.
4. **Unzip in the page, no library.** Parse the EOCD and central directory by hand,
   then run each entry through `new DecompressionStream('deflate-raw')`, which is
   native in Chrome.
5. Filter to `area_data_type === 'Total'` plus whatever `geography_id` or
   `total_units` threshold you want, and return the rows. Never download a file.

CSV columns: `area_data_type, geography_type, geography_id, geography_desc,
geography_desc_full, total_units, biz_res, technology, speed_02_02, speed_10_1,
speed_25_3, speed_100_20, speed_250_25, speed_1000_100`.
`biz_res` R = residential, B = business — the B rows are the ones no competitor
publishes, and they are the basis of the `/business-fiber/` pages.

Whole-country sweep at a 60,000-location floor is 56 requests and yields 220
places. Nothing close to the ~25-request rate limit that was hit previously.

### Making it fully headless

`https://broadbandmap.fcc.gov/api/public/map/downloads/listAvailabilityData/{date}`
reaches the application from CI and returns **401, not 403**. That is an
authentication wall, not a WAF block, so a free BDC API key (register at
broadbandmap.fcc.gov, then `username` + `hash_value` headers) would move this whole
procedure into a scheduled job. Not yet registered — worth doing.

## What is committed here

| File | Contents |
|---|---|
| `data/bdc_top50_place_fiber_D25.csv` | Top 50 Census places by serviceable locations: residential and business fiber at 100/20, plus the signed gap. |
| `data/bdc_wave1_place_full_D25.csv` | Full technology x speed-tier breakdown for the 15 markets added to the site on 2026-08-07. |
| `data/source_probe.json` | CI reachability probe output. |

Keeping extracts in git is deliberate: it makes the release-over-release diff a
`git diff`, which is what feeds the "fiber coverage changed in X" content cycle.
That diff is the one thing in this build no competitor is doing.
