import re


def normalize_response_text(text: str) -> str:
    cleaned = str(text or "")

    replacements = {
        "\\rightarrow": "->",
        "\\to": "->",
        "\\Rightarrow": "=>",
        "\\approx": "khoang",
        "\\times": "x",
        "\\cdot": "*",
        "\\(": "",
        "\\)": "",
        "\\[": "",
        "\\]": "",
        "$": "",
        "**": "",
        "`": "",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)

    cleaned = re.sub(r"\\text\{([^}]*)\}", r"\1", cleaned)
    cleaned = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", cleaned)
    cleaned = re.sub(r"\\operatorname\{([^}]*)\}", r"\1", cleaned)

    lines = []
    previous_blank = False
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if line.startswith("* "):
            line = "- " + line[2:].strip()
        line = re.sub(r"[ \t]+", " ", line)
        if not line:
            if not previous_blank:
                lines.append("")
            previous_blank = True
            continue
        lines.append(line)
        previous_blank = False

    return "\n".join(lines).strip()


def render_message_content(content) -> str:
    if isinstance(content, str):
        return normalize_response_text(content)

    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text" and part.get("text"):
                    texts.append(part["text"])
                elif isinstance(part.get("content"), str):
                    texts.append(part["content"])
            elif isinstance(part, str):
                texts.append(part)
        merged = "\n".join(t for t in texts if t).strip()
        if merged:
            return normalize_response_text(merged)

    return normalize_response_text(str(content))
