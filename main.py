from colorama import Fore, Style, init
import re
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


def clean_sheet_name(name: str, existing_names: set) -> str:
    """Sanitizes a city name to meet spreadsheet tab naming rules (<= 31 chars, no invalid chars)."""
    if pd.isna(name) or str(name).strip() == "":
        clean_name = "Unknown"
    else:
        # Remove characters not allowed in spreadsheet sheet names: \ / ? * [ ] : '
        clean_name = re.sub(r'[\\/*?:\[\]\']', '', str(name)).strip()
        if not clean_name:
            clean_name = "Unknown"

    # Spreadsheet tab names cannot exceed 31 characters
    base_name = clean_name[:31]
    final_name = base_name
    counter = 1

    # Handle duplicate truncated names (e.g., two cities starting with the same 31 chars)
    while final_name.lower() in existing_names:
        suffix = f"_{counter}"
        final_name = f"{base_name[:31 - len(suffix)]}{suffix}"
        counter += 1

    existing_names.add(final_name.lower())
    return final_name


def get_latest_csv(data_folder: Path) -> tuple[Path | None, datetime | None]:
    """Finds the most recent ActiveBusinesses_YYYYMMDD.csv file and parses its date."""
    latest_file = None
    latest_date = None

    for file_path in data_folder.glob("ActiveBusinesses_*.csv"):
        match = re.search(r"ActiveBusinesses_(\d{8})\.csv$", file_path.name)
        if match:
            try:
                file_date = datetime.strptime(match.group(1), "%Y%m%d")
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
                    latest_file = file_path
            except ValueError:
                continue  # Skip files with invalid date strings

    return latest_file, latest_date


def main():
    prime_url: str = "https://data.oregon.gov/api/v3/views/tckn-sxa6/export.csv"
    print(f"{Fore.CYAN}Primary URL Acquired:{Style.RESET_ALL} {prime_url}")

    now: datetime = datetime.now()
    ymd: str = now.strftime("%Y%m%d")
    print(f"{Fore.CYAN}Today's Date YYYYMMDD:{Style.RESET_ALL} {ymd}")

    # Create the data folder if it doesn't exist
    data_folder = Path("data")
    data_folder.mkdir(parents=True, exist_ok=True)

    # Check for existing CSV files and see if the newest one is over 7 days old
    latest_csv, latest_date = get_latest_csv(data_folder)
    needs_download = True

    if latest_csv and latest_date:
        age = now - latest_date
        if age <= timedelta(days=7):
            needs_download = False
            csv_path = latest_csv
            # Match the ODS filename to the existing CSV's date
            active_ymd = latest_date.strftime("%Y%m%d")
            print(
                f"{Fore.GREEN}Recent CSV found ({latest_csv.name}, {age.days} day(s) old). "
                f"Skipping download.{Style.RESET_ALL}"
            )
        else:
            print(
                f"{Fore.YELLOW}Latest CSV ({latest_csv.name}) is {age.days} days old (> 7 days). "
                f"Redownloading...{Style.RESET_ALL}"
            )
    else:
        print(f"{Fore.YELLOW}No existing CSV found. Downloading...{Style.RESET_ALL}")

    if needs_download:
        active_ymd = ymd
        csv_path = data_folder / f"ActiveBusinesses_{active_ymd}.csv"
        print(f"{Fore.YELLOW}Downloading CSV from Oregon Data Portal...{Style.RESET_ALL}")
        try:
            with requests.get(prime_url, stream=True, timeout=60) as response:
                response.raise_for_status()
                with open(csv_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"{Fore.GREEN}Successfully saved CSV to:{Style.RESET_ALL} {csv_path}")
        except requests.RequestException as e:
            print(f"{Fore.RED}Error downloading CSV:{Style.RESET_ALL} {e}")
            return

    ods_path = data_folder / f"ActiveBusinesses_{active_ymd}.ods"

    # Load the CSV into Pandas
    print(f"{Fore.YELLOW}Reading CSV into pandas:{Style.RESET_ALL} {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)

    # Identify the 'City' column (case-insensitive check)
    city_col = next((col for col in df.columns if col.strip().lower() == "city"), None)
    if not city_col:
        print(f"{Fore.RED}Could not find a 'City' column. Available columns:{Style.RESET_ALL} {list(df.columns)}")
        return

    # Normalize city casing/whitespace so "PORTLAND" and "Portland " group together
    df[city_col] = df[city_col].fillna("Unknown").astype(str).str.strip().str.title()

    # Group by City and write each to its own tab in an .ods file
    print(f"{Fore.YELLOW}Converting to ODS and splitting cities into tabs...{Style.RESET_ALL}")
    existing_sheet_names = set()

    # Sort groups alphabetically so the tabs are in order
    grouped = sorted(df.groupby(city_col), key=lambda x: x[0])

    with pd.ExcelWriter(ods_path, engine="odf") as writer:
        for city, group_df in grouped:
            sheet_name = clean_sheet_name(city, existing_sheet_names)
            group_df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(sheet_name)

    print(f"{Fore.GREEN}Done! Created {len(grouped)} city tabs in:{Style.RESET_ALL} {ods_path}")


if __name__ == "__main__":
    main()