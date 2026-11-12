import pandas as pd
import numpy as np

def clean_support_df1(filepath):
    spdf1 = pd.read_csv(filepath)
    # Cleaning code, in construction

    return spdf1

def clean_support_df2(filepath):
    spdf2 = pd.read_csv(filepath)
    # Cleaning code, in construction
    
    return spdf2

def clean_support_df3(filepath):
    spdf3 = pd.read_csv(filepath)
    # Cleaning code, in construction
    
    return spdf3

def clean_support_df4(filepath):
    spdf4 = pd.read_csv(filepath)
    # Cleaning code, in construction
    
    return spdf4

def clean_support_df5(filepath):
    spdf5 = pd.read_csv(filepath)
    # Cleaning code, in construction
    
    return spdf5





# TESTING (To erase after the functions return the expected results)
spdf1 = clean_support_df1("data/support_dataset1_data_job_wages.csv")
spdf2 = clean_support_df2("data/support_dataset2_quaterly_asking_rent.csv")
spdf3 = clean_support_df3("data/support_dataset3_average_rents_by_population.csv")
spdf4 = clean_support_df4("data/support_dataset4_labour_force_characteristics.csv")
spdf5 = clean_support_df5("data/support_dataset5_overall_job_vacancies.csv")

print(spdf1)