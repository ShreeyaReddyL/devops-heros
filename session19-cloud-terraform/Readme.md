# Session 19 — Cloud & Terraform in Action

Built an end-to-end cloud infrastructure project using Terraform, provisioning a complete AWS environment with VPC, Subnets, Security Groups, EC2, and S3.

---

## Project Architecture

```
Terraform
    │
    ├── VPC (10.0.0.0/16)
    │     │
    │     ├── Public Subnet (10.0.1.0/24) ── AZ: ap-south-1a
    │     │     │
    │     │     ├── Internet Gateway
    │     │     │
    │     │     └── EC2 Instance (t2.micro)
    │     │           ├── Security Group (SSH + HTTP)
    │     │           └── User Data (Apache install)
    │     │
    │     └── Private Subnet (10.0.2.0/24) ── AZ: ap-south-1b
    │
    └── S3 Bucket (terraform state / application assets)
```

---

## Terraform Project Structure

```
terraform-infra/
├── main.tf              # All resource definitions
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output values
├── versions.tf          # Terraform and provider versions
├── terraform.tfvars     # Variable values (not committed)
└── .gitignore           # Ignore .terraform, tfstate, tfvars
```

---

## Terraform Configuration

### versions.tf — Provider Requirements

```hcl
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
```

### variables.tf — Input Variables

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "devops-heros"
}
```

### main.tf — Resource Definitions

```hcl
# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# --- Public Subnet ---
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# --- Private Subnet ---
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "${var.project_name}-private-subnet"
  }
}

# --- Route Table for Public Subnet ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# --- Security Group ---
resource "aws_security_group" "web_sg" {
  name        = "${var.project_name}-web-sg"
  description = "Allow SSH and HTTP traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}

# --- EC2 Instance ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from DevOps Heros!</h1><p>Deployed with Terraform</p>" > /var/www/html/index.html
              EOF

  tags = {
    Name = "${var.project_name}-web-server"
  }
}

# --- S3 Bucket ---
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project_name}-assets-bucket"

  tags = {
    Name        = "${var.project_name}-assets"
    Environment = "dev"
  }
}
```

### outputs.tf — Output Values

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.web.public_ip
}

output "instance_public_dns" {
  description = "EC2 public DNS"
  value       = aws_instance.web.public_dns
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.assets.bucket
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.assets.arn
}
```

---

## Terraform Commands Executed

### 1. Initialize

```bash
terraform init
```
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...
Terraform has been successfully initialized!
```

### 2. Validate

```bash
terraform validate
```
```
Success! The configuration is valid.
```

### 3. Plan

```bash
terraform plan
```
```
Terraform will perform the following actions:

  # aws_instance.web will be created
  # aws_internet_gateway.igw will be created
  # aws_route_table.public will be created
  # aws_route_table_association.public will be created
  # aws_s3_bucket.assets will be created
  # aws_security_group.web_sg will be created
  # aws_subnet.private will be created
  # aws_subnet.public will be created
  # aws_vpc.main will be created

Plan: 9 to add, 0 to change, 0 to destroy.
```

### 4. Apply

```bash
terraform apply -auto-approve
```
```
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:
instance_public_ip  = "13.x.x.x"
instance_public_dns = "ec2-13-x-x-x.ap-south-1.compute.amazonaws.com"
s3_bucket_name      = "devops-heros-assets-bucket"
vpc_id              = "vpc-0abc123def456789"
```

### 5. Verify

```bash
# Check instance is running
aws ec2 describe-instances --filters "Name=tag:Name,Values=devops-heros-web-server" --query 'Reservations[].Instances[].State.Name'

# Access the web server
curl http://13.x.x.x
```
```
<h1>Hello from DevOps Heros!</h1><p>Deployed with Terraform</p>
```

### 6. Destroy

```bash
terraform destroy -auto-approve
```
```
Destroy complete! Resources: 9 destroyed.
```

---

## Terraform State

The state file (`terraform.tfstate`) is critical:
- Maps config resources to real-world infrastructure
- Tracks resource metadata and dependencies
- Must be stored securely (remote backend recommended: S3 + DynamoDB locking)
- **Never commit to git** — contains sensitive data

```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_instance.web

# Remove resource from state (without destroying)
terraform state rm aws_instance.web
```

---

## Resource Dependencies

Terraform automatically determines the order of resource creation based on references:

```
VPC → Subnets → Route Tables → Security Groups → EC2 Instance
  └→ Internet Gateway → Route Table
```

Implicit dependencies: When one resource references another's attributes (e.g., `vpc_id = aws_vpc.main.id`), Terraform creates a dependency graph.

---

## Key Learnings

- Terraform uses a declarative approach — you describe the desired end state
- The state file is the source of truth for Terraform — handle with care
- `terraform plan` is essential before `apply` — always review changes
- Variables and outputs make configurations reusable
- User data scripts enable EC2 bootstrap automation
- Resource dependencies are resolved automatically through reference chains
- Always destroy resources after demos to avoid unexpected AWS charges
