import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Bank Domain Whitelist Configuration
BANK_WHITELIST = {
    "phones":  ["0901234567", "02812345678", "19001234"],
    "emails":  ["support@vinbank.com", "contact@vinbank.com"],
    "domains": ["vinbank.com", "vinbank.vn", "vinbank.internal"],
}

# Input Guardrails: Allowed Topics
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Input Guardrails: Blocked Topics
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling",
]

# Output Guardrails: PII Regex Patterns
PII_PATTERNS = {
    "vn_phone":    r"0\d{9,10}",
    "email":       r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}",
    "national_id": r"\b\d{12}\b|\b\d{9}\b",
    "api_key":     r"sk-[a-zA-Z0-9_-]+",
    "password":    r"password\s*(?:[:=]|is)\s*\S+",
    "db_conn":     r"[\w]+\.internal[:/\w]*",
    "secret_key":  r"(secret|token|key|admin)\s*[:=]\s*['\"]?\S+['\"]?",
}
