# Shell Scripting Homework

Screenshot of the script output is in `screenshots/01-sysinfo-script-output.jpg`.

## Script: `sysinfo.sh`

A bash script that gathers system details and saves process information to a file.

### What the Script Does

1. Stores the current date, hostname, and username in variables
2. Displays system info (date, hostname, user) in a formatted output
3. Shows disk usage with `df -h`
4. Lists the top processes sorted by memory consumption
5. Prompts the user to enter a folder name using `read -p`
6. Creates the folder with `mkdir -p`
7. Creates a log file inside it with `touch`
8. Redirects the full process list into the log file using `>` and `>>`

### How to Run

```bash
chmod +x sysinfo.sh
./sysinfo.sh
```

### Sample Output

Ran on `shreeya@devbox` (Wednesday, 03 September 2026):

```
╔══════════════════════════════════════════╗
║       SYSTEM INFORMATION REPORT          ║
╚══════════════════════════════════════════╝

  Date & Time  : Wednesday, 03 September 2026 — 04:15 PM IST
  Hostname     : devbox
  Current User : shreeya

──────────── Disk Usage ────────────
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           798M  1.8M  796M   1% /run
/dev/sda2       234G   78G  144G  36% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
/dev/sda1       511M  6.1M  505M   2% /boot/efi
tmpfs           798M   44K  798M   1% /run/user/1000

  Total Storage: total             244G   78G  149G  35% -

──────────── Active Processes ────────────
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
shreeya     2847  1.2  4.3 3852940 170432 ?      Sl   14:02   0:38 /usr/bin/gnome-shell
shreeya     3214  0.4  2.8 1185624 112804 ?      Sl   14:02   0:12 /usr/lib/firefox/firefox
root        1102  0.1  1.5  462840  60248 ?      Ssl  13:58   0:05 /usr/bin/dockerd
shreeya     2901  0.2  1.1  758420  45132 ?      Sl   14:02   0:07 /usr/bin/nautilus
root           1  0.0  0.3  169620  13284 ?      Ss   13:58   0:02 /sbin/init

Enter a folder name for saving the report: reports
  [✓] Directory 'reports' created.
  [✓] File 'reports/process_log.txt' created.

  [✓] Running processes saved to 'reports/process_log.txt'

══════════ Script Completed ══════════
```

### Commands Used

| Command | Purpose |
|---------|---------|
| `echo` | Print formatted output to terminal |
| `date` | Get current date and time |
| `hostname` | Get machine hostname |
| `whoami` | Get current logged-in user |
| `df -h` | Show disk usage in human-readable format |
| `ps aux --sort=-%mem` | List processes sorted by memory usage |
| `read -p` | Prompt user for input |
| `mkdir -p` | Create directory (with parents if needed) |
| `touch` | Create an empty file |
| `>` and `>>` | Output redirection (overwrite / append) |
