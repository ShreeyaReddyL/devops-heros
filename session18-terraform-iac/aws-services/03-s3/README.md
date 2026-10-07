# S3 — Simple Storage Service

## What is S3?

Amazon Simple Storage Service (S3) is an object storage service offering industry-leading scalability, data availability, security, and performance. S3 can store and retrieve any amount of data from anywhere.

---

## Core Concepts

### Buckets

Containers for storing objects. Bucket names must be globally unique across all AWS accounts.

```bash
# Create a bucket
aws s3 mb s3://my-unique-bucket-name

# List buckets
aws s3 ls

# Delete a bucket
aws s3 rb s3://my-unique-bucket-name --force
```

### Objects

Files stored in S3 buckets. Each object consists of:
- **Key:** The unique identifier (file path) within the bucket
- **Value:** The file data (up to 5TB per object)
- **Metadata:** Key-value pairs describing the object
- **Version ID:** Unique identifier when versioning is enabled

```bash
# Upload an object
aws s3 cp myfile.txt s3://my-bucket/

# Download an object
aws s3 cp s3://my-bucket/myfile.txt ./

# List objects
aws s3 ls s3://my-bucket/

# Delete an object
aws s3 rm s3://my-bucket/myfile.txt
```

### Storage Classes

| Class | Use Case | Availability | Cost |
|:---|:---|:---|:---|
| **Standard** | Frequently accessed data | 99.99% | Highest |
| **Intelligent-Tiering** | Unknown access patterns | 99.9% | Auto-optimized |
| **Standard-IA** | Infrequent access, rapid retrieval | 99.9% | Lower storage, retrieval fee |
| **One Zone-IA** | Infrequent, re-creatable data | 99.5% | Lower than Standard-IA |
| **Glacier Instant** | Archive with instant retrieval | 99.9% | Very low storage |
| **Glacier Flexible** | Archive, minutes to hours retrieval | 99.99% | Very low storage |
| **Glacier Deep Archive** | Long-term archive, 12-hour retrieval | 99.99% | Lowest |

### Versioning

Keeps multiple versions of an object in the same bucket. Protects against accidental deletions and overwrites.

```bash
# Enable versioning
aws s3api put-bucket-versioning --bucket my-bucket --versioning-configuration Status=Enabled

# List object versions
aws s3api list-object-versions --bucket my-bucket
```

### Lifecycle Policies

Automate transitions between storage classes or object deletion based on age.

```json
{
  "Rules": [
    {
      "ID": "Move to IA after 30 days",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### Encryption

| Type | Description |
|:---|:---|
| **SSE-S3** | AWS manages encryption keys |
| **SSE-KMS** | AWS KMS manages keys (audit trail via CloudTrail) |
| **SSE-C** | Customer provides encryption keys |
| **Client-side** | Encrypt data before uploading |

### Bucket Policies

JSON-based policies controlling access at the bucket level.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-website-bucket/*"
    }
  ]
}
```

---

## Common Use Cases

- **Static website hosting:** HTML, CSS, JS files served directly from S3
- **Backup and archive:** Automated backups with lifecycle policies to Glacier
- **Data lake:** Central repository for structured and unstructured data
- **Log storage:** CloudTrail, VPC Flow Logs, ELB access logs
- **Media hosting:** Images, videos, and documents for web applications
- **Terraform state:** Remote backend for storing `terraform.tfstate`
