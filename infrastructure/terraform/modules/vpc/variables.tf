# ==============================================================================
# VPC Module Variables
# 
# This file defines all configurable parameters for the VPC infrastructure
# of the Document Management and AI Chatbot System.
# ==============================================================================

# Basic Configuration Variables
# ------------------------------------------------------------------------------

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string

  validation {
    condition     = length(var.project_name) > 0
    error_message = "Project name cannot be empty."
  }
}

# VPC Configuration Variables
# ------------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC (e.g., 10.0.0.0/16)"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "The vpc_cidr value must be a valid CIDR block."
  }
}

variable "enable_dns_hostnames" {
  description = "Whether to enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "enable_dns_support" {
  description = "Whether to enable DNS support in the VPC"
  type        = bool
  default     = true
}

# Availability Zones and Subnet Configuration
# ------------------------------------------------------------------------------

variable "availability_zones" {
  description = "List of availability zones where subnets will be created"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least two availability zones must be provided for high availability."
  }
}

variable "public_subnet_cidrs" {
  description = "List of CIDR blocks for public subnets, one per availability zone"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_cidrs) > 0
    error_message = "At least one public subnet CIDR block must be provided."
  }
}

variable "private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets, one per availability zone"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_cidrs) > 0
    error_message = "At least one private subnet CIDR block must be provided."
  }
}

variable "database_subnet_cidrs" {
  description = "List of CIDR blocks for database subnets, one per availability zone"
  type        = list(string)

  validation {
    condition     = length(var.database_subnet_cidrs) > 0
    error_message = "At least one database subnet CIDR block must be provided."
  }
}

# NAT Gateway Configuration
# ------------------------------------------------------------------------------

variable "enable_nat_gateway" {
  description = "Whether to create NAT Gateways for private subnets outbound internet access"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Whether to create a single NAT Gateway for all private subnets"
  type        = bool
  default     = false
}

# VPN Gateway Configuration
# ------------------------------------------------------------------------------

variable "enable_vpn_gateway" {
  description = "Whether to create a VPN Gateway"
  type        = bool
  default     = false
}

# VPC Endpoints Configuration
# ------------------------------------------------------------------------------

variable "enable_s3_endpoint" {
  description = "Whether to create an S3 VPC Endpoint"
  type        = bool
  default     = true
}

# VPC Flow Logs Configuration
# ------------------------------------------------------------------------------

variable "enable_flow_logs" {
  description = "Whether to enable VPC Flow Logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Retention period in days for VPC Flow Logs"
  type        = number
  default     = 30

  validation {
    condition     = var.flow_logs_retention_days >= 1 && var.flow_logs_retention_days <= 365
    error_message = "Flow logs retention days must be between 1 and 365."
  }
}

# Additional validation to ensure subnet configuration matches AZ count
# ------------------------------------------------------------------------------

locals {
  validate_public_subnet_count = length(var.public_subnet_cidrs) == length(var.availability_zones) ? true : tobool("Public subnet count must match availability zone count")
  validate_private_subnet_count = length(var.private_subnet_cidrs) == length(var.availability_zones) ? true : tobool("Private subnet count must match availability zone count")
  validate_database_subnet_count = length(var.database_subnet_cidrs) == length(var.availability_zones) ? true : tobool("Database subnet count must match availability zone count")
  
  # CIDR validation using regex patterns
  validate_cidr_blocks = alltrue([
    for cidr in concat([var.vpc_cidr], var.public_subnet_cidrs, var.private_subnet_cidrs, var.database_subnet_cidrs) :
    can(regex("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$", cidr))
  ]) ? true : tobool("All CIDR blocks must be in valid format")
}