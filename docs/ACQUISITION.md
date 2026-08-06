# How each dataset actually gets here

Verified 2026-08-06 by `scripts/probe_sources.py` running on `ubuntu-latest`.
Result is committed at `data/source_probe.json` on every run.

## Reachable from CI — automate freely

| Source | Status | Notes |
|---|---|---|
| `geo.fcc.gov/api/census/area` | **206**, 0.33s | lat/lon to census block. No key. Backs the address widget. |
| `opendata.fcc.gov` (Form 477) | **200**, 0.45s | 75.3M rows, 2014-2021, full SoQL. Public domain. |
| `www2.census.gov` Gazetteer | **206**, 0.17s | 32,333 places, 1.2 MB. Page inventory. |
| `www2.census.gov` ZCTA-Place crosswalk | **206**, 0.08s | 53,319 pairs, 9.8 MB. Solves BDC's missing ZIP dimension. |

## Blocked from CI — needs a human-in-the-loop step

`broadbandmap.fcc.gov` **times out at 45s with zero bytes returned**, from both this
container and GitHub Actions. TLS completes and the request sends; the response
never comes. It is a WAF rule on that hostname, not a network fault — `bdc.fcc.gov`
resolves to the same Akamai IP and answers 200. A normal browser gets through fine.

Two things make this a nuisance rather than a problem:

1. **BDC publishes twice a year** (June 30 and December 31 as-of dates). A manual
   fetch every six months is not a pipeline.
2. **The files are small.** The Census Place summary set — the one that gives every
   city page its headline coverage number — is **27.4 MB zipped for all 56
   states**. The nationwide "Other Geographies" summary is 9.1 MB.

### The procedure

Run from a browser signed in on a residential connection:

1. `GET /nbm/map/api/published/filing` — take the newest `process_uuid`.
2. `GET /nbm/map/api/national_map_process/nbm_get_data_download/{uuid}/` — the file
   manifest (~10,613 entries).
3. Pull the `Census Place` summary files and, when neighborhood-level pages are in
   scope, the Fiber-to-the-Premises location files (technology code **50**, 726 MB
   zipped for all states).
4. Drop the archives in `raw/bdc/{as_of_date}/` and push. CI parses from there.

Keeping the raw archives in git is deliberate: it makes the release-over-release
diff a `git diff`, which is what feeds the "fiber coverage changed in X" content
cycle. That diff is the one thing in this build no competitor is doing.
