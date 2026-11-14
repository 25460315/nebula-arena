module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "nebula-${terraform.workspace}"
  cluster_version = "1.30"

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  eks_managed_node_groups = {
    game_pool = {
      name           = "game-pool"
      instance_types = [var.tipo_instancia]

      min_size     = var.min_nodos
      max_size     = var.max_nodos
      desired_size = var.nodos_juego

      vpc_security_group_ids = [aws_security_group.juego.id]

      labels = {
        rol = "juego"
      }

      tags = {
        "k8s.io/cluster-autoscaler/enabled"                       = "true"
        "k8s.io/cluster-autoscaler/nebula-${terraform.workspace}" = "owned"
      }
    }
  }
}

resource "aws_ecr_repository" "imagenes" {
  name                 = "nebula-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}
