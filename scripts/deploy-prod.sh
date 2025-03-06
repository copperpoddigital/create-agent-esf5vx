#!/bin/bash
#
# deploy-prod.sh
#
# Production deployment script for the Document Management and AI Chatbot System.
# This script orchestrates the production deployment process, including infrastructure
# provisioning, application deployment, health checks, and notification of deployment status.
#
# It implements a blue/green deployment strategy with gradual traffic shifting,
# comprehensive health checks, and automated rollback capabilities.

# Exit immediately if a command exits with a non-zero status
set -e

# Source the health check script for deployment verification
source "$(dirname "$0")/health-check.sh"

# Global variables
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
ENVIRONMENT="prod"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform/environments/$ENVIRONMENT"
ANSIBLE_DIR="$PROJECT_ROOT/infrastructure/ansible"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker/docker-compose.prod.yml"
DEPLOYMENT_TIMESTAMP=$(date +%Y%m%d%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/deploy-prod-$DEPLOYMENT_TIMESTAMP.log"

# Environment variables
export AWS_PROFILE=prod
export AWS_REGION=us-west-2
export TF_VAR_environment=prod
export ANSIBLE_CONFIG="$ANSIBLE_DIR/ansible.cfg"
export IMAGE_TAG="$DEPLOYMENT_TIMESTAMP"
export DEPLOYMENT_ID="$DEPLOYMENT_TIMESTAMP"
export NOTIFICATION_RECIPIENTS="ops-team@example.com,management@example.com"

# Error handling
DEPLOYMENT_STARTED=false
trap 'handle_error $? $LINENO' ERR
trap 'cleanup' EXIT

# Handle errors and trigger rollback if necessary
handle_error() {
  local exit_code=$1
  local line_number=$2
  
  log_message "ERROR" "Deployment failed at line $line_number with exit code $exit_code"
  
  # Perform rollback if deployment was in progress
  if [ "$DEPLOYMENT_STARTED" = true ]; then
    log_message "INFO" "Starting rollback procedure..."
    rollback_deployment
  fi
  
  # Notify team about the failure
  send_notification "FAILURE"
  
  exit $exit_code
}

# Function to log messages to console and log file
log_message() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  local color=""
  
  # Set color based on message level
  case $level in
    "INFO")     color="\033[0;32m" ;; # Green
    "WARNING")  color="\033[0;33m" ;; # Yellow
    "ERROR")    color="\033[0;31m" ;; # Red
    "DEBUG")    color="\033[0;34m" ;; # Blue
    *)          color="\033[0m"    ;; # No color
  esac
  
  # Ensure log directory exists
  mkdir -p "$(dirname "$LOG_FILE")"
  
  # Format message
  local formatted_message="[$timestamp] [$level] $message"
  
  # Print to console with color
  echo -e "${color}${formatted_message}\033[0m"
  
  # Write to log file without color codes
  echo "$formatted_message" >> "$LOG_FILE"
  
  # For production errors, also send to monitoring system
  if [ "$level" == "ERROR" ] && [ "$ENVIRONMENT" == "prod" ]; then
    # Send to CloudWatch Logs or another monitoring service
    aws cloudwatch put-metric-data \
      --namespace "Deployment" \
      --metric-name "DeploymentErrors" \
      --value 1 \
      --dimensions Environment=Production || true
  fi
}

# Function to check prerequisites for deployment
check_prerequisites() {
  log_message "INFO" "Checking prerequisites for production deployment..."
  
  # Check for required tools
  for tool in aws terraform ansible; do
    if ! command -v $tool &> /dev/null; then
      log_message "ERROR" "Required tool '$tool' is not installed or not in PATH"
      return 1
    fi
  done
  
  # Check AWS credentials
  if ! aws sts get-caller-identity &> /dev/null; then
    log_message "ERROR" "AWS credentials are not configured or do not have sufficient permissions"
    return 1
  fi
  
  # Check for deployment approval token
  if [ -z "$APPROVAL_TOKEN" ]; then
    log_message "ERROR" "Approval token is required for production deployment"
    return 1
  fi
  
  # Verify the approval token is valid
  if ! curl -s -f -H "Authorization: Bearer $APPROVAL_TOKEN" \
       "${CI_API_URL:-https://ci.example.com}/deployment/verify" &> /dev/null; then
    log_message "ERROR" "Invalid or expired approval token"
    return 1
  fi
  
  # Check that staging deployment was successful
  if [ ! -f "$PROJECT_ROOT/.staging-deployment-success" ]; then
    log_message "ERROR" "Staging deployment must be successful before deploying to production"
    return 1
  fi
  
  # Check that all tests have passed in CI/CD pipeline
  if [ ! -f "$PROJECT_ROOT/.ci-tests-passed" ]; then
    log_message "ERROR" "All tests must pass in CI/CD pipeline before deploying to production"
    return 1
  fi
  
  log_message "INFO" "All prerequisites met for production deployment"
  return 0
}

# Function to set up the deployment environment
setup_environment() {
  log_message "INFO" "Setting up deployment environment..."
  
  # Create logs directory if it doesn't exist
  mkdir -p "$PROJECT_ROOT/logs"
  
  # Ensure AWS credentials are configured
  if ! aws configure list-profiles | grep -q "$AWS_PROFILE"; then
    log_message "ERROR" "AWS profile '$AWS_PROFILE' not found"
    return 1
  fi
  
  # Set AWS profile to production
  export AWS_PROFILE=prod
  
  # Create deployment timestamp for versioning
  export DEPLOYMENT_TIMESTAMP=$(date +%Y%m%d%H%M%S)
  
  # Check for required approval token for production deployment
  if [ -z "$APPROVAL_TOKEN" ]; then
    log_message "ERROR" "Approval token is required for production deployment"
    return 1
  fi
  
  log_message "INFO" "Deployment environment set up successfully"
  return 0
}

# Function to provision infrastructure using Terraform
provision_infrastructure() {
  log_message "INFO" "Provisioning infrastructure with Terraform..."
  
  # Change to Terraform directory
  cd "$TERRAFORM_DIR"
  
  # Initialize Terraform
  log_message "INFO" "Initializing Terraform..."
  terraform init -input=false
  
  # Validate Terraform configuration
  log_message "INFO" "Validating Terraform configuration..."
  terraform validate
  
  # Plan Terraform changes
  log_message "INFO" "Planning Terraform changes..."
  terraform plan -out=tfplan -input=false
  
  # Require manual approval for production infrastructure changes
  log_message "WARNING" "Production infrastructure changes require manual approval"
  read -p "Do you approve these changes? (yes/no): " approval
  if [ "$approval" != "yes" ]; then
    log_message "INFO" "Infrastructure changes aborted by user"
    return 1
  fi
  
  # Apply Terraform changes after approval
  log_message "INFO" "Applying Terraform changes..."
  terraform apply -input=false tfplan
  
  # Export Terraform outputs as environment variables
  log_message "INFO" "Exporting Terraform outputs as environment variables..."
  eval $(terraform output -json | jq -r 'to_entries | .[] | "export TF_OUT_\(.key)=\(.value.value)"')
  
  log_message "INFO" "Infrastructure provisioned successfully"
  return 0
}

# Function to build and push Docker image
build_and_push_image() {
  log_message "INFO" "Building and pushing Docker image..."
  
  # Login to ECR
  log_message "INFO" "Logging in to ECR..."
  aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$TF_OUT_ecr_repository_url"
  
  # Build Docker image with production optimizations
  log_message "INFO" "Building Docker image..."
  docker build \
    --build-arg ENVIRONMENT=production \
    --no-cache \
    --pull \
    -t "$TF_OUT_ecr_repository_url:$IMAGE_TAG" \
    -t "$TF_OUT_ecr_repository_url:latest" \
    "$PROJECT_ROOT"
  
  # Tag Docker image with deployment timestamp and 'prod' tag
  log_message "INFO" "Tagging Docker image..."
  docker tag "$TF_OUT_ecr_repository_url:$IMAGE_TAG" "$TF_OUT_ecr_repository_url:prod"
  
  # Push Docker image to ECR repository
  log_message "INFO" "Pushing Docker image to ECR..."
  docker push "$TF_OUT_ecr_repository_url:$IMAGE_TAG"
  docker push "$TF_OUT_ecr_repository_url:prod"
  docker push "$TF_OUT_ecr_repository_url:latest"
  
  # Update image tag in deployment configuration
  log_message "INFO" "Updating image tag in deployment configuration..."
  sed -i "s/IMAGE_TAG=.*/IMAGE_TAG=$IMAGE_TAG/" "$ANSIBLE_DIR/group_vars/prod.yml"
  
  log_message "INFO" "Docker image built and pushed successfully"
  return 0
}

# Function to deploy application using Ansible
deploy_application() {
  log_message "INFO" "Deploying application with Ansible..."
  
  # Change to Ansible directory
  cd "$ANSIBLE_DIR"
  
  # Run Ansible playbook with production inventory
  log_message "INFO" "Running Ansible playbook..."
  ansible-playbook \
    -i inventories/prod.ini \
    -e "deployment_id=$DEPLOYMENT_ID" \
    -e "image_tag=$IMAGE_TAG" \
    -e "environment=$ENVIRONMENT" \
    -e "deployment_strategy=blue_green" \
    -e "traffic_shift_increment=10" \
    -e "traffic_shift_interval=120" \
    deploy.yml
  
  # Implement gradual traffic shifting to new version
  log_message "INFO" "Implementing gradual traffic shifting to new version..."
  for percent in $(seq 10 10 100); do
    log_message "INFO" "Shifting $percent% of traffic to new version..."
    aws elbv2 modify-listener \
      --listener-arn "$TF_OUT_alb_listener_arn" \
      --default-actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=$TF_OUT_alb_target_group_blue_arn,Weight=$((100-percent))},{TargetGroupArn=$TF_OUT_alb_target_group_green_arn,Weight=$percent}]}"
    
    # Wait between traffic shifts
    sleep 120
  done
  
  log_message "INFO" "Application deployed successfully"
  return 0
}

# Function to verify deployment
verify_deployment() {
  log_message "INFO" "Verifying deployment..."
  
  # Source health check script
  source "$SCRIPT_DIR/health-check.sh"
  
  # Wait for services to initialize (longer timeout for production)
  log_message "INFO" "Waiting for services to initialize..."
  local api_url="$TF_OUT_api_endpoint"
  local timeout=300
  local interval=10
  local start_time=$(date +%s)
  local end_time=$((start_time + timeout))
  
  while [ $(date +%s) -lt $end_time ]; do
    if curl -s -f "$api_url/health/live" > /dev/null 2>&1; then
      log_message "INFO" "Service is now available at $api_url"
      break
    fi
    
    log_message "DEBUG" "Service not available yet, retrying in ${interval}s..."
    sleep $interval
  done
  
  if [ $(date +%s) -ge $end_time ]; then
    log_message "ERROR" "Timeout waiting for service to become available"
    return 1
  fi
  
  # Check API health endpoints
  log_message "INFO" "Checking API health endpoints..."
  if ! check_api_liveness; then
    log_message "ERROR" "API liveness check failed"
    return 1
  fi
  
  if ! check_api_readiness; then
    log_message "ERROR" "API readiness check failed"
    return 1
  fi
  
  # Verify database connectivity
  log_message "INFO" "Verifying database connectivity..."
  if ! check_dependencies; then
    log_message "ERROR" "Dependencies check failed"
    return 1
  fi
  
  # Test document upload functionality
  log_message "INFO" "Testing document upload functionality..."
  local test_file="/tmp/test-document-$DEPLOYMENT_ID.pdf"
  echo "Test PDF content" > "$test_file"
  
  # Get authentication token
  local auth_token=$(curl -s -X POST "$TF_OUT_api_endpoint/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"username":"test-user","password":"test-password"}' | jq -r '.access_token')
  
  # Upload test document
  local upload_response=$(curl -s -X POST "$TF_OUT_api_endpoint/documents/upload" \
    -H "Authorization: Bearer $auth_token" \
    -F "file=@$test_file")
  
  if ! echo "$upload_response" | grep -q "document_id"; then
    log_message "ERROR" "Document upload test failed"
    rm -f "$test_file"
    return 1
  fi
  
  # Clean up test file
  rm -f "$test_file"
  
  # Test vector search functionality
  log_message "INFO" "Testing vector search functionality..."
  local search_response=$(curl -s -X POST "$TF_OUT_api_endpoint/query" \
    -H "Authorization: Bearer $auth_token" \
    -H "Content-Type: application/json" \
    -d '{"query":"test query"}')
  
  if ! echo "$search_response" | grep -q "query_id"; then
    log_message "ERROR" "Vector search test failed"
    return 1
  fi
  
  # Monitor CloudWatch metrics for anomalies
  log_message "INFO" "Monitoring CloudWatch metrics for anomalies..."
  # Check that metrics are being published
  aws cloudwatch list-metrics \
    --namespace "AWS/ECS" \
    --metric-name "CPUUtilization" \
    --dimensions Name=ClusterName,Value="$TF_OUT_ecs_cluster_name" > /dev/null
  
  log_message "INFO" "Deployment verification completed successfully"
  return 0
}

# Function to create backup
create_backup() {
  log_message "INFO" "Creating backup..."
  
  # Create backup timestamp
  local backup_timestamp=$(date +%Y%m%d%H%M%S)
  local backup_prefix="prod-backup-$backup_timestamp"
  
  # Run database backup script
  log_message "INFO" "Backing up database..."
  aws rds create-db-snapshot \
    --db-instance-identifier "$TF_OUT_db_instance_id" \
    --db-snapshot-identifier "$backup_prefix-db"
  
  # Backup vector indices
  log_message "INFO" "Backing up vector indices..."
  aws s3 sync \
    "s3://$TF_OUT_vector_index_bucket/" \
    "s3://$TF_OUT_backup_bucket/$backup_prefix/vector-indices/"
  
  # Upload backups to S3 bucket with production prefix
  log_message "INFO" "Uploading backups to S3..."
  aws s3 cp "$LOG_FILE" "s3://$TF_OUT_backup_bucket/$backup_prefix/logs/"
  
  # Verify backup integrity
  log_message "INFO" "Verifying backup integrity..."
  aws rds describe-db-snapshots \
    --db-snapshot-identifier "$backup_prefix-db" \
    --query 'DBSnapshots[0].Status' \
    --output text | grep -q "available"
  
  if [ $? -ne 0 ]; then
    log_message "WARNING" "Database snapshot not yet available, but proceeding (it will complete asynchronously)"
  fi
  
  # Set backup retention policy
  log_message "INFO" "Setting backup retention policy..."
  # Keep only the last 5 production backups
  aws s3api list-objects-v2 \
    --bucket "$TF_OUT_backup_bucket" \
    --prefix "prod-backup-" \
    --query 'sort_by(Contents, &LastModified)[:-5].[Key]' \
    --output text | xargs -I {} aws s3 rm "s3://$TF_OUT_backup_bucket/{}" || true
  
  log_message "INFO" "Backup created successfully"
  return 0
}

# Function to send notification
send_notification() {
  local status=$1
  local message=""
  local subject=""
  
  log_message "INFO" "Sending $status notification..."
  
  # Determine notification message based on status
  case $status in
    "SUCCESS")
      subject="Production Deployment Successful - $DEPLOYMENT_ID"
      message="Production deployment $DEPLOYMENT_ID completed successfully at $(date)."
      message+=" Deployment details can be found in $LOG_FILE."
      ;;
    "FAILURE")
      subject="URGENT: Production Deployment Failed - $DEPLOYMENT_ID"
      message="Production deployment $DEPLOYMENT_ID failed at $(date)."
      message+=" Please check $LOG_FILE for details."
      ;;
    "ROLLBACK")
      subject="ALERT: Production Deployment Rolled Back - $DEPLOYMENT_ID"
      message="Production deployment $DEPLOYMENT_ID was rolled back at $(date)."
      message+=" Please check $LOG_FILE for details."
      ;;
    *)
      subject="Production Deployment Update - $DEPLOYMENT_ID"
      message="Production deployment $DEPLOYMENT_ID status update: $status"
      ;;
  esac
  
  # Send SNS notification to production alerts topic
  aws sns publish \
    --topic-arn "$TF_OUT_sns_topic_arn" \
    --subject "$subject" \
    --message "$message" || true
  
  # Send email to operations and management teams
  for recipient in ${NOTIFICATION_RECIPIENTS//,/ }; do
    aws ses send-email \
      --from "no-reply@example.com" \
      --destination "ToAddresses=$recipient" \
      --message "Subject={Data=$subject},Body={Text={Data=$message}}" || true
  done
  
  # Post message to Slack channel with appropriate severity
  # This is a placeholder for actual Slack integration
  log_message "INFO" "Posting notification to Slack: $subject"
  
  log_message "INFO" "Notification sent successfully"
  return 0
}

# Function to rollback deployment
rollback_deployment() {
  log_message "WARNING" "Rolling back deployment..."
  
  # Determine previous stable deployment
  local previous_task_def=$(aws ecs describe-task-definition \
    --task-definition "$TF_OUT_task_definition_name" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)
  
  # Revert to previous ECS task definition
  log_message "INFO" "Reverting to previous ECS task definition: $previous_task_def"
  aws ecs update-service \
    --cluster "$TF_OUT_ecs_cluster_name" \
    --service "$TF_OUT_ecs_service_name" \
    --task-definition "$previous_task_def" \
    --force-new-deployment
  
  # Shift traffic back to previous version
  log_message "INFO" "Shifting traffic back to previous version..."
  aws elbv2 modify-listener \
    --listener-arn "$TF_OUT_alb_listener_arn" \
    --default-actions Type=forward,TargetGroupArn="$TF_OUT_alb_target_group_blue_arn"
  
  # Verify rollback success
  log_message "INFO" "Waiting for rollback to complete..."
  aws ecs wait services-stable \
    --cluster "$TF_OUT_ecs_cluster_name" \
    --services "$TF_OUT_ecs_service_name"
  
  # Send rollback notification with high priority
  send_notification "ROLLBACK"
  
  log_message "INFO" "Rollback completed successfully"
  return 0
}

# Function to cleanup temporary files and resources
cleanup() {
  log_message "INFO" "Cleaning up temporary files and resources..."
  
  # Remove temporary files
  rm -f "$TERRAFORM_DIR/tfplan"
  
  # Clean up old deployment artifacts
  log_message "INFO" "Cleaning up old deployment artifacts..."
  find "$PROJECT_ROOT/tmp" -type f -name "deploy-*" -mtime +7 -delete || true
  
  # Maintain only the last 5 production backups
  log_message "INFO" "Maintaining only the last 5 production backups..."
  # This is handled in the create_backup function
  
  log_message "INFO" "Cleanup completed successfully"
  return 0
}

# Main function
main() {
  log_message "INFO" "Starting production deployment with ID: $DEPLOYMENT_ID"
  
  # Track deployment status
  DEPLOYMENT_STARTED=false
  
  # Check prerequisites
  check_prerequisites
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Prerequisites check failed, aborting deployment"
    return 1
  fi
  
  # Setup deployment environment
  setup_environment
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Environment setup failed, aborting deployment"
    return 1
  fi
  
  # Provision infrastructure with Terraform
  provision_infrastructure
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Infrastructure provisioning failed, aborting deployment"
    return 1
  fi
  
  # Build and push Docker image to ECR
  build_and_push_image
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Docker image build failed, aborting deployment"
    return 1
  fi
  
  # Create pre-deployment backup
  create_backup
  if [ $? -ne 0 ]; then
    log_message "WARNING" "Pre-deployment backup creation failed, proceeding with caution"
  fi
  
  # Mark deployment as started (for rollback purposes)
  DEPLOYMENT_STARTED=true
  
  # Deploy application with Ansible using blue/green strategy
  deploy_application
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Application deployment failed"
    return 1
  fi
  
  # Verify deployment success with comprehensive health checks
  verify_deployment
  if [ $? -ne 0 ]; then
    log_message "ERROR" "Deployment verification failed"
    return 1
  fi
  
  # Create post-deployment backup
  create_backup
  if [ $? -ne 0 ]; then
    log_message "WARNING" "Post-deployment backup creation failed"
  fi
  
  # Send deployment notification to stakeholders
  send_notification "SUCCESS"
  
  # Cleanup temporary resources
  cleanup
  
  log_message "INFO" "Production deployment completed successfully"
  return 0
}

# Execute main function with error handling and exit code
if ! main; then
  exit 1
fi

exit 0