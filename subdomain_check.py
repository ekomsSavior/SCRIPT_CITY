import requests

# List of subdomains
subdomains = [
    'sub1.example.com',
    'sub2.example.com',
    # Add more subdomains here
]

# Vulnerability patterns
vuln_patterns = [
    'No such host',
    'unavailable',
    'doesn’t exist',
    'Temporary failure in name resolution',
    'Server not found',
    'refused to connect',
]

# Function to check subdomain
def check_subdomain(subdomain):
    try:
        response = requests.get(f'http://{subdomain}', timeout=10)
        response_text = response.text.lower()
        for pattern in vuln_patterns:
            if pattern.lower() in response_text:
                return True
        return False
    except requests.exceptions.RequestException as e:
        return str(e)

# Run the check for each subdomain
for subdomain in subdomains:
    result = check_subdomain(subdomain)
    if result is True:
        print(f'Vulnerable: {subdomain}')
    elif isinstance(result, str):
        print(f'Error with {subdomain}: {result}')
    else:
        print(f'Secure: {subdomain}')
