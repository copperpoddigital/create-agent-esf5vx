# General variables
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

# Network and infrastructure variables
variable "vpc_id" {
  description = "ID of the VPC where ECS resources will be deployed"
  type        = string

  validation {
    condition     = length(var.vpc_id) > 0
    error_message = "Must be a valid VPC ID"
  }
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs where ECS tasks will be deployed"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least two private subnet IDs must be specified for high availability."
  }
}

variable "ecs_security_group_id" {
  description = "ID of the security group for ECS tasks"
  type        = string

  validation {
    condition     = length(var.ecs_security_group_id) > 0
    error_message = "Must be a valid security group ID"
  }
}

variable "alb_target_group_arn" {
  description = "ARN of the ALB target group for the ECS service"
  type        = string

  validation {
    condition     = length(var.alb_target_group_arn) > 0
    error_message = "Must be a valid target group ARN"
  }
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the IAM role for ECS task execution"
  type        = string

  validation {
    condition     = length(var.ecs_task_execution_role_arn) > 0
    error_message = "Must be a valid IAM role ARN"
  }
}

variable "ecs_task_role_arn" {
  description = "ARN of the IAM role for ECS tasks"
  type        = string

  validation {
    condition     = length(var.ecs_task_role_arn) > 0
    error_message = "Must be a valid IAM role ARN"
  }
}

# ECS task definition variables
variable "container_image" {
  description = "Docker image for the application container"
  type        = string
  default     = "doc-ai-chatbot:latest"

  validation {
    condition     = length(var.container_image) > 0
    error_message = "Must be a valid Docker image reference"
  }
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 8000

  validation {
    condition     = var.container_port > 0 && var.container_port < 65536
    error_message = "The container_port must be between 1 and 65535."
  }
}

variable "cpu" {
  description = "CPU units for the container (1024 = 1 vCPU)"
  type        = number
  default     = 1024

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "The cpu value must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Memory for the container in MB"
  type        = number
  default     = 2048

  validation {
    condition     = var.memory > 0
    error_message = "Must be a valid Fargate memory value compatible with the CPU value"
  }
}

# ECS service variables
variable "desired_count" {
  description = "Desired number of container instances"
  type        = number
  default     = 2

  validation {
    condition     = var.desired_count > 0
    error_message = "Must be a positive number"
  }
}

variable "min_capacity" {
  description = "Minimum number of container instances for auto-scaling"
  type        = number
  default     = 2

  validation {
    condition     = var.min_capacity > 0
    error_message = "Must be a positive number"
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

# Application configuration variables
variable "db_host" {
  description = "Database host endpoint for container environment variables"
  type        = string

  validation {
    condition     = length(var.db_host) > 0
    error_message = "Must be a valid hostname or IP address"
  }
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "docaichatbot"

  validation {
    condition     = length(var.db_name) > 0
    error_message = "Must be a valid PostgreSQL database name"
  }
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "dbadmin"

  validation {
    condition     = length(var.db_username) > 0
    error_message = "No empty strings allowed"
  }
}

variable "db_password" {
  description = "ARN of the secret containing the database password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) > 0
    error_message = "Must be a valid Secrets Manager ARN"
  }
}

variable "document_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  type        = string

  validation {
    condition     = length(var.document_bucket_name) > 0
    error_message = "Must be a valid S3 bucket name"
  }
}

variable "openai_api_key" {
  description = "ARN of the secret containing the OpenAI API key"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.openai_api_key) > 0
    error_message = "Must be a valid Secrets Manager ARN"
  }
}

# Health check variables
variable "health_check_path" {
  description = "Path for container health checks"
  type        = string
  default     = "/health/live"

  validation {
    condition     = can(regex("^/", var.health_check_path))
    error_message = "The health_check_path must start with a slash."
  }
}

variable "health_check_interval" {
  description = "Interval in seconds between health checks"
  type        = number
  default     = 30

  validation {
    condition     = var.health_check_interval >= 5 && var.health_check_interval <= 300
    error_message = "Must be between 5 and 300"
  }
}

variable "health_check_timeout" {
  description = "Timeout in seconds for health checks"
  type        = number
  default     = 5

  validation {
    condition     = var.health_check_timeout >= 2 && var.health_check_timeout <= 60
    error_message = "Must be between 2 and 60"
  }
}

variable "health_check_retries" {
  description = "Number of retries for health checks"
  type        = number
  default     = 3

  validation {
    condition     = var.health_check_retries >= 1 && var.health_check_retries <= 10
    error_message = "Must be between 1 and 10"
  }
}

variable "health_check_grace_period" {
  description = "Grace period in seconds before health checks start"
  type        = number
  default     = 60

  validation {
    condition     = var.health_check_grace_period >= 0 && var.health_check_grace_period <= 1800
    error_message = "Must be between 0 and 1800"
  }
}

# Deployment configuration
variable "deployment_maximum_percent" {
  description = "Maximum percentage of tasks that can be running during a deployment"
  type        = number
  default     = 200

  validation {
    condition     = var.deployment_maximum_percent > 100
    error_message = "Must be greater than 100"
  }
}

variable "deployment_minimum_healthy_percent" {
  description = "Minimum percentage of tasks that must remain healthy during a deployment"
  type        = number
  default     = 100

  validation {
    condition     = var.deployment_minimum_healthy_percent >= 0 && var.deployment_minimum_healthy_percent <= 100
    error_message = "Must be between 0 and 100"
  }
}

variable "enable_circuit_breaker" {
  description = "Whether to enable deployment circuit breaker with rollback"
  type        = bool
  default     = true
}

# Auto-scaling configuration
variable "cpu_scaling_target" {
  description = "Target CPU utilization percentage for auto-scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.cpu_scaling_target >= 10 && var.cpu_scaling_target <= 90
    error_message = "Must be between 10 and 90"
  }
}

variable "memory_scaling_target" {
  description = "Target memory utilization percentage for auto-scaling"
  type        = number
  default     = 75

  validation {
    condition     = var.memory_scaling_target >= 10 && var.memory_scaling_target <= 90
    error_message = "Must be between 10 and 90"
  }
}

variable "request_scaling_target" {
  description = "Target request count per target for auto-scaling"
  type        = number
  default     = 100

  validation {
    condition     = var.request_scaling_target > 0
    error_message = "Must be a positive number"
  }
}

variable "scale_in_cooldown" {
  description = "Cooldown period in seconds after a scale in activity"
  type        = number
  default     = 300

  validation {
    condition     = var.scale_in_cooldown >= 0 && var.scale_in_cooldown <= 3600
    error_message = "Must be between 0 and 3600"
  }
}

variable "scale_out_cooldown" {
  description = "Cooldown period in seconds after a scale out activity"
  type        = number
  default     = 180

  validation {
    condition     = var.scale_out_cooldown >= 0 && var.scale_out_cooldown <= 3600
    error_message = "Must be between 0 and 3600"
  }
}

# Miscellaneous variables
variable "tags" {
  description = "Additional tags for ECS resources"
  type        = map(string)
  default     = {}
}