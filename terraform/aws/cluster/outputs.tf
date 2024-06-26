output "cluster_id" {
  description = "EKS cluster ID."
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane."
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane."
  value       = module.eks.cluster_security_group_id
}

output "kubectl_config" {
  description = "kubectl config as generated by the module."
  value       = module.eks.kubeconfig
}

output "config_map_aws_auth" {
  description = "A kubernetes configuration to authenticate to this EKS cluster."
  value       = module.eks.config_map_aws_auth
}

output "region" {
  description = "AWS region"
  value       = var.region
}

output "cluster_name" {
  description = "Kubernetes Cluster Name"
  value       = local.cluster_name
}

output "elasticache_endpoint" {
  description = "Elasticache Endpoint"
  value = aws_elasticache_cluster.cluster.cluster_address
}

output "elasticache_port" {
  description = "Elasticache Port"
  value = aws_elasticache_cluster.cluster.port
}

output "postgres_endpoint" {
  description = "RDS Postgres Endpoint"
  value = aws_db_instance.postgres.address
}

output "postgres_port" {
  description = "RDS Postgres Endpoint"
  value = aws_db_instance.postgres.port
}
