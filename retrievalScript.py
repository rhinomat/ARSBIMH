'''
    retrievalScript.py
    This program retrieves a script from the Oregon Business Data Set as a CSV.
'''
import os
from colorama import Fore, Style
from playwright.sync_api import sync_playwright

def oregon_job_list_retrieval():
    print(Fore.GREEN + "Oregon State Active Business Retrieval System Initiated" + Style.RESET_ALL)
    file_folder = "businessInfo"
    with sync_playwright() as p:
        print(Fore.BLUE + "Launching new instance of firefox for interaction" + Style.RESET_ALL)
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        print(Fore.BLUE + "Transporting to needed site" + Style.RESET_ALL)
        page.goto("https://data.oregon.gov/business/Active-Businesses-County-Data/6g49-bcrm/about_data")
        print(Fore.BLUE + "Clicking Export to initiate popup" + Style.RESET_ALL)
        page.get_by_text("Export", exact=True).click()
        print(Fore.BLUE + "Clicking Download to download file" + Style.RESET_ALL)
        with page.expect_download() as download_info:
            page.get_by_text("Download", exact=True).click()
        download = download_info.value
        print("Checking for folder for information")
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        print("Clearing out folder")
        for filename in os.listdir(file_folder):
            file_path = os.path.join(file_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        save_path = os.path.join(os.getcwd(), file_folder, download.suggested_filename)
        download.save_as(save_path)
        print(f"File Saved at {save_path}")
        context.close()
        browser.close()
