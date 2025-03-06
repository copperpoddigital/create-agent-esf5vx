output "alb_id" {
  value       = aws_lb.main.id
  description = "The ID of the Application Load Balancer"
}

output "alb_arn" {
  value       = aws_lb.main.arn
  description = "The ARN of the Application Load Balancer"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "The DNS name of the Application Load Balancer"
}

output "alb_zone_id" {
  value       = aws_lb.main.zone_id
  description = "The canonical hosted zone ID of the load balancer (for Route53 alias records)"
}

output "target_group_arn" {
  value       = aws_lb_target_group.app.arn
  description = "The ARN of the target group for the Application Load Balancer"
}

output "https_listener_arn" {
  value       = var.certificate_arn != "" ? aws_lb_listener.https[0].arn : ""
  description = "The ARN of the HTTPS listener (if SSL certificate was provided)"
}

output "alb_security_group_id" {
  value       = var.alb_security_group_id
  description = "The ID of the security group associated with the ALB"
}