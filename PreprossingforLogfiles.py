import os
import re
import json
import csv

# Set to the directory containing your Log files
folder_path = os.path.dirname(os.path.abspath(__file__))

# Loop through all .csv files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".log"):
        file_path = os.path.join(folder_path, filename)
        print(f"Processing {filename}...")

        cleaned_rows = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for row in reader:
                    # Merge split array values (e.g., ip:["a","b"] split by csv.reader)
                    merged_cells = []
                    i = 0
                    while i < len(row):
                        cell = row[i]
                        # If cell has an opening '[' without matching ']', merge following cells until balanced
                        if cell.count('[') > cell.count(']'):
                            merged = cell
                            i += 1
                            while i < len(row) and merged.count('[') > merged.count(']'):
                                merged += ',' + row[i]
                                i += 1
                            merged_cells.append(merged)
                        else:
                            merged_cells.append(cell)
                            i += 1

                    cleaned_cells = []
                    for cell in merged_cells:
                        # Remove byte order mark if present
                        cell = cell.lstrip('\ufeff')
                        # Strip whitespace and outer quotes
                        cell = cell.strip().strip('"').strip()
                        # Remove non-printable/control characters
                        cell = re.sub(r'[\x00-\x1F]+', '', cell)

                        # Flatten arrays that follow a key, including non-JSON arrays
                        m = re.match(r'^([^:]+):\[(.*)\]$', cell)
                        if m:
                            key = m.group(1)
                            arr_content = m.group(2)
                            try:
                                # Try valid JSON parse
                                arr = json.loads(f'[{arr_content}]')
                            except json.JSONDecodeError:
                                # Fallback: split on commas and strip quotes
                                arr = [item.strip().strip('"').strip("'") for item in arr_content.split(',') if item.strip()]
                            cell = f"{key}:{';'.join(arr)}"

                        # Parse standalone JSON arrays into semicolon-separated strings
                        if cell.startswith('[') and cell.endswith(']'):
                            try:
                                arr = json.loads(cell)
                                cell = ';'.join(arr)
                            except json.JSONDecodeError:
                                pass

                        cleaned_cells.append(cell)

                    # Optionally skip rows with unexpected column counts here
                    cleaned_rows.append(cleaned_cells)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        try:
            csv_path = os.path.splitext(file_path)[0] + ".csv"
            with open(csv_path, "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                writer.writerows(cleaned_rows)
            print(f"Cleaned and saved as: {os.path.basename(csv_path)}")
        except Exception as e:
            print(f"Error writing to {os.path.basename(csv_path)}: {e}")