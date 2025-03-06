variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string

  validation {
    condition     = length(var.project_name) > 0
    error_message = "The project_name value cannot be empty."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "vpc_id" {
  description = "ID of the VPC where the ALB will be deployed"
  type        = string
}

variable "public_subnets" {
  description = "List of public subnet IDs for ALB deployment, should be in different availability zones for high availability"
  type        = list(string)

  validation {
    condition     = length(var.public_subnets) >= 2
    error_message = "At least two public subnets must be specified for high availability."
  }
}

variable "alb_security_group_id" {
  description = "ID of the security group for the ALB"
  type        = string
}

variable "certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = ""

  validation {
    condition     = var.certificate_arn == "" || can(regex("^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[a-zA-Z0-9-]+$", var.certificate_arn))
    error_message = "The certificate_arn value must be a valid ACM certificate ARN or an empty string."
  }
}

variable "container_port" {
  description = "Port on which the container is listening"
  type        = number
  default     = 8000

  validation {
    condition     = var.container_port > 0 && var.container_port < 65536
    error_message = "The container_port value must be between 1 and 65535."
  }
}

variable "enable_waf" {
  description = "Whether to enable WAF for the ALB"
  type        = bool
  default     = true
}

variable "log_bucket" {
  description = "S3 bucket name for ALB access logs"
  type        = string
  default     = ""
}

variable "alarm_sns_topic_arn" {
  description = "ARN of the SNS topic for CloudWatch alarms"
  type        = string
  default     = ""
}