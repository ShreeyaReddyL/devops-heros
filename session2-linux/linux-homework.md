# Linux Fundamentals — Homework

## Task 1: Soft Links vs Hard Links

### What Are They?

A **hard link** is essentially another name (directory entry) pointing to the same inode on disk. Deleting the original file does not affect the hard link because the data persists as long as at least one link references that inode.

A **soft link** (symbolic link) is a special pointer file that stores the *path* to the target. If the original file is removed, the symlink becomes a dangling reference and stops working.

### Key Differences

| Feature | Hard Link | Soft Link |
|---------|-----------|-----------|
| Points to | Same inode | File path |
| Survives original deletion | Yes | No (becomes broken) |
| Works across filesystems | No | Yes |
| Can link directories | No (usually) | Yes |
| Created with | `ln target linkname` | `ln -s target linkname` |

### Practice Commands & Output

```bash
shreeya@devbox:~$ echo "learning linux links" > original.txt

# Create a hard link
shreeya@devbox:~$ ln original.txt hardcopy.txt

# Create a soft link
shreeya@devbox:~$ ln -s original.txt softcopy.txt

shreeya@devbox:~$ ls -li original.txt hardcopy.txt softcopy.txt
262194 -rw-rw-r-- 2 shreeya shreeya 21 Sep  3 14:22 hardcopy.txt
262194 -rw-rw-r-- 2 shreeya shreeya 21 Sep  3 14:22 original.txt
262201 lrwxrwxrwx 1 shreeya shreeya 12 Sep  3 14:22 softcopy.txt -> original.txt

# Both hard link and soft link show the same content
shreeya@devbox:~$ cat hardcopy.txt
learning linux links
shreeya@devbox:~$ cat softcopy.txt
learning linux links

# Now delete the original
shreeya@devbox:~$ rm original.txt

# Hard link still works — same inode, data is intact
shreeya@devbox:~$ cat hardcopy.txt
learning linux links

# Soft link is broken
shreeya@devbox:~$ cat softcopy.txt
cat: softcopy.txt: No such file or directory

shreeya@devbox:~$ ls -l softcopy.txt
lrwxrwxrwx 1 shreeya shreeya 12 Sep  3 14:22 softcopy.txt -> original.txt  # red in terminal = broken
```

### Interview Prep

**Q: What happens when you delete the original file that has both a hard link and a soft link?**

A: The hard link continues to work because it shares the same inode — the data stays on disk until all hard links are removed. The soft link breaks because it merely stores the path to the deleted file.

---

## Task 2: `adduser` vs `useradd`

### Differences

| Feature | `adduser` | `useradd` |
|---------|-----------|-----------|
| Type | High-level, interactive script | Low-level binary |
| Home directory | Auto-created with skeleton files | Not created unless `-m` flag used |
| Password prompt | Yes (asks during creation) | No (must run `passwd` separately) |
| Shell | Sets default shell automatically | Uses `/bin/sh` unless `-s` specified |
| Preferred on Ubuntu | **Yes** | No |

On Ubuntu/Debian, `adduser` is the **recommended** command because it handles everything interactively — creates home dir, copies skeleton configs, prompts for a password, and sets proper permissions. `useradd` is the raw system call used more on RHEL/CentOS or in scripts where you want full control.

### Practice: Creating a Test User

```bash
shreeya@devbox:~$ sudo adduser devtest
Adding user `devtest' ...
Adding new group `devtest' (1002) ...
Adding new user `devtest' (1002) with group `devtest' ...
Creating home directory `/home/devtest' ...
Copying files from `/etc/skel' ...
New password:
Retype new password:
passwd: password updated successfully
Changing the user information for devtest
Enter the new value, or press ENTER for the default
    Full Name []: Dev Test
    Room Number []:
    Work Phone []:
    Home Phone []:
    Other []:
Is the information correct? [Y/n] y

shreeya@devbox:~$ id devtest
uid=1002(devtest) gid=1002(devtest) groups=1002(devtest)

shreeya@devbox:~$ ls /home/devtest/
 .bash_logout  .bashrc  .profile
```

---

## Task 3: `journalctl`

### What Is It?

`journalctl` is the utility to query and display logs collected by **systemd-journald**. It replaces the older approach of reading `/var/log/syslog` or `/var/log/messages` directly.

### Common Usage

```bash
# View all system logs (scrollable)
shreeya@devbox:~$ sudo journalctl

# Show logs since last boot
shreeya@devbox:~$ sudo journalctl -b

# Follow logs in real time (like tail -f)
shreeya@devbox:~$ sudo journalctl -f

# View logs for a specific service
shreeya@devbox:~$ sudo journalctl -u ssh.service
Sep 03 09:14:02 devbox sshd[1842]: Server listening on 0.0.0.0 port 22.
Sep 03 09:14:02 devbox sshd[1842]: Server listening on :: port 22.
Sep 03 12:31:17 devbox sshd[4521]: Accepted publickey for shreeya from 192.168.1.45 port 54322
Sep 03 12:31:17 devbox sshd[4521]: pam_unix(sshd:session): session opened for user shreeya

# Show only the last 20 lines
shreeya@devbox:~$ sudo journalctl -u ssh.service -n 20

# Filter logs by time range
shreeya@devbox:~$ sudo journalctl --since "2026-09-03 09:00" --until "2026-09-03 18:00"
```

### Why It's Useful

- Centralized log management for all systemd services
- Structured metadata (timestamps, PIDs, units) makes filtering efficient
- Persistent across reboots if configured with `Storage=persistent` in `/etc/systemd/journald.conf`

---

## Task 4: Linux Command Cheat Sheet

| Command | Description |
|---------|-------------|
| `ls` | List directory contents |
| `cd` | Change current directory |
| `pwd` | Print working directory path |
| `mkdir` | Create a new directory |
| `rmdir` | Remove an empty directory |
| `rm` | Remove files or directories (`-r` for recursive) |
| `cp` | Copy files and directories |
| `mv` | Move or rename files/directories |
| `cat` | Display file contents |
| `head` / `tail` | Show first/last N lines of a file |
| `grep` | Search for patterns in text |
| `find` | Search for files in a directory hierarchy |
| `chmod` | Change file permissions |
| `chown` | Change file owner and group |
| `ps` | Display currently running processes |
| `top` / `htop` | Real-time process monitoring |
| `kill` | Send a signal to a process |
| `df -h` | Show disk space usage (human-readable) |
| `du -sh` | Show directory size summary |
| `tar` | Archive and compress files |
| `wget` / `curl` | Download files from the web |
| `ssh` | Securely connect to a remote machine |
| `scp` | Securely copy files between machines |
| `systemctl` | Control systemd services |
| `journalctl` | Query systemd journal logs |
| `apt` / `apt-get` | Package management on Debian/Ubuntu |
| `sudo` | Execute commands with superuser privileges |
| `whoami` | Print current username |
| `hostname` | Show or set system hostname |
| `ip addr` | Show network interface addresses |
