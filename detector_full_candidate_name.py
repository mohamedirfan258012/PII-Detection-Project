import csv
import json
import re
import sys

PII_PATTERNS = {
    "phone": re.compile(r"^\d{10}$"),
    "aadhar": re.compile(r"^\d{12}$"),
    "passport": re.compile(r"^[A-Z]\d{7}$", re.I),
    "upi_id": re.compile(r"^[\w.\-]+@\w+$"),
}

COMBINATORIAL_PII_KEYS = {"name", "email", "address", "device_id", "ip_address"}

def mask_phone(number):
    return number[:2] + "XXXXXX" + number[-2:]

def mask_aadhar(number):
    return number[:4] + "XXXXXX" + number[-2:]

def mask_passport(passport_number):
    return passport_number + "XXXXXX" + passport_number[-1]

def mask_email(email):
    if "@" in email:
        prefix, domain = email.split("@", 1)
        masked_prefix = prefix[:2] + "X" * max(1, len(prefix) - 2)
        return masked_prefix + "@" + domain
    return "[REDACTED_PII]"

def mask_name(name):
    parts = name.split()
    masked_parts = [p + "XXX" + (p[-1] if len(p) > 2 else "") for p in parts]
    return " ".join(masked_parts)

def mask_upi(upi_id):
    user, domain = upi_id.split("@", 1)
    prefix = user[:2] + "XXX" if len(user) > 2 else user + "XXX"
    return prefix + "@" + domain

def mask_field(key, value):
    if key == "phone":
        return mask_phone(str(value))
    elif key == "aadhar":
        return mask_aadhar(str(value))
    elif key == "passport":
        return mask_passport(str(value))
    elif key == "upi_id":
        return mask_upi(str(value))
    elif key == "email":
        return mask_email(str(value))
    elif key == "name":
        return mask_name(str(value))
    elif key in {"address", "device_id", "ip_address"}:
        return "[REDACTED_PII]"
    else:
        return value

def is_pii_standalone(key, value):
    return key in PII_PATTERNS and PII_PATTERNS[key].fullmatch(str(value))

def is_pii_combinatorial(record):
    present = {k for k in COMBINATORIAL_PII_KEYS if k in record}
    if len(present & {"name", "email", "address"}) >= 2:
        return True
    if "device_id" in present and ({"name", "email", "ip_address"} & present):
        return True
    if "ip_address" in present and ({"name", "email", "device_id"} & present):
        return True
    return False

def process_row(record_id, data_json):
    try:
        rec = json.loads(data_json)
    except Exception:
        return record_id, data_json, False

    pii_found = False
    redacted = rec.copy()

    for k, v in rec.items():
        if is_pii_standalone(k, v):
            pii_found = True
            redacted[k] = mask_field(k, v)

    if is_pii_combinatorial(rec):
        pii_found = True
        for k in rec:
            if k in COMBINATORIAL_PII_KEYS:
                redacted[k] = mask_field(k, rec[k])

    redacted_json = json.dumps(redacted, ensure_ascii=False)
    return record_id, redacted_json, pii_found

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    results = []

    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record_id = row['record_id']
            data_json = row['data_json']
            processed = process_row(record_id, data_json)
            results.append(processed)
            print(processed)

    output_csv = r'C:\Users\moham\Downloads\redacted_output_mohamed_irfan.csv'
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Row_ID', 'Redacted_Data', 'PII_Found'])
        for row in results:
            writer.writerow(row)

    print(f"CSV file generated at: {output_csv}")

if __name__ == "__main__":
    main()
