'''
    retrievalScript.py
    This program retrieves a script from the Oregon Business Data Set as a CSV.
'''
import requests
import os
from colorama import Fore, Style

def oregon_job_list_retrieval():
    print(Fore.GREEN + "Oregon State Active Business Retrieval System Initiated" + Style.RESET_ALL)
    file_folder = "businessInfo"
    save_file = "active_businesses.csv"
    url = "https://data.oregon.gov/api/v3/views/6g49-bcrm/export.csv?accessType=DOWNLOAD"
    print("Checking for folder for information")
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    print("Clearing out folder")
    for filename in os.listdir(file_folder):
        file_path = os.path.join(file_folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    response = requests.get(url)
    save_path = os.path.join(os.getcwd(), file_folder, save_file)
    with open(save_path, "wb") as file:
        file.write(response.content)

    print(f"Active Business CSV saved to {save_path}")
