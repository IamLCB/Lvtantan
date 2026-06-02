import re

from app.services.invite_codes import generate_invite_code


def test_invite_code_has_six_alphanumeric_uppercase_chars():
    code = generate_invite_code()
    assert re.fullmatch(r"[A-Z0-9]{6}", code)
