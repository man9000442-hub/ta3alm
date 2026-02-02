import re

def normalize_egypt_phone(phone: str) -> str:
    if not phone:
        return ""
    p = re.sub(r"\D", "", phone)

    # 0020xxxxxxxxxx -> 0xxxxxxxxxx
    if p.startswith("0020"):
        p = "0" + p[4:]

    # 20xxxxxxxxxx -> 0xxxxxxxxxx
    if p.startswith("20"):
        p = "0" + p[2:]

    return p