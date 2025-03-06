#---------------------------------------------------------------
# Project and Environment Settings
#---------------------------------------------------------------
# Base project name for all resources
project_name = "doc-ai-chatbot"

# Deployment environment (dev, staging, prod)
environment = "dev"

# AWS region for resource deployment
aws_region = "us-west-2"

# AWS CLI profile to use for deployment
aws_profile = "dev"

#---------------------------------------------------------------
# Terraform State Management
#---------------------------------------------------------------
# S3 bucket for storing Terraform state
terraform_state_bucket = "doc-ai-chatbot-terraform-state-dev"

# DynamoDB table for Terraform state locking
terraform_lock_table = "doc-ai-chatbot-terraform-locks-dev"

#---------------------------------------------------------------
# Networking Configuration
#---------------------------------------------------------------
# VPC CIDR block
vpc_cidr = "10.0.0.0/16"

# Availability zones to use
availability_zones = ["us-west-2a", "us-west-2b"]

# Public subnet CIDR blocks (for ALB)
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]

# Private subnet CIDR blocks (for ECS tasks)
private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]

# Database subnet CIDR blocks (for RDS)
database_subnet_cidrs = ["10.0.5.0/24", "10.0.6.0/24"]

# ARN of the ACM certificate for HTTPS (null for development)
certificate_arn = null

#---------------------------------------------------------------
# Storage Configuration
#---------------------------------------------------------------
# S3 bucket for document storage
document_bucket_name = "doc-ai-chatbot-documents-dev"

# S3 bucket for application logs
log_bucket_name = "doc-ai-chatbot-logs-dev"

# Allow destruction of non-empty buckets during teardown
force_destroy_buckets = true

# Enable versioning on S3 buckets
enable_versioning = true

# Days before transitioning objects to Standard-IA storage class
standard_ia_transition_days = 90

# Days before log expiration
log_expiration_days = 90

#---------------------------------------------------------------
# Database Configuration
#---------------------------------------------------------------
# RDS instance class (dev uses smaller instance)
db_instance_class = "db.t3.small"

# Database name
db_name = "docaichatbot"

# Database admin username
db_username = "dbadmin"

# Database password (to be injected by CI/CD process)
db_password = null

# Allocated storage in GB
db_allocated_storage = 20

# Multi-AZ deployment (disabled for dev to reduce costs)
db_multi_az = false

#---------------------------------------------------------------
# ECS Configuration
#---------------------------------------------------------------
# ECS task execution role ARN (null to create a new one)
ecs_task_execution_role_arn = null

# ECS task role ARN (null to create a new one)
ecs_task_role_arn = null

# Container image URI
container_image = "doc-ai-chatbot:latest"

# Container port for the application
container_port = 8000

# CPU units for the container (512 = 0.5 vCPU)
container_cpu = 512

# Memory allocation for the container in MB
container_memory = 1024

# Desired number of container instances
desired_count = 1

# Minimum number of instances for auto-scaling
min_capacity = 1

# Maximum number of instances for auto-scaling
max_capacity = 3

#---------------------------------------------------------------
# Security and Monitoring
#---------------------------------------------------------------
# Enable AWS WAF for API protection
enable_waf = true

# OpenAI API key (placeholder to be replaced by CI/CD)
openai_api_key = "PLACEHOLDER_API_KEY_TO_BE_INJECTED_BY_CI_PROCESS"

# Email address for CloudWatch alarms
alarm_email = "dev-team@example.com"