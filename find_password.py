import hashlib

# The hash from the database
db_hash = "6d2861d4c0aa96b7b3d3d8c1fae7db0a0c665817e85c67767b2f53d636cbd0a8"

# Try common variations based on what might have been entered
passwords_to_try = [
    "Lubna#razal",
    "lubna#razal",
    "Lubna razal",
    "lubna razal",
    "Lubna#Razal",
    "Lubna@razal",
    "Lubna123",
    "lubna123",
    "Lubna",
    "lubna",
    "razal",
    "password",
    "Password123",
    "admin123",
]

for pwd in passwords_to_try:
    hashed = hashlib.sha256(pwd.encode()).hexdigest()
    if hashed == db_hash:
        print(f"✓ MATCH FOUND! Password is: '{pwd}'")
        break
else:
    print("No match found in common passwords")
    print(f"\nThe actual password hash in DB is: {db_hash}")
    print("But password_display shows: Lubna#razal")
    print("\nThis means the password was likely changed or entered incorrectly when the user was created.")