"""
CrossFit Open 2026 Leaderboard Scraper
Fetches 26.1 Rx'd scores for Men and Women and saves to CSV.
"""

import asyncio
import json
import os
import re
import time

import aiohttp
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://c3po.crossfit.com/api/leaderboards/v2/competitions/open/2026/leaderboards"
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
OUTPUT_CSV = os.path.join(DATA_DIR, "26.1_scores.csv")

DIVISIONS = [
    {"division": 1, "label": "men_rx",      "scaled": 0},
    {"division": 2, "label": "women_rx",    "scaled": 0},
    {"division": 1, "label": "men_scaled",  "scaled": 1},
    {"division": 2, "label": "women_scaled","scaled": 1},
]

CONCURRENT_REQUESTS = 5


def page_has_scores(rows):
    """Check if any row on a page has a non-empty score."""
    return any(
        row.get("scores") and row["scores"][0].get("scoreDisplay", "").strip()
        for row in rows
    )


async def fetch_page(session, semaphore, division, page, scaled=0):
    """Fetch a single leaderboard page."""
    params = {
        "view": 0,
        "division": division,
        "region": 0,
        "scaled": scaled,
        "sort": 0,
        "page": page,
    }
    async with semaphore:
        for attempt in range(5):
            try:
                async with session.get(BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        resp.raise_for_status()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(2 ** attempt)
    return None


async def find_last_page_with_scores(session, semaphore, division, total_pages, scaled=0):
    """Binary search for the last page that has athletes with scores."""
    lo, hi = 1, total_pages
    while lo < hi:
        mid = (lo + hi + 1) // 2
        result = await fetch_page(session, semaphore, division, mid, scaled=scaled)
        if result and page_has_scores(result.get("leaderboardRows", [])):
            lo = mid
        else:
            hi = mid - 1
    return lo


async def fetch_division(division_config):
    """Fetch all pages with scores for a division."""
    div = division_config["division"]
    label = division_config["label"]
    scaled = division_config.get("scaled", 0)

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

        first = await fetch_page(session, semaphore, div, 1, scaled=scaled)
        if not first:
            print(f"Failed to fetch first page for {label}")
            return []

        total_pages = first["pagination"]["totalPages"]
        total_athletes = first["pagination"]["totalCompetitors"]

        last_page = await find_last_page_with_scores(session, semaphore, div, total_pages, scaled=scaled)
        print(f"\n{label}: {total_athletes} registered, scores through page {last_page}/{total_pages}")

        # Save metadata
        meta_path = os.path.join(DATA_DIR, f"{label}_meta.json")
        with open(meta_path, "w") as f:
            json.dump({"total_competitors": total_athletes, "total_pages": total_pages, "scored_pages": last_page}, f)
        print(f"  Saved metadata to {meta_path}")

        all_rows = first.get("leaderboardRows", [])

        if last_page > 1:
            tasks = [
                fetch_page(session, semaphore, div, page, scaled=scaled)
                for page in range(2, last_page + 1)
            ]
            pbar = tqdm(total=last_page - 1, desc=label, unit="pg")
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result and "leaderboardRows" in result:
                    all_rows.extend(result["leaderboardRows"])
                pbar.update(1)
            pbar.close()

    # Save raw JSON
    raw_path = os.path.join(RAW_DIR, f"{label}.json")
    with open(raw_path, "w") as f:
        json.dump(all_rows, f)
    print(f"  Saved {len(all_rows)} rows to {raw_path}")

    return all_rows


def parse_reps_from_display(score_display):
    """Extract rep count from scoreDisplay like '163 reps' or '276 reps - s'."""
    if not score_display:
        return None
    m = re.match(r"(\d+)\s*reps", score_display)
    return int(m.group(1)) if m else None


def parse_time_seconds(score):
    """Parse time in seconds from score object."""
    t = score.get("time")
    if t and t != "":
        try:
            return int(t)
        except (ValueError, TypeError):
            pass
    return None


def parse_rows(raw_rows, gender, scaled=False):
    """Parse raw API rows into flat dicts."""
    records = []
    for row in raw_rows:
        entrant = row.get("entrant", {})
        scores = row.get("scores", [])
        if not scores:
            continue

        score = scores[0]
        score_display = score.get("scoreDisplay", "").strip()

        if not score_display:
            continue

        time_seconds = parse_time_seconds(score)
        reps = parse_reps_from_display(score_display)

        # For finishers, extract reps from breakdown (e.g. "354 reps\n")
        if time_seconds and not reps:
            breakdown = score.get("breakdown", "")
            m = re.match(r"(\d+)\s*reps", breakdown)
            if m:
                reps = int(m.group(1))

        records.append({
            "competitor_id": entrant.get("competitorId"),
            "name": entrant.get("competitorName"),
            "gender": gender,
            "scaled": scaled,
            "rank": row.get("overallRank"),
            "score_display": score_display,
            "time_seconds": time_seconds,
            "reps": reps,
            "country": entrant.get("countryOfOriginName"),
            "affiliate": entrant.get("affiliateName"),
            "age": entrant.get("age"),
        })
    return records


async def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    all_records = []
    start = time.time()

    for div_config in DIVISIONS:
        raw_rows = await fetch_division(div_config)
        gender = "M" if div_config["division"] == 1 else "F"
        records = parse_rows(raw_rows, gender, scaled=bool(div_config.get("scaled", 0)))
        all_records.extend(records)
        print(f"  Parsed {len(records)} valid scores")

    df = pd.DataFrame(all_records)
    df.to_csv(OUTPUT_CSV, index=False)
    elapsed = time.time() - start
    print(f"\nDone! {len(df)} total scores saved to {OUTPUT_CSV} in {elapsed:.0f}s")
    print(df.groupby("gender").size())


if __name__ == "__main__":
    asyncio.run(main())
