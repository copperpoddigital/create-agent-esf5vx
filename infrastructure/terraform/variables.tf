# ------------------------------------------------------------------------------
# Document Management and AI Chatbot System - Terraform Variables
# ------------------------------------------------------------------------------
# This file defines all input variables for the Terraform infrastructure deployment
# of the Document Management and AI Chatbot System. It configures AWS resources
# including VPC, ECS, RDS, S3, and ALB across different environments.
# ------------------------------------------------------------------------------

# Project Configuration
variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
  default     = "doc-ai-chatbot"
  
  validation {
    condition     = length(var.project_name) > 0
    error_message = "The project_name value cannot be empty."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "us-west-2"
  
  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-\\d$", var.aws_region))
    error_message = "The aws_region value must be a valid AWS region format (e.g., us-west-2)."
  }
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "default"
  
  validation {
    condition     = length(var.aws_profile) > 0
    error_message = "The aws_profile value cannot be empty."
  }
}

# Terraform Backend Configuration
variable "terraform_state_bucket" {
  description = "S3 bucket name for storing Terraform state"
  type        = string
}

variable "terraform_lock_table" {
  description = "DynamoDB table name for Terraform state locking"
  type        = string
}

# Network Configuration
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "The vpc_cidr value must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones to use for resources"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
  
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least two availability zones must be specified for high availability."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets, one per availability zone"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  
  validation {
    condition     = length(var.public_subnet_cidrs) == length(var.availability_zones)
    error_message = "The number of public subnet CIDRs must match the number of availability zones."
  }
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets, one per availability zone"
  type        = list(string)
  default     = ["10.0.4.0/24", "10.0.5.0/24"]
  
  validation {
    condition     = length(var.private_subnet_cidrs) == length(var.availability_zones)
    error_message = "The number of private subnet CIDRs must match the number of availability zones."
  }
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets, one per availability zone"
  type        = list(string)
  default     = ["10.0.7.0/24", "10.0.8.0/24"]
  
  validation {
    condition     = length(var.database_subnet_cidrs) == length(var.availability_zones)
    error_message = "The number of database subnet CIDRs must match the number of availability zones."
  }
}

# Certificate Configuration
variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
}

# S3 Bucket Configuration
variable "document_bucket_name" {
  description = "Name of the S3 bucket for document storage (optional, will be generated if not provided)"
  type        = string
  default     = null
  
  validation {
    condition     = var.document_bucket_name == null || can(regex("^[a-z0-9][a-z0-9\\.-]{1,61}[a-z0-9]$", var.document_bucket_name))
    error_message = "If provided, document_bucket_name must be a valid S3 bucket name."
  }
}

variable "log_bucket_name" {
  description = "Name of the S3 bucket for logs (optional, will be generated if not provided)"
  type        = string
  default     = null
  
  validation {
    condition     = var.log_bucket_name == null || can(regex("^[a-z0-9][a-z0-9\\.-]{1,61}[a-z0-9]$", var.log_bucket_name))
    error_message = "If provided, log_bucket_name must be a valid S3 bucket name."
  }
}

variable "force_destroy_buckets" {
  description = "Whether to force destroy S3 buckets even if they contain objects"
  type        = bool
  default     = false
}

variable "enable_versioning" {
  description = "Whether to enable versioning for the document bucket"
  type        = bool
  default     = true
}

variable "standard_ia_transition_days" {
  description = "Number of days after which objects should transition to STANDARD_IA storage class"
  type        = number
  default     = 90
  
  validation {
    condition     = var.standard_ia_transition_days > 0
    error_message = "standard_ia_transition_days must be a positive number."
  }
}

variable "log_expiration_days" {
  description = "Number of days after which log objects should be deleted"
  type        = number
  default     = 90
  
  validation {
    condition     = var.log_expiration_days > 0
    error_message = "log_expiration_days must be a positive number."
  }
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "docaichatbot"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "db_name must be a valid PostgreSQL database name."
  }
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "dbadmin"
  
  validation {
    condition     = length(var.db_username) > 0
    error_message = "db_username cannot be empty."
  }
}

variable "db_password" {
  description = "Password for the database (will be generated if not provided)"
  type        = string
  default     = null
  sensitive   = true
  
  validation {
    condition     = var.db_password == null || length(var.db_password) >= 8
    error_message = "The database password must be at least 8 characters long."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for the database in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "db_allocated_storage must be between 20 and 100 GB."
  }
}

variable "db_multi_az" {
  description = "Whether to enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

# ECS Configuration
variable "ecs_task_execution_role_arn" {
  description = "ARN of the IAM role for ECS task execution (will be created if not provided)"
  type        = string
  default     = null
  
  validation {
    condition     = var.ecs_task_execution_role_arn == null || can(regex("^arn:aws:iam::", var.ecs_task_execution_role_arn))
    error_message = "If provided, ecs_task_execution_role_arn must be a valid IAM role ARN."
  }
}

variable "ecs_task_role_arn" {
  description = "ARN of the IAM role for ECS tasks (will be created if not provided)"
  type        = string
  default     = null
  
  validation {
    condition     = var.ecs_task_role_arn == null || can(regex("^arn:aws:iam::", var.ecs_task_role_arn))
    error_message = "If provided, ecs_task_role_arn must be a valid IAM role ARN."
  }
}

variable "container_image" {
  description = "Docker image for the application container"
  type        = string
  default     = "doc-ai-chatbot:latest"
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000
  
  validation {
    condition     = var.container_port > 0 && var.container_port < 65536
    error_message = "container_port must be between 1 and 65535."
  }
}

variable "container_cpu" {
  description = "CPU units for the container (1024 = 1 vCPU)"
  type        = number
  default     = 1024
  
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.container_cpu)
    error_message = "The container_cpu value must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "container_memory" {
  description = "Memory for the container in MB"
  type        = number
  default     = 2048
  
  validation {
    condition     = var.container_memory >= 512
    error_message = "container_memory must be at least 512 MB."
  }
}

# Auto-scaling Configuration
variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 2
  
  validation {
    condition     = var.desired_count > 0
    error_message = "desired_count must be a positive number."
  }
}

variable "min_capacity" {
  description = "Minimum number of container instances for auto-scaling"
  type        = number
  default     = 2
  
  validation {
    condition     = var.min_capacity > 0
    error_message = "min_capacity must be a positive number."
  }
}

variable "max_capacity" {
  description = "Maximum number of container instances for auto-scaling"
  type        = number
  default     = 10
  
  validation {
    condition     = var.min_capacity <= var.max_capacity
    error_message = "The min_capacity must be less than or equal to max_capacity."
  }
}

# WAF Configuration
variable "enable_waf" {
  description = "Whether to enable WAF for the ALB"
  type        = bool
  default     = true
}

# OpenAI Integration
variable "openai_api_key" {
  description = "OpenAI API key for LLM integration (will be stored in AWS Secrets Manager)"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "OpenAI API key cannot be empty."
  }
}

# Monitoring Configuration
variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  
  validation {
    condition     = var.alarm_email == null || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alarm_email))
    error_message = "The alarm_email must be a valid email address."
  }
}

variable "monitoring_role_arn" {
  description = "ARN of the IAM role for RDS enhanced monitoring (will be created if not provided)"
  type        = string
  default     = null
  
  validation {
    condition     = var.monitoring_role_arn == null || can(regex("^arn:aws:iam::", var.monitoring_role_arn))
    error_message = "If provided, monitoring_role_arn must be a valid IAM role ARN."
  }
}