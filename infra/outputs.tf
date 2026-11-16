output "cluster" {
  description = "Nombre del clúster EKS creado"
  value       = module.eks.cluster_name
}

output "registro" {
  description = "URL del repositorio Amazon ECR"
  value       = aws_ecr_repository.imagenes.repository_url
}
