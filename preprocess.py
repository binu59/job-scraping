"""
Preprocessing Script — ikman.lk Job Listings
==============================================
Inputs:
    data/ikman_job_listings_raw.csv   (from ikman_scraper.py)
    data/ikman_job_details.csv        (from ikman_detail_scraper.py)

Steps:
    1. Load both CSVs
    2. Clean category names (strip encoding artifacts)
    3. Filter to IT/tech-relevant categories only
    4. Extract structured fields from raw_card_text (company, location)
    5. Parse salary_raw into salary_min and salary_max (numeric)
    6. Parse posted_raw into days_ago (numeric)
    7. Merge listings with descriptions on detail_url
    8. Clean description text (fix encoding, strip noise)
    9. Drop non-English descriptions (Sinhala/Tamil)
    10. Drop rows with no usable description
    11. Save cleaned dataset to data/ikman_jobs_clean.csv

Output:
    data/ikman_jobs_clean.csv
"""

import pandas as pd
import re
import os
from langdetect import detect, LangDetectException

INPUT_LISTINGS = "data/ikman_job_listings_raw.csv"
INPUT_DETAILS  = "data/ikman_job_details.csv"
OUTPUT_CLEAN   = "data/ikman_jobs_clean.csv"

# Only keep these categories (after cleaning category names)
KEEP_CATEGORIES = {
    "IT and Network Industry",
    "Digital Marketing",
    "Designer",
    "Analyst",
    "Engineering",
}


# ─────────────────────────────────────────────
# Step 1: Load
# ─────────────────────────────────────────────
print("Loading CSVs...")
listings = pd.read_csv(INPUT_LISTINGS, encoding="utf-8")
details  = pd.read_csv(INPUT_DETAILS,  encoding="utf-8")
print(f"  Listings : {len(listings):,} rows")
print(f"  Details  : {len(details):,} rows")


# ─────────────────────────────────────────────
# Step 2: Clean category names
# ─────────────────────────────────────────────
def clean_category(cat: str) -> str:
    if not isinstance(cat, str):
        return cat
    # Remove UTF-8 artifact characters (\xa0 shows as Â in some encodings)
    cat = cat.replace("\xa0", "").replace("Â", "").strip()
    return cat

listings["category"] = listings["category"].apply(clean_category)
print(f"\nCategories found: {sorted(listings['category'].unique())}")


# ─────────────────────────────────────────────
# Step 3: Filter to IT/tech categories
# ─────────────────────────────────────────────
before = len(listings)
listings = listings[listings["category"].isin(KEEP_CATEGORIES)].copy()
print(f"\nAfter category filter: {len(listings):,} rows (dropped {before - len(listings):,})")
print(f"Category counts:\n{listings['category'].value_counts().to_string()}")


# ─────────────────────────────────────────────
# Step 4: Extract company & location from raw_card_text
# raw_card_text format: "Title|Company|Salary|MEMBER|Location, Category|Time"
# ─────────────────────────────────────────────
def extract_field(text: str, index: int) -> str | None:
    if not isinstance(text, str):
        return None
    parts = text.split("|")
    if len(parts) > index:
        val = parts[index].strip()
        return val if val and val != "MEMBER" else None
    return None

def extract_location(text: str) -> str | None:
    
    if not isinstance(text, str):
        return None
    parts = text.split("|")
    for part in parts:
        
        if "," in part:
            city = part.split(",")[0].strip()
            
            if city and not city.startswith("Rs") and len(city) < 40:
                return city
    return None

listings["company"]  = listings["raw_card_text"].apply(lambda x: extract_field(x, 1))
listings["location"] = listings["raw_card_text"].apply(extract_location)

print(f"\nLocation sample:\n{listings['location'].value_counts().head(10).to_string()}")
print(f"Company nulls: {listings['company'].isna().sum()} / {len(listings)}")



# Step 5: Parse salary into salary_min, salary_max


def parse_salary(raw: str):
    if not isinstance(raw, str):
        return None, None
    # Remove "Rs" and commas, then find all numbers
    nums = re.findall(r"[\d]+", raw.replace(",", ""))
    nums = [int(n) for n in nums if int(n) > 999]  
    if len(nums) == 0:
        return None, None
    elif len(nums) == 1:
        return nums[0], nums[0]
    else:
        return nums[0], nums[1]

listings[["salary_min", "salary_max"]] = listings["salary_raw"].apply(
    lambda x: pd.Series(parse_salary(x))
)
listings["salary_mid"] = (listings["salary_min"] + listings["salary_max"]) / 2

salary_present = listings["salary_min"].notna().sum()
print(f"\nSalary parsed: {salary_present:,} / {len(listings):,} listings have salary data")


# ─────────────────────────────────────────────
# Step 6: Parse posted_raw into days_ago
# Input looks like: "7 hours", "2 days", "1 week", "3 weeks"
# ─────────────────────────────────────────────
def parse_days_ago(raw: str) -> float | None:
    if not isinstance(raw, str):
        return None
    raw = raw.lower().strip()
    match = re.match(r"(\d+)\s*(hour|hours|day|days|week|weeks|minute|minutes)", raw)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    if "minute" in unit:
        return round(value / 1440, 2)
    elif "hour" in unit:
        return round(value / 24, 2)
    elif "day" in unit:
        return float(value)
    elif "week" in unit:
        return float(value * 7)
    return None

listings["days_ago"] = listings["posted_raw"].apply(parse_days_ago)
print(f"Days ago parsed: {listings['days_ago'].notna().sum():,} / {len(listings):,}")


# ─────────────────────────────────────────────
# Step 7: Merge with descriptions
# ─────────────────────────────────────────────
# Drop unneeded columns from details before merging
details_clean = details[["detail_url", "description"]].copy()
details_clean = details_clean.dropna(subset=["description"])
details_clean = details_clean[details_clean["error"].isna()] if "error" in details_clean.columns else details_clean

df = listings.merge(details_clean, on="detail_url", how="left")
print(f"\nAfter merge: {len(df):,} rows")
print(f"Rows with description: {df['description'].notna().sum():,}")


# ─────────────────────────────────────────────
# Step 8: Clean description text
# ─────────────────────────────────────────────
def fix_encoding(text: str) -> str:
    """Attempt to fix common UTF-8/Latin-1 mismatch artifacts."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text

def clean_description(text: str) -> str:
    if not isinstance(text, str):
        return text
    # Fix encoding artifacts
    text = fix_encoding(text)
    # Remove URLs
    text = re.sub(r"http\S+", "", text)
    # Remove phone numbers
    text = re.sub(r"\b0\d{9}\b", "", text)
    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    # Remove markdown-style headers (###)
    text = re.sub(r"#+\s*", "", text)
    # Strip leading/trailing whitespace
    return text.strip()

df["description"] = df["description"].apply(clean_description)


# ─────────────────────────────────────────────
# Step 9: Drop non-English descriptions
# ─────────────────────────────────────────────
def is_english(text: str) -> bool:
    if not isinstance(text, str) or len(text.strip()) < 20:
        return False
    try:
        return detect(text) == "en"
    except LangDetectException:
        return False

print("\nDetecting language of descriptions")
df["is_english"] = df["description"].apply(is_english)
non_english = (~df["is_english"]).sum()
print(f"Non-English / undetectable descriptions: {non_english:,} (will be dropped)")
df = df[df["is_english"]].copy()
df.drop(columns=["is_english"], inplace=True)



# Step 10: Drop rows with no usable description

before = len(df)
df = df.dropna(subset=["description"])
df = df[df["description"].str.strip().str.len() > 30]
print(f"After dropping empty/short descriptions: {len(df):,} rows (dropped {before - len(df):,})")



# Step 11: Final column selection & save

final_cols = [
    "category", "title", "company", "location",
    "salary_min", "salary_max", "salary_mid",
    "days_ago", "detail_url", "description",
]
df = df[final_cols].reset_index(drop=True)

os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_CLEAN, index=False, encoding="utf-8")

print(f"\n{'='*50}")
print(f"Clean dataset saved to: {OUTPUT_CLEAN}")
print(f"Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\nColumn summary:")
print(df.dtypes.to_string())
print(f"\nMissing values:")
print(df.isna().sum().to_string())
print(f"\nCategory distribution:")
print(df["category"].value_counts().to_string())
print(f"\nSample row (description):")
print(df["description"].iloc[0][:300])