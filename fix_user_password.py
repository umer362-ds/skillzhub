"""Fix user password hash in database - run this script to get the correct SQL"""
import hashlib

# The ACTUAL password that should work
ACTUAL_PASSWORD = "Lubna#razal"

# Calculate the correct hash
correct_hash = hashlib.sha256(ACTUAL_PASSWORD.encode()).hexdigest()

print("="*70)
print("STEP 1: Run this SQL query in Supabase SQL Editor:")
print("="*70)
print(f"UPDATE users SET password = '{correct_hash}', password_display = '{ACTUAL_PASSWORD}' WHERE username LIKE '%Lubna%razal%';")
print("\n" + "="*70)
print("STEP 2: Verify the update worked:")
print("="*70)
print(f"SELECT username, password, password_display FROM users WHERE username LIKE '%Lubna%razal%';")
print("\n" + "="*70)
print("STEP 3: Try logging in again with:")
print("="*70)
print(f"Username: Lubna razal (with single space)")
print(f"Password: {ACTUAL_PASSWORD}")
print("="*70)
