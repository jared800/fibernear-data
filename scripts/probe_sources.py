"""Probe every upstream data source FiberNear's page engine depends on.

Writes data/source_probe.json so the result is visible without reading CI logs.
The FCC's broadbandmap.fcc.gov host WAF-drops some datacenter egress, so this
establishes whether GitHub Actions is a viable ingest home before we build on it.
"""
import json, os, ssl, time, urllib.error, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "\
     "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"

TARGETS = [
    ("fcc_bdc_filings",
     "https://broadbandmap.fcc.gov/nbm/map/api/published/filing"),
    ("fcc_bdc_asof",
     "https://broadbandmap.fcc.gov/nbm/map/api/national_map_process/nbm_get_as_of_dates"),
    ("fcc_geo_block",
     "https://geo.fcc.gov/api/census/area?lat=39.7392&lon=-104.9903&censusYear=2020&format=json"),
    ("fcc_opendata_477",
     "https://opendata.fcc.gov/resource/hicn-aujz.json?$limit=1"),
    ("census_gazetteer_places",
     "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip"),
    ("census_zcta_place_xwalk",
     "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_place20_natl.txt"),
]


def probe(name, url, timeout=45):
    started = time.time()
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Range": "bytes=0-2047",
    })
    row = {"name": name, "url": url}
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=ssl.create_default_context()) as r:
            body = r.read(2048)
            row.update(status=r.status,
                       content_type=r.headers.get("Content-Type"),
                       content_range=r.headers.get("Content-Range"),
                       bytes_read=len(body),
                       sample=body[:400].decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        row.update(status=e.code, error=f"HTTPError {e.code}",
                   sample=e.read(400).decode("utf-8", "replace"))
    except Exception as e:
        row.update(status=0, error=f"{type(e).__name__}: {e}")
    row["seconds"] = round(time.time() - started, 2)
    return row


def discover_manifest(filings_row):
    """If the filings endpoint answered, walk on to the file manifest."""
    if filings_row.get("status") != 200:
        return {"skipped": "filings endpoint unreachable"}
    try:
        req = urllib.request.Request(filings_row["url"], headers={"User-Agent": UA})
        filings = json.loads(urllib.request.urlopen(req, timeout=60).read())
        rows = filings.get("data", filings) if isinstance(filings, dict) else filings
        latest = rows[0]
        uuid = latest.get("process_uuid") or latest.get("processUuid")
        murl = ("https://broadbandmap.fcc.gov/nbm/map/api/national_map_process/"
                f"nbm_get_data_download/{uuid}/")
        mreq = urllib.request.Request(murl, headers={"User-Agent": UA})
        manifest = json.loads(urllib.request.urlopen(mreq, timeout=120).read())
        files = manifest.get("data", manifest)
        place = [f for f in files
                 if "place" in json.dumps(f).lower()
                 and "summary" in json.dumps(f).lower()]
        return {"latest_filing": latest, "process_uuid": uuid,
                "manifest_file_count": len(files),
                "place_summary_matches": len(place),
                "place_summary_sample": place[:3]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main():
    results = [probe(n, u) for n, u in TARGETS]
    report = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runner": "github-actions/ubuntu-latest",
        "results": results,
        "reachable": [r["name"] for r in results if r.get("status") == 200 or r.get("status") == 206],
        "blocked": [r["name"] for r in results if r.get("status") not in (200, 206)],
        "fcc_manifest": discover_manifest(next(r for r in results if r["name"] == "fcc_bdc_filings")),
    }
    os.makedirs("data", exist_ok=True)
    with open("data/source_probe.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
