from src import api_keys_jobs
import pandas as pd
import numpy as np
import re
import html
from pathlib import Path

#function to clean text
def clean_text(value):
    if pd.isna(value):
        return np.nan
    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>" , " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if value.lower() in {"", "nan", "none", "null", "n/a"}:
        return np.nan
    return value

def standardize_city(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip().lower()
    if "toronto" in value: 
        return "Toronto"
    elif "vancouver" in value:
        return "Vancouver"
    elif "montreal" in value or "montréal" in value:
        return "Montréal"
    return np.nan

def standardize_role(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip().lower()
    if "analyst" in value:
        return "Data Analyst"
    elif "scientist" in value:
        return "Data Scientist"
    elif "engineer" in value:
        return "Data Engineer"  
    return np.nan

# Create normalized keys for identifying potential cross-source duplicates.
def normalize_key(value):
    if pd.isna(value):
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())

#function to parse jooble salary
def parse_jooble_salary(value):
    result = {"salary_min_annual": np.nan,
              "salary_max_annual": np.nan,
              "salary_period": "Unkown"}
    
    if pd.isna(value):
        return result
    text = str(value).lower().strip()
    # Normalize thousands separators: 50,000 -> 50000
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    # Determine the pay period from explicit wording.
    if re.search(r"\b(per hour|hourly|/hour|/hr)\b", text):
        multiplier = 37.5 * 52
        period = "Hourly"

    elif re.search(r"\b(per month|monthly|/month)\b", text):
        multiplier = 12
        period = "Monthly"

    elif re.search(r"\b(per week|weekly|/week)\b", text):
        multiplier = 52
        period = "Weekly"

    elif re.search(r"\b(per day|daily|/day)\b", text):
        multiplier = 260
        period = "Daily"

    elif re.search(
        r"\b(annually|annual|yearly|per year|per annum|a year)\b",
        text
    ):
        multiplier = 1
        period = "Annual"

    else:
        # Do not guess the pay period.
        return result

    # Match complete numbers with optional k/m suffixes.
    pattern = r"(?<!\w)(\d+(?:,\d{3})*(?:\.\d+)?)\s*([km]?)(?!\w)"
    matches = re.findall(pattern, text)

    amounts = []

    for number, suffix in matches:
        amount = float(number.replace(",", ""))

        if suffix == "k":
            amount *= 1_000
        elif suffix == "m":
            amount *= 1_000_000

        amounts.append(amount)

    if not amounts:
        return result

    low = amounts[0]
    high = amounts[1] if len(amounts) > 1 else amounts[0]

    if low > high:
        low, high = high, low

    result["salary_min_annual"] = low * multiplier
    result["salary_max_annual"] = high * multiplier
    result["salary_period"] = period

    return result



def clean_data_jobs(jooble_raw_path = None , adzuna_raw_path = None):
    # Load datasets
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    # Set default paths
    if jooble_raw_path is None:
        jooble_raw_path = DATA_DIR / "jooble_raw_jobs.csv"

    if adzuna_raw_path is None:
        adzuna_raw_path = DATA_DIR / "adzuna_raw_jobs.csv"

    # Load datasets
    adzuna_raw = pd.read_csv(adzuna_raw_path)
    jooble_raw = pd.read_csv(jooble_raw_path)


    ### Standardizing both datasets    
    # --------------ADZUNA-----------------
    adzuna = pd.DataFrame({"source": "Adzuna",
                       "source_id": adzuna_raw["id"].astype("string"),
                       "title": adzuna_raw["title"].map(clean_text),
                       "company": adzuna_raw["company.display_name"].map(clean_text),
                       "city_raw": adzuna_raw["location.display_name"].map(clean_text),
                       "search_position": adzuna_raw["search_position"].map(clean_text),
                       "description": adzuna_raw["description"].map(clean_text),
                       "salary_min_raw": pd.to_numeric(adzuna_raw["salary_min"], errors="coerce"),
                       "salary_max_raw": pd.to_numeric(adzuna_raw["salary_max"], errors="coerce"),
                       "salary_period": "Annual (assumed by source)",
                       "job_type": adzuna_raw["contract_time"].map(clean_text),
                       "posted_date": pd.to_datetime(adzuna_raw["created"], errors="coerce", utc=True),
                       "url": adzuna_raw["redirect_url"].map(clean_text),
                       "collected_at": pd.to_datetime(adzuna_raw["request_datetime"], errors="coerce", utc=True)})

    adzuna["salary_min_annual"] = adzuna["salary_min_raw"].where(adzuna["salary_min_raw"].between(15000, 500000))
    adzuna["salary_max_annual"] = adzuna["salary_max_raw"].where(adzuna["salary_max_raw"].between(15000, 500000))
    both_endpoints = (adzuna["salary_min_annual"].notna()& adzuna["salary_max_annual"].notna())
    reversed_salary = (both_endpoints& (adzuna["salary_min_annual"]> adzuna["salary_max_annual"]))
    old_min = adzuna.loc[reversed_salary, "salary_min_annual"].copy()
    adzuna.loc[reversed_salary, "salary_min_annual"] = adzuna.loc[reversed_salary, "salary_max_annual"].to_numpy()
    adzuna.loc[reversed_salary, "salary_max_annual"] = old_min.to_numpy()
    # --------------JOBBLE-----------------
    jooble = pd.DataFrame({
        "source": "Jooble",
        "source_id": jooble_raw["id"].astype("string"),
        "title": jooble_raw["title"].map(clean_text),
        "company": jooble_raw["company"].map(clean_text),
        "city_raw": jooble_raw["location"].map(clean_text),
        "search_position": jooble_raw["search_position"].map(clean_text),
        "description": jooble_raw["snippet"].map(clean_text),
        "salary_min_raw": np.nan,
        "salary_max_raw": np.nan,
        "salary_period": "Unknown",
        "job_type": jooble_raw["type"].map(clean_text),
        "posted_date": pd.to_datetime(jooble_raw["updated"], errors="coerce", utc=True),
        "url": jooble_raw["link"].map(clean_text),
        "collected_at": pd.to_datetime(jooble_raw["request_datetime"], errors="coerce", utc=True)})

    jooble_salary = jooble_raw["salary"].apply(parse_jooble_salary)
    jooble["salary_min_annual"] = jooble_salary.apply(lambda x: x["salary_min_annual"])
    jooble["salary_max_annual"] = jooble_salary.apply(lambda x: x["salary_max_annual"])
    jooble["salary_period"] = jooble_salary.apply(lambda x: x["salary_period"])
    # Retain the original salary text for auditing.
    jooble["salary_original"] = jooble_raw["salary"].map(clean_text)
    # Retain original salary values for Adzuna too.
    adzuna["salary_original"] = (adzuna_raw["salary_min"].astype("string")
        + " - "
        + adzuna_raw["salary_max"].astype("string"))

    mask = (adzuna["salary_min_annual"].notna()& adzuna["salary_max_annual"].notna()& (adzuna["salary_min_annual"]>adzuna["salary_max_annual"]))
    old_min = adzuna.loc[mask, "salary_min_annual"].copy()
    adzuna.loc[mask, "salary_min_annual"] = (adzuna.loc[mask, "salary_max_annual"].values)
    adzuna.loc[mask, "salary_max_annual"] = old_min.values

    jobs = pd.concat([adzuna, jooble], ignore_index=True)
    jobs["city"] = jobs["city_raw"].apply(standardize_city)
    jobs["job_role"] = jobs["search_position"].apply(standardize_role)
    # Standardizing common employment type labels
    jobs["job_type"] = (jobs["job_type"].str.lower().str.replace("_", " ", regex=False).str.strip())

    # Calculate midpoint only when both salary endpoints are available
    jobs["salary_mid_annual"] = (jobs["salary_min_annual"] + jobs["salary_max_annual"])/2

    # Flag potentially invalid or unusual salary figures for review
    jobs["salary_needs_review"] = (jobs["salary_min_annual"].notna()& ((jobs["salary_min_annual"] < 15000)| (jobs["salary_min_annual"] > 500000))) | (jobs["salary_max_annual"].notna()&((jobs["salary_max_annual"] < 15000)| (jobs["salary_max_annual"] > 500000)))

    # Keeping only the three intended cities and three intended roles
    jobs = jobs[jobs["city"].isin(["Toronto", "Vancouver", "Montréal"])
                & jobs["job_role"].isin(["Data Analyst", "Data Scientist", "Data Engineer"])].copy()
    print("Combined records after city and role validation:", len(jobs))

    # Remove duplicate IDs within the same source.
    jobs = jobs.drop_duplicates(subset=["source", "source_id"],keep="first").copy()

    # Remove duplicate URLs within the same source, ignoring missing URLs.
    duplicate_url = (jobs["url"].notna()& jobs.duplicated(subset=["source", "url"], keep="first"))
    jobs = jobs.loc[~duplicate_url].copy()

    # Create normalized keys for identifying potential cross-source duplicates.
    jobs["title_key"] = jobs["title"].apply(normalize_key)
    jobs["company_key"] = jobs["company"].apply(normalize_key)

    # Only compare records with a known title and company.
    valid_key = (jobs["title_key"].ne("")& jobs["company_key"].ne(""))
    jobs["duplicate_candidate"] = False

    duplicate_keys = (jobs.loc[valid_key].groupby(["title_key", "company_key", "city"])["source"].nunique())

    cross_source_keys = duplicate_keys[duplicate_keys > 1].index

    jobs.loc[valid_key, "duplicate_candidate"] = (jobs.loc[valid_key, ["title_key", "company_key", "city"]].apply(tuple, axis=1).isin(cross_source_keys))

    
    print("Records after within-source deduplication:", len(jobs))
    print("Potential cross-source duplicate records:",jobs["duplicate_candidate"].sum())

    # Review possible duplicates rather than deleting them automatically.
    duplicate_review = jobs.loc[jobs["duplicate_candidate"],["source", "title", "company", "city", "salary_original", "url"]].sort_values(["city", "company", "title"])

    # Removing helper columns used only for duplicate matching
    jobs = jobs.drop(columns=["title_key", "company_key"],errors="ignore").copy()
    jobs = jobs.dropna(subset=["salary_mid_annual"])
    return adzuna_raw, jooble_raw, jobs, duplicate_review


# Overall Cleaning Summary
def cleaning_summary(adzuna_raw, jooble_raw, jobs, duplicate_review):
    cleaning_summary = pd.DataFrame({"Metric": ["Original Adzuna records",
                                            "original Jooble records",
                                            "Total raw records",
                                            "Records retained after cleaning",
                                            "Records with a missing salary midpoint",
                                            "Records flagged for salary review",
                                            "Potential cross-source duplicate records"],
                                "Value": [len(adzuna_raw),
                                          len(jooble_raw),
                                          len(adzuna_raw) + len(jooble_raw),
                                          len(jobs),
                                          jobs["salary_mid_annual"].isna().sum(),
                                          jobs["salary_needs_review"].sum(),
                                          jobs["duplicate_candidate"].sum()]})

    print(cleaning_summary)

    #Data quality by source, city and job role
    quality_report = (jobs.groupby(["source", "city", "job_role"], dropna=False)
                      .agg(total_jobs = ("title", "size"),
                       missing_company = ("company", lambda s: s.isna().sum()),
                       missing_salary = ("salary_mid_annual", lambda s: s.isna().sum()),
                       salary_review_requested = ("salary_needs_review", "sum")).reset_index())
    print(quality_report)
