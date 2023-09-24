import secrets

def get_verification_code() -> str:
    verification_code = ""

    LENGTH = 6
    for _ in range(LENGTH):
        verification_code += str(secrets.randbelow(10))

    return verification_code