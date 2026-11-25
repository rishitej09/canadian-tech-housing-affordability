import pandas as pd
import numpy as np
from pathlib import Path
import openpyxl
from IPython.display import display
from src.indicators import get_indicators,calculate_indicators
#print("---------------------------------------")
df_indicators,df_summary=get_indicators()

df_indicators.to_csv("jobs_clean.csv",index=False,encoding="utf-8-sig")

df_summary.to_csv("affordability_summary.csv",index=False,encoding="utf-8-sig")

display(
    df_indicators[[
        "city",
        "job_role",
        "salary_mid_annual",
        "city_rent_burden_pct",
        "city_affordable_listings_pct",
        "pooled_rent_burden_pct",
        "pooled_affordable_listings_pct"
    ]].head(10)
)

display(df_summary.sort_values(["city", "job_role"]))
