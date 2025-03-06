# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC where all resources are deployed"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.vpc.database_subnet_ids
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "ecs_service_name" {
  description = "Name of the ECS service running the application"
  value       = module.ecs.service_name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.ecs.task_definition_arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for container logs"
  value       = module.ecs.cloudwatch_log_group_name
}

# RDS Outputs
output "db_endpoint" {
  description = "Connection endpoint of the RDS instance"
  value       = module.rds.db_endpoint
}

output "db_name" {
  description = "Name of the database"
  value       = module.rds.db_name
}

output "db_username" {
  description = "Username for the database"
  value       = module.rds.db_username
}

output "db_port" {
  description = "Port of the database"
  value       = module.rds.db_port
}

output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = module.rds.db_instance_id
}

output "db_multi_az" {
  description = "Whether the RDS instance is configured for Multi-AZ deployment"
  value       = module.rds.db_multi_az
}

# S3 Outputs
output "document_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  value       = module.s3.document_bucket_name
}

output "document_bucket_arn" {
  description = "ARN of the S3 bucket for document storage"
  value       = module.s3.document_bucket_arn
}

output "log_bucket_name" {
  description = "Name of the S3 bucket for logs"
  value       = module.s3.log_bucket_name
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer for accessing the application"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Route 53 zone ID of the Application Load Balancer for DNS record creation"
  value       = module.alb.alb_zone_id
}

# Application Outputs
output "app_url" {
  description = "URL for accessing the application (using ALB DNS name)"
  value       = "https://${module.alb.alb_dns_name}"
}

output "db_connection_string" {
  description = "PostgreSQL connection string for the application (without password)"
  value       = "postgresql://${module.rds.db_username}@${module.rds.db_endpoint}/${module.rds.db_name}"
}

# Auto-scaling Outputs
output "autoscaling_policies" {
  description = "ARNs of the auto-scaling policies for the ECS service"
  value = {
    cpu     = module.ecs.cpu_autoscaling_policy_arn
    memory  = module.ecs.memory_autoscaling_policy_arn
    request = module.ecs.request_autoscaling_policy_arn
  }
}