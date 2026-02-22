def mask_phone_number(phone_number: str) -> str:
    if not phone_number:
        return ""

    digits = phone_number.strip()
    if len(digits) <= 8:
        return "***"

    return f"{digits[:5]}***{digits[-4:]}"
