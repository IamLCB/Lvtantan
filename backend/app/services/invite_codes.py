import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def generate_invite_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(6))
