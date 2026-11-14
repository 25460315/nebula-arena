output "cluster" {
  description = "Nombre del clúster Amazon EKS"
  value       = module.eks.cluster_name
}

output "registro" {
  description = "URL del repositorio Amazon ECR para nebula-server"
  value       = aws_ecr_repository.imagenes.repository_url
}

output "leaderboard_url" {
  description = "Function URL pública de la tabla de líderes Serverless (Lambda + DynamoDB)"
  value       = aws_lambda_function_url.leaderboard_url.function_url
}

output "kubeconfig_command" {
  description = "Comando para conectar kubectl al clúster EKS"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
