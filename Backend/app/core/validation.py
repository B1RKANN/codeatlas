def validate_password(password: str) -> str:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    return password
