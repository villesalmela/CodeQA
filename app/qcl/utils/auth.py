import secrets


LENGTH = 6

def get_verification_code() -> str:
    verification_code = ""

    for _ in range(LENGTH):
        verification_code += str(secrets.randbelow(10))

    return verification_code
