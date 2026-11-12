import pandas as pd
import numpy as np
from config import (SPDF1_FILEPATHCSV,
                    SPDF2_FILEPATHCSV,
                    SPDF3_FILEPATHCSV,
                    SPDF4_FILEPATHCSV,
                    SPDF5_FILEPATHCSV)

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
spdf1 = clean_support_df1(SPDF1_FILEPATHCSV)
spdf2 = clean_support_df2(SPDF2_FILEPATHCSV)
spdf3 = clean_support_df3(SPDF3_FILEPATHCSV)
spdf4 = clean_support_df4(SPDF4_FILEPATHCSV)
spdf5 = clean_support_df5(SPDF5_FILEPATHCSV)

print(spdf1)