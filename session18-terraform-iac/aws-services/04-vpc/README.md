# VPC — Virtual Private Cloud

## What is VPC?

Amazon Virtual Private Cloud (VPC) lets you launch AWS resources in a logically isolated virtual network. You have complete control over your virtual networking environment — IP ranges, subnets, route tables, and gateways.

---

## Core Components

### CIDR (Classless Inter-Domain Routing)

Defines the IP address range for the VPC.

| CIDR Block | IP Range | Total IPs |
|:---|:---|:---|
| `10.0.0.0/16` | 10.0.0.0 – 10.0.255.255 | 65,536 |
| `10.0.0.0/24` | 10.0.0.0 – 10.0.0.255 | 256 |
| `172.16.0.0/16` | 172.16.0.0 – 172.16.255.255 | 65,536 |

**VPC CIDR:** Typically `/16` (65,536 IPs)
**Subnet CIDR:** Typically `/24` (256 IPs)

### Subnets

Segments of the VPC CIDR block, each placed in a specific Availability Zone.

**Public Subnet:**
- Has a route to the Internet Gateway
- Resources can have public IPs
- Used for: web servers, NAT gateways, bastion hosts

**Private Subnet:**
- No direct route to the internet
- Uses NAT Gateway for outbound internet access
- Used for: databases, application servers, internal services

```
VPC: 10.0.0.0/16
├── Public Subnet (AZ-a):  10.0.1.0/24
├── Public Subnet (AZ-b):  10.0.2.0/24
├── Private Subnet (AZ-a): 10.0.3.0/24
└── Private Subnet (AZ-b): 10.0.4.0/24
```

### Route Tables

Define rules for where network traffic is directed.

**Public route table:**
| Destination | Target |
|:---|:---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | Internet Gateway |

**Private route table:**
| Destination | Target |
|:---|:---|
| `10.0.0.0/16` | local |
| `0.0.0.0/0` | NAT Gateway |

### Internet Gateway (IGW)

Enables communication between VPC resources and the internet. Attached to the VPC and referenced in public subnet route tables.

- Horizontally scaled, redundant, and highly available
- Supports IPv4 and IPv6
- No bandwidth constraints

### NAT Gateway

Allows instances in private subnets to access the internet for outbound traffic (e.g., downloading updates) while preventing inbound connections.

- Placed in a public subnet
- Requires an Elastic IP
- Managed service — AWS handles availability

```
Private Instance → NAT Gateway (public subnet) → Internet Gateway → Internet
```

### Security Groups

**Stateful** firewall rules at the instance level. If you allow inbound traffic, the return traffic is automatically allowed.

| Feature | Security Group |
|:---|:---|
| Level | Instance |
| State | Stateful |
| Rules | Allow only (implicit deny) |
| Evaluation | All rules evaluated |

### Network ACLs (NACLs)

**Stateless** firewall rules at the subnet level. Both inbound and outbound rules must be explicitly defined.

| Feature | Network ACL |
|:---|:---|
| Level | Subnet |
| State | Stateless |
| Rules | Allow and Deny |
| Evaluation | Rules processed in order (lowest number first) |

### Security Groups vs NACLs

| Aspect | Security Group | Network ACL |
|:---|:---|:---|
| **Scope** | Instance level | Subnet level |
| **Statefulness** | Stateful | Stateless |
| **Default** | Deny all inbound, allow all outbound | Allow all inbound and outbound |
| **Rules** | Allow rules only | Allow and Deny rules |
| **Processing** | All rules evaluated | Rules evaluated in order |

---

## VPC Architecture Diagram

```
                        Internet
                           │
                    ┌──────┴──────┐
                    │Internet GW  │
                    └──────┬──────┘
                           │
        ┌──────────────────┴──────────────────┐
        │              VPC 10.0.0.0/16        │
        │                                      │
        │  ┌─────────────┐  ┌─────────────┐   │
        │  │Public Subnet│  │Public Subnet│   │
        │  │ 10.0.1.0/24 │  │ 10.0.2.0/24 │   │
        │  │  (AZ-a)     │  │  (AZ-b)     │   │
        │  │ [Web Server] │  │ [NAT GW]   │   │
        │  └──────┬──────┘  └──────┬──────┘   │
        │         │                │           │
        │  ┌──────┴──────┐  ┌─────┴───────┐   │
        │  │Priv Subnet  │  │Priv Subnet  │   │
        │  │ 10.0.3.0/24 │  │ 10.0.4.0/24 │   │
        │  │  (AZ-a)     │  │  (AZ-b)     │   │
        │  │ [App Server] │  │ [Database]  │   │
        │  └─────────────┘  └─────────────┘   │
        │                                      │
        └──────────────────────────────────────┘
```

---

## Common Use Cases

- **Multi-tier architecture:** Public subnet for web, private subnet for app and database
- **Hybrid cloud:** VPN or Direct Connect to on-premises network
- **Isolated environments:** Separate VPCs for dev, staging, production
- **Microservices:** Service-to-service communication within private subnets
