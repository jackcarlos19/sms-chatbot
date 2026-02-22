import re


def mask_phone_number(phone_number: str) -> str:
    """Masks a phone number for logs: +1234567890 -> +1234***7890."""
    if not phone_number or len(phone_number) < 8:
        return phone_number

    return re.sub(r"(\+\d{1,3}\d{3})\d+(\d{4})$", r"\1***\2", phone_number.strip())
