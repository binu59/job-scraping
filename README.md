# 🇱🇰 Sri Lankan IT/Tech Job Market Analysis

> **End-to-end data analytics project**  from raw web scraping to an interactive dashboard, analysing the Sri Lankan IT/tech job market using real data collected from [ikman.lk](https://ikman.lk/en/jobs).

---

## 📌 Project Overview

This project builds a complete data pipeline to analyse the Sri Lankan IT/tech job market. Rather than using a pre-cleaned Kaggle dataset, all data was collected independently via web scraping, reflecting real-world data engineering challenges such as encoding issues, missing values, non-English content, and inconsistent formatting.

**Key Questions Explored:**
- Which IT/tech job categories are most active in Sri Lanka?
- What skills do Sri Lankan employers demand most?
- How do salaries vary across categories, job titles, and skills?
- Which cities concentrate the most tech hiring?
- Do listings that mention more skills offer higher salaries?

---

## 🗂️ Project Structure

```
sri-lanka-job-market-analysis/
│
├── data/
│   ├── ikman_job_listings_raw.csv     
│   ├── ikman_job_details.csv          
│   ├── ikman_jobs_clean.csv           
│   └── ikman_jobs_with_skills.csv     
│
├── ikman_scraper.py                  
├── ikman_detail_scraper.py            
├── preprocess.py                      
├── ikman_jobs_eda.ipynb               
├── ikman_jobs_nlp.ipynb              
├── dashboard.py                       
└── README.md
```

---

## 🔄 Pipeline

```
ikman.lk
    │
    ▼
ikman_scraper.py           scrapes 5 IT/tech categories, paginates all listing pages
    │                        Output: ikman_job_listings_raw.csv (731 rows)
    ▼
ikman_detail_scraper.py    visits each individual ad URL to extract description text
    │                        Output: ikman_job_details.csv (691 rows)
    ▼
preprocess.py              cleans categories, parses salary/location/recency,
    │                        merges CSVs, drops non-English rows, saves clean dataset
    │                        Output: ikman_jobs_clean.csv (216 rows)
    ▼
ikman_jobs_eda.ipynb       EDA: category distribution, location, salary, recency,
    │                        title word frequency
    ▼
ikman_jobs_nlp.ipynb       NLP: dictionary-based skill extraction, heatmap,
    │                        co-occurrence analysis, salary vs skill count
    ▼
dashboard.py               Interactive 4-page Streamlit dashboard
```

---

## 📊 Dataset

| Field | Description |
|---|---|
| `category` | Job category (IT & Network, Digital Marketing, Engineering, Designer, Analyst) |
| `title` | Job title as listed |
| `company` | Employer name (extracted from listing card) |
| `location` | City (extracted from listing card) |
| `salary_min` | Minimum salary in LKR (where disclosed) |
| `salary_max` | Maximum salary in LKR (where disclosed) |
| `salary_mid` | Midpoint salary in LKR |
| `days_ago` | Days since listing was posted |
| `description` | Full job description text (English only) |
| `skills_extracted` | Pipe-separated skills detected via NLP |

**Note:** ~58% of listings do not disclose salary , typical for Sri Lankan classifieds platforms where salary is negotiated.

---

## 🔍 Key Findings

### Job Market
- **IT & Network Industry** is the most active category (37% of listings), followed by **Digital Marketing** (31%)
- **Colombo** dominates with ~71% of all IT/tech listings — Sri Lanka's hiring is heavily centralised
- Most listings are posted within the **last 2 weeks**, indicating a fast-moving market

### Skills in Demand
- **Communication** appears in 59% of all listings — Sri Lankan employers heavily emphasise soft skills even in technical roles
- Top technical skills: **Excel (9)**, **Python (8)**, **Networking (8)**, **HTML (5)**
- Top digital marketing skills: **Social Media (78)**, **Instagram (36)**, **Photoshop (35)**
- Only **41 unique skills** detected out of 60+ in the dictionary — ikman's informal job ads are less structured than LinkedIn, mentioning fewer specific tools

### Salary Insights *(based on 90 listings that disclosed salary)*
- **Google Ads** commands the highest average salary at **LKR 148,800/month**
- Salary correlation with skill count: **weak** — salary in Sri Lankan classifieds is not strongly determined by the number of skills listed
- Engineering roles show the widest salary range, reflecting seniority variation

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Web Scraping | `requests`, `BeautifulSoup4`, `lxml` |
| Data Processing | `pandas`, `numpy`, `re` |
| Language Detection | `langdetect` |
| EDA & Visualisation | `matplotlib`, `seaborn` |
| NLP | Dictionary-based regex matching |
| Dashboard | `streamlit`, `plotly` |
| Environment | Python 3.13 |

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/binu59/job-scraping.git
cd sri-lanka-job-market-analysis
```

### 2. Install dependencies
```bash
pip install requests beautifulsoup4 lxml pandas numpy matplotlib seaborn langdetect streamlit plotly nbformat jupyter
```

### 3. Run the scraper *(optional - clean data already included)*
```bash
python ikman_scraper.py
python ikman_detail_scraper.py
```

### 4. Run preprocessing
```bash
python preprocess.py
```

### 5. Explore the notebooks
```bash
jupyter notebook ikman_jobs_eda.ipynb
jupyter notebook ikman_jobs_nlp.ipynb
```

### 6. Launch the dashboard
```bash
streamlit run dashboard.py
```

---

## ⚠️ Scraping Ethics

This project respects responsible scraping practices:
- Random delays (1.5–3.5s) between requests to avoid server overload
- Checks `robots.txt` programmatically before scraping
- Uses a standard browser User-Agent header
- Data collected for academic/portfolio purposes only, not commercial use

---

