# Development environment configuration for Document Management and AI Chatbot System
# This file serves as the entry point for the development environment infrastructure

# Configure Terraform backend for state management
terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "doc-ai-chatbot-terraform-state-dev"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "doc-ai-chatbot-terraform-locks-dev"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Configure AWS provider for development environment
provider "aws" {
  region  = "us-west-2"
  profile = "dev"
}

provider "random" {}

# Local values for development environment
locals {
  environment_tags = {
    Environment = "dev"
    Project     = "doc-ai-chatbot"
    ManagedBy   = "Terraform"
  }
}

# Call the main module with development-specific variables
module "doc_ai_chatbot" {
  source = "../.."

  # Project settings
  project_name = "doc-ai-chatbot"
  environment  = "dev"
  aws_region   = "us-west-2"
  aws_profile  = "dev"

  # State management
  terraform_state_bucket = "doc-ai-chatbot-terraform-state-dev"
  terraform_lock_table   = "doc-ai-chatbot-terraform-locks-dev"

  # Network configuration
  vpc_cidr              = "10.0.0.0/16"
  availability_zones    = ["us-west-2a", "us-west-2b"]
  public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs  = ["10.0.3.0/24", "10.0.4.0/24"]
  database_subnet_cidrs = ["10.0.5.0/24", "10.0.6.0/24"]
  certificate_arn       = null # No HTTPS for dev environment

  # Storage configuration
  document_bucket_name        = "doc-ai-chatbot-documents-dev"
  log_bucket_name             = "doc-ai-chatbot-logs-dev"
  force_destroy_buckets       = true # Safe for dev environment
  enable_versioning           = true
  standard_ia_transition_days = 90
  log_expiration_days         = 90

  # Database configuration
  db_instance_class    = "db.t3.small" # Cost-effective for dev
  db_name              = "docaichatbot"
  db_username          = "dbadmin"
  db_password          = null # Will be generated if not provided
  db_allocated_storage = 20
  db_multi_az          = false # Cost optimization for dev

  # ECS configuration
  ecs_task_execution_role_arn = null # Will be created if not provided
  ecs_task_role_arn           = null # Will be created if not provided
  container_image             = "doc-ai-chatbot:latest"
  container_port              = 8000
  container_cpu               = 512  # 0.5 vCPU
  container_memory            = 1024 # 1 GB
  desired_count               = 1
  min_capacity                = 1
  max_capacity                = 3

  # Security configuration
  enable_waf = true # Basic WAF protection even for dev

  # Application configuration
  openai_api_key = null # To be provided via environment variable or parameter store

  # Monitoring configuration
  alarm_email = "dev-team@example.com"
}

# Output key resource identifiers
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.doc_ai_chatbot.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.doc_ai_chatbot.alb_dns_name
}

output "document_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = module.doc_ai_chatbot.document_bucket_name
}

output "db_endpoint" {
  description = "Endpoint of the RDS database"
  value       = module.doc_ai_chatbot.db_endpoint
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.doc_ai_chatbot.ecs_cluster_name
}