import pandas as pd
import numpy as np
from pathlib import Path
from src.data_cleaning_jobs import clean_data_jobs, cleaning_summary

adzuna_raw, jooble_raw, jobs, duplicate_review= clean_data_jobs()
jobs.to_csv("jobs_clean.csv", index=False)
#print(jobs["job_type"].value_counts(dropna=False))
cleaning_summary(adzuna_raw, jooble_raw, jobs, duplicate_review)
