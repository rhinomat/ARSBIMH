from colorama import Fore, Style, init
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Initialize colorama for terminal logging alongside the GUI
init(autoreset=True)

PRIME_URL = "https://data.oregon.gov/api/v3/views/tckn-sxa6/export.csv"
DATA_FOLDER = Path("data")


def clean_sheet_name(name: str, existing_names: set) -> str:
    """Sanitizes a city name to meet spreadsheet tab naming rules (<= 31 chars, no invalid chars)."""
    if pd.isna(name) or str(name).strip() == "":
        clean_name = "Unknown"
    else:
        clean_name = re.sub(r'[\\/*?:\[\]\']', '', str(name)).strip()
        if not clean_name:
            clean_name = "Unknown"

    base_name = clean_name[:31]
    final_name = base_name
    counter = 1

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
                continue

    return latest_file, latest_date


class BusinessExportWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Oregon Active Businesses — ODS Export Wizard")
        self.geometry("620x520")
        self.resizable(False, False)

        # State variables
        self.df: pd.DataFrame | None = None
        self.city_col: str | None = None
        self.all_cities: list[str] = []
        self.selected_cities: set[str] = set()
        self.active_ymd: str = datetime.now().strftime("%Y%m%d")
        self.ods_path: Path | None = None

        # Main container holding wizard steps
        self.container = ttk.Frame(self, padding=20)
        self.container.pack(fill="both", expand=True)

        # Header
        self.header_label = ttk.Label(
            self.container, text="", font=("Segoe UI", 14, "bold")
        )
        self.header_label.pack(anchor="w")

        self.sub_label = ttk.Label(
            self.container, text="", font=("Segoe UI", 9), foreground="#555555"
        )
        self.sub_label.pack(anchor="w", pady=(2, 12))

        ttk.Separator(self.container, orient="horizontal").pack(fill="x", pady=(0, 15))

        # Dynamic content area for each wizard page
        self.body_frame = ttk.Frame(self.container)
        self.body_frame.pack(fill="both", expand=True)

        # Footer navigation bar
        ttk.Separator(self.container, orient="horizontal").pack(fill="x", pady=(15, 10))
        self.footer_frame = ttk.Frame(self.container)
        self.footer_frame.pack(fill="x")

        self.cancel_btn = ttk.Button(
            self.footer_frame, text="Cancel", command=self.destroy
        )
        self.cancel_btn.pack(side="left")

        self.next_btn = ttk.Button(
            self.footer_frame, text="Next >", command=self.on_next
        )
        self.next_btn.pack(side="right")

        self.back_btn = ttk.Button(
            self.footer_frame, text="< Back", command=self.on_back
        )
        self.back_btn.pack(side="right", padx=(0, 8))

        self.current_step = 0
        self.show_step_1()

    def clear_body(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # STEP 1: Data Acquisition (Cache check / Download / Load CSV)
    # ------------------------------------------------------------------
    def show_step_1(self):
        self.current_step = 1
        self.header_label.config(text="Step 1 of 3: Acquire & Load Dataset")
        self.sub_label.config(
            text="Checking local cache (7-day freshness rule) and loading CSV data..."
        )
        self.back_btn.config(state="disabled")
        self.next_btn.config(text="Next >", state="disabled")

        self.clear_body()

        self.step1_status = ttk.Label(
            self.body_frame, text="Initializing...", font=("Segoe UI", 10), wraplength=560
        )
        self.step1_status.pack(anchor="w", pady=(20, 10))

        self.step1_progress = ttk.Progressbar(self.body_frame, mode="indeterminate")
        self.step1_progress.pack(fill="x", pady=10)
        self.step1_progress.start(12)

        self.step1_details = ttk.Label(
            self.body_frame, text="", font=("Segoe UI", 9), foreground="#444444", wraplength=560
        )
        self.step1_details.pack(anchor="w", pady=(10, 0))

        # Run download & CSV parsing in background thread
        threading.Thread(target=self._worker_load_data, daemon=True).start()

    def _worker_load_data(self):
        try:
            DATA_FOLDER.mkdir(parents=True, exist_ok=True)
            now = datetime.now()
            latest_csv, latest_date = get_latest_csv(DATA_FOLDER)

            needs_download = True
            if latest_csv and latest_date:
                age = now - latest_date
                if age <= timedelta(days=7):
                    needs_download = False
                    csv_path = latest_csv
                    self.active_ymd = latest_date.strftime("%Y%m%d")
                    self._update_step1_ui(
                        f"Using cached dataset: {latest_csv.name}",
                        f"File is {age.days} day(s) old (within the 7-day window). Skipping download.",
                    )

            if needs_download:
                self.active_ymd = now.strftime("%Y%m%d")
                csv_path = DATA_FOLDER / f"ActiveBusinesses_{self.active_ymd}.csv"
                self._update_step1_ui(
                    "Downloading fresh CSV from Oregon Data Portal...",
                    f"Target: {csv_path}\nThis may take a moment depending on connection speed.",
                )
                with requests.get(PRIME_URL, stream=True, timeout=60) as response:
                    response.raise_for_status()
                    with open(csv_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

            self._update_step1_ui(
                "Parsing CSV and extracting unique cities...",
                f"Reading {csv_path.name} into memory...",
            )
            df = pd.read_csv(csv_path, low_memory=False)
            city_col = next(
                (col for col in df.columns if col.strip().lower() == "city"), None
            )
            if not city_col:
                raise ValueError(f"Could not find a 'City' column in {list(df.columns)}")

            df[city_col] = (
                df[city_col].fillna("Unknown").astype(str).str.strip().str.title()
            )
            unique_cities = sorted(df[city_col].unique().tolist())

            self.df = df
            self.city_col = city_col
            self.all_cities = unique_cities
            # Default: select all cities initially, or leave empty if you prefer
            self.selected_cities = set(unique_cities)

            self.after(0, self._on_step1_complete, csv_path.name, len(df), len(unique_cities))

        except Exception as e:
            self.after(0, self._on_worker_error, str(e))

    def _update_step1_ui(self, status: str, details: str):
        self.after(0, lambda: self.step1_status.config(text=status))
        self.after(0, lambda: self.step1_details.config(text=details))

    def _on_step1_complete(self, filename: str, row_count: int, city_count: int):
        self.step1_progress.stop()
        self.step1_progress.config(mode="determinate", value=100)
        self.step1_status.config(text="Dataset Ready!")
        self.step1_details.config(
            text=(
                f"Loaded file: {filename}\n"
                f"Total records: {row_count:,}\n"
                f"Unique cities found: {city_count:,}\n\n"
                "Click 'Next >' to filter which cities to include in your spreadsheet."
            )
        )
        self.next_btn.config(state="normal")

    # ------------------------------------------------------------------
    # STEP 2: City Filter Selection
    # ------------------------------------------------------------------
    def show_step_2(self):
        self.current_step = 2
        self.header_label.config(text="Step 2 of 3: Select Cities to Export")
        self.sub_label.config(
            text="Each selected city will become its own tab in the OpenDocument (.ods) file."
        )
        self.back_btn.config(state="normal")
        self.next_btn.config(text="Export ODS >", state="normal")

        self.clear_body()

        # Search & Quick-Action bar
        top_controls = ttk.Frame(self.body_frame)
        top_controls.pack(fill="x", pady=(0, 8))

        ttk.Label(top_controls, text="Search:").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_city_listbox())
        search_entry = ttk.Entry(top_controls, textvariable=self.search_var, width=28)
        search_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(
            top_controls, text="Select Visible", command=self._select_visible
        ).pack(side="left", padx=(8, 4))
        ttk.Button(
            top_controls, text="Clear Visible", command=self._deselect_visible
        ).pack(side="left")

        # Listbox with scrollbar
        list_frame = ttk.Frame(self.body_frame)
        list_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.city_listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            yscrollcommand=scrollbar.set,
            exportselection=False,
            font=("Segoe UI", 10),
        )
        scrollbar.config(command=self.city_listbox.yview)

        self.city_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.city_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Selection counter label
        self.selection_count_label = ttk.Label(
            self.body_frame, text="", font=("Segoe UI", 9, "bold")
        )
        self.selection_count_label.pack(anchor="w", pady=(8, 0))

        self.visible_cities: list[str] = []
        self._refresh_city_listbox()

    def _refresh_city_listbox(self):
        query = self.search_var.get().strip().lower()
        self.visible_cities = [
            c for c in self.all_cities if query in c.lower()
        ]

        self.city_listbox.delete(0, tk.END)
        for idx, city in enumerate(self.visible_cities):
            self.city_listbox.insert(tk.END, city)
            if city in self.selected_cities:
                self.city_listbox.selection_set(idx)

        self._update_selection_label()

    def _on_listbox_select(self, _event=None):
        selected_indices = set(self.city_listbox.curselection())
        for idx, city in enumerate(self.visible_cities):
            if idx in selected_indices:
                self.selected_cities.add(city)
            else:
                self.selected_cities.discard(city)
        self._update_selection_label()

    def _select_visible(self):
        for idx, city in enumerate(self.visible_cities):
            self.city_listbox.selection_set(idx)
            self.selected_cities.add(city)
        self._update_selection_label()

    def _deselect_visible(self):
        for idx, city in enumerate(self.visible_cities):
            self.city_listbox.selection_clear(idx)
            self.selected_cities.discard(city)
        self._update_selection_label()

    def _update_selection_label(self):
        count = len(self.selected_cities)
        self.selection_count_label.config(
            text=f"Selected: {count:,} of {len(self.all_cities):,} cities"
        )

    # ------------------------------------------------------------------
    # STEP 3: Export Filtered Cities to ODS
    # ------------------------------------------------------------------
    def show_step_3(self):
        self.current_step = 3
        self.header_label.config(text="Step 3 of 3: Generating ODS Spreadsheet")
        self.sub_label.config(
            text=f"Writing {len(self.selected_cities):,} selected city tab(s)..."
        )
        self.back_btn.config(state="disabled")
        self.next_btn.config(text="Finish", state="disabled")

        self.clear_body()

        self.step3_status = ttk.Label(
            self.body_frame, text="Starting export...", font=("Segoe UI", 10)
        )
        self.step3_status.pack(anchor="w", pady=(20, 8))

        self.step3_progress = ttk.Progressbar(
            self.body_frame, mode="determinate", maximum=len(self.selected_cities)
        )
        self.step3_progress.pack(fill="x", pady=10)

        self.step3_details = ttk.Label(
            self.body_frame, text="", font=("Segoe UI", 9), foreground="#444444", wraplength=560
        )
        self.step3_details.pack(anchor="w", pady=(10, 0))

        threading.Thread(target=self._worker_export_ods, daemon=True).start()

    def _worker_export_ods(self):
        try:
            self.ods_path = DATA_FOLDER / f"ActiveBusinesses_{self.active_ymd}.ods"
            filtered_df = self.df[self.df[self.city_col].isin(self.selected_cities)]
            grouped = sorted(filtered_df.groupby(self.city_col), key=lambda x: x[0])

            existing_sheet_names = set()
            total = len(grouped)

            with pd.ExcelWriter(self.ods_path, engine="odf") as writer:
                for idx, (city, group_df) in enumerate(grouped, start=1):
                    sheet_name = clean_sheet_name(city, existing_sheet_names)
                    group_df.to_excel(writer, sheet_name=sheet_name, index=False)

                    # Update progress bar smoothly on the main thread
                    self.after(
                        0,
                        self._update_step3_progress,
                        idx,
                        total,
                        city,
                        len(group_df),
                    )

            self.after(0, self._on_step3_complete, total, len(filtered_df))

        except Exception as e:
            self.after(0, self._on_worker_error, str(e))

    def _update_step3_progress(self, current: int, total: int, city: str, rows: int):
        self.step3_progress["value"] = current
        self.step3_status.config(
            text=f"Writing tab {current:,} of {total:,}: {city} ({rows:,} rows)"
        )

    def _on_step3_complete(self, tab_count: int, total_rows: int):
        self.step3_status.config(text="Export Complete!")
        self.step3_details.config(
            text=(
                f"Saved file: {self.ods_path.resolve()}\n"
                f"City tabs created: {tab_count:,}\n"
                f"Total business records exported: {total_rows:,}"
            )
        )
        self.cancel_btn.config(state="disabled")
        self.next_btn.config(state="normal")

    # ------------------------------------------------------------------
    # Navigation & Error Handling
    # ------------------------------------------------------------------
    def on_next(self):
        if self.current_step == 1:
            self.show_step_2()
        elif self.current_step == 2:
            if not self.selected_cities:
                messagebox.showwarning(
                    "No Cities Selected",
                    "Please select at least one city before exporting.",
                )
                return
            self.show_step_3()
        elif self.current_step == 3:
            self.destroy()

    def on_back(self):
        if self.current_step == 2:
            self.show_step_1()

    def _on_worker_error(self, error_msg: str):
        messagebox.showerror("Error", f"An error occurred:\n\n{error_msg}")
        self.next_btn.config(state="disabled")


if __name__ == "__main__":
    app = BusinessExportWizard()
    app.mainloop()