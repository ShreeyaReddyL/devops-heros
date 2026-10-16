# CampusFix AWS Terraform

This Terraform stack creates the VPC, EKS control plane, two-node managed node
group, EBS CSI driver IAM role/add-on, and optional GitHub Actions EKS access
entry for CampusFix. The account setup, cost review, deployment bootstrap,
GitHub OIDC configuration, verification, and cleanup steps are in
[`AWS_SETUP.md`](../AWS_SETUP.md).

**No AWS resources are created by running `terraform init`, `fmt`, `validate`,
or `plan`. `terraform apply` creates billable resources. Do not apply until you
have reviewed the plan and the regional estimate in AWS Pricing Calculator.**

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -recursive
terraform validate
terraform plan -out=campusfix.tfplan
# Review costs and the complete plan before applying.
terraform apply campusfix.tfplan
```

The working `terraform.tfvars`, state files, and plan files are ignored by Git.
Never add AWS credentials or database passwords to this folder or commit them.
