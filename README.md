# fibernear-data

The data engine behind [FiberNear.com](https://fibernear.com). WordPress renders;
this repo decides what there is to render.

## Why it lives here and not on the web host

The FCC's `broadbandmap.fcc.gov` WAF drops traffic from some datacenter IPs
(confirmed: TLS completes, request sends, zero bytes come back). GitHub Actions
gives us clean egress, a free scheduler, version history on every dataset, and a
diff between releases we can turn into content. `scripts/probe_sources.py`
verifies reachability on every run and writes `data/source_probe.json`.

## Sources

| Source | License | Cadence | Use |
|---|---|---|---|
| FCC BDC — Census Place summaries | Public domain (USGOV_WORKS) | Biannual | Fiber / gigabit availability % per city |
| FCC BDC — location-level fiber (tech code 50) | Public domain | Biannual | Which providers serve which census blocks |
| FCC Form 477 (`opendata.fcc.gov`) | Public domain | Static, 2014–2021 | Historical trend nobody else publishes |
| `geo.fcc.gov` census area API | Public domain | Live | lat/lon → census block, no key |
| Census Gazetteer + ZCTA↔Place crosswalk | Public domain | Annual | Page inventory, ZIP↔city mapping |

**Excluded on purpose:** Ookla Open Data is CC BY-NC-SA — the NonCommercial term
is incompatible with an affiliate site and ShareAlike would force our own pages
open. M-Lab (CC0) is the clean substitute if we ever want measured speeds.
Carrier availability endpoints are undocumented internal APIs behind consumer
ToS; we link users to them, we do not ingest them.

## Attribution

FCC data is public domain and requires no attribution, but every generated page
cites it anyway. On a comparison site, a visible source is the cheapest trust
signal there is.
