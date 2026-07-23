import hashlib

# Test the password from the database screenshot
password = "Lubna#razal"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(f"Password: {password}")
print(f"Hash: {hashed}")
print(f"Expected from DB: 6d2861d4c0aa96b7b3d3d8c1fae7db0a0c665817e85c67767b2f53d636cbd0a8")
print(f"Match: {hashed == '6d2861d4c0aa96b7b3d3d8c1fae7db0a0c665817e85c67767b2f53d636cbd0a8'}")

# Also test without #
password2 = "Lubna#razal"
hashed2 = hashlib.sha256(password2.encode()).hexdigest()
print(f"\nPassword2: {password2}")
print(f"Hash2: {hashed2}")
print(f"Match2: {hashed2 == '6d2861d4c0aa96b7b3d3d8c1fae7db0a0c665817e85c67767b2f53d636cbd0a8'}")