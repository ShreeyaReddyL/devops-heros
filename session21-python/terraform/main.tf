locals {
  # Name prefix shared by the VPC, the cluster and every tag.
  name_prefix = "${var.cluster_name}-${var.environment}"

  common_tags = {
    Project     = "campusfix"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# --------------------------------------------------------------------------- #
# Networking: 2 public + 2 private subnets across 2 AZs, one NAT gateway.
# --------------------------------------------------------------------------- #
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = var.cluster_name
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = [cidrsubnet(var.vpc_cidr, 8, 1), cidrsubnet(var.vpc_cidr, 8, 2)]
  public_subnets  = [cidrsubnet(var.vpc_cidr, 8, 101), cidrsubnet(var.vpc_cidr, 8, 102)]

  # A single NAT gateway keeps the monthly bill down for a capstone cluster.
  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = local.common_tags
}

# --------------------------------------------------------------------------- #
# EKS control plane + one managed worker node group.
# --------------------------------------------------------------------------- #
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.29.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Needed once the node group IAM role is managed explicitly below.
  enable_cluster_creator_admin_permissions = true

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    eks-pod-identity-agent = {}
  }

  eks_managed_node_groups = {
    main = {
      name = "${var.cluster_name}-ng"

      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      labels = {
        role = "worker"
      }

      update_config = {
        max_unavailable = 1
      }
    }
  }

  tags = local.common_tags
}