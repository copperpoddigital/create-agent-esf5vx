output "document_bucket_name" {
  description = "Name of the S3 bucket created for document storage"
  value       = aws_s3_bucket.document_bucket.id
}

output "document_bucket_arn" {
  description = "ARN of the S3 bucket created for document storage"
  value       = aws_s3_bucket.document_bucket.arn
}

output "document_bucket_domain_name" {
  description = "Domain name of the S3 bucket created for document storage"
  value       = aws_s3_bucket.document_bucket.bucket_domain_name
}

output "document_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket created for document storage"
  value       = aws_s3_bucket.document_bucket.bucket_regional_domain_name
}

output "log_bucket_name" {
  description = "Name of the S3 bucket created for access logs"
  value       = aws_s3_bucket.log_bucket.id
}

output "log_bucket_arn" {
  description = "ARN of the S3 bucket created for access logs"
  value       = aws_s3_bucket.log_bucket.arn
}