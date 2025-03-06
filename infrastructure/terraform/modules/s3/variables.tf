# -----------------------------------------------------------------------------
# S3 Module Variables - Document Management and AI Chatbot System
# -----------------------------------------------------------------------------
# This module creates and configures S3 buckets used for document storage and
# logs in the Document Management and AI Chatbot System. It handles bucket
# creation, lifecycle policies, versioning, and security settings.
# -----------------------------------------------------------------------------

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "The environment value must be one of: dev, staging, prod."
  }
}

variable "project_name" {
  description = "Name of the project, used for resource naming and tagging"
  type        = string
  default     = "doc-ai-chatbot"

  validation {
    condition     = length(var.project_name) > 0
    error_message = "The project_name value cannot be empty."
  }
}

variable "document_bucket_name" {
  description = "Name of the S3 bucket for document storage (optional, will be generated if not provided)"
  type        = string
  default     = null

  validation {
    condition     = var.document_bucket_name == null || can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.document_bucket_name))
    error_message = "The document_bucket_name must be a valid S3 bucket name."
  }
}

variable "log_bucket_name" {
  description = "Name of the S3 bucket for logs (optional, will be generated if not provided)"
  type        = string
  default     = null

  validation {
    condition     = var.log_bucket_name == null || can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.log_bucket_name))
    error_message = "The log_bucket_name must be a valid S3 bucket name."
  }
}

variable "force_destroy" {
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
    error_message = "The standard_ia_transition_days must be a positive number."
  }
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days after which noncurrent object versions should be deleted"
  type        = number
  default     = 30

  validation {
    condition     = var.noncurrent_version_expiration_days > 0
    error_message = "The noncurrent_version_expiration_days must be a positive number."
  }
}

variable "log_expiration_days" {
  description = "Number of days after which log objects should be deleted"
  type        = number
  default     = 90

  validation {
    condition     = var.log_expiration_days > 0
    error_message = "The log_expiration_days must be a positive number."
  }
}

variable "enable_cors" {
  description = "Whether to enable CORS for the document bucket"
  type        = bool
  default     = true
}

# Optional KMS key ARN for server-side encryption
variable "kms_key_arn" {
  description = "ARN of the KMS key to use for server-side encryption (if not provided, AES256 encryption will be used)"
  type        = string
  default     = null
}

# Tags to apply to all resources
variable "tags" {
  description = "A map of tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Block public access settings
variable "block_public_acls" {
  description = "Whether Amazon S3 should block public ACLs for this bucket"
  type        = bool
  default     = true
}

variable "block_public_policy" {
  description = "Whether Amazon S3 should block public bucket policies for this bucket"
  type        = bool
  default     = true
}

variable "ignore_public_acls" {
  description = "Whether Amazon S3 should ignore public ACLs for this bucket"
  type        = bool
  default     = true
}

variable "restrict_public_buckets" {
  description = "Whether Amazon S3 should restrict public bucket policies for this bucket"
  type        = bool
  default     = true
}

# CORS configuration (if enabled)
variable "cors_allowed_origins" {
  description = "List of origins allowed for CORS requests (if CORS is enabled)"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allowed_methods" {
  description = "List of HTTP methods allowed for CORS requests (if CORS is enabled)"
  type        = list(string)
  default     = ["GET", "HEAD"]
}

variable "cors_allowed_headers" {
  description = "List of headers allowed for CORS requests (if CORS is enabled)"
  type        = list(string)
  default     = ["*"]
}

variable "cors_max_age_seconds" {
  description = "Time in seconds browsers can cache the response for a preflight request (if CORS is enabled)"
  type        = number
  default     = 3600
}