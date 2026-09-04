#!/bin/bash

# ============================================================
# sysinfo.sh — System Information Gathering Script
# Author: Shreeya Reddy L
# Purpose: Shell scripting homework — collects system details,
#          accepts user input, creates directories/files, and
#          redirects process information to a log file.
# ============================================================

# ---------- Gather system details into variables ----------
cur_date=$(date "+%A, %d %B %Y — %I:%M %p %Z")
machine_name=$(hostname)
logged_user=$(whoami)
storage_info=$(df -h --total | tail -1)

# ---------- Display system information ----------
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║       SYSTEM INFORMATION REPORT          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Date & Time  : $cur_date"
echo "  Hostname     : $machine_name"
echo "  Current User : $logged_user"
echo ""

echo "──────────── Disk Usage ────────────"
df -h
echo ""
echo "  Total Storage: $storage_info"
echo ""

echo "──────────── Active Processes ────────────"
ps aux --sort=-%mem | head -12
echo ""

# ---------- User input section ----------
read -p "Enter a folder name for saving the report: " folder_name

# Create the directory
mkdir -p "$folder_name"
echo "  [✓] Directory '$folder_name' created."

# Create a log file inside that directory
report_file="$folder_name/process_log.txt"
touch "$report_file"
echo "  [✓] File '$report_file' created."

# ---------- Redirect process list to the file ----------
echo "Process snapshot captured on: $cur_date" > "$report_file"
echo "Host: $machine_name | User: $logged_user" >> "$report_file"
echo "───────────────────────────────────────────" >> "$report_file"
ps aux --sort=-%mem >> "$report_file"

echo ""
echo "  [✓] Running processes saved to '$report_file'"
echo ""
echo "══════════ Script Completed ══════════"
