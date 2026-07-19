'''
    businessProcessing.py
    This program:
    * removes unwanted fields from the retrieved business CSV.
    * Trims down CSV for needed area range 
'''

import os
import pandas as pd

folder_area = "businessInfo"

active_directory = os.path.join(os.getcwd(), folder_area)

def trimColumns():
    global folder_area, active_directory
    for filename in os.listdir(active_directory):
        file_path = os.path.join(folder_area, filename)
        #print(file_path[-4:])
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            df = df.drop(columns=["Registry Number", "Registry Date", "Anniversary Date", "PPB State", "PPB CityZip"])
            output_path = os.path.splitext(file_path)[0] + '_sanitized.csv'
            df.to_csv(output_path, index=False)
            print(output_path)

def location_filter():
    global folder_area, active_directory
    filter_params = ["PORTLAND", "GRESHAM", "TROUTDALE"]
    for filename in os.listdir(active_directory):
        file_path = os.path.join(folder_area, filename)
        if file_path.endswith("_sanitized.csv"):
            df = pd.read_csv(file_path)
            filtered_df = df[df["PPB City"].isin(filter_params)]
            output_path = os.path.splitext(file_path)[0] + '_local_filtered_default.csv'
            filtered_df.to_csv(output_path, index=False)
            print(output_path)

def status_filter():
    global folder_area, active_directory
    filter_params = ["DNP"]
    for filename in os.listdir(active_directory):
        file_path = os.path.join(folder_area, filename)
        if file_path.endswith("_local_filtered_default.csv"):
            df = pd.read_csv(file_path)
            filtered_df = df[~df["EntityType"].isin(filter_params)]
            output_path = os.path.splitext(file_path)[0] + '_clean.csv'
            filtered_df.to_csv(output_path, index=False)
            print(output_path)
            
def spreadsheet_transform():
    global folder_area, active_directory
    for filename in os.listdir(active_directory):
        file_path = os.path.join(folder_area, filename)
        if file_path.endswith("_clean.csv"):
            df = pd.read_csv(file_path)
            output_path = os.path.splitext(file_path)[0] + '_spreadsheet.ods'
            with pd.ExcelWriter(output_path, engine="odf") as writer:
                df.to_excel(writer, sheet_name="Sheet1", index=False)
            print(output_path)