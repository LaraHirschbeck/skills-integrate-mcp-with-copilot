import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

if __name__ == "__main__":
    password = "pw123456"
    print(f"Password hash for '{password}': {hash_password(password)}")
