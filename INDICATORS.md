Following the papers used, it was decided to use a threshold of 30% as the acceptable limit for the rent burden, and the median per city and in general.

##############################################
job_affordability_indicators.csv: indicators calculated for each job posting. This dataset is basically the same as jobs_clean.csv with the addition of the indicators calculation.
----------------------------------------------
New columns per city
city_rent_burden_pct		Percentage of the job's gross annual salary needed to pay the median monthly rent in that city. Lower is better. For example, 42% means that 42% of the Salary is required to pay the median rent.
city_affordable_listings_pct	Percentage of rental listings in that city that cost no more than 30% of the job's gross monthly salary. Higher is better. For example, 20% means that only 20% of the published housing entries can be paid using the poster Salary.
city_affordable_listings_count	Number of rental listings in that city that meet the 30% affordability threshold for that job's salary.
city_total_rental_listings	Total number of rental listings in that city included in the calculation.
----------------------------------------------
New pooled columns (using all the housing dataset)
pooled_rent_burden_pct			Percentage of the job's gross salary needed to cover the median monthly rent across the combined rental sample.
pooled_affordable_listings_pct		Percentage of all included rental listings across the three cities that meet the 30% affordability threshold for that job.
pooled_affordable_listings_count	Number of affordable listings across the three-city rental sample for that salary.
pooled_total_rental_listings		Total number of rental listings used in the pooled calculation.
----------------------------------------------
##############################################
New Dataset with the summary of hte indicators
affordability_summary.csv: summarizing the results for the three occupations across the three cities.
----------------------------------------------
city			City being analyzed
job_role		Data Analyst, Data Scientist, or Data Engineer.
job_count		Number of job records included in that city-occupation group.
median_annual_salary	Median annual advertised salary for jobs in that group.
rent_burden_pct		Percentage of that median salary needed to pay the city's median monthly rent. Lower is better.
affordable_listings_pct	Percentage of the city's rental listings considered affordable at that occupation's median salary. Higher is better.
affordable_listings_count	Number of rental listings that meet the threshold for that city's occupation-specific median salary.
total_rental_listings	Total number of rental listings included for that city.
median_monthly_rent	Median monthly rental price for the included housing listings in that city.
----------------------------------------------