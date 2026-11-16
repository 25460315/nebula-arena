terraform {
  required_version = ">= 1.6"
  required_providers {
    aws  = { source = "hashicorp/aws", version = "~> 5.0" }
    helm = { source = "hashicorp/helm", version = "~> 2.13" }
  }
  backend "s3" {
    bucket         = "nebula-tfstate-131470772842"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "nebula-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}
