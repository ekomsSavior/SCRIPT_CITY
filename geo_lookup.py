#!/usr/bin/env python3
import requests
import os
import sys
from datetime import datetime

def lookup_ip(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}").json()
        if res.get("status") != "success":
            print(f"[!] Lookup failed: {res.get('message')}")
            return None
        return res
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def log_result(ip_data, ip):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, "geo_results.txt")

    log_entry = (
        f"\n=== IP Lookup: {ip} | {datetime.utcnow().isoformat()} UTC ===\n"
        f"IP Address   : {ip}\n"
        f"Country      : {ip_data.get('country')}\n"
        f"Region       : {ip_data.get('regionName')}\n"
        f"City         : {ip_data.get('city')}\n"
        f"ZIP          : {ip_data.get('zip')}\n"
        f"Lat/Lon      : {ip_data.get('lat')}, {ip_data.get('lon')}\n"
        f"ISP          : {ip_data.get('isp')}\n"
        f"Org          : {ip_data.get('org')}\n"
        f"Timezone     : {ip_data.get('timezone')}\n"
        f"------------------------------------------------------------\n"
    )

    with open(logfile, "a") as f:
        f.write(log_entry)

    print(log_entry)

def main():
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter IP to lookup: ").strip()

    print(f"[+] Looking up {ip}...")
    data = lookup_ip(ip)
    if data:
        log_result(data, ip)
    else:
        print("[!] Failed to get geolocation.")

if __name__ == "__main__":
    main()
