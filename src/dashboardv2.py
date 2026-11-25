import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
from indicators import calculate_indicators

# Color configuration
ROLE_COLORS = {
    "Data Analyst": "#636EFA",
    "Data Engineer": "#00CC96",
    "Data Scientist": "#AB63FA"
}
ROLE_SYMBOLS = {
    "Data Analyst": "circle",
    "Data Engineer": "square",
    "Data Scientist": "diamond"
}
ROLE_ORDER = ["Data Analyst","Data Engineer","Data Scientist"]

CITY_ORDER = ["Montreal", "Toronto", "Vancouver"]
CITY_COLORS = {
    "Montreal": "#F2B66D",
    "Toronto": "#4DB6AC",
    "Vancouver": "#5B9BD5"
}
BEDROOM_COLORS = {
    "0": "#C6DBEF",
    "1": "#9ECAE1",
    "2": "#6BAED6",
    "3": "#4292C6",
    "4": "#3182BD",
    "5": "#2171B5",
    "6": "#08519C",
    "7": "#08306B"
}

# function to set the standard chart format
def format_chart(fig, height=400):
    fig.update_layout(
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=65,
            b=45
        ),
        title=dict(
            x=0.02,
            font=dict(size=16)
        ),
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            title_text=""
        ),
        hoverlabel=dict(
            font_size=12
        )
    )
    return fig
#AFFORDABILITY_THRESHOLD = 0.30

# 1. Page Configuration
# ------------------------------

st.set_page_config(page_title="Canadian Tech Housing Affordability",
                   layout="wide")
st.title("Canadian Tech Job Market and Housing Affordability")
st.write("Explore tech job opportunities, salaries and rental housing across major Canadian cities")

# 2. Loading Cleaned Datasets
# ------------------------------

project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir/"data"

@st.cache_data
def load_data():
    jobs = pd.read_csv(data_dir/"jobs_clean.csv")
    housing = pd.read_excel(data_dir/"Master_Housing_Dataset_V2.xlsx")

    # Standardising city names 
    #jobs["city"] = (jobs["city"].astype(str).str.replace("Montréal", "Montreal", regex=False).str.strip())
    #housing["city"] = (housing["city"].astype(str).str.replace("Montréal", "Montreal", regex=False).str.strip())
    for df in [jobs, housing]:
        df["city"] = df["city"].astype("string").str.strip().str.lower().str.replace("montréal", "montreal", regex=False).str.title()

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

#selected_roles = st.sidebar.multiselect("Selected Job Roles",
#                                        job_roles,
#                                        default=job_roles)

selected_roles = st.sidebar.multiselect(
    "Selected Job Roles",
    job_roles,
    default=job_roles,
    key="job_role_filter"
)

filtered_jobs = filtered_jobs[filtered_jobs["job_role"].isin(selected_roles)]

#Job source filter
sources = sorted(filtered_jobs["source"].dropna().unique())

#selected_sources = st.sidebar.multiselect("Selected Job Roles",
#                                          sources,
#                                          default=sources)
selected_sources = st.sidebar.multiselect(
    "Selected Job Sources",
    sources,
    default=sources,
    key="job_source_filter"
)

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

# Housing Affordability Settings and filter for the threshold
#st.sidebar.divider()
st.sidebar.header("Affordability Settings")

AFFORDABILITY_THRESHOLD = st.sidebar.slider(
        "Affordability Threshold (%)",
        min_value=10,
        max_value=75,
        value=30,
        step=5,
        key="affordability_threshold",
        help="Maximum percentage of gross monthly income allocated to rental housing."
    ) / 100

st.sidebar.caption("30% is the reference threshold used in our research.")


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
job_col1, job_col2 = st.columns(2, gap="large")

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
                          "job_role": "Job Role"},
                color_discrete_map=ROLE_COLORS,
                category_orders={
                    "city": CITY_ORDER,
                    "job_role": ROLE_ORDER
                }
            )
    #st.plotly_chart(fig1, use_container_width=True)
    job_col1.plotly_chart(
        format_chart(fig1),
        use_container_width=True
    )   

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
                              "job_role": "Job Role"},
                    color_discrete_map=ROLE_COLORS,
                    category_orders={
                    "city": CITY_ORDER,
                    "job_role": ROLE_ORDER}
                )
        #st.plotly_chart(fig2, use_container_width=True)
        job_col2.plotly_chart(
            format_chart(fig2),
            use_container_width=True
        )
else: st.info("No job listings match the selected filters")

# 6. Housing Analysis
# ------------------------------

st.header("Housing Market Analysis")
housing_col1, housing_col2 = st.columns(2, gap="large")

if not filtered_housing.empty:
    rent_data = (filtered_housing.groupby("city")["monthly_rent_cad"].median().reset_index())
    fig3 = px.bar(
        rent_data,
        x="city",
        y="monthly_rent_cad",
        color="city",
        color_discrete_map=CITY_COLORS,
        category_orders={"city": CITY_ORDER},
        title="Median Monthly Rent by City",
        labels={"city": "City","monthly_rent_cad": "Median Monthly Rent (CAD)" },
        text_auto="$,.0f"
    )
    fig3.update_traces(textposition="outside")

    fig3.update_yaxes(
        tickprefix="$",
        tickformat=",.0f",
        rangemode="tozero",
        range=[0,rent_data["monthly_rent_cad"].max() * 1.15]
    )
    #fig3.update_yaxes()   

    fig3.update_layout(showlegend=False)

    #st.plotly_chart(fig3, use_container_width=True)
    housing_col1.plotly_chart(
        format_chart(fig3),
        use_container_width=True
    )

    # Rental listings by bedroom count
    bedroom_data = (filtered_housing.groupby("bedrooms").size().reset_index(name="Rental Listings"))

    # Convert bedrooms to labels for coloring
    bedroom_data["bedroom_category"] = (bedroom_data["bedrooms"].astype(int).astype(str))

    fig4 = px.bar(
        bedroom_data,
        x="bedroom_category",
        y="Rental Listings",
        color="bedroom_category",
        color_discrete_map=BEDROOM_COLORS,
        category_orders={
            "bedroom_category": ["0", "1", "2", "3", "4", "5", "6", "7"]
        },
        title="Rental Listings by Number of Bedrooms",
        labels={
            "bedroom_category": "Number of Bedrooms",
            "Rental Listings": "Number of Listings"
        },
        text_auto=True
    )

    fig4.update_traces(textposition="outside")
    fig4.update_xaxes(type="category")
    fig4.update_yaxes(range=[0,bedroom_data["Rental Listings"].max() * 1.15])
    fig4.update_layout(showlegend=False)

    #st.plotly_chart(fig4, use_container_width=True)
    housing_col2.plotly_chart(
        format_chart(fig4),   
        use_container_width=True
    )
else: st.info("No rental listings match the selected features")


# ============================================================
# 7. HOUSING AFFORDABILITY ANALYSIS
# ============================================================
st.header("Housing Affordability Analysis")
###############################
# Affordability Methodology
with st.expander("Understanding the Affordability Indicators",expanded=False):
    st.markdown("""
        This analysis uses two complementary indicators to evaluate the 
        relationship between advertised salaries and rental
        housing costs across Montreal, Toronto, and Vancouver.
    """)
    # Indicator 1
    st.markdown("#### Indicator 1: Estimated Rent Burden")
    st.markdown("Measures the percentage of gross monthly salary required to cover the median monthly rent in the corresponding city.")

    st.latex(
        r"\frac{\text{Median Monthly Rent}}"
        r"{\text{Annual Gross Salary}/12}\times 100"
    )
    st.success("Lower values indicate more favorable affordability conditions.")
    st.divider()

    # Indicator 2
    st.markdown("#### Indicator 2: Share of Affordable Rental Listings")

    st.markdown("Measures the percentage of rental listings with monthly rents within the estimated affordable rental budget.")

    st.latex(
        r"\frac{\text{Affordable Rental Listings}}"
        r"{\text{Total Eligible Rental Listings}}\times 100"
    )
    st.markdown("Where:")
    st.latex(
        r"\text{Affordable Budget}="
        r"\frac{\text{Annual Gross Salary}}{12}\times T"
    )
    st.caption("T = Selected affordability threshold (0.30 by default).")
    st.success("Higher values indicate greater access to rental housing.")
    st.divider()

    # Level of analysis
    st.markdown("#### Level of Analysis")

    st.markdown("""
        - **City and occupation:** Indicators are calculated
        using median advertised salaries for each combination.

        - **Individual job listings:** Indicators are calculated
        using each advertised salary and the corresponding
        city's rental market.
    """)

    # Threshold and interactivity
    st.markdown("#### Affordability Threshold and Interactivity")

    st.markdown("""
        The research uses 30% of gross monthly income as its
        reference affordability threshold. Users can modify
        this threshold and apply dashboard filters to explore
        alternative scenarios.

        All affordability indicators are recalculated based
        on the selected job and housing records.
    """)

    st.info(
        f"Current affordability threshold: "
        f"{AFFORDABILITY_THRESHOLD:.0%}"
    )

    # Limitations
    st.markdown("#### Limitations")

    st.markdown("""
        The indicators provide estimated affordability based
        on advertised salaries and sampled rental listings.
        They do not account for taxes, actual household income,
        additional living expenses or individual housing
        preferences.

        Results should be interpreted within the selected
        sample rather than as representative estimates of
        the entire Canadian job or rental market.
    """)
###############################
# Select valid records from the filtered datasets
aff_jobs = filtered_jobs[filtered_jobs["salary_mid_annual"] > 0].copy()

aff_housing = filtered_housing[filtered_housing["monthly_rent_cad"] > 0].copy()

# Create rental distributions by city
rent_by_city = {
    city: np.sort(group["monthly_rent_cad"].to_numpy())
    for city, group in aff_housing.groupby("city")
}

# Calculate individual job-level indicators
results = []

for _, job in aff_jobs.iterrows():
    city = job["city"]
    salary = job["salary_mid_annual"]
    rents = rent_by_city.get(city, np.array([]))
    metrics = calculate_indicators(
        salary,
        rents,
        AFFORDABILITY_THRESHOLD
    )
    record = job.to_dict()
    record.update(metrics.to_dict())
    results.append(record)
aff_job_indicators = pd.DataFrame(results)

# Calculate median salaries by city and occupation
salary_summary = (
    aff_jobs.groupby(["city", "job_role"])
    .agg(
        job_count=("salary_mid_annual", "size"),
        median_annual_salary=("salary_mid_annual", "median")
    )
    .reset_index()
)

# Calculate city-occupation indicators
summary_results = []
for _, group in salary_summary.iterrows():
    city = group["city"]
    salary = group["median_annual_salary"]
    rents = rent_by_city.get(city, np.array([]))
    metrics = calculate_indicators(
        salary,
        rents,
        AFFORDABILITY_THRESHOLD
    )
    record = group.to_dict()
    record.update(metrics.to_dict())
    record["median_monthly_rent"] = (
        np.median(rents) if len(rents) else np.nan
    )
    summary_results.append(record)
aff_summary = pd.DataFrame(summary_results)


# ============================================================
# AFFORDABILITY KEY PERFORMANCE INDICATORS
# ============================================================
st.caption("Understanding the relationship between advertised salaries and rental housing costs.")

if not aff_job_indicators.empty:
    median_burden = aff_job_indicators["rent_burden_pct"].median()
    median_affordable_share = aff_job_indicators["affordable_listings_pct"].median()
    threshold_pct = AFFORDABILITY_THRESHOLD * 100
    burden_difference = median_burden - threshold_pct
    kpi_aff1, kpi_aff2 = st.columns(2, gap="large")
    kpi_aff1.metric(
        label="Median Estimated Rent Burden",
        value=(
            f"{median_burden:.1f}%"
            if pd.notna(median_burden) else "N/A"
        ),
        delta=(
            f"{burden_difference:+.1f} pp vs. threshold"
            if pd.notna(burden_difference) else None
        ),
        delta_color="inverse",
        help="Median estimated rent burden across individual job listings with available affordability data.",
        border=True
    )

    kpi_aff2.metric(
        label="Median Share of Affordable Rentals",
        value=(
            f"{median_affordable_share:.1f}%"
            if pd.notna(median_affordable_share) else "N/A"
        ),
        help="Median percentage of local rental listings affordable across individual advertised salaries.",
        border=True
    )

else:
    st.info("No affordability data available for the selected filters.")

st.divider()


# ------------------------------------------------------------
# Visualization 1: Estimated Rent Burden
# ------------------------------------------------------------
st.subheader("Comparing Housing Affordability")
st.caption(
    "Compare the estimated rent burden and the share "
    "of affordable rental listings based on median "
    "advertised salaries across cities and occupations."
)
aff_col1, aff_col2 = st.columns(2, gap="large")

if not aff_summary.empty:
    fig5 = px.bar(
        aff_summary,
        x="city",
        y="rent_burden_pct",
        color="job_role",
        barmode="group",
        text_auto=".1f",
        title="Estimated Rent Burden by City and Occupation",
        color_discrete_map=ROLE_COLORS,
        category_orders={
            "city": CITY_ORDER,
            "job_role": ROLE_ORDER
        },
        labels={
            "city": "City",
            "rent_burden_pct": "Estimated Rent Burden (%)",
            "job_role": "Occupation"
        },
        hover_data={
            "median_annual_salary": ":,.0f",
            "median_monthly_rent": ":,.0f",
            "job_count": True
        }
    )
    fig5.add_hline(
        y=AFFORDABILITY_THRESHOLD * 100,
        line_dash="dash",
        line_color="#EF553B",
        annotation_text=(f"{AFFORDABILITY_THRESHOLD:.0%} Affordability Threshold")
    )
    fig5.update_yaxes(ticksuffix="%")
    fig5.update_traces(textposition="outside")
    #st.plotly_chart(fig5,use_container_width=True,key="rent_burden_chart")
    aff_col1.plotly_chart(
        format_chart(fig5, height=500),
        use_container_width=True,
        key="rent_burden_chart"
    )
else:
    st.info("No data available for affordability analysis")

# ------------------------------------------------------------
# Visualization 2: Affordable Rental Listings
# ------------------------------------------------------------
if not aff_summary.empty:
    rental_share = aff_summary.dropna(subset=["affordable_listings_pct"]).copy()
    rental_share["Affordable"] = rental_share["affordable_listings_pct"]
    rental_share["Unaffordable"] = 100 - rental_share["Affordable"]
    rental_share["City and Occupation"] = rental_share["city"] + " | " + rental_share["job_role"]

    fig6 = px.bar(
        rental_share,
        x=["Affordable", "Unaffordable"],
        y="City and Occupation",
        orientation="h",
        barmode="stack",
        text_auto=".1f",
        title="Share of Affordable Rental Listings",
        color_discrete_map={
            "Affordable": "#00CC96",
            "Unaffordable": "#EF553B"
        },
        labels={
            "value": "Rental Listings (%)",
            "variable": "Affordability Status"
        },
        hover_data=[
            "affordable_listings_count",
            "total_rental_listings",
            "median_annual_salary"
        ]
    )
    fig6.update_xaxes(
        range=[0, 100],
        ticksuffix="%"
    )
    fig6.update_yaxes(autorange="reversed")
    #st.plotly_chart(fig6,use_container_width=True,key="affordable_rentals_chart")
    aff_col2.plotly_chart(
        format_chart(fig6, height=500),
        use_container_width=True,
        key="affordable_rentals_chart"
    )

# ------------------------------------------------------------
# Visualization 3: Affordability Heatmap
# ------------------------------------------------------------
st.subheader("Identifying Affordability Patterns")
st.caption("Explore similarities and differences in housing affordability by examining both indicators together.")
aff_col3, aff_col4 = st.columns(2, gap="large")

if not aff_summary.empty:
    #selected_indicator = st.radio(
    selected_indicator = aff_col3.radio(
        "Select Affordability Indicator",
        [
            "Estimated Rent Burden",
            "Affordable Rental Listings"
        ],
        horizontal=True,
        key="heatmap_indicator"
    )

    indicator_column = {
        "Estimated Rent Burden": "rent_burden_pct",
        "Affordable Rental Listings": "affordable_listings_pct"
    }[selected_indicator]

    heatmap_data = aff_summary.pivot(
        index="job_role",
        columns="city",
        values=indicator_column
    )

    heatmap_data = heatmap_data.reindex(
        index=[
            role for role in ROLE_ORDER
            if role in heatmap_data.index
        ],
        columns=[
            city for city in CITY_ORDER
            if city in heatmap_data.columns
        ]
    )

    color_scale = (
        "RdYlGn_r"
        if indicator_column == "rent_burden_pct"
        else "RdYlGn"
    )

    fig7 = px.imshow(
        heatmap_data,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale=color_scale,
        zmin=0,
        zmax=(
            max(60, heatmap_data.max().max())
            if indicator_column == "rent_burden_pct"
            else 100
        ),
        title=f"Affordability Matrix: {selected_indicator}",
        labels={
            "x": "City",
            "y": "Occupation",
            "color": "Percentage (%)"
        }
    )

    fig7.update_coloraxes(colorbar_ticksuffix="%")

    #st.plotly_chart(fig7,use_container_width=True,key="affordability_heatmap" )
    aff_col3.plotly_chart(
        format_chart(fig7, height=420),
        use_container_width=True,
        key="affordability_heatmap"
    )
# ------------------------------------------------------------
# Visualization 4: Relationship Between Indicators
# ------------------------------------------------------------
if not aff_summary.empty:
    # City abbreviations for point labels
    scatter_data = aff_summary.copy()

    scatter_data["city_label"] = scatter_data["city"].map({
        "Montreal": "MTL",
        "Toronto": "TOR",
        "Vancouver": "VAN"
    })

    fig8 = px.scatter(
        scatter_data,
        x="rent_burden_pct",
        y="affordable_listings_pct",
        color="job_role",
        symbol="job_role",
        text="city_label",
        size="job_count",
        size_max=18,
        title="Relationship Between Affordability Indicators",
        color_discrete_map=ROLE_COLORS,
        symbol_map=ROLE_SYMBOLS,
        category_orders={"job_role": ROLE_ORDER},
        labels={
            "rent_burden_pct": "Estimated Rent Burden (%)",
            "affordable_listings_pct": "Affordable Rental Listings (%)",
            "job_role": "Occupation",
            "city": "City",
            "job_count": "Job Listings"
        },
        hover_data={
            "city": True,
            "city_label": False,
            "median_annual_salary": ":,.0f",
            "median_monthly_rent": ":,.0f"
        }
    )

    fig8.update_traces(
        textposition="top center",
        marker=dict(opacity=0.85)
    )

    fig8.add_vline(
        x=AFFORDABILITY_THRESHOLD * 100,
        line_dash="dash",
        line_color="#EF553B",
        #annotation_text="30% Threshold"
        annotation_text=f"{AFFORDABILITY_THRESHOLD:.0%} Threshold"
    )

    fig8.update_xaxes(ticksuffix="%",rangemode="tozero")

    fig8.update_yaxes(ticksuffix="%",range=[0, 105])

    #st.plotly_chart(fig8,use_container_width=True,key="affordability_scatter")
    aff_col4.plotly_chart(
        format_chart(fig8, height=470),
        use_container_width=True,
        key="affordability_scatter"
    )

# ------------------------------------------------------------
# Visualization 5: Rent Burden Distribution
# ------------------------------------------------------------
st.subheader("Individual Job-Level Affordability")
st.caption("Examine how housing affordability varies across individual advertised salaries, beyond median values.")
if not aff_job_indicators.empty:
    show_full_range = st.checkbox(
        "Show full range, including extreme outliers",
        value=False,
        key="rent_burden_full_range"
    )

    fig9 = px.box(
        aff_job_indicators,
        x="city",
        y="rent_burden_pct",
        color="job_role",
        points="outliers",
        title="Distribution of Estimated Rent Burden",
        color_discrete_map=ROLE_COLORS,
        category_orders={
            "city": CITY_ORDER,
            "job_role": ROLE_ORDER
        },
        labels={
            "city": "City",
            "rent_burden_pct": "Estimated Rent Burden (%)",
            "job_role": "Occupation"
        },
        hover_data=[
            "salary_mid_annual"
        ]
    )

    fig9.add_hline(
        y=AFFORDABILITY_THRESHOLD * 100,
        line_dash="dash",
        line_color="#EF553B",
        #annotation_text="30% Affordability Threshold"
        annotation_text=(f"{AFFORDABILITY_THRESHOLD:.0%} Affordability Threshold")
    )

    #fig9.update_yaxes(ticksuffix="%")
    if show_full_range:
        fig9.update_yaxes(ticksuffix="%",autorange=True )
    else:
        fig9.update_yaxes(ticksuffix="%",range=[0, 100],dtick=25)

    #st.plotly_chart(fig9,use_container_width=True,key="rent_burden_distribution")
    st.plotly_chart(
        format_chart(fig9, height=450),
        use_container_width=True,
        key="rent_burden_distribution"
    )

    if not show_full_range:
        extreme_count = (aff_job_indicators["rent_burden_pct"] > 100).sum()
        st.caption(
            f"Display limited to 0–100% for readability. "
            f"{extreme_count:,} observations above 100% "
            "remain included in the statistical calculations."
        )

# ------------------------------------------------------------
# Visualization 6: Jobs Offering Affordable Salaries
# ------------------------------------------------------------

if not aff_job_indicators.empty:
    job_affordability = aff_job_indicators.dropna(subset=["rent_burden_pct"]).copy()
    job_affordability["is_affordable"] = job_affordability["rent_burden_pct"]<= AFFORDABILITY_THRESHOLD * 100

    affordable_jobs = (
        job_affordability.groupby(["city", "job_role"])
        .agg(
            total_jobs=("is_affordable", "size"),
            affordable_jobs_count=("is_affordable", "sum"),
            affordable_jobs_pct=("is_affordable", "mean")
        )
        .reset_index()
    )

    affordable_jobs["Affordable"] = affordable_jobs["affordable_jobs_pct"] * 100

    affordable_jobs["Unaffordable"] = 100 - affordable_jobs["Affordable"]

    affordable_jobs["City and Occupation"] = (
        affordable_jobs["city"] + " | " +
        affordable_jobs["job_role"]
    )

    fig10 = px.bar(
        affordable_jobs,
        x=["Affordable", "Unaffordable"],
        y="City and Occupation",
        orientation="h",
        barmode="stack",
        text_auto=".1f",
        title="Share of Jobs Offering Affordable Salaries",
        color_discrete_map={
            "Affordable": "#00CC96",
            "Unaffordable": "#EF553B"
        },
        labels={
            "value": "Job Listings (%)",
            "variable": "Affordability Status"
        },
        hover_data=[
            "total_jobs",
            "affordable_jobs_count"
        ]
    )

    fig10.update_xaxes(range=[0, 100],ticksuffix="%")

    fig10.update_yaxes(autorange="reversed")

    #st.plotly_chart(fig10,use_container_width=True,key="affordable_jobs_chart")
    st.plotly_chart(
        format_chart(fig10, height=450),
        use_container_width=True,
        key="affordable_jobs_chart"
    )

# 8. Data Preview
# ------------------------------

with st.expander("View Filtered Job Data"):
    st.dataframe(filtered_jobs, use_container_width=True)

with st.expander("View Filtered Housing Data"):
    st.dataframe(filtered_housing, use_container_width=True)