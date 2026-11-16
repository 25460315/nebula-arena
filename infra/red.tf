data "aws_availability_zones" "disponibles" {
  state = "available"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.proyecto}-vpc"
  cidr = "10.0.0.0/16"

  azs             = slice(data.aws_availability_zones.disponibles.names, 0, 2)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway      = true
  single_nat_gateway      = true
  enable_dns_hostnames    = true
  map_public_ip_on_launch = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

resource "aws_security_group" "juego" {
  name        = "${var.proyecto}-gameservers"
  description = "Puertos dinamicos TCP/UDP 7000-8000 para Agones GameServers"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Agones UDP GameServers"
    from_port   = 7000
    to_port     = 8000
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Agones TCP/WebSocket GameServers"
    from_port   = 7000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
