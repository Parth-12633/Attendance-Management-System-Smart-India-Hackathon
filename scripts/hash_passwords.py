#!/usr/bin/env python3
"""
Script to generate password hashes for sample users
Run this to get the proper password hashes for your SQL scripts
"""

from werkzeug.security import generate_password_hash

def generate_sample_hashes():
    passwords = {
        'admin123': 'admin',
        'teacher123': 'teacher',
        'student123': 'student'  # Optional for testing
    }
    
    print("Password hashes for sample users:")
    print("=" * 50)
    
    for password, role in passwords.items():
        hash_value = generate_password_hash(password)
        print(f"{role.upper()} password '{password}': {hash_value}")
        print()

if __name__ == '__main__':
    generate_sample_hashes()
