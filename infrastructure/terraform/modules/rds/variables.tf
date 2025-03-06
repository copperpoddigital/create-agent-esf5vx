variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
  
  validation {
    condition     = length(var.project_name) > 0
    error_message = "The project_name value cannot be empty."
  }
}

variable "vpc_id" {
  description = "ID of the VPC where the RDS instance will be deployed"
  type        = string
  
  validation {
    condition     = can(regex("^vpc-", var.vpc_id))
    error_message = "The vpc_id must be a valid VPC ID starting with 'vpc-'."
  }
}

variable "database_subnet_ids" {
  description = "List of subnet IDs for the database subnet group"
  type        = list(string)
  
  validation {
    condition     = length(var.database_subnet_ids) >= 2
    error_message = "At least two database subnet IDs must be provided for high availability."
  }
}

variable "db_security_group_id" {
  description = "ID of the security group for the RDS instance"
  type        = string
  
  validation {
    condition     = can(regex("^sg-", var.db_security_group_id))
    error_message = "The db_security_group_id must be a valid security group ID starting with 'sg-'."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
  
  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "The db_instance_class must be a valid RDS instance class starting with 'db.'."
  }
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "docaichatbot"
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9_]+$", var.db_name))
    error_message = "The db_name must contain only alphanumeric characters and underscores."
  }
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  
  validation {
    condition     = length(var.db_username) > 0
    error_message = "The db_username value cannot be empty."
  }
}

variable "db_password" {
  description = "Password for the database (will be generated if not provided)"
  type        = string
  default     = null
  sensitive   = true
  
  validation {
    condition     = var.db_password == null || length(var.db_password) >= 8
    error_message = "If provided, the db_password must be at least 8 characters long."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for the database in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "The db_allocated_storage must be between 20 and 100 GB."
  }
}

variable "db_multi_az" {
  description = "Whether to enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

variable "monitoring_role_arn" {
  description = "ARN of the IAM role for RDS enhanced monitoring"
  type        = string
  
  validation {
    condition     = can(regex("^arn:aws:iam::", var.monitoring_role_arn))
    error_message = "The monitoring_role_arn must be a valid IAM role ARN."
  }
}

variable "alarm_actions" {
  description = "List of ARNs for CloudWatch alarm actions (SNS topics)"
  type        = list(string)
  default     = []
  
  validation {
    condition     = length([for arn in var.alarm_actions : arn if !can(regex("^arn:aws:sns:", arn)) && length(var.alarm_actions) > 0]) == 0
    error_message = "All items in alarm_actions must be valid SNS topic ARNs starting with 'arn:aws:sns:'."
  }
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_period >= 1 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 1 and 35 days."
  }
}

variable "backup_window" {
  description = "The daily time range during which automated backups are created (UTC)"
  type        = string
  default     = "02:00-04:00"  # 2 AM - 4 AM UTC
  
  validation {
    condition     = can(regex("^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$", var.backup_window))
    error_message = "The backup_window must be in the format of 'HH:MM-HH:MM' in 24-hour clock UTC."
  }
}

variable "maintenance_window" {
  description = "The weekly time range during which system maintenance can occur (UTC)"
  type        = string
  default     = "sun:02:00-sun:04:00"  # Sunday 2 AM - 4 AM UTC
  
  validation {
    condition     = can(regex("^[a-z]{3}:[0-9]{2}:[0-9]{2}-[a-z]{3}:[0-9]{2}:[0-9]{2}$", var.maintenance_window))
    error_message = "The maintenance_window must be in the format of 'ddd:HH:MM-ddd:HH:MM'."
  }
}

variable "monitoring_interval" {
  description = "The interval, in seconds, between points when Enhanced Monitoring metrics are collected"
  type        = number
  default     = 60
  
  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "The monitoring_interval must be one of: 0, 1, 5, 10, 15, 30, 60."
  }
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "14.6"
  
  validation {
    condition     = can(regex("^[0-9]+\\.[0-9]+$", var.db_engine_version))
    error_message = "The db_engine_version must be a valid PostgreSQL version in the format 'XX.XX'."
  }
}

variable "db_parameter_group_name" {
  description = "Name of the DB parameter group to associate with this DB instance"
  type        = string
  default     = null
}

variable "db_storage_type" {
  description = "Storage type for the database (gp2, io1, etc.)"
  type        = string
  default     = "gp2"
  
  validation {
    condition     = contains(["gp2", "io1", "standard"], var.db_storage_type)
    error_message = "The db_storage_type must be one of: gp2, io1, standard."
  }
}

variable "tags" {
  description = "A map of tags to assign to the RDS instance and related resources"
  type        = map(string)
  default     = {}
}

variable "skip_final_snapshot" {
  description = "Determines whether a final DB snapshot is created before the DB instance is deleted"
  type        = bool
  default     = false
}

variable "apply_immediately" {
  description = "Specifies whether modifications are applied immediately, or during the next maintenance window"
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "If the DB instance should have deletion protection enabled"
  type        = bool
  default     = true
}

variable "performance_insights_enabled" {
  description = "Specifies whether Performance Insights are enabled"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "The amount of time in days to retain Performance Insights data"
  type        = number
  default     = 7  # Free tier is 7 days
  
  validation {
    condition     = contains([7, 731], var.performance_insights_retention_period) || (var.performance_insights_retention_period >= 7 && var.performance_insights_retention_period % 31 == 0 && var.performance_insights_retention_period <= 731)
    error_message = "Performance Insights retention period must be 7 days (free tier) or a multiple of 31 days between 31 and 731 days."
  }
}