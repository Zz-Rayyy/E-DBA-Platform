import re


_LOCAL_PART = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
_DOMAIN_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_EMAIL_PATTERN = re.compile(rf"{_LOCAL_PART}@(?:{_DOMAIN_LABEL}\.)+[A-Za-z]{{2,63}}")


def is_valid_email(email):
    """Accept common email addresses without restricting their domain."""
    return isinstance(email, str) and _EMAIL_PATTERN.fullmatch(email) is not None
