import argparse
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
from scipy import stats
import scikit_posthocs as sp
from statsmodels.stats.multitest import multipletests

# ============================================================
# 1. CONFIGURATION
# ============================================================
CITIES = ['Montreal', 'Toronto', 'Vancouver']
ROLES = ['Data Analyst', 'Data Engineer', 'Data Scientist']
AFFORDABILITY_THRESHOLD = 0.30
IQR_MULTIPLIER = 1.5
BOOTSTRAP_ITERATIONS = 5000
RANDOM_SEED = 42
MIN_GROUP_SIZE = 5

# ============================================================
# 2. LOAD DATA AND APPLY EDA ELIGIBILITY RULES
# ============================================================
def load_data(jobs_path, housing_path):
    project_dir = Path(__file__).resolve().parent.parent
    data_dir = project_dir/"data"/jobs_path
    jobs = pd.read_csv(data_dir/jobs_path, dtype={'source_id': 'string'})
    housing = pd.read_excel(data_dir/housing_path)
    print('Original jobs:', len(jobs))
    print('Original rentals:', len(housing))

    #shaping the datatypes and cleaning the city names to match between the two datasets
    for df in [jobs, housing]:
        df['city'] = (df['city'].astype('string').str.strip().str.lower()
                      .str.replace('montréal', 'montreal', regex=False).str.title())
    jobs['salary_mid_annual'] = pd.to_numeric(jobs['salary_mid_annual'], errors='coerce')
    housing['monthly_rent_cad'] = pd.to_numeric(housing['monthly_rent_cad'], errors='coerce')
    jobs = jobs[jobs['city'].isin(CITIES) & jobs['job_role'].isin(ROLES)
                & np.isfinite(jobs['salary_mid_annual']) & (jobs['salary_mid_annual'] > 0)].copy()
    housing = housing[housing['city'].isin(CITIES)
                      & np.isfinite(housing['monthly_rent_cad']) & (housing['monthly_rent_cad'] > 0)].copy()

    # Exclude salaries flagged for review.
    review = jobs['salary_needs_review'].astype(str).str.lower().isin(['true', '1', 'yes'])
    jobs = jobs.loc[~review].copy()
    print('Jobs after salary review:', len(jobs))

    # Follow the EDA duplicate heuristic: prioritize Adzuna, then latest date.
    for column in ['title', 'company']:
        jobs[column + '_key'] = (jobs[column].fillna('').str.lower()
                                .str.replace(r'[^a-z0-9]', '', regex=True))
    jobs['source_order'] = jobs['source'].map({'Adzuna': 0, 'Jooble': 1})
    jobs['posted_date'] = pd.to_datetime(jobs['posted_date'], errors='coerce', utc=True)
    jobs = jobs.sort_values(['source_order', 'posted_date'], ascending=[True, False])
    duplicate_flag = jobs['duplicate_candidate'].astype(str).str.lower().isin(['true', '1', 'yes'])
    repeated = jobs.duplicated(['title_key', 'company_key', 'city'], keep='first')
    jobs = jobs.loc[~(duplicate_flag & repeated)].copy()
    jobs = jobs.drop(columns=['title_key', 'company_key', 'source_order'])
    print('Jobs after duplicate handling:', len(jobs))
    return jobs, housing

# ============================================================
# 3. REMOVE OUTLIERS USING THE EDA IQR RULE
# ============================================================
def flag_outliers(values):
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - IQR_MULTIPLIER * iqr
    upper = q3 + IQR_MULTIPLIER * iqr
    return (values < lower) | (values > upper)


def group_bedrooms(value):
    # Use the same bedroom categories as the housing EDA.
    if pd.isna(value):
        return 'Not stated'
    if value == 0:
        return 'Studio'
    if value in [1, 2, 3]:
        return str(int(value)) + ' bedroom(s)'
    return '4+ bedrooms'


def remove_outliers(jobs, housing):
    jobs = jobs.copy()
    housing = housing.copy()
    housing['bedrooms'] = pd.to_numeric(housing['bedrooms'], errors='coerce')
    #Adding a feature for grouped bedrooms
    housing['bedroom_group'] = housing['bedrooms'].apply(group_bedrooms)
    #flagging outliers (1.5 IQR)
    jobs['salary_outlier'] = jobs.groupby(['city', 'job_role'])['salary_mid_annual'].transform(flag_outliers)
    housing['rent_outlier'] = housing.groupby(['city', 'bedroom_group'])['monthly_rent_cad'].transform(flag_outliers)
    print('Salary outliers removed:', jobs['salary_outlier'].sum())
    print('Rental outliers removed:', housing['rent_outlier'].sum())
    jobs = jobs.loc[~jobs['salary_outlier']].copy()
    housing = housing.loc[~housing['rent_outlier']].copy()
    print('Final jobs:', len(jobs))
    print('Final rentals:', len(housing))
    return jobs, housing

# ============================================================
# 4. INFERENTIAL STATISTICS: KRUSKAL-WALLIS, DUNN AND EFFECT SIZE
# ============================================================
# Holm-Bonferroni correction 
# Used to adjust the p-values before determining statistical significance.
def holm_correction(p_values):
    # Adjust p-values using the Holm method.
    results = multipletests(p_values,alpha=0.05,method="holm")
    adjusted = results[1]
    return adjusted


def run_statistical_tests(jobs, housing):
    # Define the salary comparisons across cities and occupations.
    test_designs = []
    #setting up prerequisites for comparisons
    for role in ROLES:
        # tuples with (Name, data, group column, Value column)
        role_jobs = jobs[jobs['job_role'] == role]
        test_designs.append(('Salary: cities within ' + role, role_jobs, 'city', 'salary_mid_annual'))
    for city in CITIES:
        city_jobs = jobs[jobs['city'] == city]
        test_designs.append(('Salary: roles within ' + city, city_jobs, 'job_role', 'salary_mid_annual'))

    # Include all bedrooms in the overall rental comparison.
    test_designs.append(('Rent: cities, all bedrooms', housing, 'city', 'monthly_rent_cad'))

    # Test each exact bedroom count only when all three cities have enough listings.
    bedroom_categories = sorted(housing['bedrooms'].dropna().unique())
    for bedrooms in bedroom_categories:
        bedroom_data = housing[housing['bedrooms'] == bedrooms]
        city_counts = bedroom_data.groupby('city').size().reindex(CITIES, fill_value=0)
        if (city_counts >= MIN_GROUP_SIZE).all():
            test_designs.append((f'Rent: cities, {bedrooms:g} bedroom(s)', bedroom_data, 'city', 'monthly_rent_cad'))
            print(f'Bedroom comparison included: {bedrooms:g}; counts: {city_counts.to_dict()}')
        else:
            print(f'Bedroom comparison skipped: {bedrooms:g}; counts: {city_counts.to_dict()}')

    omnibus_results = []
    pairwise_results = []
    for test_name, data, group_column, value_column in test_designs:
        # Prepare groups with enough valid observations.
        data = data.dropna(subset=[group_column, value_column])
        groups = {}
        for group_name, group in data.groupby(group_column):
            if len(group) >= MIN_GROUP_SIZE:
                groups[group_name] = group[value_column].to_numpy()
        if len(groups) < 2:
            continue

        group_values = list(groups.values())
        total_observations = sum(len(values) for values in group_values)
        number_of_groups = len(group_values)
        pooled_values = np.concatenate(group_values)
        if np.all(pooled_values == pooled_values[0]):
            continue

        # Kruskal-Wallis test and overall rank-based effect size.
        h_statistic, p_value = stats.kruskal(*group_values)
        eta_squared = max(0, (h_statistic - number_of_groups + 1) /
                          (total_observations - number_of_groups))
        omnibus_results.append({
            'test_name': test_name,
            'kruskal_wallis_h_statistic': h_statistic,
            'degrees_of_freedom': number_of_groups - 1,
            'p_value': p_value,
            'eta_squared_h': eta_squared,
            'total_observations': total_observations
        })

        # Dunn's test uses only the eligible groups. Adjust p-values later.
        eligible_data = data[data[group_column].isin(groups.keys())]
        dunn_p_values = sp.posthoc_dunn(
            eligible_data,
            val_col=value_column,
            group_col=group_column,
            p_adjust=None
        )

        # Record each unique pair and calculate Cliff's delta.
        for group_a, group_b in combinations(groups, 2):
            values_a = groups[group_a]
            values_b = groups[group_b]
            p_value = dunn_p_values.loc[group_a, group_b]
            u_statistic = stats.mannwhitneyu(values_a, values_b, alternative='two-sided').statistic
            cliffs_delta = 2 * u_statistic / (len(values_a) * len(values_b)) - 1
            median_a = np.median(values_a)
            median_b = np.median(values_b)
            pairwise_results.append({
                'test_name': test_name,
                'group_a': group_a,
                'group_b': group_b,
                'group_a_sample_size': len(values_a),
                'group_b_sample_size': len(values_b),
                'group_a_median': median_a,
                'group_b_median': median_b,
                'median_difference_a_minus_b': median_a - median_b,
                'p_value': p_value,
                'cliffs_delta': cliffs_delta
            })
    #Internal note: we found that when comparing multiple test, it is called omnibus =O
    omnibus_results = pd.DataFrame(omnibus_results)
    pairwise_results = pd.DataFrame(pairwise_results)
    # Adjust the two families separately, across all planned tests in each.
    if not omnibus_results.empty:
        omnibus_results['holm_adjusted_p_value'] = holm_correction(omnibus_results['p_value'])
        omnibus_results['significant_at_5_percent'] = omnibus_results['holm_adjusted_p_value'] <= 0.05
    if not pairwise_results.empty:
        pairwise_results['holm_adjusted_p_value'] = holm_correction(pairwise_results['p_value'])
        pairwise_results['significant_at_5_percent'] = pairwise_results['holm_adjusted_p_value'] <= 0.05
    return omnibus_results, pairwise_results

# ============================================================
# 5. AFFORDABILITY INDICATORS AND BOOTSTRAP CONFIDENCE INTERVALS
# ============================================================
def rent_burden(salary, rents):
    return np.median(rents) / (salary / 12) * 100

def affordable_share(salary, rents, threshold=AFFORDABILITY_THRESHOLD):
    budget = salary / 12 * threshold
    return np.mean(rents <= budget) * 100

def calculate_estimates(jobs, housing, iterations):
    # CI = confidence interval; pct = percentage; pp = percentage points.
    # Use the 2.5th and 97.5th bootstrap percentiles for pointwise 95% intervals.
    random_generator = np.random.default_rng(RANDOM_SEED)
    salaries = {}
    rents = {}
    bootstrap = {}
    rows = []
    for city in CITIES:
        city_rents = housing.loc[housing['city'] == city, 'monthly_rent_cad'].to_numpy()
        if len(city_rents) == 0:
            raise ValueError(f'No eligible rentals in {city}')
        rents[city] = np.sort(city_rents)
        # Reuse the same rental resamples for all occupations in a city.
        rent_samples = random_generator.choice(city_rents, size=(iterations, len(city_rents)), replace=True)
        for role in ROLES:
            group = jobs[(jobs['city'] == city) & (jobs['job_role'] == role)]
            values = group['salary_mid_annual'].to_numpy()
            if len(values) == 0:
                raise ValueError(f'No eligible salaries for {city}, {role}')
            salary = np.median(values)
            salaries[city, role] = salary
            salary_samples = random_generator.choice(values, size=(iterations, len(values)), replace=True)
            salary_medians = np.median(salary_samples, axis=1)
            bootstrap_rent_burdens = 1200 * np.median(rent_samples, axis=1) / salary_medians
            bootstrap_affordable_shares = 100 * np.mean(rent_samples <= salary_medians[:, None] / 12 * AFFORDABILITY_THRESHOLD, axis=1)
            bootstrap[city, role] = [bootstrap_rent_burdens, bootstrap_affordable_shares]
            rent_burden_ci_lower, rent_burden_ci_upper = np.percentile(bootstrap_rent_burdens, [2.5, 97.5])
            affordable_share_ci_lower, affordable_share_ci_upper = np.percentile(bootstrap_affordable_shares, [2.5, 97.5])
            rows.append({'city': city, 'job_role': role, 'job_listing_count': len(values),
                         'rental_listing_count': len(city_rents), 'median_annual_salary': salary,
                         'median_monthly_rent': np.median(city_rents),
                         'rent_burden_pct': rent_burden(salary, city_rents),
                         'affordable_listings_pct': affordable_share(salary, city_rents),
                         'rent_burden_95_ci_lower_pct': rent_burden_ci_lower, 'rent_burden_95_ci_upper_pct': rent_burden_ci_upper,
                         'affordable_listings_95_ci_lower_pct': affordable_share_ci_lower, 'affordable_listings_95_ci_upper_pct': affordable_share_ci_upper})
    return pd.DataFrame(rows), salaries, rents, bootstrap


def compare_affordability(salaries, rents, bootstrap):
    # Pointwise intervals for differences; not multiple-comparison adjusted.
    rows = []
    comparisons = []
    for role in ROLES:
        for a, b in combinations(CITIES, 2):
            comparisons.append(('cities_within_role', role, None, a, b, (a, role), (b, role)))
    for city in CITIES:
        for a, b in combinations(ROLES, 2):
            comparisons.append(('roles_within_city', None, city, a, b, (city, a), (city, b)))
    for kind, role, city, a, b, key_a, key_b in comparisons:
        for i, metric, function in [(0, 'rent_burden_pct', rent_burden), (1, 'affordable_listings_pct', affordable_share)]:
            difference = function(salaries[key_b], rents[key_b[0]]) - function(salaries[key_a], rents[key_a[0]])
            samples = bootstrap[key_b][i] - bootstrap[key_a][i]
            low, high = np.percentile(samples, [2.5, 97.5])
            rows.append({'comparison_type': kind, 'job_role': role, 'city': city,
                         'baseline_group': a, 'comparison_group': b, 'affordability_indicator': metric,
                         'comparison_minus_baseline_pp': difference, 'difference_95_ci_lower_pp': low, 'difference_95_ci_upper_pp': high})
    return pd.DataFrame(rows)

# ============================================================
# 6. AFFORDABILITY THRESHOLD SENSITIVITY ANALYSIS
# ============================================================
def threshold_sensitivity(salaries, rents):
    curves = []
    targets = []
    for city in CITIES:
        for role in ROLES:
            salary = salaries[city, role]
            city_rents = rents[city]
            for threshold in range(10, 76):
                share = affordable_share(salary, city_rents, threshold / 100)
                curves.append({'city': city, 'job_role': role, 'affordability_threshold_pct': threshold,
                               'affordable_listings_pct': share})
            # Exact empirical threshold needed to afford at least the target share.
            for target in [50, 75, 90]:
                index = int(np.ceil(target / 100 * len(city_rents))) - 1
                required_rent = city_rents[index]
                required_threshold = required_rent / (salary / 12) * 100
                targets.append({'city': city, 'job_role': role, 'target_affordable_listings_pct': target,
                                'required_salary_allocation_pct': required_threshold})
    return pd.DataFrame(curves), pd.DataFrame(targets)

# ============================================================
# 7. SHAPLEY DECOMPOSITION OF CITY AFFORDABILITY GAPS
# ============================================================
def shapley_decomposition(salaries, rents):
    rows = []
    for role in ROLES:
        for a, b in combinations(CITIES, 2):
            salary_a = salaries[a, role]
            salary_b = salaries[b, role]
            rent_a = rents[a]
            rent_b = rents[b]
            for metric, function in [('rent_burden_pct', rent_burden),
                                     ('affordable_listings_pct', affordable_share)]:
                baseline = function(salary_a, rent_a)
                rent_only_scenario = function(salary_a, rent_b)
                salary_only_scenario = function(salary_b, rent_a)
                final = function(salary_b, rent_b)
                salary_contribution = ((salary_only_scenario - baseline) + (final - rent_only_scenario)) / 2
                rental_market_contribution = ((rent_only_scenario - baseline) + (final - salary_only_scenario)) / 2
                affordability_gap = final - baseline
                assert np.isclose(salary_contribution + rental_market_contribution, affordability_gap)
                rows.append({'job_role': role, 'baseline_city': a, 'comparison_city': b,
                             'affordability_indicator': metric, 'baseline_indicator_pct': baseline, 'comparison_indicator_pct': final,
                             'salary_contribution_pp': salary_contribution, 'rental_market_contribution_pp': rental_market_contribution,
                             'total_affordability_gap_pp': affordability_gap})
    return pd.DataFrame(rows)

# ============================================================
# 8. RUN ANALYSIS AND EXPORT RESULTS
# ============================================================

root = Path(__file__).resolve().parent
if root.name == 'src':
    root = root.parent
parser = argparse.ArgumentParser()
parser.add_argument('--jobs', type=Path, default=root / 'data/jobs_clean.csv')
parser.add_argument('--housing', type=Path, default=root / 'data/Master_Housing_Dataset_V2.xlsx')
parser.add_argument('--output', type=Path, default=root / 'output/advanced_analysis')
parser.add_argument('--iterations', type=int, default=BOOTSTRAP_ITERATIONS)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
jobs, housing = load_data(args.jobs, args.housing)
jobs, housing = remove_outliers(jobs, housing)
tests, pairs = run_statistical_tests(jobs, housing)
summary, salaries, rents, bootstrap = calculate_estimates(jobs, housing, args.iterations)
gaps = compare_affordability(salaries, rents, bootstrap)
sensitivity, targets = threshold_sensitivity(salaries, rents)
decomposition = shapley_decomposition(salaries, rents)
tests.to_csv(args.output / '01_omnibus_tests.csv', index=False)
pairs.to_csv(args.output / '02_dunn_pairwise.csv', index=False)
summary.to_csv(args.output / '03_affordability_estimates.csv', index=False)
sensitivity.to_csv(args.output / '04_threshold_sensitivity.csv', index=False)
gaps.to_csv(args.output / '05_bootstrap_gaps.csv', index=False)
decomposition.to_csv(args.output / '06_shapley_decomposition.csv', index=False)
targets.to_csv(args.output / '07_required_thresholds.csv', index=False)
print('\nResults saved to:', args.output)
print(summary.round(2).to_string(index=False))



