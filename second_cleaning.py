import pandas as pd
import re

df = pd.read_csv("data/ikman_jobs_clean.csv")

def clean_text(text):
    if not isinstance(text, str):
        return text
    # Remove non-ASCII characters (emojis, Sinhala, encoding artifacts)
    text = text.encode("ascii", errors="ignore").decode("ascii")
    # Remove leftover symbols and extra whitespace
    text = re.sub(r"[^\w\s\.,\-\/\(\)&%+#@]", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

df["description"] = df["description"].apply(clean_text)

# Drop rows where description became too short after cleaning
df = df[df["description"].str.len() > 30]

df.to_csv("data/ikman_jobs_clean.csv", index=False, encoding="utf-8")
print(f"Done. {len(df)} rows saved.")
print(df["description"].iloc[0][:300])