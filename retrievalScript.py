'''
    retrievalScript.py
    This program retrieves a script from the Oregon Business Data Set as a CSV.
'''
import os
from playwright.sync_api import sync_playwright

def main():
    file_folder = "businessInfo"
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://data.oregon.gov/business/Active-Businesses-County-Data/6g49-bcrm/about_data")
        page.get_by_text("Export", exact=True).click()
        with page.expect_download() as download_info:
            page.get_by_text("Download", exact=True).click()
        download = download_info.value
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        for filename in os.listdir(file_folder):
            file_path = os.path.join(file_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        save_path = os.path.join(os.getcwd(), file_folder, download.suggested_filename)
        download.save_as(save_path)

        context.close()
        browser.close()

if __name__ == "__main__":
    main()