# Basic Configuration
project_name = "doc-ai-chatbot"
environment  = "prod"
aws_region   = "us-west-2"
aws_profile  = "prod"

# Terraform State Management
terraform_state_bucket = "doc-ai-chatbot-terraform-state-prod"
terraform_lock_table   = "doc-ai-chatbot-terraform-locks-prod"

# Networking Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = [
  "us-west-2a",
  "us-west-2b",
  "us-west-2c"
]
public_subnet_cidrs = [
  "10.0.1.0/24",
  "10.0.2.0/24",
  "10.0.3.0/24"
]
private_subnet_cidrs = [
  "10.0.4.0/24",
  "10.0.5.0/24",
  "10.0.6.0/24"
]
database_subnet_cidrs = [
  "10.0.7.0/24",
  "10.0.8.0/24",
  "10.0.9.0/24"
]

# SSL/TLS Configuration
certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/abcd1234-ef56-gh78-ij90-klmnopqrstuv"

# S3 Storage Configuration
document_bucket_name = "doc-ai-chatbot-documents-prod"
log_bucket_name      = "doc-ai-chatbot-logs-prod"
force_destroy_buckets    = false  # Prevent accidental destruction in production
enable_versioning        = true   # Enable versioning for production data protection
standard_ia_transition_days = 90  # Move to IA storage class after 90 days
log_expiration_days      = 365    # Retain logs for one year

# Database Configuration
db_instance_class    = "db.t3.large"
db_name              = "docaichatbot"
db_username          = "dbadmin"
db_password          = "PLACEHOLDER_PASSWORD_TO_BE_INJECTED_BY_CI_PROCESS"
db_allocated_storage = 100  # GB
db_multi_az          = true # Enable multi-AZ for high availability in production

# ECS Configuration
ecs_task_execution_role_arn = null # Will be created if null
ecs_task_role_arn           = null # Will be created if null
container_image             = "doc-ai-chatbot:prod"
container_port              = 8000
container_cpu               = 2048  # 2 vCPU
container_memory            = 4096  # 4 GB
desired_count               = 4     # Higher task count for production load
min_capacity                = 4     # Minimum 4 tasks running at all times
max_capacity                = 10    # Scale up to 10 tasks during high load

# Security Configuration
enable_waf = true # Enable WAF for production environment

# External Service Configuration
openai_api_key = "PLACEHOLDER_API_KEY_TO_BE_INJECTED_BY_CI_PROCESS"

# Monitoring and Alerting
alarm_email       = "prod-alerts@example.com"
monitoring_role_arn = null # Will be created if null