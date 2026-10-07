# IAM — Identity and Access Management

## What is IAM?

AWS Identity and Access Management (IAM) is a web service that helps you securely control access to AWS resources. IAM enables you to manage authentication (who can sign in) and authorization (what permissions they have).

---

## Core Components

### Users

IAM users represent individual people or applications that interact with AWS. Each user has:
- A unique name within the AWS account
- Credentials: password (console access), access keys (programmatic access)
- Directly attached or inherited permissions

```bash
# Create a user
aws iam create-user --user-name developer1

# List users
aws iam list-users
```

### Groups

Groups are collections of IAM users. Permissions assigned to a group apply to all users in that group.

```bash
# Create a group
aws iam create-group --group-name Developers

# Add user to group
aws iam add-user-to-group --user-name developer1 --group-name Developers

# Attach policy to group
aws iam attach-group-policy --group-name Developers --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### Roles

Roles provide temporary security credentials. Unlike users, roles don't have permanent credentials — they are assumed by users, services, or applications.

**Common role use cases:**
- EC2 instance accessing S3 buckets
- Lambda function accessing DynamoDB
- Cross-account access
- Federated user access (SAML/OIDC)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Policies

JSON documents that define permissions. Policies specify which actions are allowed or denied on which resources.

**Policy structure:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

**Policy types:**
- **AWS Managed:** Pre-built by AWS (e.g., `AmazonS3FullAccess`)
- **Customer Managed:** Created and managed by you
- **Inline:** Embedded directly within a user, group, or role

### Permissions

Permissions are the rules within policies that determine what actions are allowed or denied.

**Evaluation logic:**
1. By default, all requests are denied (implicit deny)
2. An explicit allow overrides implicit deny
3. An explicit deny always wins over any allow

---

## Principle of Least Privilege

Grant only the minimum permissions required to perform a specific task. This reduces the blast radius of compromised credentials.

**Bad practice:**
```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

**Good practice:**
```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::specific-bucket/specific-prefix/*"
}
```

---

## IAM Best Practices

1. **Enable MFA** on all user accounts, especially root
2. **Don't use root account** for day-to-day operations
3. **Use roles** instead of long-term access keys
4. **Rotate credentials** regularly
5. **Use IAM Access Analyzer** to identify unused permissions
6. **Apply least privilege** — start with minimal permissions and add as needed
7. **Use groups** to assign permissions, not individual users
8. **Monitor with CloudTrail** — log all API calls for audit

---

## Common Use Cases

| Use Case | IAM Feature |
|:---|:---|
| Developer access to staging | IAM User + Group + Policy |
| EC2 reading from S3 | IAM Role attached to EC2 |
| Cross-account access | IAM Role with trust policy |
| CI/CD pipeline credentials | IAM Role with OIDC (GitHub Actions) |
| Temporary contractor access | IAM User with time-limited credentials |
