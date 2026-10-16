# CampusFix AWS account and deployment guide

## Current state

- The AWS account exists, and the AWS CLI profile `campusfix` has successfully
  authenticated with temporary credentials in `ap-southeast-2`. Credentials
  remain in the local AWS config/cache and are not stored in this repository.
- No CampusFix AWS infrastructure has been provisioned.
- `terraform init` and `terraform validate` succeeded. The first read-only plan
  proposed 62 additions, 0 changes, and 0 deletions. That plan included an IAM
  OIDC provider and must not be applied because an AWS Organizations SCP denies
  OIDC-provider operations. No CampusFix resources have been created.
- Terraform has since been changed to disable IRSA and give the EBS CSI driver
  AWS access through EKS Pod Identity. Regenerate and inspect the plan; it must
  not contain `aws_iam_openid_connect_provider` before applying.
- The same SCP prevents GitHub Actions from using OIDC to deploy to AWS. Keep
  `github_actions_deploy_role_arn` empty and deploy manually with Helm from the
  authenticated Ubuntu session. Do not put long-lived AWS keys in GitHub.
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
3. EKS is listed as available in the new Free Tier experience, but usage still
   consumes credits. Do not activate Advanced AWS features just to bypass the
   OIDC restriction: AWS requires an account upgrade, removes any project spend
   limit, and says activation cannot be reversed. Review the account plan and
   credits first.
4. If EKS or a required action is unavailable in the plan shown to you, stop
   before provisioning and review the account policy and cost impact.

### Cost to review before Terraform apply

The planned stack includes an EKS control plane, two `t3.medium` EC2 nodes, a
NAT gateway, an internet-facing ALB, public IPv4 addresses, worker EBS root
volumes, a database PVC, a KMS key, and CloudWatch logs. Those are separate
billable resources. For a 730-hour month, the current rates for just three
always-on components are approximately:

| Component | Calculation | Monthly subtotal |
|---|---:|---:|
| EKS standard-support control plane | $0.10/hour × 730 | $73.00 |
| One Sydney NAT gateway | $0.059/hour × 730 | $43.07 |
| Two Sydney `t3.medium` Linux nodes | $0.0528/hour × 2 × 730 | $77.09 |
| **Baseline for these three components** |  | **$193.16** |

This is a floor, not a full estimate. It excludes the ALB hourly and capacity
charges, public IPv4 addresses, EBS, KMS, log ingestion/storage, NAT data
processing, and data transfer. AWS charges NAT gateways by the hour and by
processed data; ALBs have hourly and LCU charges; public IPv4 addresses are
charged separately. The AWS Price List API returned the `t3.medium` Sydney
rate used above. See [EKS pricing](https://aws.amazon.com/eks/pricing/), the
[Sydney NAT gateway pricing example](https://aws.amazon.com/network-firewall/pricing/),
[VPC pricing](https://aws.amazon.com/vpc/pricing/), [ELB
pricing](https://aws.amazon.com/elasticloadbalancing/pricing/), and the [AWS
Price List Query API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-price-list-query-api.html).

The displayed $100 credit balance is below this full-month baseline. Confirm
which charges the account plan credits cover, use the [AWS Pricing
Calculator](https://calculator.aws/#/) for `ap-southeast-2`, and run the stack
only for the evidence window. Do not leave the cluster running unattended.
After evidence capture, follow the cleanup steps below and check Billing for
remaining resources.

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

The AWS CLI profile `campusfix` is already signed in. If its session expires,
sign in again from Ubuntu/WSL with the remote flow:

```bash
aws login --profile campusfix --remote
aws sts get-caller-identity --profile campusfix
```

The Terraform AWS provider uses the AWS SDK for Go v2, which AWS currently
lists as not supporting the `aws login` credentials provider directly. Use
AWS CLI's `credential_process` bridge for Terraform instead of creating
long-term access keys:

```bash
aws configure set credential_process \
  "aws configure export-credentials --profile campusfix --format process" \
  --profile campusfix-terraform
aws configure set region ap-southeast-2 --profile campusfix-terraform
aws sts get-caller-identity --profile campusfix-terraform
```

The final command should identify the same AWS account and role. Terraform
commands must use `AWS_PROFILE=campusfix-terraform`. AWS documents the
credential-process workaround in [login credential provider
support](https://docs.aws.amazon.com/sdkref/latest/guide/feature-login-credentials.html).

## 3. GitHub Actions deployment status

The Free Tier project SCP explicitly denies
`iam:ListOpenIDConnectProviders`; the original Terraform plan also showed that
it would create an IAM OIDC provider. Do not try to create a GitHub OIDC
provider or apply a plan that contains `aws_iam_openid_connect_provider`.
Account-level `AdministratorAccess` cannot override an SCP deny.

For this Free Tier deployment, leave
`github_actions_deploy_role_arn = ""` in the ignored `terraform.tfvars` file.
GitHub Actions can still test the code, build and scan the images, and publish
them to GHCR. Its optional AWS deploy job will remain skipped. Deploy to EKS
manually from the Ubuntu session with the temporary `campusfix-terraform`
profile. Do not store AWS access keys or a kubeconfig in GitHub.

AWS EKS Pod Identity is used for the EBS CSI and Load Balancer Controller
workloads. Pod Identity associates an IAM role directly with a Kubernetes
service account and does not require an IAM OIDC provider. See [EKS Pod
Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html).

## 4. Review Terraform before creating resources

From Ubuntu, in `session21-python/terraform`, first ensure the
`campusfix-terraform` profile passed the identity check above. Then run:

```bash
export AWS_PROFILE=campusfix-terraform
export AWS_DEFAULT_REGION=ap-southeast-2
terraform init
terraform validate
terraform plan -var-file=terraform.tfvars.example -out=campusfix.tfplan
```

This plan should include the VPC, EKS cluster and node group, EBS CSI driver,
and Pod Identity association. It must not include an
`aws_iam_openid_connect_provider`. `terraform plan` does not show the AWS bill,
so compare the plan with the Pricing Calculator estimate. Review the summary
before applying; redact account-sensitive details if sharing the output.

After the review and the user's go-ahead:

```bash
terraform apply campusfix.tfplan
aws eks update-kubeconfig --region ap-southeast-2 --name campusfix-eks
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

Download the IAM policy for the pinned AWS Load Balancer Controller release,
create a Pod Identity role, and associate it with the controller's service
account. The controller supports both IRSA and EKS Pod Identity; Pod Identity
avoids the IAM OIDC-provider operations blocked in this account.

```bash
curl -fsSL -o /tmp/campusfix-lbc-iam-policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.14.1/docs/install/iam_policy.json
LBC_POLICY_ARN=$(aws iam create-policy \
  --policy-name CampusFixLoadBalancerControllerPolicy \
  --policy-document file:///tmp/campusfix-lbc-iam-policy.json \
  --query 'Policy.Arn' --output text)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
EKS_CLUSTER_ARN=$(aws eks describe-cluster --name campusfix-eks \
  --query 'cluster.arn' --output text --region ap-southeast-2)
cat > /tmp/campusfix-lbc-pod-identity-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"],
    "Condition": {"StringEquals": {
      "aws:RequestTag/eks-cluster-arn": "$EKS_CLUSTER_ARN",
      "aws:RequestTag/kubernetes-namespace": "kube-system",
      "aws:RequestTag/kubernetes-service-account": "aws-load-balancer-controller"
    }}
  }]
}
EOF
aws iam create-role \
  --role-name CampusFixLoadBalancerControllerRole \
  --assume-role-policy-document file:///tmp/campusfix-lbc-pod-identity-trust.json
aws iam attach-role-policy \
  --role-name CampusFixLoadBalancerControllerRole \
  --policy-arn "$LBC_POLICY_ARN"
kubectl create serviceaccount aws-load-balancer-controller -n kube-system
LBC_ROLE_ARN=$(aws iam get-role --role-name CampusFixLoadBalancerControllerRole \
  --query 'Role.Arn' --output text)
aws eks create-pod-identity-association \
  --cluster-name campusfix-eks \
  --namespace kube-system \
  --service-account aws-load-balancer-controller \
  --role-arn "$LBC_ROLE_ARN" \
  --region ap-southeast-2
```

Install the controller chart and the ALB class. The service account already
exists and is associated through Pod Identity:

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update eks
VPC_ID=$(terraform output -raw vpc_id)
helm upgrade --install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  --namespace kube-system \
  --version 1.14.0 \
  --set clusterName=campusfix-eks \
  --set region=ap-southeast-2 \
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

## 6. Create the database secret and deploy manually

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

Use an image tag from a successful GitHub Actions run that published both
images to GHCR. The GHCR packages must be public so EKS can pull them without
storing a GitHub token in the cluster. From `session21-python/terraform`, set
`TAG` to that run's commit SHA and deploy with Helm:

```bash
TAG=<successful-github-run-commit-sha>
helm upgrade --install campusfix ../helm/campusfix \
  --namespace campusfix \
  --values ../helm/campusfix/values-prod.yaml \
  --set backend.image=ghcr.io/shreeyareddyl/campusfix-backend \
  --set backend.tag="$TAG" \
  --set frontend.image=ghcr.io/shreeyareddyl/campusfix-frontend \
  --set frontend.tag="$TAG" \
  --wait --timeout 8m
```

The GitHub Actions workflow still tests, builds, scans, and publishes images.
Its AWS deploy job stays skipped because the Free Tier project SCP blocks the
OIDC provider. Do not add static AWS access keys to GitHub Actions.

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
updated Terraform plan (before apply), EKS cluster and node group, healthy
CampusFix pods/services, Helm release, ALB Ingress address and browser app,
and the successful GitHub Actions image build/publish. The AWS deployment is
manual because the current SCP blocks GitHub OIDC. Capture the destroy result
after the evidence is complete. Keep AWS billing/account screenshots private
unless the instructor specifically requests them.

When the demo is finished, first remove the application so its ALB and EBS
volume can be released, then remove the controller and cluster:

```bash
helm uninstall campusfix -n campusfix
# Wait until the Ingress is gone and its ALB disappears from EC2 → Load Balancers.
helm uninstall aws-load-balancer-controller -n kube-system
LBC_ASSOCIATION_ID=$(aws eks list-pod-identity-associations \
  --cluster-name campusfix-eks --namespace kube-system \
  --query "associations[?serviceAccount=='aws-load-balancer-controller'].associationId | [0]" \
  --output text --region ap-southeast-2)
aws eks delete-pod-identity-association --cluster-name campusfix-eks \
  --association-id "$LBC_ASSOCIATION_ID" --region ap-southeast-2
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LBC_POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/CampusFixLoadBalancerControllerPolicy"
aws iam detach-role-policy --role-name CampusFixLoadBalancerControllerRole \
  --policy-arn "$LBC_POLICY_ARN"
aws iam delete-role --role-name CampusFixLoadBalancerControllerRole
aws iam delete-policy --policy-arn "$LBC_POLICY_ARN"
kubectl delete -f ../k8s/storageclass-gp3.yaml
terraform destroy
```

Confirm the ALB is gone in EC2 → Load Balancers before destroying the cluster;
if it remains, do not leave it running. If cleanup reports that the custom IAM
policy has non-default versions, remove those versions before deleting its
default policy. Check Billing for remaining NAT gateways, load balancers, EBS
volumes, snapshots, and public IPv4 addresses.
