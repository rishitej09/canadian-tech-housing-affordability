import pandas as pd
import numpy as np

def clean_support_df1(filepath):
    spdf1_raw = pd.read_csv(filepath)
    spdf1_clean = spdf1_raw.copy()

    # Standardize column names
    spdf1_clean.columns = [
        "title",
        "city",
        "salary_min_hourly",
        "salary_mid_hourly",
        "salary_max_hourly",
        "job_prospects_rating",
        "job_prospects_meaning",
        "noc_id"
        ]

    # Trim any spaces found in the beginning or end of the string values from each text column
    spdf1_clean["title"] = spdf1_clean["title"].str.strip()
    spdf1_clean["city"] = spdf1_clean["city"].str.strip()
    spdf1_clean["salary_min_hourly"] = spdf1_clean["salary_min_hourly"].str.strip()
    spdf1_clean["salary_mid_hourly"] = spdf1_clean["salary_mid_hourly"].str.strip()
    spdf1_clean["salary_max_hourly"] = spdf1_clean["salary_max_hourly"].str.strip()
    spdf1_clean["job_prospects_meaning"] = spdf1_clean["job_prospects_meaning"].str.strip()
    
    # Standardize "title" and "city" values
    spdf1_clean["title"] = spdf1_clean["title"].str.replace({"Business Data Analyst":"Data Analyst"})
    spdf1_clean["city"] = spdf1_clean["city"].str.replace({"Vancouver Island and Coast Region":"Vancouver",
                                                       "Toronto Region":"Toronto",
                                                       "Montréal Region":"Montreal"})

    # Create "province" column based on "city"
    spdf1_clean["province"] = spdf1_clean["city"]
    spdf1_clean["province"] = spdf1_clean["province"].str.replace("Vancouver","BC")
    spdf1_clean["province"] = spdf1_clean["province"].str.replace("Toronto","ON")
    spdf1_clean["province"] = spdf1_clean["province"].str.replace("Montreal","QC")
    
    # Delete "$" sign from hourly salaries columns
    spdf1_clean["salary_min_hourly"] = spdf1_clean["salary_min_hourly"].str.replace("$","")
    spdf1_clean["salary_mid_hourly"] = spdf1_clean["salary_mid_hourly"].str.replace("$","")
    spdf1_clean["salary_max_hourly"] = spdf1_clean["salary_max_hourly"].str.replace("$","")

    # Specify hourly salaries columns as float type
    spdf1_clean["salary_min_hourly"] = spdf1_clean["salary_min_hourly"].astype(float)
    spdf1_clean["salary_mid_hourly"] = spdf1_clean["salary_mid_hourly"].astype(float)
    spdf1_clean["salary_max_hourly"] = spdf1_clean["salary_max_hourly"].astype(float)

    # Create a calculation for annual salaries based on the hourly wages
    # Formula: annual salary = hourly salary * work hours per week * weeks per year = hourly salary * 40 * 52
    spdf1_clean["salary_min_annual"] = spdf1_clean["salary_min_hourly"] * 40 * 52
    spdf1_clean["salary_mid_annual"] = spdf1_clean["salary_mid_hourly"] * 40 * 52
    spdf1_clean["salary_max_annual"] = spdf1_clean["salary_max_hourly"] * 40 * 52
    spdf1_clean["salary_min_annual"] = spdf1_clean["salary_min_annual"].round(0).astype("int64[pyarrow]")
    spdf1_clean["salary_mid_annual"] = spdf1_clean["salary_mid_annual"].round(0).astype("int64[pyarrow]")
    spdf1_clean["salary_max_annual"] = spdf1_clean["salary_max_annual"].round(0).astype("int64[pyarrow]")

    spdf1_clean = spdf1_clean.drop_duplicates()

    spdf1_clean = spdf1_clean.reset_index(drop=True)

    return spdf1_raw, spdf1_clean





def clean_support_df2(filepath):
    spdf2_raw = pd.read_csv(filepath)
    spdf2_clean = spdf2_raw.copy()

    # Standardize column names
    spdf2_clean.columns = [
        "city",
        "building_type",
        "quarter",
        "monthly_rent_cad"
        ]

    # Trim any spaces found in the beginning or end of the string values from each text column
    spdf2_clean["city"] = spdf2_clean["city"].str.strip()
    spdf2_clean["building_type"] = spdf2_clean["building_type"].str.strip()
    spdf2_clean["quarter"] = spdf2_clean["quarter"].str.strip()
    
    # Standardize "city" values
    spdf2_clean["city"] = spdf2_clean["city"].str.replace({"Vancouver, Census metropolitan area (CMA)":"Vancouver",
                                                           "Toronto, Census metropolitan area (CMA)":"Toronto",
                                                           "Montréal, Census metropolitan area (CMA)":"Montreal"})

    # # Create "province" column based on "city"
    spdf2_clean["province"] = spdf2_clean["city"]
    spdf2_clean["province"] = spdf2_clean["province"].str.replace("Vancouver","BC")
    spdf2_clean["province"] = spdf2_clean["province"].str.replace("Toronto","ON")
    spdf2_clean["province"] = spdf2_clean["province"].str.replace("Montreal","QC")

    # Replace ".." entries in monthly rent column with NA
    spdf2_clean["monthly_rent_cad"] = spdf2_clean["monthly_rent_cad"].str.replace("..","0")
    spdf2_clean["monthly_rent_cad"] = spdf2_clean["monthly_rent_cad"].str.replace(",","")
    spdf2_clean["monthly_rent_cad"] = spdf2_clean["monthly_rent_cad"].astype("int64[pyarrow]")
    spdf2_clean["monthly_rent_cad"] = spdf2_clean["monthly_rent_cad"].replace(0,np.nan)
    spdf2_clean = spdf2_clean.dropna()

    # Create a calculation for annual rent based on the monthly rent
    spdf2_clean["annual_rent_cad"] = spdf2_clean["monthly_rent_cad"]
    spdf2_clean["annual_rent_cad"] = spdf2_clean["annual_rent_cad"] * 12

    # Separate building_type to have the builting type and the number of bedrooms (named "bedrooms")
    spdf2_clean["bedrooms"] = spdf2_clean["building_type"]
    spdf2_clean["building_type"] = spdf2_clean["building_type"].str.replace({'House - 2 bedrooms':'House',
                                                                             'House - 3 or more bedrooms':'House',
                                                                             'Apartment - No bedroom':'Apartment',
                                                                             'Apartment - 1 bedroom':'Apartment',
                                                                             'Apartment - 2 bedrooms':'Apartment',
                                                                             'Apartment - 3 or more bedrooms':'Apartment',
                                                                             'Room':'Room'})
    spdf2_clean["bedrooms"] = spdf2_clean["bedrooms"].str.replace({'House - 2 bedrooms':'2',
                                                                   'House - 3 or more bedrooms':'3',
                                                                   'Apartment - No bedroom':'0',
                                                                   'Apartment - 1 bedroom':'1',
                                                                   'Apartment - 2 bedrooms':'2',
                                                                   'Apartment - 3 or more bedrooms':'3',
                                                                   'Room':'1'})
    spdf2_clean["bedrooms"] = spdf2_clean["bedrooms"].astype("int64[pyarrow]")

    # Filter the data to the most recent complete years
    spdf2_clean = spdf2_clean[spdf2_clean["quarter"].str[-4:].astype(int).between(2021, 2025)]

    spdf2_clean = spdf2_clean.drop_duplicates()

    spdf2_clean = spdf2_clean.reset_index(drop=True)
    
    return spdf2_raw, spdf2_clean





def clean_support_df3(filepath):
    spdf3_raw = pd.read_csv(filepath)
    spdf3_clean = spdf3_raw.copy()

    # Standardize column names
    spdf3_clean.columns = [
        'building_type',
        'bedrooms',
        'year',
        'Montreal',
        'Toronto',
        'Vancouver'
        ]

    # Trim any spaces found in the beginning or end of the string values from each text column
    spdf3_clean["building_type"] = spdf3_clean["building_type"].str.strip()
    spdf3_clean["bedrooms"] = spdf3_clean["bedrooms"].str.strip()
    spdf3_clean["Montreal"] = spdf3_clean["Montreal"].str.strip()
    spdf3_clean["Toronto"] = spdf3_clean["Toronto"].str.strip()
    spdf3_clean["Vancouver"] = spdf3_clean["Vancouver"].str.strip()

    # Create "structure" column based on "building_type" and standardize "bedrooms"
    spdf3_clean["building_structure"] = spdf3_clean["building_type"]
    spdf3_clean["building_type"] = spdf3_clean["building_type"].str.replace({
        'Row structures of three units and over':'Row / Townhouse',
        'Apartment structures of three units and over':'Apartment',
        'Apartment structures of six units and over':'Apartment'})
    spdf3_clean["building_structure"] = spdf3_clean["building_structure"].str.replace({
        'Row structures of three units and over':'Three units and over',
        'Apartment structures of three units and over':'Three units and over',
        'Apartment structures of six units and over':'Six units and over'})
    spdf3_clean["bedrooms"] = spdf3_clean["bedrooms"].str.replace({'One bedroom units':'1',
                                                                   'Two bedroom units':'2',
                                                                   'Three bedroom units':'3'})

    # Replace "F" entries in "Montreal", "Toronto" & "Vancouver" columns with NA
    spdf3_clean["Montreal"] = spdf3_clean["Montreal"].str.replace("F","0")
    spdf3_clean["Toronto"] = spdf3_clean["Toronto"].str.replace("F","0")
    spdf3_clean["Vancouver"] = spdf3_clean["Vancouver"].str.replace("F","0")

    spdf3_clean["Montreal"] = spdf3_clean["Montreal"].str.replace(",","")
    spdf3_clean["Toronto"] = spdf3_clean["Toronto"].str.replace(",","")
    spdf3_clean["Vancouver"] = spdf3_clean["Vancouver"].str.replace(",","")

    spdf3_clean["Montreal"] = spdf3_clean["Montreal"].astype("int64[pyarrow]")
    spdf3_clean["Toronto"] = spdf3_clean["Toronto"].astype("int64[pyarrow]")
    spdf3_clean["Vancouver"] = spdf3_clean["Vancouver"].astype("int64[pyarrow]")

    spdf3_clean["Montreal"] = spdf3_clean["Montreal"].replace(0,np.nan)
    spdf3_clean["Toronto"] = spdf3_clean["Toronto"].replace(0,np.nan)
    spdf3_clean["Vancouver"] = spdf3_clean["Vancouver"].replace(0,np.nan)
    
    spdf3_clean = spdf3_clean.dropna()

    # Turn each city into separate datasets and concatenate all to have a single dataset
    spdf3_clean_Montreal = spdf3_clean[["building_type","bedrooms","building_structure","year","Montreal"]]
    spdf3_clean_Montreal["city"] = "Montreal"
    spdf3_clean_Montreal["province"] = "QC"
    spdf3_clean_Montreal.columns = ["building_type","bedrooms","building_structure","year","monthly_rent_cad","city","province"]

    spdf3_clean_Toronto = spdf3_clean[["building_type","bedrooms","building_structure","year","Toronto"]]
    spdf3_clean_Toronto["city"] = "Toronto"
    spdf3_clean_Toronto["province"] = "ON"
    spdf3_clean_Toronto.columns = ["building_type","bedrooms","building_structure","year","monthly_rent_cad","city","province"]

    spdf3_clean_Vancouver = spdf3_clean[["building_type","bedrooms","building_structure","year","Vancouver"]]
    spdf3_clean_Vancouver["city"] = "Vancouver"
    spdf3_clean_Vancouver["province"] = "BC"
    spdf3_clean_Vancouver.columns = ["building_type","bedrooms","building_structure","year","monthly_rent_cad","city","province"]

    spdf3_clean = pd.concat([spdf3_clean_Montreal, spdf3_clean_Toronto, spdf3_clean_Vancouver], ignore_index=True)

    # Create a calculation for annual rent based on the monthly rent
    spdf3_clean["annual_rent_cad"] = spdf3_clean["monthly_rent_cad"]
    spdf3_clean["annual_rent_cad"] = spdf3_clean["annual_rent_cad"] * 12

    # Filter the data to the most recent complete years
    spdf3_clean = spdf3_clean[spdf3_clean["year"].between(2021, 2025)]

    spdf3_clean = spdf3_clean.drop_duplicates()

    spdf3_clean = spdf3_clean.reset_index(drop=True)

    return spdf3_raw, spdf3_clean





def clean_support_df4(filepath):
    spdf4_raw = pd.read_csv(filepath)
    spdf4_clean = spdf4_raw.copy()

    # Standardize column names
    spdf4_clean.columns = [
        "city",
        "quarter",
        "job_vacancies",
        "payroll_employees",
        "job_vacancy_rate",
        "salary_average_hourly"
        ]

    # Trim any spaces found in the beginning or end of the string values from each text column
    spdf4_clean["city"] = spdf4_clean["city"].str.strip()
    spdf4_clean["quarter"] = spdf4_clean["quarter"].str.strip()
    spdf4_clean["job_vacancies"] = spdf4_clean["job_vacancies"].str.strip()
    spdf4_clean["payroll_employees"] = spdf4_clean["payroll_employees"].str.strip()
    spdf4_clean["job_vacancy_rate"] = spdf4_clean["job_vacancy_rate"].str.strip()
    spdf4_clean["salary_average_hourly"] = spdf4_clean["salary_average_hourly"].str.strip()
    
    # Standardize "title" and "city" values
    spdf4_clean["city"] = spdf4_clean["city"].str.replace({"Vancouver Island and Coast, British Columbia":"Vancouver",
                                                           "Toronto, Ontario":"Toronto",
                                                           "Montréal, Quebec":"Montreal"})

    # Create "province" column based on "city"
    spdf4_clean["province"] = spdf4_clean["city"]
    spdf4_clean["province"] = spdf4_clean["province"].str.replace("Vancouver","BC")
    spdf4_clean["province"] = spdf4_clean["province"].str.replace("Toronto","ON")
    spdf4_clean["province"] = spdf4_clean["province"].str.replace("Montreal","QC")
    
    # Delete "," sign from "job_vacancies" and "payroll_employees" column
    spdf4_clean["job_vacancies"] = spdf4_clean["job_vacancies"].str.replace(",","")
    spdf4_clean["payroll_employees"] = spdf4_clean["payroll_employees"].str.replace(",","")

    # Replace ".." entries in job_vacancies, payroll_employees, job_vacancy_rate and salary_average_hourly columns with NA
    spdf4_clean["job_vacancies"] = spdf4_clean["job_vacancies"].str.replace("..","0")
    spdf4_clean["job_vacancies"] = spdf4_clean["job_vacancies"].astype("int64[pyarrow]")
    spdf4_clean["job_vacancies"] = spdf4_clean["job_vacancies"].replace(0,np.nan)

    spdf4_clean["payroll_employees"] = spdf4_clean["payroll_employees"].str.replace("..","0")
    spdf4_clean["payroll_employees"] = spdf4_clean["payroll_employees"].astype("int64[pyarrow]")
    spdf4_clean["payroll_employees"] = spdf4_clean["payroll_employees"].replace(0,np.nan)

    spdf4_clean["job_vacancy_rate"] = spdf4_clean["job_vacancy_rate"].str.replace("..","0")
    spdf4_clean["job_vacancy_rate"] = spdf4_clean["job_vacancy_rate"].astype(float)
    spdf4_clean["job_vacancy_rate"] = spdf4_clean["job_vacancy_rate"].replace(0,np.nan)

    spdf4_clean["salary_average_hourly"] = spdf4_clean["salary_average_hourly"].str.replace("..","0")
    spdf4_clean["salary_average_hourly"] = spdf4_clean["salary_average_hourly"].astype(float)
    spdf4_clean["salary_average_hourly"] = spdf4_clean["salary_average_hourly"].replace(0,np.nan)

    # Create a calculation for annual salaries based on the hourly salary
    # Formula: annual salary = hourly salary * work hours per week * weeks per year = hourly salary * 40 * 52
    spdf4_clean["salary_average_annually"] = spdf4_clean["salary_average_hourly"] * 40 * 52

    # Filter the data to the most recent complete years
    spdf4_clean = spdf4_clean[spdf4_clean["quarter"].str[-4:].astype(int).between(2021, 2025)]

    spdf4_clean = spdf4_clean.dropna()

    spdf4_clean = spdf4_clean.drop_duplicates()

    spdf4_clean = spdf4_clean.reset_index(drop=True)
    
    return spdf4_raw, spdf4_clean



# spdf1_raw, spdf1_clean = clean_support_df1("data/support_dataset1_data_job_wages.csv")
# spdf2_raw, spdf2_clean = clean_support_df2("data/support_dataset2_quaterly_asking_rent.csv")
# spdf3_raw, spdf3_clean = clean_support_df3("data/support_dataset3_average_rents_by_population.csv")
# spdf4_raw, spdf4_clean = clean_support_df4("data/support_dataset4_overall_job_vacancies.csv")

# spdf1_clean.to_csv("data/support_dataset1_clean.csv", index=False)
# spdf2_clean.to_csv("data/support_dataset2_clean.csv", index=False)
# spdf3_clean.to_csv("data/support_dataset3_clean.csv", index=False)
# spdf4_clean.to_csv("data/support_dataset4_clean.csv", index=False)