import re


def sanitize(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if any(s in k.lower() for s in ("secret","token","api_key","authorization","password")) else sanitize(v)) for k,v in value.items()}
    if isinstance(value,list):
        return [sanitize(v) for v in value]
    if isinstance(value,str):
        value = re.sub(r"sk-[A-Za-z0-9_-]+","[REDACTED]",value)
        return re.sub(r"(?i)(?:bearer\s+)[A-Za-z0-9._-]+","Bearer [REDACTED]",value)
    return value

