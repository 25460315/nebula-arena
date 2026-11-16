module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.proyecto}-${terraform.workspace}"
  cluster_version = "1.30"

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  node_security_group_additional_rules = {
    agones_udp = {
      description = "Agones gameservers UDP"
      protocol    = "udp"
      from_port   = 7000
      to_port     = 8000
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
    agones_tcp = {
      description = "Agones gameservers TCP"
      protocol    = "tcp"
      from_port   = 7000
      to_port     = 8000
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  eks_managed_node_groups = {
    juego = {
      name           = "game-pool"
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = ["c7i.xlarge"]

      min_size     = 3
      max_size     = 20
      desired_size = var.nodos_juego

      vpc_security_group_ids = [aws_security_group.juego.id]

      labels = {
        rol = "juego"
      }
    }
  }
}

import {
  to = aws_ecr_repository.imagenes
  id = "nebula-server"
}

resource "aws_ecr_repository" "imagenes" {
  name                 = "nebula-server"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}
