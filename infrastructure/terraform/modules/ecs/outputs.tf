# Outputs for the ECS module
# These outputs expose ECS cluster, service, task definition, and autoscaling resources
# to other modules or the root Terraform configuration

#----------------------------------------
# Cluster outputs
#----------------------------------------
output "cluster_id" {
  description = "ID of the created ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "Name of the created ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the created ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

#----------------------------------------
# Service outputs
#----------------------------------------
output "service_id" {
  description = "ID of the created ECS service"
  value       = aws_ecs_service.app.id
}

output "service_name" {
  description = "Name of the created ECS service"
  value       = aws_ecs_service.app.name
}

output "service_arn" {
  description = "ARN of the created ECS service"
  value       = aws_ecs_service.app.arn
}

#----------------------------------------
# Task definition outputs
#----------------------------------------
output "task_definition_arn" {
  description = "ARN of the created ECS task definition"
  value       = aws_ecs_task_definition.app.arn
}

output "task_definition_family" {
  description = "Family of the created ECS task definition"
  value       = aws_ecs_task_definition.app.family
}

output "task_definition_revision" {
  description = "Revision of the created ECS task definition"
  value       = aws_ecs_task_definition.app.revision
}

#----------------------------------------
# CloudWatch log group outputs
#----------------------------------------
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for ECS container logs"
  value       = aws_cloudwatch_log_group.ecs_logs.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for ECS container logs"
  value       = aws_cloudwatch_log_group.ecs_logs.arn
}

#----------------------------------------
# Auto Scaling outputs
#----------------------------------------
output "autoscaling_target_id" {
  description = "ID of the Application Auto Scaling target for the ECS service"
  value       = aws_appautoscaling_target.ecs_target.id
}

output "autoscaling_policy_cpu_arn" {
  description = "ARN of the CPU-based Auto Scaling policy"
  value       = aws_appautoscaling_policy.cpu_scaling.arn
}

output "autoscaling_policy_memory_arn" {
  description = "ARN of the memory-based Auto Scaling policy"
  value       = aws_appautoscaling_policy.memory_scaling.arn
}

output "autoscaling_policy_request_arn" {
  description = "ARN of the request count-based Auto Scaling policy"
  value       = aws_appautoscaling_policy.request_scaling.arn
}