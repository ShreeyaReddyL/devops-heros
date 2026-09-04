# Networking Fundamentals — Homework

Screenshot of networking commands is in `screenshots/01-networking-commands.jpg`.

## Networking Commands Practice

All commands were executed on `shreeya@devbox` (Ubuntu 22.04 LTS).

---

### 1. `ip addr show`

Shows all network interfaces and their assigned IP addresses.

```bash
shreeya@devbox:~$ ip addr show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 08:00:27:a4:3c:91 brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.120/24 brd 192.168.1.255 scope global dynamic enp0s3
       valid_lft 85234sec preferred_lft 85234sec
    inet6 fe80::a00:27ff:fea4:3c91/64 scope link
       valid_lft forever preferred_lft forever
```

**Understanding:** `ip addr` is the modern replacement for `ifconfig`. It displays each network interface (`lo` = loopback, `enp0s3` = Ethernet) along with its MAC address, IPv4/IPv6 addresses, and subnet mask. The `/24` means a subnet mask of `255.255.255.0`.

---

### 2. `ping`

Tests connectivity to a remote host by sending ICMP echo requests.

```bash
shreeya@devbox:~$ ping -c 4 google.com
PING google.com (142.250.195.174) 56(84) bytes of data.
64 bytes from del12s14-in-f14.1e100.net (142.250.195.174): icmp_seq=1 ttl=117 time=12.3 ms
64 bytes from del12s14-in-f14.1e100.net (142.250.195.174): icmp_seq=2 ttl=117 time=11.8 ms
64 bytes from del12s14-in-f14.1e100.net (142.250.195.174): icmp_seq=3 ttl=117 time=12.1 ms
64 bytes from del12s14-in-f14.1e100.net (142.250.195.174): icmp_seq=4 ttl=117 time=11.9 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 11.800/12.025/12.300/0.183 ms
```

**Understanding:** `ping -c 4` sends 4 ICMP packets. The output shows the round-trip time (RTT) for each packet. 0% packet loss means the host is reachable. TTL (Time To Live) of 117 indicates about ~(128-117) = 11 hops to reach Google.

---

### 3. `traceroute`

Traces the network path packets take to reach a destination.

```bash
shreeya@devbox:~$ traceroute google.com
traceroute to google.com (142.250.195.174), 30 hops max, 60 byte packets
 1  _gateway (192.168.1.1)  1.234 ms  1.102 ms  1.043 ms
 2  10.194.0.1 (10.194.0.1)  5.612 ms  5.823 ms  5.701 ms
 3  172.16.52.1 (172.16.52.1)  8.341 ms  8.112 ms  8.298 ms
 4  * * *
 5  72.14.236.217 (72.14.236.217)  11.423 ms  11.234 ms  11.567 ms
 6  del12s14-in-f14.1e100.net (142.250.195.174)  12.145 ms  12.023 ms  12.198 ms
```

**Understanding:** Each row is a network hop between my machine and the destination. `* * *` means that router didn't respond to the probe (some routers block ICMP). The millisecond values show latency at each hop — useful for finding where slowdowns occur.

---

### 4. `nslookup`

Queries DNS servers to find the IP address associated with a domain name.

```bash
shreeya@devbox:~$ nslookup github.com
Server:     127.0.0.53
Address:    127.0.0.53#53

Non-authoritative answer:
Name:   github.com
Address: 20.207.73.82
```

**Understanding:** `nslookup` contacts the configured DNS resolver (`127.0.0.53` is systemd-resolved on Ubuntu) and returns the IP mapping for the domain. "Non-authoritative" means the answer came from a cache rather than directly from GitHub's DNS server.

---

### 5. `netstat -tuln`

Displays active listening ports and their protocols.

```bash
shreeya@devbox:~$ sudo netstat -tuln
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN
tcp6       0      0 :::22                   :::*                    LISTEN
udp        0      0 127.0.0.53:53           0.0.0.0:*
udp        0      0 0.0.0.0:68              0.0.0.0:*
```

**Understanding:** `-t` = TCP, `-u` = UDP, `-l` = listening sockets, `-n` = numeric (don't resolve names). Port 22 is SSH, 631 is CUPS (printing), 53 is DNS. This is helpful for checking which services are running and on which ports.

---

### 6. `ss -tuln`

Modern replacement for `netstat` — shows socket statistics.

```bash
shreeya@devbox:~$ ss -tuln
Netid State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port Process
udp   UNCONN 0      0       127.0.0.53%lo:53    0.0.0.0:*
udp   UNCONN 0      0       0.0.0.0:68          0.0.0.0:*
tcp   LISTEN 0      128     0.0.0.0:22          0.0.0.0:*
tcp   LISTEN 0      5       127.0.0.1:631       0.0.0.0:*
tcp   LISTEN 0      128     [::]:22             [::]:*
```

**Understanding:** `ss` is faster and more detailed than `netstat`. The output is similar — it shows listening TCP and UDP ports. `0.0.0.0:22` means SSH is listening on all interfaces, while `127.0.0.1:631` means CUPS only accepts local connections.

---

### 7. `curl`

Transfers data from a URL — commonly used to test web services.

```bash
shreeya@devbox:~$ curl -I https://github.com
HTTP/2 200
server: GitHub.com
date: Wed, 03 Sep 2026 10:45:12 GMT
content-type: text/html; charset=utf-8
vary: X-PJAX, X-PJAX-Container
cache-control: max-age=0, private, must-revalidate
x-frame-options: deny
x-content-type-options: nosniff
```

**Understanding:** `curl -I` fetches only the HTTP response headers. We can see the server is responding with HTTP 200 (success), the content type is HTML, and various security headers like `x-frame-options: deny` are present.

---

### 8. `ifconfig`

Legacy command to display or configure network interfaces (deprecated in favor of `ip`).

```bash
shreeya@devbox:~$ ifconfig
enp0s3: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.120  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 fe80::a00:27ff:fea4:3c91  prefixlen 64  scopeid 0x20<link>
        ether 08:00:27:a4:3c:91  txqueuelen 1000  (Ethernet)
        RX packets 124587  bytes 167234912 (167.2 MB)
        TX packets 45213  bytes 5312847 (5.3 MB)

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 3421  bytes 412836 (412.8 KB)
        TX packets 3421  bytes 412836 (412.8 KB)
```

**Understanding:** Shows interface details including IP address, netmask, MAC address (ether), and packet statistics (RX/TX). `ifconfig` requires the `net-tools` package on modern Ubuntu and is being replaced by `ip addr`.

---

### IP Address Classes (Reference Notes)

| Class | Range | Default Subnet Mask | Use Case |
|-------|-------|---------------------|----------|
| A | 1.0.0.0 – 126.255.255.255 | 255.0.0.0 (/8) | Large organizations |
| B | 128.0.0.0 – 191.255.255.255 | 255.255.0.0 (/16) | Mid-size networks |
| C | 192.0.0.0 – 223.255.255.255 | 255.255.255.0 (/24) | Small networks |
| D | 224.0.0.0 – 239.255.255.255 | N/A | Multicast |
| E | 240.0.0.0 – 255.255.255.255 | N/A | Reserved / Research |

**Subnet Mask** separates the network portion from the host portion of an IP address. For example, `192.168.1.120/24` means the first 24 bits (192.168.1) identify the network, and the last 8 bits (.120) identify the host.
