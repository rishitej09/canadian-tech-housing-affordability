import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# 1. Page Configuration
# ------------------------------

st.set_page_config(page_title="Canadian Tech Housing Affordability",
                   layout="wide")
st.title("Canadian Tech Job Market and Housing Affordability")
st.write("Explore tech job opportunities, salaries and rental housing across major Canadian cities")

# 2. Loading Cleaned Datasets
# ------------------------------

project_dir = Path(__file__).resolve().parent
data_dir = project_dir/"data"

@st.cache_data
def load_data():
    jobs = pd.read_csv(data_dir/"jobs_clean.csv")
    housing = pd.read_excel(data_dir/"Master_Housing_Dataset_V2.xlsx")

    # Standardising city names 
    jobs["city"] = (jobs["city"].astype(str).str.replace("Montréal", "Montreal", regex=False).str.strip())
    housing["city"] = (housing["city"].astype(str).str.replace("Montréal", "Montreal", regex=False).str.strip())

    jobs["salary_mid_annual"] = pd.to_numeric(jobs["salary_mid_annual"], errors="coerce")
    housing["monthly_rent_cad"] = pd.to_numeric(housing["monthly_rent_cad"], errors="coerce")
    
    return jobs, housing

try:
    jobs, housing = load_data()
except Exception as e:
    st.error(f"Error loading datasets: {e}")
    st.stop()

# 3. Sidebar Filters
# ------------------------------

st.sidebar.header("Dashboard Filters")
available_cities = sorted(set(jobs["city"].dropna()) & 
                          set(housing["city"].dropna()))

selected_cities = st.sidebar.multiselect("Selected Cities",
                                         available_cities,
                                         default=available_cities)

filtered_jobs = jobs[jobs["city"].isin(selected_cities)].copy()

filtered_housing = housing[housing["city"].isin(selected_cities)].copy()

job_roles = sorted(filtered_jobs["job_role"].dropna().unique())

selected_roles = st.sidebar.multiselect("Selected Job Roles",
                                        job_roles,
                                        default=job_roles)

filtered_jobs = filtered_jobs[filtered_jobs["job_role"].isin(selected_roles)]

#Job source filter
sources = sorted(filtered_jobs["source"].dropna().unique())

selected_sources = st.sidebar.multiselect("Selected Job Roles",
                                          sources,
                                          default=sources)

filtered_jobs = filtered_jobs[filtered_jobs["source"].isin(selected_sources)]

#Employment type filter
employment_types = sorted(filtered_jobs["job_type"].dropna().unique())

selected_types = st.sidebar.multiselect("Select Employment Types",
                                        employment_types,
                                        default=employment_types)

filtered_jobs = filtered_jobs[filtered_jobs["job_type"].isin(selected_types)]

# Housing rent filter
rent_values = filtered_housing["monthly_rent_cad"].dropna()
if not rent_values.empty:
    min_rent = int(rent_values.min())
    max_rent = int(rent_values.max())

    if min_rent < max_rent:
        rent_range = st.sidebar.slider("Monthly Rent CAD",
                                       min_value=min_rent,
                                       max_value=max_rent,
                                       value=(min_rent, max_rent),
                                       step=100)
        filtered_housing = filtered_housing[filtered_housing["monthly_rent_cad"].between(rent_range[0], rent_range[1])]

# Bedroom Filter
bedroom_options = sorted(filtered_housing["bedrooms"].dropna().unique())

selected_bedrooms = st.sidebar.multiselect("Number of Bedrooms",
                                           bedroom_options,
                                           default=bedroom_options)
filtered_housing = filtered_housing[filtered_housing["bedrooms"].isin(selected_bedrooms)]

# 4. Key Performance Indicators
# ------------------------------

st.header("Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)


total_jobs = len(filtered_jobs)
total_rentals = len(filtered_housing)

valid_salaries = filtered_jobs["salary_mid_annual"].dropna()

# Excluding salaries flagged for manual review
if "salary_needs_review" in filtered_jobs.columns:
    review_flags = (filtered_jobs["salary_needs_review"].astype(str).str.lower().isin(["true", "1", "yes"]))
    valid_salaries = filtered_jobs.loc[~review_flags, "salary_mid_annual"].dropna()

average_salary = (valid_salaries.mean()
                  if not valid_salaries.empty else None)
median_salary = (valid_salaries.median()
                 if not valid_salaries.empty else None)
median_rent = filtered_housing["monthly_rent_cad"].median()

col1.metric("Total Job Listings", f"{total_jobs:,}")

col2.metric("Average Annual Salary",
            f"${average_salary:,.0f}" if pd.notna(average_salary) else "N/A")

col3.metric("Median Annual Salary",
            f"${median_salary:,.0f}" if pd.notna(median_salary)else "N/A")

col4.metric("Rental Listings", f"{total_rentals:,}")

col5.metric("Median Monthly Rent",
            f"${median_rent:,.0f}" if pd.notna(median_rent)else "N/A")

# 5. Visualizations
# ------------------------------

st.header("Job Market Analysis")

if not filtered_jobs.empty:
    # Job listings by city and role
    job_counts = (filtered_jobs.groupby(["city", "job_role"]).size().reset_index(name="Job Listings"))

    fig1 = px.bar(job_counts,
                  x="city",
                  y="Job Listings",
                  color="job_role",
                  barmode="group",
                  title="Job Listings by City and Role",
                  labels={"city": "City",
                          "job_role": "Job Role"})
    st.plotly_chart(fig1, use_container_width=True)

    # Median salary by city and role
    salary_data = (filtered_jobs.dropna(subset=["salary_mid_annual"]).groupby(["city", "job_role"])["salary_mid_annual"].median().reset_index())

    if not salary_data.empty:
        fig2 = px.bar(salary_data,
                      x= "city",
                      y= "salary_mid_annual",
                      color="job_role",
                      barmode="group",
                      title="Median Annual Salary by City and Job Role",
                      labels={"city": "City",
                              "salary_mid_annual": "Median Annual Salary CAD",
                              "job_role": "Job Role"})
        st.plotly_chart(fig2, use_container_width=True)
else: st.info("No job listings match the selected filters")

# 6. Housing Analysis
# ------------------------------

st.header("Housing Market Analysis")

if not filtered_housing.empty:
    rent_data = (filtered_housing.groupby("city")["monthly_rent_cad"].median().reset_index())
    fig3 = px.bar(rent_data,
                  x="city",
                  y="monthly_rent_cad",
                  title="Median Monthly Rent by City",
                  labels={"city": "City",
                          "monthly_rent_cad": "Median Monthly Rent CAD"},
                          text_auto=".2s")
    st.plotly_chart(fig3, use_container_width=True)

    # Rental listings by bedroom count
    bedroom_data = (filtered_housing.groupby("bedrooms").size().reset_index(name="Rental Listings"))

    fig4 = px.bar(bedroom_data,
                  x="bedrooms",
                  y="Rental Listings",
                  title="Rental Listings by Number of Bedrooms",
                  labels={"bedrooms": "Number of Bedrooms",
                          "Rental Listings": "Number of Listings"})
    st.plotly_chart(fig4, use_container_width=True)
else: st.info("No rental listings match the selected features")

# 7. Data Preview
# ------------------------------

with st.expander("View Filtered Job Data"):
    st.dataframe(filtered_jobs, use_container_width=True)

with st.expander("View Filtered Housing Data"):
    st.dataframe(filtered_housing, use_container_width=True)