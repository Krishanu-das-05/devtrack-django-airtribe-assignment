import json


def read_records(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_records(filename, records):
    with open(filename, "w") as f:
        json.dump(records, f, indent=2)