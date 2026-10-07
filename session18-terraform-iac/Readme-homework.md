# Session 18 — Terraform & Infrastructure as Code

Explored Infrastructure as Code (IaC) principles and hands-on Terraform usage. Created an AWS S3 bucket using Terraform and documented AWS services.

---

## Task 1: Terraform S3 Demo

### Project Structure

```
terraform-s3-demo/
├── main.tf              # S3 bucket resource definition
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output value definitions
├── provider.tf          # AWS provider configuration
├── terraform.tfvars     # Variable values
└── README.md            # Documentation
```

### Terraform Files

**provider.tf:**
```hcl
provider "aws" {
  region = var.aws_region
}
```

**variables.tf:**
```hcl
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-south-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}
```

**terraform.tfvars:**
```hcl
aws_region  = "ap-south-1"
bucket_name = "devops-heros-demo-bucket"
environment = "dev"
```

**main.tf:**
```hcl
resource "aws_s3_bucket" "demo" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
```

**outputs.tf:**
```hcl
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.demo.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.demo.arn
}

output "bucket_region" {
  description = "Region of the S3 bucket"
  value       = aws_s3_bucket.demo.region
}
```

### Terraform Workflow Execution

#### 1. terraform init
Initializes the working directory, downloads provider plugins.

```bash
terraform init
```
```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of hashicorp/aws...
- Installing hashicorp/aws v5.x.x...
- Installed hashicorp/aws v5.x.x

Terraform has been successfully initialized!
```

#### 2. terraform fmt
Formats `.tf` files to canonical HCL style.

```bash
terraform fmt
```

#### 3. terraform validate
Validates the configuration syntax and internal consistency.

```bash
terraform validate
```
```
Success! The configuration is valid.
```

#### 4. terraform plan
Creates an execution plan showing what will be created/changed/destroyed.

```bash
terraform plan
```
```
Terraform will perform the following actions:

  # aws_s3_bucket.demo will be created
  + resource "aws_s3_bucket" "demo" {
      + arn                    = (known after apply)
      + bucket                 = "devops-heros-demo-bucket"
      + id                     = (known after apply)
      + region                 = (known after apply)
      + tags                   = {
          + "Environment" = "dev"
          + "ManagedBy"   = "Terraform"
          + "Name"        = "devops-heros-demo-bucket"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

#### 5. terraform apply
Applies the changes to reach the desired state.

```bash
terraform apply
```
```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:
bucket_arn    = "arn:aws:s3:::devops-heros-demo-bucket"
bucket_name   = "devops-heros-demo-bucket"
bucket_region = "ap-south-1"
```

#### 6. terraform show
Shows the current state of managed resources.

```bash
terraform show
```
```
# aws_s3_bucket.demo:
resource "aws_s3_bucket" "demo" {
    arn            = "arn:aws:s3:::devops-heros-demo-bucket"
    bucket         = "devops-heros-demo-bucket"
    hosted_zone_id = "Z11RGJOFQNVJUP"
    id             = "devops-heros-demo-bucket"
    region         = "ap-south-1"
    tags           = {
        "Environment" = "dev"
        "ManagedBy"   = "Terraform"
        "Name"        = "devops-heros-demo-bucket"
    }
}
```

#### 7. terraform output
Displays output values.

```bash
terraform output
```
```
bucket_arn    = "arn:aws:s3:::devops-heros-demo-bucket"
bucket_name   = "devops-heros-demo-bucket"
bucket_region = "ap-south-1"
```

#### 8. terraform destroy
Tears down all managed infrastructure.

```bash
terraform destroy
```
```
Destroy complete! Resources: 1 destroyed.
```

---

## Task 2: AWS Services Research

### 01. IAM — Identity and Access Management (Governance)

**What is IAM?** AWS service for managing access to AWS resources securely. Controls who (authentication) can do what (authorization).

| Concept | Description |
|:---|:---|
| **Users** | Individual identities with long-term credentials (password, access keys) |
| **Groups** | Collections of users sharing the same permissions |
| **Roles** | Temporary credentials assumed by users, services, or applications |
| **Policies** | JSON documents defining allowed/denied actions on resources |
| **Permissions** | The actual allow/deny rules within policies |

**Principle of Least Privilege:** Grant only the minimum permissions required to perform a task.

**Best Practices:**
- Enable MFA for all users, especially root
- Use roles instead of long-term access keys
- Regularly rotate credentials
- Use IAM Access Analyzer to identify unused permissions
- Never use root account for daily operations

### 02. EC2 — Elastic Compute Cloud (Compute)

**What is EC2?** Virtual servers in the cloud that provide resizable compute capacity.

| Concept | Description |
|:---|:---|
| **AMI** | Amazon Machine Image — template containing OS, applications, and configuration |
| **Instance Types** | Hardware configurations (e.g., `t2.micro`, `m5.large`, `c5.xlarge`) |
| **Key Pairs** | SSH key pairs for secure instance access |
| **Security Groups** | Virtual firewall controlling inbound/outbound traffic |
| **EBS** | Elastic Block Store — persistent block storage volumes |
| **Public/Private IP** | Public IPs for internet access, private IPs for internal communication |

**Instance Lifecycle:** `Pending → Running → Stopping → Stopped → Terminated`

**Common use cases:** Web servers, application servers, development environments, batch processing.

### 03. S3 — Simple Storage Service (Storage)

**What is S3?** Object storage service offering scalability, data availability, security, and performance.

| Concept | Description |
|:---|:---|
| **Buckets** | Containers for objects; globally unique names |
| **Objects** | Files stored in buckets (up to 5TB each) |
| **Storage Classes** | Standard, Intelligent-Tiering, Glacier, Deep Archive |
| **Versioning** | Keep multiple versions of objects for protection |
| **Lifecycle Policies** | Automate transitions between storage classes or deletion |
| **Encryption** | SSE-S3, SSE-KMS, SSE-C for data at rest |
| **Bucket Policies** | JSON-based access control at the bucket level |

**Common use cases:** Static website hosting, backup/archive, data lake, log storage.

### 04. VPC — Virtual Private Cloud (Networking)

**What is VPC?** Isolated virtual network within AWS where you launch resources.

| Concept | Description |
|:---|:---|
| **CIDR** | IP address range for the VPC (e.g., `10.0.0.0/16`) |
| **Subnets** | Segments of VPC CIDR, placed in specific Availability Zones |
| **Route Tables** | Rules determining where network traffic is directed |
| **Internet Gateway** | Enables communication between VPC and the internet |
| **NAT Gateway** | Allows private subnet instances to access internet (outbound only) |
| **Security Groups** | Stateful firewall at the instance level |
| **Network ACLs** | Stateless firewall at the subnet level |

**Public subnet:** Has route to Internet Gateway → resources get public IPs.
**Private subnet:** No direct internet route → uses NAT Gateway for outbound traffic.

### 05. DynamoDB & RDS — Database Services

#### DynamoDB (NoSQL)

| Concept | Description |
|:---|:---|
| **Tables** | Collections of items (similar to rows) |
| **Items** | Individual records with attributes |
| **Partition Key** | Primary key for data distribution |
| **Sort Key** | Optional secondary key for range queries |
| **Use Cases** | Real-time apps, gaming, IoT, session management |

#### RDS (Relational Database Service)

| Concept | Description |
|:---|:---|
| **Supported Engines** | MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Aurora |
| **DB Instances** | Managed database server instances |
| **Multi-AZ** | Synchronous replication to standby in different AZ |
| **Read Replicas** | Asynchronous read copies for scaling read workloads |
| **Backups** | Automated backups with point-in-time recovery |
| **Use Cases** | E-commerce, CRM, ERP, financial applications |

---

## Terraform Lifecycle Summary

```
Write Code (.tf)
      │
      ▼
terraform init      ← Downloads provider plugins, initializes backend
      │
      ▼
terraform fmt       ← Formats code to canonical style
      │
      ▼
terraform validate  ← Checks syntax and configuration validity
      │
      ▼
terraform plan      ← Preview changes (dry run)
      │
      ▼
terraform apply     ← Apply changes to infrastructure
      │
      ▼
terraform show      ← Inspect current state
      │
      ▼
terraform destroy   ← Tear down infrastructure
```

---

## Key Learnings

- **IaC** makes infrastructure reproducible, version-controlled, and auditable
- Terraform uses HCL (HashiCorp Configuration Language) for declarative infrastructure definition
- **State file** (`terraform.tfstate`) tracks the mapping between config and real resources — never commit to git
- `terraform plan` is the safety net — always review before `apply`
- Variables and outputs make configurations reusable across environments
- AWS services work together: VPC provides networking, EC2 provides compute, S3 provides storage, IAM secures everything
