---
id: morning-cleaning-sprint
summary: A 45-minute sprint to sanitize "toxic" data for AI ingestion.
authors: Vo Tu Duc
categories: Data Engineering
status: Published
---

# Morning Mini-Lab: Data Cleaning Sprint

## 1. Introduction: The "Toxic Sample"
Duration: 0:05:00

In your `morning_v2/` folder, you will find `toxic_sample.json`. This data is "toxic" because it contains:
- **PII (Personally Identifiable Information)**: Real names and emails.
- **Zombies**: Duplicate records.
- **Extreme Outliers**: Prices that make no sense.
- **Garbage**: Negative prices and missing categories.

---

## 2. Challenge 1: PII Masking (Privacy)
Duration: 0:15:00

Your AI Agent does not need to know the customer's real name or email to answer product questions. In fact, keeping this data in your Vector DB is a **security risk**.

### Task
Write a script to:
1.  **Remove** the `name` field completely.
2.  **Mask** the `email` field (e.g., `vana@gmail.com` -> `v***@gmail.com`).

```python
import json

def mask_email(email):
    parts = email.split('@')
    return parts[0][0] + "***@" + parts[1]

# TODO: Apply to toxic_sample.json
```

---

## 3. Challenge 2: Deduplication & Outliers
Duration: 0:15:00

AI Agents get confused by duplicates and outliers.

### Task
1.  **Deduplicate**: Ensure each `id` only appears once.
2.  **Outlier Check**: 
    - A pen costing $99,999 is likely an error. 
    - Set a threshold (e.g., $5,000) and remove any item above it.
3.  **Sanity Check**: Remove any item with a price < 0.

---

## 4. Final Verification
Duration: 0:10:00

### The Deliverable
Your script should output a `sanitized_sample.json` that is:
- **Private**: No names, masked emails.
- **Lean**: No duplicates.
- **Realistic**: No $99,999 pencils or negative smartphones.

### Discussion Question
"Why did we use **ETL** (Cleaning before storage) for the PII masking instead of **ELT** (Cleaning after storage)?"
*(Hint: Think about where the raw PII would be sitting if we used ELT).*
