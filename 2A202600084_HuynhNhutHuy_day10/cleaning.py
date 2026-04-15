import json

def mask_email(email):
    """
    Masks the email address by keeping the first character of the username 
    and adding '***' before the domain.
    Example: vana@gmail.com -> v***@gmail.com
    """
    if not email or '@' not in email:
        return email
    parts = email.split('@')
    return parts[0][0] + "***@" + parts[1]

def clean_data(input_file, output_file):
    # Load the toxic data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}.")
        return

    seen_ids = set()
    sanitized_data = []

    for item in data:
        # 1. Deduplication: Ensure each id only appears once
        # TODO: Check if item['id'] is already in seen_ids. If yes, skip it.
        item_id = item.get('id')
        if item_id in seen_ids:
            continue
        price = item.get('price')
        # 2. Outlier Check: Remove any item with price > $5,000
        # TODO: Get price and check if it's > 5000. If yes, skip it.
        if price is not None and price > 5000:
            continue
            
        # 3. Sanity Check: Remove any item with price < 0
        if price is not None and price < 0:
            continue

        # 4. PII Masking: Remove name and mask email
        if 'name' in item:
            del item['name']
        if 'email' in item:
            item['email'] = mask_email(item['email'])

        # Add to cleaned list and track ID
        sanitized_data.append(item)
        seen_ids.add(item_id)

    # Save the sanitized data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sanitized_data, f, indent=4)

    print(f"Successfully sanitized data. Output saved to {output_file}")
    print(f"Original records: {len(data)}")
    print(f"Sanitized records: {len(sanitized_data)}")

if __name__ == "__main__":
    INPUT_PATH = "toxic_sample.json"
    OUTPUT_PATH = "sanitized_sample.json"
    clean_data(INPUT_PATH, OUTPUT_PATH)
