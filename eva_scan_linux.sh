#!/bin/bash

LOG=~/eva_scan_report.txt
echo "[*] EVA SCAN – Linux Threat Hunt" | tee "$LOG"
echo "Generated on: $(date)" | tee -a "$LOG"
echo "User: $(whoami)" | tee -a "$LOG"
echo "Hostname: $(hostname)" | tee -a "$LOG"
echo "--------------------------------------" | tee -a "$LOG"

# 1. Active network connections
echo -e "\n[+] Active Network Connections:" | tee -a "$LOG"
ss -tupna | tee -a "$LOG"

# 2. Top processes by CPU
echo -e "\n[+] Top Processes by CPU:" | tee -a "$LOG"
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 15 | tee -a "$LOG"

# 3. Suspicious binaries in /tmp, /dev/shm, ~/.cache
echo -e "\n[+] Suspicious Executables in tmp-like folders:" | tee -a "$LOG"
find /tmp /dev/shm ~/.cache -type f -perm /111 -exec ls -lh {} \; 2>/dev/null | tee -a "$LOG"

# 4. Crontab entries
echo -e "\n[+] Crontab Entries:" | tee -a "$LOG"
crontab -l 2>/dev/null | tee -a "$LOG"
ls -lah /etc/cron* 2>/dev/null | tee -a "$LOG"

# 5. Autostart files (systemd + ~/.config)
echo -e "\n[+] Startup Scripts & Services:" | tee -a "$LOG"
systemctl list-unit-files --type=service --state=enabled 2>/dev/null | tee -a "$LOG"
ls ~/.config/autostart/*.desktop 2>/dev/null | tee -a "$LOG"

# 6. Suspicious bash history
echo -e "\n[+] Suspicious bash history entries:" | tee -a "$LOG"
grep -E 'curl|wget|nc|ncat|bash|\.sh|python|exec|chmod' ~/.bash_history 2>/dev/null | tee -a "$LOG"

# 7. Users on the system
echo -e "\n[+] Local Users:" | tee -a "$LOG"
cut -d: -f1 /etc/passwd | tee -a "$LOG"

# 8. Sudo permissions (privilege abuse detection)
echo -e "\n[+] Sudo Permissions:" | tee -a "$LOG"
sudo -l 2>/dev/null | tee -a "$LOG"

# 9. Kernel modules
echo -e "\n[+] Kernel Modules (malicious LKM check):" | tee -a "$LOG"
lsmod | tee -a "$LOG"

# 10. Recent detections from ClamAV (if installed)
if command -v clamscan &> /dev/null; then
  echo -e "\n[+] ClamAV Scan:" | tee -a "$LOG"
  clamscan -r --bell -i ~ | tee -a "$LOG"
else
  echo -e "\n[!] ClamAV not installed. Skipping malware scan." | tee -a "$LOG"
fi

echo -e "\n✅ EVA SCAN COMPLETE – Report saved to $LOG" | tee -a "$LOG"
