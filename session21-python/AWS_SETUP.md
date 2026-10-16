# CampusFix AWS account and deployment guide

## Current state

- The AWS account has **not** been created or connected here.
- No AWS resources have been provisioned.
- Terraform now includes the EKS EBS CSI add-on and namespace-scoped GitHub
  Actions access. The CI workflow uses GitHub OIDC; it does not need a stored
  AWS access key or kubeconfig.
- The production Helm values target an AWS Application Load Balancer (ALB).
- A push to the deployment branch starts the workflow after the AWS role is
  configured. The workflow also has a manual trigger; GitHub exposes manual
  dispatch only when the workflow file is present on the repository's default
  branch.

## 1. Create and secure your AWS account

Open [AWS account signup](https://portal.aws.amazon.com/billing/signup). AWS
requires you to personally enter and verify your email, identity, phone, and
payment method and accept the account terms. Keep those details private; do
not send passwords, MFA codes, or card information in chat.

AWS currently offers a **Free account plan** and a **Paid account plan**. New
customers receive $100 in signup credits with either plan. If the signup page
offers the Free account plan and EKS is available for your account, that is the
safer starting choice: AWS says it does not charge while that plan is active.
The plan ends when the credits are used or after six months, whichever comes
first, and the account then closes unless upgraded. The Paid plan can access
all services but charges for eligible use beyond credits and for any charges
credits do not cover. AWS's current supported-service list includes EKS for
the new Free Tier signup experience. See [AWS account plan details](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)
and [supported services for new signup](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html).

After signup:

1. Turn on MFA for the root account. Do not create root access keys.
2. In Billing, confirm the plan and credit balance. Create budget email alerts
   (for example at $25, $50, and $75). Budget alerts notify you; they are not
   a hard spending cap.
3. Avoid enabling AWS Organizations or Control Tower for this project. AWS
   says these can upgrade a Free account plan and immediately expire the free
   plan credits.
4. If EKS is unavailable in the plan shown to you, stop and tell me what the
   console says before upgrading or provisioning anything.

### Cost to review before Terraform apply

The current stack includes an EKS control plane, two `t3.medium` EC2 nodes, a
NAT gateway, an internet-facing ALB, public IPv4 addresses, and a 20 GiB EBS
volume. Those are separate billable resources. AWS currently lists EKS standard
support at $0.10 per cluster-hour and gives a NAT gateway example of $0.045 per
hour before data processing. Those two example rates alone are about $0.145 per
hour, or about $106 for 730 hours, before nodes, ALB, storage, IPs, and data
transfer. Actual prices vary by region and usage. Use the [AWS Pricing
Calculator](https://calculator.aws/#/) for `ap-south-1` and this resource list
before applying. Credits are finite: a Paid plan can bill beyond them, while a
Free plan ends when they are depleted.

We should run EKS only for the class demo/evidence window and destroy the stack
afterward. Do not apply Terraform until we have reviewed the actual plan and
regional estimate together.

## 2. Prepare a short-lived AWS CLI session

Use Ubuntu/WSL for Terraform, Helm, `kubectl`, and `eksctl`. First check which
tools are present:

```bash
aws --version
terraform version
helm version
kubectl version --client
eksctl version
```

Do not create long-lived AWS access keys. A practical single-account option is
to use an MFA-protected, non-root console identity for the short project setup
and sign into the CLI with temporary console credentials. AWS CLI v2.32 or
newer supports `aws login`; AWS CloudShell is another browser-authenticated
option with AWS CLI already installed. AWS documents both in [CLI
authentication](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-authentication.html)
and [CloudShell authentication](https://docs.aws.amazon.com/cloudshell/latest/userguide/working-with-aws-cli.html).

Once the account and a non-root console identity are ready, in Ubuntu run:

```bash
aws login --profile campusfix
export AWS_PROFILE=campusfix
export AWS_DEFAULT_REGION=ap-south-1
aws sts get-caller-identity
```

The last command should show the account you just created. If `aws login` is
not available, stop rather than falling back to root access keys; we can use
CloudShell or install/update the CLI together.

## 3. Create a GitHub OIDC deployment role

This role lets only GitHub Actions from this repository's two deployment
branches request temporary AWS credentials. It is separate from the EKS OIDC
provider Terraform creates for the EBS driver and AWS Load Balancer Controller.

1. In AWS IAM, add an OpenID Connect identity provider with URL
   `https://token.actions.githubusercontent.com` and audience
   `sts.amazonaws.com`.
2. Create a role for web identity using that provider.
3. Restrict its trust policy to the repository and branches below. GitHub
   repositories can use either the legacy or immutable subject format. Check
   the repo's creation date and OIDC subject setting; use **only** the matching
   format. For immutable subjects, get the numeric IDs from
   `https://api.github.com/repos/ShreeyaReddyL/devops-heros` and replace the
   placeholders. Do not use a wildcard for the branch or repository.

Legacy subject values:

```text
repo:ShreeyaReddyL/devops-heros:ref:refs/heads/main
repo:ShreeyaReddyL/devops-heros:ref:refs/heads/capstone/campusfix-session21
```

Immutable subject values:

```text
repo:ShreeyaReddyL@<OWNER_ID>/devops-heros@<REPO_ID>:ref:refs/heads/main
repo:ShreeyaReddyL@<OWNER_ID>/devops-heros@<REPO_ID>:ref:refs/heads/capstone/campusfix-session21
```

The role trust policy structure is:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": [
          "<MATCHING_SUBJECT_FOR_MAIN>",
          "<MATCHING_SUBJECT_FOR_CAPSTONE_BRANCH>"
        ]
      }
    }
  }]
}
```

Attach a custom permission policy that allows only EKS cluster discovery for
this cluster. Replace `<ACCOUNT_ID>` with your AWS account ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "eks:DescribeCluster",
    "Resource": "arn:aws:eks:ap-south-1:<ACCOUNT_ID>:cluster/campusfix-eks"
  }]
}
```

The role does not get broad AWS permissions. Terraform will grant it the EKS
`AmazonEKSAdminPolicy` scoped only to the `campusfix` namespace. This lets the
workflow deploy the application without permission to administer the whole
cluster. GitHub's [AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
describes the provider URL, audience, subject condition, and `id-token: write`
permission used by the workflow.

Copy the role ARN (not a key) into `session21-python/terraform/terraform.tfvars`
as `github_actions_deploy_role_arn`. That file is Git-ignored. The example
file contains an empty value intentionally.

## 4. Review Terraform before creating resources

From Ubuntu, in `session21-python/terraform`:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set github_actions_deploy_role_arn to the role ARN.
terraform init
terraform fmt -recursive
terraform validate
terraform plan -out=campusfix.tfplan
```

The plan should include the VPC, EKS cluster and node group, EBS CSI driver,
and the GitHub Actions access entry. `terraform plan` does not show the AWS
bill, so compare this plan with the Pricing Calculator estimate. Share the
plan summary and estimate for review before applying; redact account-sensitive
details if desired. **Do not run `terraform apply` until the plan and cost are
reviewed.**

After the review and the user's go-ahead:

```bash
terraform apply campusfix.tfplan
aws eks update-kubeconfig --region ap-south-1 --name campusfix-eks
kubectl get nodes
```

The EBS CSI add-on is installed by Terraform. Apply the encrypted gp3 Storage
Class:

```bash
kubectl apply -f ../k8s/storageclass-gp3.yaml
```

## 5. Install AWS load balancing and HPA metrics

The production Ingress uses AWS Load Balancer Controller directly, rather than
an in-cluster Nginx ingress controller. The controller creates an internet-
facing ALB for the `/` and `/api` routes. AWS documents this Helm installation
and its IAM policy in [Install AWS Load Balancer Controller with Helm](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html).

Download the current IAM policy version referenced in that AWS procedure,
create a policy, and give it to the controller's Kubernetes service account
using IRSA:

```bash
curl -fsSL -o /tmp/campusfix-lbc-iam-policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.14.1/docs/install/iam_policy.json
aws iam create-policy --policy-name CampusFixLoadBalancerControllerPolicy \
  --policy-document file:///tmp/campusfix-lbc-iam-policy.json
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LBC_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/CampusFixLoadBalancerControllerPolicy"
eksctl create iamserviceaccount \
  --cluster campusfix-eks \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn "$LBC_POLICY_ARN" \
  --override-existing-serviceaccounts \
  --region ap-south-1 \
  --approve
```

Install the controller chart and the ALB class:

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks
VPC_ID=$(terraform output -raw vpc_id)
helm upgrade --install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  --namespace kube-system \
  --version 1.14.0 \
  --set clusterName=campusfix-eks \
  --set region=ap-south-1 \
  --set vpcId="$VPC_ID" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --wait --timeout 5m
# The AWS Load Balancer Controller Helm chart creates the `alb` IngressClass.
kubectl get ingressclass alb
```

Install Metrics Server so the chart's CPU-based HPA can read pod metrics:

```bash
kubectl apply -f \
  https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl wait --for=condition=Available deployment/metrics-server \
  -n kube-system --timeout=180s
```

## 6. Create the database secret and enable GitHub deployment

Create the namespace and a private random database password. The secret is
created in the cluster and is never written to Git:

```bash
kubectl create namespace campusfix --dry-run=client -o yaml | kubectl apply -f -
DB_PASSWORD=$(openssl rand -hex 24)
DATABASE_URL="postgresql+psycopg://campusfix:${DB_PASSWORD}@campusfix-postgres:5432/campusfix"
kubectl -n campusfix create secret generic campusfix-postgres \
  --from-literal=username=campusfix \
  --from-literal=password="$DB_PASSWORD" \
  --from-literal=database=campusfix \
  --from-literal=url="$DATABASE_URL" \
  --dry-run=client -o yaml | kubectl apply -f -
unset DB_PASSWORD DATABASE_URL
```

In the GitHub repository, open **Settings → Secrets and variables → Actions →
Variables** and add:

| Variable | Value |
|---|---|
| `AWS_ROLE_ARN` | The role ARN created in §3 |
| `AWS_REGION` | `ap-south-1` (optional; this is the workflow default) |
| `EKS_CLUSTER_NAME` | `campusfix-eks` (optional; this is the workflow default) |

Do not add AWS access keys or a kubeconfig. Once this workflow version is on
the default branch, open **Actions → CampusFix CI/CD → Run workflow**, select
`capstone/campusfix-session21`, and run it. Otherwise, push a normal commit to
the capstone branch after adding the variable; the workflow builds and scans
the commit, publishes both GHCR images, assumes the role through OIDC, deploys
the Helm release, and checks the rollout. The deployment job stays skipped
until `AWS_ROLE_ARN` exists.

When it succeeds, verify from Ubuntu:

```bash
kubectl get pods -n campusfix
kubectl get svc -n campusfix
helm list -n campusfix
kubectl get ingress -n campusfix
```

The Ingress `ADDRESS` is the AWS ALB DNS name. Open it in a browser to show the
public CampusFix app; test ticket creation and the `/api` route.

## 7. Evidence and cleanup

For the AWS portion of the submission, capture genuine screenshots of the
Terraform plan (before apply), EKS cluster and node group, healthy CampusFix
pods/services, Helm release, ALB Ingress address and browser app, and the
successful GitHub Actions deployment. Capture the destroy result after the
evidence is complete. Keep AWS billing/account screenshots private unless the
instructor specifically requests them.

When the demo is finished, first remove the application so its ALB and EBS
volume can be released, then remove the cluster:

```bash
helm uninstall campusfix -n campusfix
# Wait until the Ingress is gone and its ALB disappears from EC2 → Load Balancers.
helm uninstall aws-load-balancer-controller -n kube-system
eksctl delete iamserviceaccount \
  --cluster campusfix-eks \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --region ap-south-1
kubectl delete -f ../k8s/storageclass-gp3.yaml
terraform destroy
```

Confirm the ALB is gone in EC2 → Load Balancers before destroying the cluster;
if it remains, do not leave it running. After cleanup, remove the GitHub
`AWS_ROLE_ARN` variable and delete the project-only IAM role, policy, and
GitHub OIDC provider if nothing else uses them. Check Billing for remaining
NAT gateways, load balancers, EBS volumes, snapshots, and public IPv4 addresses.
