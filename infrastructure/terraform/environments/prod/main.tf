# ------------------------------------------------------------------------------
# Document Management and AI Chatbot System - Production Environment
# ------------------------------------------------------------------------------
# This Terraform configuration defines the production infrastructure for the
# Document Management and AI Chatbot System, implementing a highly available,
# scalable, and secure AWS environment.
# ------------------------------------------------------------------------------

# Configure Terraform providers
terraform {
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
  required_version = ">= 1.0.0"

  # Configure S3 backend for state management with DynamoDB locking
  backend "s3" {
    bucket         = "${var.terraform_state_bucket}"
    key            = "prod/terraform.tfstate"
    region         = "${var.aws_region}"
    dynamodb_table = "${var.terraform_lock_table}"
    encrypt        = true
    profile        = "${var.aws_profile}"
  }
}

# Configure AWS provider
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Define local values
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# VPC Module - Creates the VPC infrastructure with public, private, and database subnets
module "vpc" {
  source = "../../modules/vpc"

  environment           = var.environment
  project_name          = var.project_name
  vpc_cidr              = var.vpc_cidr
  availability_zones    = var.availability_zones
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
}

# Security Groups Module - Creates security groups for ALB, ECS, and RDS resources
module "security_groups" {
  source = "../../modules/security_groups"

  environment    = var.environment
  project_name   = var.project_name
  vpc_id         = module.vpc.vpc_id
  vpc_cidr       = module.vpc.vpc_cidr_block
  container_port = var.container_port
}

# S3 Module - Creates S3 buckets for document storage and logging
module "s3" {
  source = "../../modules/s3"

  environment                      = var.environment
  project_name                     = var.project_name
  document_bucket_name             = var.document_bucket_name
  log_bucket_name                  = var.log_bucket_name
  force_destroy                    = var.force_destroy_buckets
  enable_versioning                = true
  standard_ia_transition_days      = 90
  noncurrent_version_expiration_days = 365
  log_expiration_days              = 90
  enable_cors                      = false
}

# SNS Module - Creates SNS topics for alarms and notifications
module "sns" {
  source = "../../modules/sns"

  environment  = var.environment
  project_name = var.project_name
  alarm_email  = var.alarm_email
}

# IAM Module - Creates IAM roles and policies for ECS tasks and RDS monitoring
module "iam" {
  source = "../../modules/iam"

  environment          = var.environment
  project_name         = var.project_name
  document_bucket_name = module.s3.document_bucket_name
}

# Secrets Module - Creates and manages secrets in AWS Secrets Manager
module "secrets" {
  source = "../../modules/secrets"

  environment     = var.environment
  project_name    = var.project_name
  db_password     = var.db_password
  openai_api_key  = var.openai_api_key
}

# RDS Module - Creates the RDS PostgreSQL database instance with high availability
module "rds" {
  source = "../../modules/rds"

  environment           = var.environment
  project_name          = var.project_name
  vpc_id                = module.vpc.vpc_id
  database_subnet_ids   = module.vpc.database_subnet_ids
  db_security_group_id  = module.security_groups.db_security_group_id
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = module.secrets.db_password_secret_arn
  db_allocated_storage  = var.db_allocated_storage
  db_multi_az           = var.db_multi_az
  monitoring_role_arn   = module.iam.rds_monitoring_role_arn
  alarm_actions         = [module.sns.alarm_topic_arn]
}

# ALB Module - Creates the Application Load Balancer for routing traffic to ECS services
module "alb" {
  source = "../../modules/alb"

  environment           = var.environment
  project_name          = var.project_name
  vpc_id                = module.vpc.vpc_id
  public_subnets        = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
  certificate_arn       = var.certificate_arn
  container_port        = var.container_port
  enable_waf            = true
  log_bucket            = module.s3.log_bucket_name
  alarm_sns_topic_arn   = module.sns.alarm_topic_arn
}

# ECS Module - Creates the ECS cluster, task definitions, and services
module "ecs" {
  source = "../../modules/ecs"

  environment               = var.environment
  project_name              = var.project_name
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = module.vpc.private_subnet_ids
  ecs_security_group_id     = module.security_groups.ecs_security_group_id
  alb_target_group_arn      = module.alb.target_group_arn
  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_role_arn         = module.iam.ecs_task_role_arn
  container_image           = var.container_image
  container_port            = var.container_port
  cpu                       = var.container_cpu
  memory                    = var.container_memory
  desired_count             = var.desired_count
  min_capacity              = var.min_capacity
  max_capacity              = var.max_capacity
  db_host                   = module.rds.db_endpoint
  db_name                   = var.db_name
  db_username               = var.db_username
  db_password               = module.secrets.db_password_secret_arn
  document_bucket_name      = module.s3.document_bucket_name
  openai_api_key            = module.secrets.openai_api_key_secret_arn
}

# CloudWatch Module - Creates CloudWatch dashboards, alarms, and monitoring resources
module "cloudwatch" {
  source = "../../modules/cloudwatch"

  environment             = var.environment
  project_name            = var.project_name
  vpc_id                  = module.vpc.vpc_id
  cluster_name            = module.ecs.cluster_name
  service_name            = module.ecs.service_name
  db_instance_id          = module.rds.db_instance_id
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.target_group_arn_suffix
  alarm_sns_topic_arn     = module.sns.alarm_topic_arn
}

# Output values for reference
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "db_endpoint" {
  description = "Endpoint of the RDS database"
  value       = module.rds.db_endpoint
}

output "document_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = module.s3.document_bucket_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

output "alarm_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  value       = module.sns.alarm_topic_arn
}