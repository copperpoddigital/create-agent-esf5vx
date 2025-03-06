# Output values for the RDS module that expose the PostgreSQL database connection details
# These outputs can be used by other modules or the root module to integrate with the database

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

output "db_password" {
  description = "Password for the database"
  value       = var.db_password != null ? var.db_password : random_password.db_password[0].result
  sensitive   = true
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

output "db_connection_string" {
  description = "PostgreSQL connection string for the database (without password)"
  value       = "postgresql://${aws_db_instance.this.username}@${aws_db_instance.this.endpoint}/${aws_db_instance.this.db_name}"
}