terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    # The bucket name needs to be replaced and create one before deploy cloud infrustructures
    bucket = "guardian-articles-config-bucket"
    key = "terraform.tfstate"
    region = "eu-west-2"
  }
}


provider "aws" {
  region = var.region_name
  default_tags {
    tags = {
      projectName = "Streaming Guardian Articles"
      DeployedFrom = "Terraform"
    }
  }
}


resource "aws_sqs_queue" "guardian_queue" {
    name = var.queue_name
    message_retention_seconds = var.message_retention_seconds
}


resource "aws_secretsmanager_secret" "guardian_api_key_secret" {
    name = var.secret_name
}


resource "aws_secretsmanager_secret_version" "guardian_api_key_version" {
    secret_id = aws_secretsmanager_secret.guardian_api_key_secret.id
    secret_string = var.guardian_api_key
}


data "aws_caller_identity" "current" {}
data "aws_region" "current" {} 