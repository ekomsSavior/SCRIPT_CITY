### For eva_scan.ps1:

logs all output to:

```makefile
C:\Users\<You>\Desktop\eva_scan_report.txt
```

How to Use

Save as eva_scan.ps1

Run like this:

```powershell
powershell -ExecutionPolicy Bypass -File .\eva_scan.ps1

```

Check your Desktop — you'll find

eva_scan_report.txt

---

### FOR: eva_scan_linux.sh

make file executable:

```bash
chmod +x ~/eva_scan_linux.sh
```

Run the Scan:

```bash
~/eva_scan_linux.sh
```

Logs everything to:

```bash
~/eva_scan_report.txt
```

---

### for geo_lookup.py

```bash
python3 geo_lookup.py
> Enter IP to lookup: 8.8.8.8
```

###  Output Log: `logs/geo_results.txt`

```
=== IP Lookup: 8.8.8.8 | 2025-08-03T14:31:15.951Z UTC ===
IP Address   : 8.8.8.8
Country      : United States
Region       : California
City         : Mountain View
ZIP          : 94043
Lat/Lon      : 37.4056, -122.0775
ISP          : Google LLC
Org          : Google Public DNS
Timezone     : America/Los_Angeles
------------------------------------------------------------
```

---


