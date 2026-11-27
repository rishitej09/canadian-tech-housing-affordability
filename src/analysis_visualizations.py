"""Reusable Plotly figures for the capstone report and Streamlit dashboard."""
from pathlib import Path
import argparse
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuration and result files
CITIES = ['Montreal', 'Toronto', 'Vancouver']
ROLES = ['Data Analyst', 'Data Engineer', 'Data Scientist']
CITY_COLORS = {'Montreal': '#F2B66D', 'Toronto': '#4DB6AC', 'Vancouver': '#5B9BD5'}
CITY_SYMBOLS = {'Montreal': 'circle', 'Toronto': 'square', 'Vancouver': 'diamond'}
METRICS = {'rent_burden_pct': 'Estimated rent burden',
           'affordable_listings_pct': 'Affordable rental listings'}
CI_COLUMNS = {'rent_burden_pct': ('rent_burden_95_ci_lower_pct', 'rent_burden_95_ci_upper_pct'),
              'affordable_listings_pct': ('affordable_listings_95_ci_lower_pct', 'affordable_listings_95_ci_upper_pct')}
FILES = {'tests': '01_omnibus_tests.csv', 'pairs': '02_dunn_pairwise.csv',
         'estimates': '03_affordability_estimates.csv', 'sensitivity': '04_threshold_sensitivity.csv',
         'gaps': '05_bootstrap_gaps.csv', 'shapley': '06_shapley_decomposition.csv',
         'targets': '07_required_thresholds.csv'}
PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == 'src':
    PROJECT_DIR = PROJECT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'output' / 'advanced_analysis'
FIGURES_DIR = PROJECT_DIR / 'output' / 'report_figures'

# Load results in a dictionary
def load_results(results_dir=RESULTS_DIR):
    results = {}
    for name, filename in FILES.items():
        results[name] = pd.read_csv(Path(results_dir) / filename)
    return results

def format_figure(fig, title, height=470):
    fig.update_layout(template='plotly_white', title=dict(text=title, x=0.02),
                      font=dict(size=13, color='#243447'), height=height,
                      margin=dict(l=30, r=35, t=85, b=75),
                      legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center'),
                      hoverlabel=dict(font_size=12))
    return fig

# 2. Dunn pairwise comparisons: effect sizes and adjusted significance
def pairwise_heatmap(pairs, comparison_type='Across cities'):
    if comparison_type == 'Across cities':
        names = ['Salary: cities within ' + role for role in ROLES] + ['Rent: cities, all bedrooms']
        labels = ROLES + ['Rental costs']
        groups = CITIES
    elif comparison_type == 'Across occupations':
        names = ['Salary: roles within ' + city for city in CITIES]
        labels = CITIES
        groups = sorted(ROLES)
    else:
        names = [name for name in pairs['test_name'].unique() if name.startswith('Rent: cities,')]
        labels = [name.replace('Rent: cities, ', '') for name in names]
        groups = CITIES
    from itertools import combinations
    group_pairs = list(combinations(groups, 2))
    columns = [a + ' vs. ' + b for a, b in group_pairs]
    values, annotations, hover = [], [], []
    for name in names:
        effect_row, text_row, hover_row = [], [], []
        for a, b in group_pairs:
            row = pairs[(pairs['test_name'] == name) & (pairs['group_a'] == a) & (pairs['group_b'] == b)]
            direction = 1
            if row.empty:
                row = pairs[(pairs['test_name'] == name) & (pairs['group_a'] == b) & (pairs['group_b'] == a)]
                direction = -1
            if row.empty:
                effect_row.append(None); text_row.append('N/A'); hover_row.append('Not tested')
                continue
            record = row.iloc[0]
            effect = direction * record['cliffs_delta']
            p = record['holm_adjusted_p_value']
            effect_row.append(effect)
            text_row.append(f'{effect:+.3f}' + ('*' if p <= .05 else ''))
            hover_row.append(f'{name}<br>{a} vs. {b}<br>Cliff’s delta: {effect:+.3f}<br>Adjusted p: {p:.3g}<br>Median difference: ${direction * record["median_difference_a_minus_b"]:,.0f}')
        values.append(effect_row); annotations.append(text_row); hover.append(hover_row)
    fig = go.Figure(go.Heatmap(z=values, x=columns, y=labels, zmin=-1, zmax=1,
                    colorscale='RdBu_r', text=annotations, texttemplate='%{text}',
                    customdata=hover, hovertemplate='%{customdata}<extra></extra>',
                    colorbar=dict(title='Cliff’s delta')))
    fig.update_yaxes(autorange='reversed')
    fig.update_layout(xaxis_title='First group vs. second group')
    return format_figure(fig, 'Pairwise differences: Cliff’s delta (* adjusted p ≤ 0.05)', 430)


# 3. Forest plots: point estimates and bootstrap confidence intervals
def affordability_forest(estimates, metric):
    lower, upper = CI_COLUMNS[metric]
    fig = go.Figure()
    labels = [role + ' | ' + city for role in ROLES for city in CITIES]
    for city in CITIES:
        data = estimates[estimates['city'] == city].copy()
        data['label'] = data['job_role'] + ' | ' + data['city']
        # Draw interval endpoints directly, including intervals not containing the estimate.
        for _, row in data.iterrows():
            fig.add_trace(go.Scatter(x=[row[lower], row[upper]], y=[row['label']]*2,
                          mode='lines', line=dict(color=CITY_COLORS[city], width=3),
                          showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=data[metric], y=data['label'], mode='markers', name=city,
                      marker=dict(color=CITY_COLORS[city], symbol=CITY_SYMBOLS[city], size=11, line=dict(color='#243447', width=.6)),
                      customdata=data[[lower, upper, 'median_annual_salary', 'median_monthly_rent']].to_numpy(),
                      hovertemplate='%{y}<br>Estimate: %{x:.2f}%<br>95% CI: %{customdata[0]:.2f}% to %{customdata[1]:.2f}%<br>Median salary: $%{customdata[2]:,.0f}<br>Median rent: $%{customdata[3]:,.0f}<extra></extra>'))
    fig.update_yaxes(categoryorder='array', categoryarray=labels[::-1])
    fig.update_xaxes(title=METRICS[metric]+' (%)', ticksuffix='%', rangemode='tozero')
    if metric == 'rent_burden_pct':
        fig.add_vline(x=30, line_dash='dash', line_color='#D97757', annotation_text='30% benchmark')
    else:
        fig.update_xaxes(range=[0, 100])
    return format_figure(fig, METRICS[metric] + ' with 95% bootstrap intervals', 520)


# 4. Change the reference city without rerunning the statistical analysis
def reference_comparisons(data, baseline, kind):
    data = data.copy()
    if kind == 'gaps':
        data = data[data['comparison_type'] == 'cities_within_role'].copy()
        first, second = 'baseline_group', 'comparison_group'
    else:
        first, second = 'baseline_city', 'comparison_city'
    data = data[(data[first] == baseline) | (data[second] == baseline)].copy()
    reverse = data[second] == baseline
    data.loc[reverse, [first, second]] = data.loc[reverse, [second, first]].to_numpy()
    if kind == 'gaps':
        gap = 'comparison_minus_baseline_pp'
        low, high = 'difference_95_ci_lower_pp', 'difference_95_ci_upper_pp'
        data.loc[reverse, gap] *= -1
        data.loc[reverse, [low, high]] = -data.loc[reverse, [high, low]].to_numpy()
    else:
        columns = ['salary_contribution_pp', 'rental_market_contribution_pp', 'total_affordability_gap_pp']
        data.loc[reverse, columns] *= -1
        a, b = 'baseline_indicator_pct', 'comparison_indicator_pct'
        data.loc[reverse, [a, b]] = data.loc[reverse, [b, a]].to_numpy()
    return data

def gap_forest(gaps, baseline='Toronto', metric='rent_burden_pct'):
    data = reference_comparisons(gaps, baseline, 'gaps')
    data = data[data['affordability_indicator'] == metric].copy()
    data['label'] = data['job_role'] + ' | ' + data['comparison_group']
    fig = go.Figure()
    for city in CITIES:
        if city == baseline: continue
        subset = data[data['comparison_group'] == city]
        for _, row in subset.iterrows():
            fig.add_trace(go.Scatter(x=[row['difference_95_ci_lower_pp'], row['difference_95_ci_upper_pp']], y=[row['label']]*2,
                          mode='lines', line=dict(color=CITY_COLORS[city], width=3), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=subset['comparison_minus_baseline_pp'], y=subset['label'], mode='markers', name=city,
                      marker=dict(color=CITY_COLORS[city], symbol=CITY_SYMBOLS[city], size=11),
                      customdata=subset[['difference_95_ci_lower_pp','difference_95_ci_upper_pp']].to_numpy(),
                      hovertemplate='%{y}<br>Difference: %{x:+.2f} pp<br>95% CI: %{customdata[0]:+.2f} to %{customdata[1]:+.2f} pp<extra></extra>'))
    fig.add_vline(x=0, line_dash='dash', line_color='#65758B')
    fig.update_yaxes(categoryorder='array', categoryarray=[r+' | '+c for r in ROLES for c in CITIES if c != baseline][::-1])
    fig.update_xaxes(title='Comparison city minus '+baseline+' (percentage points)', ticksuffix=' pp')
    return format_figure(fig, METRICS[metric]+' relative to '+baseline, 450)


# 5. Threshold sensitivity: precomputed grid, not a smoothed curve
def sensitivity_curves(sensitivity, threshold=30):
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=ROLES, horizontal_spacing=.07)
    for index, role in enumerate(ROLES, start=1):
        for city in CITIES:
            data = sensitivity[(sensitivity['city'] == city) & (sensitivity['job_role'] == role)].sort_values('affordability_threshold_pct')
            fig.add_trace(go.Scatter(x=data['affordability_threshold_pct'], y=data['affordable_listings_pct'],
                          mode='lines', line=dict(color=CITY_COLORS[city], width=2.5, shape='hv'), name=city,
                          legendgroup=city, showlegend=index==1,
                          hovertemplate=city+'<br>Salary allocation: %{x}%<br>Affordable listings: %{y:.1f}%<extra></extra>'), row=1, col=index)
            selected = data[data['affordability_threshold_pct'] == threshold]
            fig.add_trace(go.Scatter(x=selected['affordability_threshold_pct'], y=selected['affordable_listings_pct'], mode='markers',
                          marker=dict(color=CITY_COLORS[city], size=8), showlegend=False, legendgroup=city,
                          hovertemplate=city+'<br>%{x}% budget: %{y:.1f}% affordable<extra></extra>'), row=1, col=index)
        fig.add_vline(x=threshold, line_dash='dash', line_color='#D97757', row=1, col=index)
    fig.update_xaxes(title='Salary allocation (%)', ticksuffix='%', range=[10,75])
    fig.update_yaxes(ticksuffix='%', range=[0,100])
    fig.update_yaxes(title='Affordable rentals (%)', row=1, col=1)
    return format_figure(fig, f'Rental market accessibility at alternative thresholds ({threshold}% highlighted)', 460)


# 6. Required income allocation heatmap
def required_allocation_heatmap(targets, target=75):
    data = targets[targets['target_affordable_listings_pct'] == target]
    matrix = data.pivot(index='job_role', columns='city', values='required_salary_allocation_pct').reindex(index=ROLES, columns=CITIES)
    # Fixed scale centered at the reference threshold (30%).
    max_value = max(60, float(targets['required_salary_allocation_pct'].max()))
    midpoint = 30 / max_value
    colors = [[0, '#32998D'], [midpoint, '#F5F5F5'], [1, '#D97757']]
    fig = go.Figure(go.Heatmap(z=matrix.to_numpy(), x=CITIES, y=ROLES,
                    zmin=0, zmax=max_value, colorscale=colors, texttemplate='%{z:.1f}%',
                    colorbar=dict(title='Salary allocation', ticksuffix='%'),
                    hovertemplate='%{y} | %{x}<br>Required gross salary: %{z:.2f}%<extra></extra>'))
    fig.update_yaxes(autorange='reversed')
    return format_figure(fig, f'Income allocation required to afford at least {target}% of rental listings', 400)


# 7. Shapley decomposition: contributions and net difference
def shapley_chart(shapley, baseline='Toronto', metric='rent_burden_pct'):
    data = reference_comparisons(shapley, baseline, 'shapley')
    data = data[data['affordability_indicator'] == metric].copy()
    data['label'] = data['job_role'] + ' | ' + data['comparison_city']
    fig = go.Figure()
    for column, name, color in [('salary_contribution_pp', 'Salary contribution', '#319B91'),
                                ('rental_market_contribution_pp', 'Rental market contribution', '#D97757')]:
        fig.add_trace(go.Bar(x=data[column], y=data['label'], orientation='h', name=name,
                      marker_color=color, hovertemplate='%{y}<br>'+name+': %{x:+.2f} pp<extra></extra>'))
    fig.add_trace(go.Scatter(x=data['total_affordability_gap_pp'], y=data['label'], mode='markers', name='Net gap',
                  marker=dict(symbol='diamond', size=11, color='#243447', line=dict(color='white',width=1)),
                  hovertemplate='%{y}<br>Net gap: %{x:+.2f} pp<extra></extra>'))
    fig.update_layout(barmode='relative')
    fig.add_vline(x=0, line_color='#65758B', line_dash='dash')
    fig.update_yaxes(categoryorder='array', categoryarray=[r+' | '+c for r in ROLES for c in CITIES if c != baseline][::-1])
    fig.update_xaxes(title='Contribution to difference vs. '+baseline+' (percentage points)', ticksuffix=' pp')
    return format_figure(fig, METRICS[metric]+' decomposition relative to '+baseline, 460)


# 8. Static report exports: seven figure groups, nine individual images.
def report_figures(results):
    return {
        '01_pairwise_effect_sizes': pairwise_heatmap(results['pairs']),
        '02_rent_burden_intervals': affordability_forest(results['estimates'], 'rent_burden_pct'),
        '03_affordable_listings_intervals': affordability_forest(results['estimates'], 'affordable_listings_pct'),
        '04a_rent_burden_gaps': gap_forest(results['gaps']),
        '04b_affordable_listings_gaps': gap_forest(results['gaps'], metric='affordable_listings_pct'),
        '05_threshold_sensitivity': sensitivity_curves(results['sensitivity']),
        '06_required_salary_allocation': required_allocation_heatmap(results['targets']),
        '07a_shapley_rent_burden': shapley_chart(results['shapley']),
        '07b_shapley_affordable_listings': shapley_chart(results['shapley'], metric='affordable_listings_pct')}


def export_figures(results_dir=RESULTS_DIR, output_dir=FIGURES_DIR, html_only=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = report_figures(load_results(results_dir))
    for filename, fig in figures.items():
        fig.write_html(output_dir / (filename+'.html'), include_plotlyjs=True)
        if not html_only:
            # SVG is resolution independent; PNG is 3x for report use.
            fig.write_image(output_dir / (filename+'.svg'), width=1200, height=fig.layout.height)
            fig.write_image(output_dir / (filename+'.png'), width=1200, height=fig.layout.height, scale=3)
    print('Figures exported to:', output_dir)

# To make it reusable for dashboard
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path, default=RESULTS_DIR)
    parser.add_argument('--output', type=Path, default=FIGURES_DIR)
    parser.add_argument('--html-only', action='store_true')
    args = parser.parse_args()
    export_figures(args.results, args.output, args.html_only)
