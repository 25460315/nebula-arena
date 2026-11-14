terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Estado remoto en S3 con bloqueo en DynamoDB (descomenta tras crear el bucket en el paso 0):
  # backend "s3" {
  #   bucket         = "nebula-tfstate-<TU-ID>"
  #   key            = "dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "nebula-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Proyecto = var.proyecto
      Entorno  = terraform.workspace
      Curso    = "Unidad3-VideojuegosNube"
    }
  }
}
