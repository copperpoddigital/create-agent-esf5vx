# -----------------------------------------------------------------------------
# S3 Module - Document Management and AI Chatbot System
# -----------------------------------------------------------------------------
# Creates and configures S3 buckets for document storage and logging with
# appropriate security settings, lifecycle policies, and access controls.
# This module supports secure document storage with versioning, lifecycle
# management for cost optimization, and comprehensive access logging.
# -----------------------------------------------------------------------------

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

# Generate a random suffix for bucket names if not explicitly provided
resource "random_id" "suffix" {
  byte_length = 8
}

# Define local variables for bucket names
locals {
  # Generate document bucket name if not provided
  document_bucket_name_final = var.document_bucket_name != null ? var.document_bucket_name : lower(
    "${var.project_name}-documents-${var.environment}-${random_id.suffix.hex}"
  )

  # Generate log bucket name if not provided
  log_bucket_name_final = var.log_bucket_name != null ? var.log_bucket_name : lower(
    "${var.project_name}-logs-${var.environment}-${random_id.suffix.hex}"
  )
}

# -----------------------------------------------------------------------------
# Log Bucket Configuration
# -----------------------------------------------------------------------------

# Create S3 bucket for storing access logs
resource "aws_s3_bucket" "log_bucket" {
  bucket        = local.log_bucket_name_final
  force_destroy = var.force_destroy

  tags = {
    Name        = "${var.project_name}-logs-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Configure lifecycle policy for the log bucket to automatically expire old logs
resource "aws_s3_bucket_lifecycle_configuration" "log_bucket_lifecycle" {
  bucket = aws_s3_bucket.log_bucket.id

  rule {
    id     = "log-expiration"
    status = "Enabled"

    expiration {
      days = var.log_expiration_days
    }
  }
}

# Configure server-side encryption for the log bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "log_bucket_encryption" {
  bucket = aws_s3_bucket.log_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access to the log bucket for security
resource "aws_s3_bucket_public_access_block" "log_bucket_public_access_block" {
  bucket = aws_s3_bucket.log_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Document Bucket Configuration
# -----------------------------------------------------------------------------

# Create S3 bucket for storing PDF documents uploaded to the system
resource "aws_s3_bucket" "document_bucket" {
  bucket        = local.document_bucket_name_final
  force_destroy = var.force_destroy

  tags = {
    Name        = "${var.project_name}-documents-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Versioning configuration for the document bucket to maintain document history
resource "aws_s3_bucket_versioning" "document_bucket_versioning" {
  bucket = aws_s3_bucket.document_bucket.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Lifecycle configuration for the document bucket to transition objects
# to cheaper storage classes and expire old versions
resource "aws_s3_bucket_lifecycle_configuration" "document_bucket_lifecycle" {
  bucket = aws_s3_bucket.document_bucket.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = var.standard_ia_transition_days
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "noncurrent-version-expiration"
    status = var.enable_versioning ? "Enabled" : "Disabled"

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# Server-side encryption configuration for the document bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "document_bucket_encryption" {
  bucket = aws_s3_bucket.document_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Logging configuration for the document bucket to track access
resource "aws_s3_bucket_logging" "document_bucket_logging" {
  bucket = aws_s3_bucket.document_bucket.id

  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "document-bucket-logs/"
}

# CORS configuration for the document bucket to allow cross-origin requests if enabled
resource "aws_s3_bucket_cors_configuration" "document_bucket_cors" {
  count  = var.enable_cors ? 1 : 0
  bucket = aws_s3_bucket.document_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Block all public access to the document bucket for security
resource "aws_s3_bucket_public_access_block" "document_bucket_public_access_block" {
  bucket = aws_s3_bucket.document_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -----------------------------------------------------------------------------
# Output Values
# -----------------------------------------------------------------------------

output "document_bucket_name" {
  description = "Name of the created document S3 bucket"
  value       = aws_s3_bucket.document_bucket.id
}

output "document_bucket_arn" {
  description = "ARN of the created document S3 bucket"
  value       = aws_s3_bucket.document_bucket.arn
}

output "log_bucket_name" {
  description = "Name of the created log S3 bucket"
  value       = aws_s3_bucket.log_bucket.id
}

output "log_bucket_arn" {
  description = "ARN of the created log S3 bucket"
  value       = aws_s3_bucket.log_bucket.arn
}