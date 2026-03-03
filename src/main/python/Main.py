# === Suppress all warnings BEFORE any library imports ===
import os
import sys
import warnings
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed


def emit_progress(percentage, message=""):
    """Emit a PROGRESS line matching the standard format."""
    pct = min(100.0, max(0.0, percentage))
    safe_msg = message.replace("|", "-").replace("\n", " ").replace("\r", "").strip()
    print(f"PROGRESS|{pct:.1f}|{safe_msg}", flush=True)


def calc_eta(start_time, current_idx, total):
    """Calculate ETA string based on progress."""
    elapsed = time.time() - start_time
    if current_idx <= 0:
        return "00:00"
    avg_per_item = elapsed / current_idx
    remaining = avg_per_item * (total - current_idx)
    return time.strftime("%M:%S", time.gmtime(remaining))


def elapsed_str(start_time):
    """Get elapsed time in seconds."""
    return f"{time.time() - start_time:.0f}s"


def get_issuer_codes():
    """Fetch all issuer codes from the Macedonian Stock Exchange dropdown."""
    url = "https://www.mse.mk/mk/stats/symbolhistory/ADIN"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    dropdown = soup.find("select", {"id": "Code"})
    if not dropdown:
        print("ERROR: Could not find issuer dropdown on MSE website", flush=True)
        return []

    codes = []
    for option in dropdown.find_all("option"):
        code = option.get("value", "").strip()
        if code and not any(char.isdigit() for char in code):
            codes.append(code)

    return codes


def fetch_issuer_names():
    """Fetch issuer codes and full names from the MSE current-schedule page."""
    url_base = "https://www.mse.mk/mk/stats/current-schedule"
    categories = [
        url_base + "?category=10",
        url_base + "?category=20",
        url_base + "?category=no-limit"
    ]

    all_issuers = []
    seen = set()

    for cat_url in categories:
        try:
            response = requests.get(cat_url, timeout=30)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:
                    columns = row.find_all('td')
                    if len(columns) >= 3:
                        code = columns[0].get_text(strip=True)
                        name = columns[1].get_text(strip=True)
                        link_tag = columns[0].find('a')
                        link = ('https://www.mse.mk' + link_tag.get('href')) if link_tag else None

                        if code and not re.search(r'\d', code) and (code, name) not in seen:
                            seen.add((code, name))
                            all_issuers.append({
                                'Issuer code': code,
                                'Issuer name': name,
                                'Issuer link': link
                            })
        except Exception:
            continue

    return all_issuers


def get_issuer_link(code):
    """Build the issuer link for the MSE website."""
    return f"https://www.mse.mk/mk/stats/symbolhistory/{code}"


def save_names_json(named_issuers, all_codes, filepath):
    """Save issuer codes, names and links to names.json.
    Uses fetched names where available, falls back to code as name."""
    name_map = {item['Issuer code']: item for item in named_issuers}

    result = []
    for code in all_codes:
        if code in name_map:
            result.append(name_map[code])
        else:
            result.append({
                'Issuer code': code,
                'Issuer name': code,
                'Issuer link': get_issuer_link(code)
            })

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def fetch_issuer_history(code, from_date, to_date):
    """Fetch historical data for a single issuer code."""
    url = "https://www.mse.mk/mk/stats/symbolhistory/" + code
    data = {
        "FromDate": from_date.strftime("%d.%m.%Y"),
        "ToDate": to_date.strftime("%d.%m.%Y"),
        "Code": code
    }

    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "resultsTable"})

        if not table:
            return None

        rows = []
        tbody = table.find("tbody")
        if not tbody:
            return None

        for tr in tbody.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) >= 8:
                row = {
                    "date": cells[0].text.strip(),
                    "close": cells[1].text.strip().replace(".", "").replace(",", "."),
                    "max": cells[2].text.strip().replace(".", "").replace(",", "."),
                    "low": cells[3].text.strip().replace(".", "").replace(",", "."),
                    "avg": cells[4].text.strip().replace(".", "").replace(",", "."),
                    "volume": cells[6].text.strip().replace(".", "").replace(",", "."),
                    "turnover in BEST": cells[7].text.strip().replace(".", "").replace(",", "."),
                    "total turnover": cells[8].text.strip().replace(".", "").replace(",", ".") if len(cells) > 8 else "0",
                    "code": code
                }
                rows.append(row)

        return rows

    except Exception as e:
        return None


def main():
    start_time = time.time()

    smestuvanje_dir = os.path.join(os.path.dirname(__file__), 'Smestuvanje')
    os.makedirs(smestuvanje_dir, exist_ok=True)

    names_json_path = os.path.join(smestuvanje_dir, 'names.json')
    mega_data_path = os.path.join(smestuvanje_dir, 'mega-data.csv')

    # Step 1: Get all issuer codes from dropdown
    print("PROGRESS|0.0|Fetching issuer codes from MSE...", flush=True)
    codes = get_issuer_codes()

    if not codes:
        print("PROGRESS|100.0|No issuer codes found", flush=True)
        print("DONE|0|No codes found", flush=True)
        sys.exit(0)

    total = len(codes)
    print(f"TOTAL|{total}", flush=True)

    # Step 2: Fetch real issuer names from schedule page
    print("PROGRESS|0.5|Fetching issuer names...", flush=True)
    named_issuers = fetch_issuer_names()
    print(f"  Fetched {len(named_issuers)} issuer names from schedule page", flush=True)

    # Step 3: Save names.json (merging names with full code list)
    save_names_json(named_issuers, codes, names_json_path)

    # Step 4: Determine date range
    to_date = datetime.today()
    from_date = to_date - timedelta(days=365 * 10)

    # Check if mega-data.csv already exists — only fetch new data
    existing_data = None
    if os.path.exists(mega_data_path):
        try:
            existing_data = pd.read_csv(mega_data_path)
            if 'date' in existing_data.columns and len(existing_data) > 0:
                existing_data['date_parsed'] = pd.to_datetime(existing_data['date'], format='%d.%m.%Y', errors='coerce')
                last_date = existing_data['date_parsed'].max()
                if pd.notna(last_date):
                    from_date = last_date + timedelta(days=1)
                    if from_date.date() >= to_date.date():
                        print("PROGRESS|100.0|Data already up to date", flush=True)
                        print(f"DONE|{total}|Already up to date", flush=True)
                        sys.exit(0)
                existing_data = existing_data.drop(columns=['date_parsed'], errors='ignore')
        except Exception:
            existing_data = None

    # Step 5: Fetch historical data for each issuer
    all_rows = []
    processed_count = 0

    for idx, code in enumerate(codes):
        pct = ((idx) / total) * 100
        eta = calc_eta(start_time, idx, total)
        elapsed = elapsed_str(start_time)

        emit_progress(pct, f"[{idx + 1}/{total}]: {code} | Elapsed: {elapsed} | ETA: {eta}")

        try:
            rows = fetch_issuer_history(code, from_date, to_date)
            if rows:
                all_rows.extend(rows)
                processed_count += 1
                print(f"  Done — fetched {len(rows)} records", flush=True)
            else:
                print(f"  Skipped — no data available", flush=True)
        except Exception as e:
            print(f"  Error: {e}", flush=True)

    # Step 6: Save to mega-data.csv
    emit_progress(95.0, f"Saving data... | Elapsed: {elapsed_str(start_time)} | ETA: 00:05")

    if all_rows:
        new_data = pd.DataFrame(all_rows)

        numeric_cols = ['close', 'max', 'low', 'avg', 'volume', 'turnover in BEST', 'total turnover']
        for col in numeric_cols:
            if col in new_data.columns:
                new_data[col] = pd.to_numeric(new_data[col], errors='coerce')

        new_data.dropna(subset=['close'], inplace=True)

        if existing_data is not None and len(existing_data) > 0:
            combined = pd.concat([existing_data, new_data], ignore_index=True)
            combined.drop_duplicates(subset=['date', 'code'], keep='last', inplace=True)
            combined.to_csv(mega_data_path, index=False)
            print(f"  Merged {len(new_data)} new rows with {len(existing_data)} existing rows", flush=True)
        else:
            new_data.to_csv(mega_data_path, index=False)
            print(f"  Saved {len(new_data)} rows to {mega_data_path}", flush=True)
    else:
        print("  No new data to save", flush=True)

    duration = time.time() - start_time
    print(f"DONE|{processed_count}|Completed in {duration:.2f}s", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
