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
}

# Generate a secure random password for the database if none is provided
resource "random_password" "db_password" {
  length  = 16
  special = false
  count   = var.db_password == null ? 1 : 0
}

# Create a subnet group for the RDS instance using provided database subnet IDs
resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.database_subnet_ids
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Parameter group with PostgreSQL-specific optimizations for the system
resource "aws_db_parameter_group" "this" {
  name        = "${var.project_name}-${var.environment}-db-params"
  family      = "postgres14"
  description = "PostgreSQL parameter group for ${var.project_name} ${var.environment}"
  
  parameter {
    name  = "log_connections"
    value = "1"
  }
  
  parameter {
    name  = "log_disconnections"
    value = "1"
  }
  
  parameter {
    name  = "log_statement"
    value = "ddl"
  }
  
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32768}MB"
  }
  
  parameter {
    name  = "work_mem"
    value = "16MB"
  }
  
  parameter {
    name  = "maintenance_work_mem"
    value = "128MB"
  }
  
  parameter {
    name  = "max_connections"
    value = "100"
  }
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-params"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# RDS PostgreSQL instance with the specified configuration
resource "aws_db_instance" "this" {
  identifier                  = "${var.project_name}-${var.environment}-db"
  engine                      = "postgres"
  engine_version              = "14.6"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  storage_type                = "gp3"
  storage_encrypted           = true
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = var.db_password != null ? var.db_password : random_password.db_password[0].result
  port                        = 5432
  vpc_security_group_ids      = [var.db_security_group_id]
  db_subnet_group_name        = aws_db_subnet_group.this.name
  parameter_group_name        = aws_db_parameter_group.this.name
  multi_az                    = var.db_multi_az
  backup_retention_period     = 30
  backup_window               = "03:00-05:00"
  maintenance_window          = "sun:05:00-sun:07:00"
  auto_minor_version_upgrade  = true
  deletion_protection         = true
  skip_final_snapshot         = false
  final_snapshot_identifier   = "${var.project_name}-${var.environment}-db-final-snapshot"
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval         = 60
  monitoring_role_arn         = var.monitoring_role_arn
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  copy_tags_to_snapshot       = true
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# CloudWatch alarm for high CPU utilization on the RDS instance
resource "aws_cloudwatch_metric_alarm" "db_cpu_utilization" {
  count               = length(var.alarm_actions) > 0 ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-db-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This alarm monitors RDS database CPU utilization"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
  
  alarm_actions             = var.alarm_actions
  ok_actions                = var.alarm_actions
  insufficient_data_actions = []
  treat_missing_data        = "missing"
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-high-cpu"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# CloudWatch alarm for low free storage space on the RDS instance
resource "aws_cloudwatch_metric_alarm" "db_free_storage_space" {
  count               = length(var.alarm_actions) > 0 ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-db-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 10737418240  # 10GB in bytes
  alarm_description   = "This alarm monitors RDS database free storage space (less than 10GB)"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
  
  alarm_actions             = var.alarm_actions
  ok_actions                = var.alarm_actions
  insufficient_data_actions = []
  treat_missing_data        = "missing"
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-low-storage"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# CloudWatch alarm for high database connection count
resource "aws_cloudwatch_metric_alarm" "db_connection_count" {
  count               = length(var.alarm_actions) > 0 ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-db-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80  # 80% of max connections (from the max_connections parameter)
  alarm_description   = "This alarm monitors RDS database connection count (>80% of max)"
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
  
  alarm_actions             = var.alarm_actions
  ok_actions                = var.alarm_actions
  insufficient_data_actions = []
  treat_missing_data        = "missing"
  
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-high-connections"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Local values
locals {
  db_password = var.db_password != null ? var.db_password : random_password.db_password[0].result
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Variables
variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  type        = string
  description = "Name of the project, used for resource naming and tagging"
  
  validation {
    condition     = length(var.project_name) > 0
    error_message = "Project name cannot be empty."
  }
}

variable "vpc_id" {
  type        = string
  description = "ID of the VPC where the RDS instance will be deployed"
  
  validation {
    condition     = length(var.vpc_id) > 0 && can(regex("^vpc-", var.vpc_id))
    error_message = "Must be a valid VPC ID starting with 'vpc-'."
  }
}

variable "database_subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs for the database subnet group"
  
  validation {
    condition     = length(var.database_subnet_ids) >= 2
    error_message = "Must provide at least two subnet IDs for Multi-AZ deployment."
  }
}

variable "db_security_group_id" {
  type        = string
  description = "ID of the security group for the RDS instance"
  
  validation {
    condition     = length(var.db_security_group_id) > 0 && can(regex("^sg-", var.db_security_group_id))
    error_message = "Must be a valid security group ID starting with 'sg-'."
  }
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t3.medium"
  
  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Must be a valid RDS instance class starting with 'db.'."
  }
}

variable "db_name" {
  type        = string
  description = "Name of the PostgreSQL database"
  default     = "docaichatbot"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9_]+$", var.db_name))
    error_message = "Database name must only contain alphanumeric characters and underscores."
  }
}

variable "db_username" {
  type        = string
  description = "Username for the database"
  
  validation {
    condition     = length(var.db_username) > 0
    error_message = "Database username cannot be empty."
  }
}

variable "db_password" {
  type        = string
  description = "Password for the database (will be generated if not provided)"
  default     = null
  sensitive   = true
  
  validation {
    condition     = var.db_password == null || length(var.db_password) >= 8
    error_message = "Database password, if provided, must be at least 8 characters."
  }
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage for the database in GB"
  default     = 20
  
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "Allocated storage must be between 20 and 100 GB."
  }
}

variable "db_multi_az" {
  type        = bool
  description = "Whether to enable Multi-AZ deployment for RDS"
  default     = true
}

variable "monitoring_role_arn" {
  type        = string
  description = "ARN of the IAM role for RDS enhanced monitoring"
  
  validation {
    condition     = length(var.monitoring_role_arn) > 0 && can(regex("^arn:aws:iam::", var.monitoring_role_arn))
    error_message = "Must be a valid IAM role ARN starting with 'arn:aws:iam::'."
  }
}

variable "alarm_actions" {
  type        = list(string)
  description = "List of ARNs for CloudWatch alarm actions (SNS topics)"
  default     = []
  
  validation {
    condition     = length(var.alarm_actions) == 0 || alltrue([for arn in var.alarm_actions : can(regex("^arn:aws:sns:", arn))])
    error_message = "Alarm actions must be valid SNS topic ARNs starting with 'arn:aws:sns:'."
  }
}

# Outputs
output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.this.id
}

output "db_endpoint" {
  description = "Connection endpoint of the RDS instance"
  value       = aws_db_instance.this.endpoint
}

output "db_name" {
  description = "Name of the database"
  value       = aws_db_instance.this.db_name
}

output "db_username" {
  description = "Username for the database"
  value       = aws_db_instance.this.username
}

output "db_port" {
  description = "Port of the database"
  value       = aws_db_instance.this.port
}

output "db_security_group_id" {
  description = "ID of the security group attached to the RDS instance"
  value       = var.db_security_group_id
}

output "db_subnet_group_name" {
  description = "Name of the database subnet group"
  value       = aws_db_subnet_group.this.name
}

output "db_parameter_group_name" {
  description = "Name of the database parameter group"
  value       = aws_db_parameter_group.this.name
}

output "db_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.this.arn
}

output "db_multi_az" {
  description = "Whether the RDS instance is configured for Multi-AZ deployment"
  value       = aws_db_instance.this.multi_az
}