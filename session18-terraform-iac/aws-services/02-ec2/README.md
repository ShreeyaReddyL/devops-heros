# EC2 — Elastic Compute Cloud

## What is EC2?

Amazon Elastic Compute Cloud (EC2) provides resizable virtual servers in the cloud. EC2 allows you to launch instances with different operating systems, hardware configurations, and software stacks within minutes.

---

## Core Components

### AMI (Amazon Machine Image)

A template containing the operating system, application server, and applications. AMIs are region-specific.

**Types of AMIs:**
- **AWS-provided:** Amazon Linux, Ubuntu, Windows Server
- **Marketplace:** Third-party pre-configured images
- **Custom:** Your own images created from running instances

### Instance Types

Define the hardware of the host computer — CPU, memory, storage, and networking capacity.

| Family | Purpose | Example |
|:---|:---|:---|
| **t** | General purpose, burstable | `t2.micro`, `t3.medium` |
| **m** | General purpose, balanced | `m5.large`, `m6i.xlarge` |
| **c** | Compute optimized | `c5.2xlarge` |
| **r** | Memory optimized | `r5.large` |
| **g/p** | GPU instances | `g4dn.xlarge`, `p3.2xlarge` |
| **i** | Storage optimized | `i3.large` |

**Naming convention:** `t3.medium` → Family: t, Generation: 3, Size: medium

### Key Pairs

SSH key pairs for secure remote access to EC2 instances.

```bash
# Create a key pair
aws ec2 create-key-pair --key-name my-key --query 'KeyMaterial' --output text > my-key.pem
chmod 400 my-key.pem

# Connect to instance
ssh -i my-key.pem ec2-user@<public-ip>
```

### Security Groups

Virtual firewalls controlling inbound and outbound traffic at the instance level. Security groups are **stateful** — if you allow inbound traffic, the response is automatically allowed.

```bash
# Create security group
aws ec2 create-security-group --group-name web-sg --description "Web server SG" --vpc-id vpc-xxx

# Allow SSH and HTTP
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-xxx --protocol tcp --port 80 --cidr 0.0.0.0/0
```

### EBS (Elastic Block Store)

Persistent block storage volumes that attach to EC2 instances.

**Volume types:**
| Type | Use Case | IOPS |
|:---|:---|:---|
| **gp3** | General purpose SSD | Up to 16,000 |
| **io2** | High-performance SSD | Up to 64,000 |
| **st1** | Throughput-optimized HDD | Up to 500 |
| **sc1** | Cold storage HDD | Up to 250 |

### Public vs Private IP

| Feature | Public IP | Private IP |
|:---|:---|:---|
| **Accessibility** | Internet-reachable | VPC-internal only |
| **Persistence** | Changes on stop/start (unless Elastic IP) | Stays the same |
| **Cost** | Free with running instance (Elastic IP costs if unused) | Free |
| **Use case** | Web servers, bastion hosts | Databases, internal services |

---

## Instance Lifecycle

```
Pending → Running → Stopping → Stopped → Terminated
                  ↘ Shutting-down → Terminated
```

- **Pending:** Instance is launching
- **Running:** Instance is operational and billing
- **Stopping:** Instance is transitioning to stopped (EBS-backed only)
- **Stopped:** Instance is halted, no compute charges (EBS charges continue)
- **Terminated:** Instance is permanently deleted

---

## Common Use Cases

- **Web servers:** Running Apache, Nginx, or application servers
- **Application hosting:** Backend APIs, microservices
- **Development environments:** Temporary dev/test instances
- **Batch processing:** Data processing, scientific computing
- **Bastion hosts:** Secure SSH jump boxes for accessing private instances
