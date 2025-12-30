import secrets
import string

def generate_random_password(length=12):
    """Generates a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    # Ensure at least one of each type using standard logic or just pure random
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password