
from demo.demo_cleaning import jobs
import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from IPython.display import display

# ============================================================
# CALCULATE BOTH INDICATORS
# ============================================================

def calculate_indicators(annual_salary, rents,AFFORDABILITY_THRESHOLD):

    if pd.isna(annual_salary) or annual_salary <= 0:
        return pd.Series({
            "rent_burden_pct": np.nan,
            "affordable_listings_pct": np.nan,
            "affordable_listings_count": np.nan,
            "total_rental_listings": 0
        })

    if len(rents) == 0:
        return pd.Series({
            "rent_burden_pct": np.nan,
            "affordable_listings_pct": np.nan,
            "affordable_listings_count": 0,
            "total_rental_listings": 0
        })

    monthly_salary = annual_salary / 12
    maximum_affordable_rent = (
        monthly_salary * AFFORDABILITY_THRESHOLD
    )

    # Indicator 1: Estimated rent burden
    median_rent = np.median(rents)

    rent_burden_pct = (
        median_rent / monthly_salary
    ) * 100

    # Indicator 2: Share of affordable listings
    # searchsorted counts values <= maximum affordable rent
    affordable_count = np.searchsorted(
        rents,
        maximum_affordable_rent,
        side="right"
    )

    affordable_pct = (
        affordable_count / len(rents)
    ) * 100

    return pd.Series({
        "rent_burden_pct": rent_burden_pct,
        "affordable_listings_pct": affordable_pct,
        "affordable_listings_count": affordable_count,
        "total_rental_listings": len(rents)
    })

# ============================================================
# MAIN FUNCTION
# ============================================================
def get_indicators(JOBS_FILE = "data/jobs_clean.csv",HOUSING_FILE = "data/Master_Housing_Dataset_V2.xlsx",AFFORDABILITY_THRESHOLD = 0.30,BEDROOMS_TO_INCLUDE = [0,1,2,4,5,6,7]):
    
    # ============================================================
    # LOAD DATASETS
    # ============================================================
    jobs = pd.read_csv(JOBS_FILE)
    housing = pd.read_excel(HOUSING_FILE)

    #print("Initial jobs:", len(jobs))
    #print("Initial rental listings:", len(housing))

    # Select valid job records
    jobs = jobs[
        (jobs["salary_mid_annual"] > 0) 
        #& (jobs["salary_needs_review"] == False) 
        #& (jobs["duplicate_candidate"] == False)
    ].copy()

    # Select valid rental records
    housing = housing[
        (housing["monthly_rent_cad"] > 0) &
        (housing["bedrooms"].isin(BEDROOMS_TO_INCLUDE))
    ].copy()

    # Standardize city names
    for df in [jobs, housing]:
        df["city"] = df["city"].astype(str).str.strip().str.lower()

    #print("Eligible jobs:", len(jobs))
    #print("Eligible rental listings:", len(housing))
    

    # ============================================================
    # PREPARE RENT DISTRIBUTIONS
    # ============================================================

    # Create sorted rent arrays for efficient calculations
    rent_by_city = {
        city: np.sort(group["monthly_rent_cad"].to_numpy())
        for city, group in housing.groupby("city")
    }

    all_rents = np.sort(
        housing["monthly_rent_cad"].to_numpy()
    )

    # ============================================================
    # JOB-LEVEL INDICATORS
    # ============================================================
    results = []
    for _, job in jobs.iterrows():
        salary = job["salary_mid_annual"]
        city = job["city"]
        # Same-city calculation
        city_rents = rent_by_city.get(city, np.array([]))
        city_result = calculate_indicators(salary, city_rents,AFFORDABILITY_THRESHOLD)

        # All-city calculation
        pooled_result = calculate_indicators(salary, all_rents,AFFORDABILITY_THRESHOLD)
        record = job.to_dict()
        for field, value in city_result.items():
            record[f"city_{field}"] = value
        for field, value in pooled_result.items():
            record[f"pooled_{field}"] = value
        results.append(record)
    df_indicators = pd.DataFrame(results)

    # ============================================================
    # 6. CITY-OCCUPATION SUMMARY
    # ============================================================

    salary_summary = (
        jobs.groupby(["city", "job_role"])
        .agg(
            job_count=("salary_mid_annual", "size"),
            median_annual_salary=("salary_mid_annual", "median")
        )
        .reset_index()
    )

    summary_results = []

    for _, group in salary_summary.iterrows():
        city = group["city"]
        salary = group["median_annual_salary"]
        rents = rent_by_city.get(city, np.array([]))
        metrics = calculate_indicators(salary, rents,AFFORDABILITY_THRESHOLD)
        record = group.to_dict()
        record.update(metrics.to_dict())
        record["median_monthly_rent"] = (
            np.median(rents) if len(rents) else np.nan
        )
        summary_results.append(record)
    df_summary = pd.DataFrame(summary_results)


    # ============================================================
    # ROUND AND VALIDATE
    # ============================================================
    for col in df_indicators.columns:
        if col.endswith("_pct"):
            df_indicators[col] = df_indicators[col].round(3)

    for col in df_summary.columns:
        if col.endswith("_pct"):
            df_summary[col] = df_summary[col].round(3)

    assert df_indicators["city_affordable_listings_pct"].dropna().between(0, 100).all()
    assert df_summary["affordable_listings_pct"].dropna().between(0, 100).all()

    return df_indicators,df_summary

