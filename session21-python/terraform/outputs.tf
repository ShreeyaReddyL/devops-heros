output "cluster_name" {
  description = "Name of the CampusFix EKS cluster."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "HTTPS endpoint of the Kubernetes API server."
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version the control plane was created with."
  value       = module.eks.cluster_version
}

output "oidc_provider_arn" {
  description = "OIDC provider ARN, used for IAM roles for service accounts."
  value       = module.eks.oidc_provider.arn
}

output "vpc_id" {
  description = "ID of the VPC hosting the cluster."
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs, required for the AWS Load Balancer Controller."
  value       = module.vpc.public_subnets
}

output "private_subnet_ids" {
  description = "Private subnet IDs the EKS control plane and nodes run in."
  value       = module.vpc.private_subnets
}

output "nat_gateway_public_ip" {
  description = "Elastic IP of the NAT gateway (a recurring charge). Destroy this stack to stop it."
  value       = module.vpc.nat_public_ips
}

output "region" {
  description = "Region the stack was provisioned in."
  value       = var.aws_region
}