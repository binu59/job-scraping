"""
ikman.lk Job Listings Scraper
==============================
Scrapes job listings from ikman.lk across all job categories.

Two-stage approach:
  Stage 1: Discover all category URLs from the /en/jobs landing page.
  Stage 2: For each category, paginate through listing pages and extract
           summary fields (title, company, salary, location, posted time, URL).
  Stage 3 (separate script, run after this): visit each individual ad URL
           to pull the full description text for NLP skill extraction.

Run this on YOUR LOCAL MACHINE (not in a restricted sandbox), since it
needs real internet access to ikman.lk.

Usage:
    pip install requests beautifulsoup4 lxml
    python ikman_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
import os
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

BASE_URL = "https://ikman.lk"
JOBS_LANDING_URL = "https://ikman.lk/en/jobs"
OUTPUT_DIR = "data"
LISTINGS_CSV = os.path.join(OUTPUT_DIR, "ikman_job_listings_raw.csv")
CATEGORIES_CSV = os.path.join(OUTPUT_DIR, "ikman_job_categories.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Be polite: delay range (seconds) between requests
MIN_DELAY = 1.5
MAX_DELAY = 3.5

# Safety cap: max pages to paginate per category (avoid runaway loops)
MAX_PAGES_PER_CATEGORY = 40
LISTINGS_PER_PAGE = 25  # ikman shows 25 per page based on "Showing 1-25 of N"

# Only scrape categories whose name contains one of these keywords (case-insensitive).
# Set to None to scrape ALL categories instead.
CATEGORY_KEYWORDS_FILTER = ["it", "network", "analyst", "digital marketing", "designer", "engineer"]


def filter_categories(categories: list[dict]) -> list[dict]:
    """Keep only categories matching CATEGORY_KEYWORDS_FILTER. No-op if filter is None."""
    if CATEGORY_KEYWORDS_FILTER is None:
        return categories
    filtered = []
    for cat in categories:
        name_lower = cat["category"].lower()
        if any(kw in name_lower for kw in CATEGORY_KEYWORDS_FILTER):
            filtered.append(cat)
    return filtered


def check_robots_allowed(path: str) -> bool:
    """Check robots.txt before scraping a given path."""
    rp = RobotFileParser()
    rp.set_url(urljoin(BASE_URL, "/robots.txt"))
    try:
        rp.read()
    except Exception as e:
        print(f"Warning: could not read robots.txt ({e}). Proceeding cautiously.")
        return True
    return rp.can_fetch(HEADERS["User-Agent"], urljoin(BASE_URL, path))


def polite_sleep():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def get_soup(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  Non-200 status ({resp.status_code}) for {url}")
            return None
        return BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as e:
        print(f"  Request failed for {url}: {e}")
        return None


def discover_categories() -> list[dict]:
    """
    Stage 1: Parse the /en/jobs landing page to find every category link
    and its advertised count, e.g.
        <a href="/en/ads/sri-lanka/sales-and-marketing-jobs">Sales and Marketing (1,001)</a>
    """
    print(f"Discovering categories from {JOBS_LANDING_URL} ...")
    soup = get_soup(JOBS_LANDING_URL)
    if soup is None:
        raise RuntimeError("Could not load jobs landing page to discover categories.")

    categories = []
    seen_urls = set()

    # Category links live under /en/ads/sri-lanka/<slug>-jobs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/en/ads/sri-lanka/" in href and href.endswith("-jobs"):
            full_url = urljoin(BASE_URL, href)
            if full_url in seen_urls:
                continue
            text = a.get_text(strip=True)
            # Text looks like "Sales and Marketing (1,001)"
            match = re.match(r"^(.*?)\s*\(([\d,]+)\)$", text)
            if match:
                name = match.group(1).strip()
                count = int(match.group(2).replace(",", ""))
            else:
                name = text
                count = None
            categories.append({"category": name, "url": full_url, "advertised_count": count})
            seen_urls.add(full_url)

    print(f"Found {len(categories)} categories.")
    return categories


def parse_listing_card(card) -> dict | None:
    """
    Parse a single job card from a category listing page.
    ikman's markup is inconsistent (some cards are link-wrapped, some aren't),
    so this function is defensive and returns None if it can't find a title+url.
    """
    link_tag = card.find("a", href=re.compile(r"^/en/ad/"))
    if link_tag is None:
        return None

    detail_url = urljoin(BASE_URL, link_tag["href"])

    # Title: prefer the title attribute, fall back to link text
    title = link_tag.get("title", "").replace(" for sale", "").strip()
    if not title:
        title = link_tag.get_text(strip=True)
    if not title:
        return None

    full_text = card.get_text(separator="|", strip=True)

    # Salary pattern: "Rs 60,000 - 65,000" or "Rs 60,000"
    salary_match = re.search(r"Rs\s?[\d,]+(?:\s?-\s?[\d,]+)?", full_text)
    salary_raw = salary_match.group(0) if salary_match else None

    # Posted time: things like "2 hours", "3 days", "1 week"
    time_match = re.search(r"\b\d+\s?(hour|hours|day|days|week|weeks|minute|minutes)\b", full_text)
    posted_raw = time_match.group(0) if time_match else None

    return {
        "title": title,
        "detail_url": detail_url,
        "raw_card_text": full_text,
        "salary_raw": salary_raw,
        "posted_raw": posted_raw,
    }


def scrape_category(category: dict, writer: csv.DictWriter):
    """
    Stage 2: Paginate through a category's listing pages and write
    each parsed listing to the CSV writer immediately (so partial
    progress is never lost if the script is interrupted).
    """
    cat_name = category["category"]
    base_cat_url = category["url"]
    print(f"\nScraping category: {cat_name} ({base_cat_url})")

    total_scraped = 0
    for page_num in range(1, MAX_PAGES_PER_CATEGORY + 1):
        # ikman pagination param - adjust if real pagination differs
        page_url = base_cat_url if page_num == 1 else f"{base_cat_url}?page={page_num}"

        soup = get_soup(page_url)
        polite_sleep()
        if soup is None:
            break

        # Listing cards are <li> elements containing an ad link
        cards = soup.find_all("li")
        page_results = []
        for card in cards:
            parsed = parse_listing_card(card)
            if parsed:
                parsed["category"] = cat_name
                parsed["page"] = page_num
                page_results.append(parsed)

        if not page_results:
            print(f"  Page {page_num}: no listings found, stopping pagination.")
            break

        for row in page_results:
            writer.writerow(row)
        total_scraped += len(page_results)
        print(f"  Page {page_num}: {len(page_results)} listings (running total: {total_scraped})")

        # Stop if this page returned fewer than expected -> likely last page
        if len(page_results) < LISTINGS_PER_PAGE // 2:
            break

    print(f"Done with {cat_name}: {total_scraped} listings scraped.")
    return total_scraped


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not check_robots_allowed("/en/ads/sri-lanka/jobs"):
        print("robots.txt disallows this path. Stopping.")
        return

    categories = discover_categories()
    categories = filter_categories(categories)
    print(f"After filtering: {len(categories)} categories will be scraped -> "
          f"{[c['category'] for c in categories]}")

    # Save category list for reference / resuming later
    with open(CATEGORIES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["category", "url", "advertised_count"])
        w.writeheader()
        w.writerows(categories)
    print(f"Saved category list to {CATEGORIES_CSV}")

    fieldnames = [
        "category", "page", "title", "detail_url",
        "salary_raw", "posted_raw", "raw_card_text",
    ]

    grand_total = 0
    write_header = not os.path.exists(LISTINGS_CSV)
    with open(LISTINGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for category in categories:
            try:
                count = scrape_category(category, writer)
                grand_total += count
            except Exception as e:
                print(f"  ERROR scraping {category['category']}: {e}")
                continue

    print(f"\nAll done. Total listings scraped: {grand_total}")
    print(f"Raw output saved to: {LISTINGS_CSV}")


if __name__ == "__main__":
    main()