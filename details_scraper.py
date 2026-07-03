"""
ikman.lk Job Detail Scraper (Stage 3)
=======================================
Run this AFTER ikman_scraper.py has produced data/ikman_job_listings_raw.csv.

For each unique detail_url in that CSV, visits the individual ad page and
extracts the full job description text (needed later for NLP skill extraction),
plus any structured fields available on the detail page (location, exact
salary if shown differently here, company name).

Resumable: if interrupted, re-running will skip URLs already saved in the
output CSV.

Usage:
    python ikman_detail_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import os

INPUT_CSV = "data/ikman_job_listings_raw.csv"
OUTPUT_CSV = "data/ikman_job_details.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MIN_DELAY = 1.5
MAX_DELAY = 3.0


def polite_sleep():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def load_done_urls() -> set:
    if not os.path.exists(OUTPUT_CSV):
        return set()
    done = set()
    with open(OUTPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            done.add(row["detail_url"])
    return done


def load_target_urls() -> list:
    urls = []
    seen = set()
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("detail_url")
            if url and url not in seen:
                urls.append(url)
                seen.add(url)
    return urls


def scrape_detail_page(url: str) -> dict:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return {"detail_url": url, "description": None, "error": f"status_{resp.status_code}"}
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Description: confirmed from real HTML inspection.
        # ikman uses class "description--1nRbz" for the actual job description.
        # The class has a hash suffix that may change, so we match on the prefix "description--".
        desc_tag = soup.find(attrs={"class": lambda c: c and any(
            cls.startswith("description--") for cls in (c if isinstance(c, list) else c.split())
        )})
        if desc_tag:
            # Grab all <p> tags inside for clean text, skip heading divs
            paragraphs = desc_tag.find_all("p")
            if paragraphs:
                description = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            else:
                description = desc_tag.get_text(separator="\n", strip=True)
        else:
            description = None

        # Company name: ikman shows it in the ad title area or a seller block
        company = None
        company_tag = soup.find(attrs={"class": lambda c: c and any(
            cls.startswith("seller-") or cls.startswith("shop-") for cls in (c if isinstance(c, list) else c.split())
        )})
        if company_tag:
            company = company_tag.get_text(strip=True)

        return {
            "detail_url": url,
            "description": description,
            "company": company,
            "error": None,
        }
    except requests.RequestException as e:
        return {"detail_url": url, "description": None, "error": str(e)}


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Input file not found: {INPUT_CSV}. Run ikman_scraper.py first.")
        return

    targets = load_target_urls()
    done = load_done_urls()
    remaining = [u for u in targets if u not in done]

    print(f"Total listings: {len(targets)} | Already done: {len(done)} | Remaining: {len(remaining)}")

    write_header = not os.path.exists(OUTPUT_CSV)
    fieldnames = ["detail_url", "description", "company", "error"]

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for i, url in enumerate(remaining, 1):
            result = scrape_detail_page(url)
            writer.writerow(result)
            f.flush()
            status = "OK" if result["error"] is None else f"ERROR: {result['error']}"
            print(f"[{i}/{len(remaining)}] {url} -> {status}")
            polite_sleep()

    print(f"\nDone. Output saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()