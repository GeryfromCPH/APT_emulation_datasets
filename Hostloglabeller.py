import pandas as pd
import json
import csv
import re
import argparse


# Recursively flattens nested dictionaries and converts lists to JSON strings
def flatten_dict(d, parent_key='', sep='_'):
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        elif isinstance(v, list):
            # Convert lists to JSON strings so DataFrame can store them
            items[new_key] = json.dumps(v)
        else:
            items[new_key] = v
    return items

# Parses logs CSV files flattens nested structures
def parse_sysmon_log(filepath):
    parsed_records = []
    # Open CSV and read each row
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Handle rows that are a single JSON blob (common in some Sysmon exports)
            if len(row) == 1 and isinstance(row[0], str) and row[0].lstrip().startswith('{'):
                raw = row[0].strip()
                if raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                raw = raw.replace('""', '"')
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                parsed = flatten_dict(data)
                parsed_records.append(parsed)
                continue
            # Otherwise, assume row is delimited key-value pairs
            record = {}
            for cell in row:
                # Skip empty cells
                if not cell:
                    continue
                # Remove BOM if present
                cell = cell.lstrip('\ufeff')
                # Strip outer quotes from CSV quoting
                if cell.startswith('"') and cell.endswith('"'):
                    cell = cell[1:-1]
                # Unescape doubled quotes
                cell = cell.replace('""', '"').strip()

                # Flatten arrays that follow a key, e.g., ip:["fe80::...", "192.168.56.103"]
                m = re.match(r'^([^:]+):(\[.*\])$', cell)
                if m:
                    key = m.group(1)
                    arr_str = m.group(2)
                    try:
                        arr = json.loads(arr_str)
                        cell = f"{key}:{';'.join(arr)}"
                    except json.JSONDecodeError:
                        pass

                # If cell is a standalone JSON array, convert to semicolon joined string
                if cell.startswith('[') and cell.endswith(']'):
                    try:
                        arr = json.loads(cell)
                        cell = ';'.join(arr)
                    except json.JSONDecodeError:
                        pass

                # Split into key and value at first colon
                if ':' not in cell:
                    continue
                key, val = cell.split(':', 1)
                key = key.strip()
                val = val.strip()
                # Remove any stray trailing '}' characters
                val = val.rstrip('}').strip()
                # If value is a JSON object, parse and flatten with prefix
                if val.startswith('{') and val.endswith('}'):
                    try:
                        sub = json.loads(val)
                        flat = flatten_dict(sub, parent_key=key)
                        record.update(flat)
                        continue
                    except json.JSONDecodeError:
                        pass
                # Otherwise store raw string, handling duplicates
                if key in record:
                    # aggregate repeated fields by appending only unique values
                    existing = record[key]
                    values = existing.split(';') if isinstance(existing, str) else [existing]
                    if val not in values:
                        record[key] = f"{existing};{val}"
                else:
                    record[key] = val
            # Clean keys and values by stripping problematic characters (like quotes, backslashes, etc.)
            cleaned = {}
            for k, v in record.items():
                clean_key = k.replace('.', '_').rstrip('_').replace('\\', '').replace('"', '')
                if isinstance(v, str):
                    clean_val = v.replace('\\', '').strip().strip('"').strip("'")
                else:
                    clean_val = v
                cleaned[clean_key] = clean_val
            record = cleaned
            parsed_records.append(record)
    return pd.DataFrame(parsed_records)

import os

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="Process Windows/Linux logs with customizable column filtering"
    )
    parser.add_argument(
        "--input-folder",
        default=None,
        help="Path to folder containing CSV files to process"
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path/File for the input CSV file"
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Path/Filename for the output CSV file"
    )
    parser.add_argument(
        "--filter-columns",
        nargs="*",
        default=[],
        help=(
            "List of column names to filter by (rows with non-empty "
            "values in any of these columns will be kept)"
        )
    )
    parser.add_argument(
        "--label-column",
        default=None,
        help="Name of the column to check for malicious values"
    )
    parser.add_argument(
        "--malicious-values",
        nargs="*",
        default=[],
        help="List of values in the label column to mark as malicious"
    )
    parser.add_argument(
        "--label-mappings",
        nargs="*",
        default=[],
        help="List of value=label pairs for custom labeling (e.g. 4234=T.234 5678=T.5343 cmd.exe=T.2342)"
    )
    parser.add_argument(
        "--default-label",
        default="",
        help="Default label for any value not matched by a mapping is empty change if needed"
    )
    args = parser.parse_args()

    # Batch mode: process all CSV files in the given folder
    if args.input_folder:
        folder = args.input_folder
        if not os.path.isdir(folder):
            print(f"Input folder {folder} does not exist.")
            return
        for file in os.listdir(folder):
            if file.endswith(".csv"):
                input_path = os.path.join(folder, file)
                output_path = os.path.join(folder, file.replace(".csv", "-labeled.csv"))
                df = parse_sysmon_log(input_path)
                df = df.map(lambda x: x.replace('"', '') if isinstance(x, str) else x)
                if args.filter_columns:
                    df = df[df[args.filter_columns]
                        .fillna("")
                        .astype(str)
                        .apply(lambda col: col.str.strip().ne(""), axis=0)
                        .any(axis=1)
                    ]
                # Apply labeling based on specified column and mappings or malicious values
                if args.label_column:
                    label_series = df[args.label_column].fillna("").astype(str)
                    if args.label_mappings:
                        mapping_dict = {}
                        # Parse mapping entries like key=value into a dictionary
                        for pair in args.label_mappings:
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                mapping_dict[key] = value
                        df['label'] = label_series.map(mapping_dict).fillna(args.default_label)
                    elif args.malicious_values:
                        df['label'] = label_series.isin(args.malicious_values).map({True: 'malicious', False: args.default_label})
                    else:
                        df['label'] = args.default_label
                df.to_csv(output_path, index=False)
                print(f"Processed data saved to {output_path}")
    # Single file mode: process one input CSV and save to the given output file
    elif args.input_file and args.output_file:
        df = parse_sysmon_log(args.input_file)
        df = df.map(lambda x: x.replace('"', '') if isinstance(x, str) else x)
        if args.filter_columns:
            df = df[df[args.filter_columns]
                .fillna("")
                .astype(str)
                .apply(lambda col: col.str.strip().ne(""), axis=0)
                .any(axis=1)
            ]
        # Apply labeling based on specified column and mappings or malicious values
        if args.label_column:
            label_series = df[args.label_column].fillna("").astype(str)
            if args.label_mappings:
                mapping_dict = {}
                # Parse mapping entries like key=value into a dictionary
                for pair in args.label_mappings:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        mapping_dict[key] = value
                df['label'] = label_series.map(mapping_dict).fillna(args.default_label)
            elif args.malicious_values:
                df['label'] = label_series.isin(args.malicious_values).map({True: 'malicious', False: args.default_label})
            else:
                df['label'] = args.default_label
        df.to_csv(args.output_file, index=False)
        print(f"Processed data saved to {args.output_file}")
    else:
        print("Error: Either --input-folder or both input_file and output_file must be provided.")

# Entry point of the script
if __name__ == "__main__":
    main()