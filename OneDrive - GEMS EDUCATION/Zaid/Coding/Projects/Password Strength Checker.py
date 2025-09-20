import re
from collections import Counter
import getpass

COMMON_PASSWORDS {
    "12345678",
    "qwerty123",
    "password1",
    "iloveyou",
    "admin123",
    "123123123",
    "abc12345",
    "11111111",
    "qwertyuiop",
    "1q2w3e4r",
    "Password123",
    "monkey123",
}


def password_strength(pw: str) -> dict:
    score = 0
    reasons = []

    # length
    if len(pw) >= 12:
        score += 2
    elif len(pw) >= 8:
        score += 1
    else:
        reasons.append("Too short (use at least 8–12 characters).")

    # variety
    checks = [
        (r'[a-z]', "lowercase letters"),
        (r'[A-Z]', "uppercase letters"),
        (r'\d', "digits"),
        (r'[^A-Za-z0-9]', "symbols")
    ]
    passed = 0
    for pattern, _ in checks:
        if re.search(pattern, pw):
            passed += 1
    score += passed
    if passed < 3:
        reasons.append(
            "Use a mix of uppercase, lowercase, digits and symbols.")

    # repeated characters or sequences
    if re.search(r'(.)\1\1', pw):
        reasons.append("Avoid repeated characters (e.g., 'aaa').")
    if re.search(r'0123|1234|abcd|qwer', pw.lower()):
        reasons.append("Avoid obvious sequences.")

    # common passwords
    if pw.lower() in COMMON_PASSWORDS:
        reasons.append(
            "This is on the common-password lists — choose something unique.")

    # unique chars
    uniq = len(set(pw))
    if uniq < max(4, len(pw) * 0.4):
        reasons.append("Low character variety compared to length.")

    # final rating
    if score >= 5 and not reasons:
        rating = "Very strong"
    elif score >= 4:
        rating = "Strong"
    elif score >= 2:
        rating = "Weak"
    else:
        rating = "Very weak"

    if reasons == []:
        return {"password": pw, "score": score, "rating": rating}
    else:
        return {"password": pw, "score": score, "rating": rating, "reasons": reasons}


if __name__ == "__main__":
    pw = getpass.getpass("Password: ")
    print(f"Received a password of {len(pw)} characters long.")
    result = password_strength(pw)
    print(result)
