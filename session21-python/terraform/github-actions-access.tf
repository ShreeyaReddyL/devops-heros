resource "aws_eks_access_entry" "github_actions_deploy" {
  count = var.github_actions_deploy_role_arn == "" ? 0 : 1

  cluster_name  = module.eks.cluster_name
  principal_arn  = var.github_actions_deploy_role_arn
  type          = "STANDARD"
  user_name     = "github-actions-campusfix"
}

resource "aws_eks_access_policy_association" "github_actions_deploy" {
  count = var.github_actions_deploy_role_arn == "" ? 0 : 1

  cluster_name  = module.eks.cluster_name
  principal_arn = var.github_actions_deploy_role_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"

  access_scope {
    type       = "namespace"
    namespaces = ["campusfix"]
  }

  depends_on = [aws_eks_access_entry.github_actions_deploy]
}
