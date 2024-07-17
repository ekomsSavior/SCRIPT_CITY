import subprocess
import requests
import re

# Function to run sublist3r and get the list of subdomains
def run_sublist3r(domain):
    try:
        result = subprocess.run(['sublist3r', '-d', domain, '-o', 'subdomains.txt'], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running sublist3r: {result.stderr}")
            return []
        with open('subdomains.txt', 'r') as file:
            subdomains = file.read().splitlines()
        return subdomains
    except Exception as e:
        print(f"Error: {e}")
        return []

# Function to check subdomain for vulnerability patterns
def check_subdomain(subdomain, vuln_patterns):
    try:
        response = requests.get(f'http://{subdomain}', timeout=10)
        response_text = response.text.lower()
        for pattern in vuln_patterns:
            if pattern.lower() in response_text:
                return True
        return False
    except requests.exceptions.RequestException as e:
        return str(e)

# Function to check for NXDOMAIN using dig
def check_nxdomain(subdomain):
    try:
        result = subprocess.run(['dig', '+short', subdomain], capture_output=True, text=True)
        if 'NXDOMAIN' in result.stdout:
            return True
        return False
    except Exception as e:
        return str(e)

# Main function
def main(domain):
    vuln_patterns = [
        'No such host',
        'unavailable',
        'doesn’t exist',
        'Temporary failure in name resolution',
        'Server not found',
        'refused to connect',
    ]

    # Step 1: Run sublist3r to get subdomains
    subdomains = run_sublist3r(domain)
    if not subdomains:
        print("No subdomains found.")
        return

    # Step 2: Check each subdomain for vulnerability patterns
    potentially_vulnerable_subdomains = []
    for subdomain in subdomains:
        result = check_subdomain(subdomain, vuln_patterns)
        if result is True:
            potentially_vulnerable_subdomains.append(subdomain)
        elif isinstance(result, str):
            print(f"Error with {subdomain}: {result}")

    # Step 3: Run dig to check for NXDOMAIN
    nxdomain_subdomains = []
    for subdomain in potentially_vulnerable_subdomains:
        if check_nxdomain(subdomain):
            nxdomain_subdomains.append(subdomain)

    # Final output: List of subdomains with NXDOMAIN
    if nxdomain_subdomains:
        print("Subdomains with NXDOMAIN:")
        for sub in nxdomain_subdomains:
            print(sub)
    else:
        print("No subdomains with NXDOMAIN found.")

if __name__ == "__main__":
    main_domain = input("Enter the main domain: ")
    main(main_domain)
