project_name             = "doc-ai-chatbot"
environment              = "staging"

# AWS Configuration
aws_region               = "us-west-2"
aws_profile              = "staging"
terraform_state_bucket   = "doc-ai-chatbot-terraform-state-staging"
terraform_lock_table     = "doc-ai-chatbot-terraform-locks-staging"

# Network Configuration
vpc_cidr                 = "10.0.0.0/16"
availability_zones       = ["us-west-2a", "us-west-2b"]
public_subnet_cidrs      = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs     = ["10.0.3.0/24", "10.0.4.0/24"]
database_subnet_cidrs    = ["10.0.5.0/24", "10.0.6.0/24"]

# SSL/TLS Certificate
certificate_arn          = "arn:aws:acm:us-west-2:123456789012:certificate/abcd1234-ef56-gh78-ij90-klmnopqrstuv"

# S3 Bucket Configuration
document_bucket_name     = "doc-ai-chatbot-documents-staging"
log_bucket_name          = "doc-ai-chatbot-logs-staging"
force_destroy_buckets    = true
enable_versioning        = true
standard_ia_transition_days = 90
log_expiration_days      = 90

# Database Configuration
db_instance_class        = "db.t3.medium"
db_name                  = "docaichatbot"
db_username              = "dbadmin"
db_password              = "PLACEHOLDER_PASSWORD_TO_BE_INJECTED_BY_CI_PROCESS"
db_allocated_storage     = 50
db_multi_az              = true

# ECS Configuration
ecs_task_execution_role_arn = null
ecs_task_role_arn        = null
container_image          = "doc-ai-chatbot:staging"
container_port           = 8000
container_cpu            = 1024
container_memory         = 2048
desired_count            = 2
min_capacity             = 2
max_capacity             = 6

# Security Configuration
enable_waf               = true

# API Keys and External Services
openai_api_key           = "PLACEHOLDER_API_KEY_TO_BE_INJECTED_BY_CI_PROCESS"

# Alarms and Notifications
alarm_email              = "staging-alerts@example.com"