variable "aws_region" {
  description = "AWS region to provision the CampusFix infrastructure in."
  type        = string
  default     = "ap-southeast-2"
}

variable "cluster_name" {
  description = "Name of the EKS control plane."
  type        = string
  default     = "campusfix-eks"
}

variable "cluster_version" {
  description = <<-EOT
    EKS Kubernetes minor version. 1.35 is in Amazon EKS standard support
    (end of standard support: March 2027). Versions 1.31-1.33 have moved to
    extended support, which is billed at a higher hourly rate.
  EOT
  type        = string
  default     = "1.35"
}

variable "environment" {
  description = "Environment tag applied to every resource."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the CampusFix VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones used for the public and private subnets."
  type        = list(string)
  default     = ["ap-southeast-2a", "ap-southeast-2b"]
}

variable "node_instance_types" {
  description = "EC2 instance types for the EKS managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "github_actions_deploy_role_arn" {
  description = "Optional IAM role ARN trusted by GitHub OIDC for CampusFix deployments."
  type        = string
  default     = ""
}
