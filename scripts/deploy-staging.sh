#!/bin/bash
#
# deploy-staging.sh
#
# Staging deployment script for the Document Management and AI Chatbot System
# This script automates the deployment process to the staging environment,
# including infrastructure provisioning, application deployment, health checks,
# and deployment notifications.

# Exit immediately if a command exits with a non-zero status
set -e

# Script directory and project root
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

# Environment settings
ENVIRONMENT="staging"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform/environments/$ENVIRONMENT"
ANSIBLE_DIR="$PROJECT_ROOT/infrastructure/ansible"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker/docker-compose.prod.yml"
DEPLOYMENT_TIMESTAMP=$(date +%Y%m%d%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/deploy-staging-$DEPLOYMENT_TIMESTAMP.log"

# Import health check functions
source "$SCRIPT_DIR/health-check.sh"

# Environment variables
export AWS_PROFILE=staging
export AWS_REGION=us-west-2
export TF_VAR_environment=staging
export ANSIBLE_CONFIG="$ANSIBLE_DIR/ansible.cfg"
export IMAGE_TAG="$DEPLOYMENT_TIMESTAMP"
export DEPLOYMENT_ID="$DEPLOYMENT_TIMESTAMP"
export NOTIFICATION_RECIPIENTS="dev-team@example.com,qa-team@example.com"
export OPENAI_API_KEY  # Required for LLM functionality, should be set in the environment

# Error handling
trap 'handle_error $? $LINENO' ERR
trap 'cleanup' EXIT

# Function to handle errors
handle_error() {
    local exit_code=$1
    local line_number=$2
    log_message "ERROR" "Error on line $line_number, exit code $exit_code"
    
    # Roll back deployment if it was started
    if [ -n "$DEPLOYMENT_STARTED" ]; then
        log_message "INFO" "Attempting to roll back deployment..."
        rollback_deployment
    fi
    
    # Send failure notification
    send_notification "failure"
    
    exit $exit_code
}

# Function to log messages
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Define colors for console output
    local color_reset='\033[0m'
    local color_level=""
    
    case $level in
        "INFO")
            color_level='\033[0;32m'  # Green
            ;;
        "WARNING")
            color_level='\033[0;33m'  # Yellow
            ;;
        "ERROR")
            color_level='\033[0;31m'  # Red
            ;;
        *)
            color_level='\033[0;34m'  # Blue
            ;;
    esac
    
    # Echo to console with color
    echo -e "${color_level}[$timestamp] [$level] $message${color_reset}"
    
    # Append to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log_message "INFO" "Checking prerequisites..."
    
    # Check required tools are installed
    for cmd in aws terraform ansible docker; do
        if ! command -v $cmd &> /dev/null; then
            log_message "ERROR" "$cmd is not installed or not in PATH"
            return 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
        log_message "ERROR" "AWS credentials not valid or missing for profile $AWS_PROFILE"
        return 1
    fi
    
    # Check that all tests have passed in CI/CD pipeline
    if [ -z "$CI_TESTS_PASSED" ] && [ -z "$FORCE_DEPLOY" ]; then
        log_message "ERROR" "CI tests have not passed. Set CI_TESTS_PASSED=true or FORCE_DEPLOY=true to override."
        return 1
    fi
    
    # Ensure development deployment was successful
    if [ -z "$DEV_DEPLOYMENT_SUCCESSFUL" ] && [ -z "$FORCE_DEPLOY" ]; then
        log_message "ERROR" "Development deployment was not successful. Set DEV_DEPLOYMENT_SUCCESSFUL=true or FORCE_DEPLOY=true to override."
        return 1
    fi
    
    log_message "INFO" "All prerequisites satisfied"
    return 0
}

# Function to set up the environment
setup_environment() {
    log_message "INFO" "Setting up deployment environment..."
    
    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Ensure AWS CLI is configured with the staging profile
    if ! aws configure list --profile $AWS_PROFILE &> /dev/null; then
        log_message "WARNING" "AWS profile $AWS_PROFILE not configured"
        return 1
    fi
    
    log_message "INFO" "Environment setup complete"
    return 0
}

# Function to provision infrastructure
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
    
    # Apply Terraform changes
    log_message "INFO" "Applying Terraform changes..."
    terraform apply -input=false tfplan
    
    # Export Terraform outputs as environment variables
    log_message "INFO" "Exporting Terraform outputs as environment variables..."
    eval $(terraform output -json | jq -r 'to_entries | .[] | "export TF_OUT_\(.key)=\"\(.value.value)\""')
    
    log_message "INFO" "Infrastructure provisioning complete"
    return 0
}

# Function to build and push Docker image
build_and_push_image() {
    log_message "INFO" "Building and pushing Docker image..."
    
    # Get ECR repository URL from Terraform output
    ECR_REPO_URL="$TF_OUT_ecr_repository_url"
    if [ -z "$ECR_REPO_URL" ]; then
        log_message "ERROR" "ECR repository URL not found in Terraform outputs"
        return 1
    fi
    
    # Login to ECR
    log_message "INFO" "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin "$ECR_REPO_URL"
    
    # Build Docker image
    log_message "INFO" "Building Docker image..."
    docker build -f "$PROJECT_ROOT/Dockerfile" \
                --build-arg ENVIRONMENT=staging \
                --build-arg BUILD_ID="$DEPLOYMENT_TIMESTAMP" \
                -t "$ECR_REPO_URL:$IMAGE_TAG" \
                -t "$ECR_REPO_URL:staging-latest" \
                "$PROJECT_ROOT"
    
    # Push Docker image to ECR
    log_message "INFO" "Pushing Docker image to ECR..."
    docker push "$ECR_REPO_URL:$IMAGE_TAG"
    docker push "$ECR_REPO_URL:staging-latest"
    
    # Update image tag in deployment configuration
    log_message "INFO" "Updating image tag in deployment configuration..."
    sed -i.bak "s|image: .*|image: $ECR_REPO_URL:$IMAGE_TAG|g" "$ANSIBLE_DIR/vars/staging.yml"
    
    log_message "INFO" "Docker image build and push complete"
    return 0
}

# Function to deploy application
deploy_application() {
    log_message "INFO" "Deploying application using Ansible..."
    DEPLOYMENT_STARTED=true
    
    # Change to Ansible directory
    cd "$ANSIBLE_DIR"
    
    # Run Ansible playbook
    log_message "INFO" "Running Ansible playbook with staging inventory..."
    ansible-playbook -i inventories/staging deploy.yml \
        --extra-vars "environment=$ENVIRONMENT deployment_id=$DEPLOYMENT_ID image_tag=$IMAGE_TAG" \
        --extra-vars "deployment_strategy=blue_green traffic_shift_increment=10 traffic_shift_interval=120"
    
    log_message "INFO" "Application deployment complete"
    return 0
}

# Function to verify deployment
verify_deployment() {
    log_message "INFO" "Verifying deployment..."
    
    # Get the API endpoint from Terraform output
    API_ENDPOINT="$TF_OUT_api_endpoint"
    if [ -z "$API_ENDPOINT" ]; then
        log_message "ERROR" "API endpoint not found in Terraform outputs"
        return 1
    fi
    
    # Wait for services to initialize (using imported function)
    log_message "INFO" "Waiting for services to initialize..."
    wait_for_service "$API_ENDPOINT/health/live" 300  # Wait up to 5 minutes
    
    # Check API health endpoints (using imported function)
    log_message "INFO" "Checking API health endpoints..."
    if ! check_health --url "$API_ENDPOINT" --timeout 30 --verbose; then
        log_message "ERROR" "Health check failed"
        return 1
    fi
    
    # Verify database connectivity
    log_message "INFO" "Verifying database connectivity..."
    if ! curl -s "$API_ENDPOINT/health/dependencies" | grep -q '"database":.*"status":"healthy"'; then
        log_message "ERROR" "Database connectivity check failed"
        return 1
    fi
    
    # Test document upload functionality
    log_message "INFO" "Testing document upload functionality..."
    local test_result=$(curl -s -F "file=@$PROJECT_ROOT/tests/fixtures/test_document.pdf" "$API_ENDPOINT/documents/upload")
    if ! echo "$test_result" | grep -q "document_id"; then
        log_message "ERROR" "Document upload test failed"
        return 1
    fi
    
    # Test vector search functionality
    log_message "INFO" "Testing vector search functionality..."
    local search_result=$(curl -s -X POST -H "Content-Type: application/json" -d '{"query":"test query"}' "$API_ENDPOINT/query")
    if ! echo "$search_result" | grep -q "response"; then
        log_message "ERROR" "Vector search test failed"
        return 1
    fi
    
    log_message "INFO" "Deployment verification complete"
    return 0
}

# Function to create a backup
create_backup() {
    log_message "INFO" "Creating backup..."
    
    # Create backup timestamp
    BACKUP_TIMESTAMP=$(date +%Y%m%d%H%M%S)
    
    # Get S3 backup bucket from Terraform output
    S3_BACKUP_BUCKET="$TF_OUT_backup_bucket_name"
    if [ -z "$S3_BACKUP_BUCKET" ]; then
        log_message "WARNING" "S3 backup bucket not found in Terraform outputs, using default"
        S3_BACKUP_BUCKET="docmgmt-backups-staging"
    fi
    
    # Run database backup
    log_message "INFO" "Running database backup..."
    aws rds create-db-snapshot \
        --profile $AWS_PROFILE \
        --db-instance-identifier "$TF_OUT_rds_instance_id" \
        --db-snapshot-identifier "staging-backup-$BACKUP_TIMESTAMP"
    
    # Backup vector indices
    log_message "INFO" "Backing up vector indices..."
    aws s3 sync \
        --profile $AWS_PROFILE \
        "$TF_OUT_ecs_container_path/vector_indices/" \
        "s3://$S3_BACKUP_BUCKET/vector_indices/staging-$BACKUP_TIMESTAMP/"
    
    # Verify backup integrity
    log_message "INFO" "Verifying backup integrity..."
    aws s3 ls --profile $AWS_PROFILE "s3://$S3_BACKUP_BUCKET/vector_indices/staging-$BACKUP_TIMESTAMP/" > /dev/null
    
    log_message "INFO" "Backup creation complete"
    return 0
}

# Function to send notification
send_notification() {
    local status=$1
    log_message "INFO" "Sending deployment notification..."
    
    # Determine notification message based on status
    local subject
    local message
    
    if [ "$status" == "success" ]; then
        subject="Staging Deployment Successful"
        message="The deployment to staging environment was successful.\n\nDeployment ID: $DEPLOYMENT_ID\nTimestamp: $(date)\nImage: $ECR_REPO_URL:$IMAGE_TAG\n\nAPI Endpoint: $TF_OUT_api_endpoint"
    else
        subject="Staging Deployment Failed"
        message="The deployment to staging environment failed.\n\nDeployment ID: $DEPLOYMENT_ID\nTimestamp: $(date)\n\nPlease check the logs for more details: $LOG_FILE"
    fi
    
    # Send SNS notification
    if [ -n "$TF_OUT_sns_topic_arn" ]; then
        log_message "INFO" "Sending SNS notification..."
        aws sns publish \
            --profile $AWS_PROFILE \
            --topic-arn "$TF_OUT_sns_topic_arn" \
            --subject "$subject" \
            --message "$message"
    fi
    
    # Send email
    log_message "INFO" "Sending email notification..."
    # This is a simplified example, in a real environment you would use a proper email service
    echo -e "$message" | mail -s "$subject" $NOTIFICATION_RECIPIENTS
    
    # Post to Slack if webhook URL is configured
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        log_message "INFO" "Posting to Slack..."
        curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"$subject\n$message\"}" "$SLACK_WEBHOOK_URL"
    fi
    
    log_message "INFO" "Notification sent"
    return 0
}

# Function to roll back deployment
rollback_deployment() {
    log_message "WARNING" "Rolling back deployment..."
    
    # Determine previous stable deployment
    log_message "INFO" "Determining previous stable deployment..."
    local previous_task_def=$(aws ecs describe-task-definition \
        --profile $AWS_PROFILE \
        --task-definition "$TF_OUT_ecs_task_definition_family" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    
    if [ -z "$previous_task_def" ]; then
        log_message "ERROR" "Could not determine previous task definition"
        return 1
    fi
    
    # Update service to use previous task definition
    log_message "INFO" "Updating service to use previous task definition..."
    aws ecs update-service \
        --profile $AWS_PROFILE \
        --cluster "$TF_OUT_ecs_cluster_name" \
        --service "$TF_OUT_ecs_service_name" \
        --task-definition "$previous_task_def" \
        --force-new-deployment
    
    # Shift traffic back to previous version
    log_message "INFO" "Shifting traffic back to previous version..."
    aws elbv2 modify-listener \
        --profile $AWS_PROFILE \
        --listener-arn "$TF_OUT_alb_listener_arn" \
        --default-actions Type=forward,TargetGroupArn="$TF_OUT_alb_target_group_blue_arn"
    
    # Verify rollback success
    log_message "INFO" "Waiting for rollback to complete..."
    aws ecs wait services-stable \
        --profile $AWS_PROFILE \
        --cluster "$TF_OUT_ecs_cluster_name" \
        --services "$TF_OUT_ecs_service_name"
    
    # Verify health of rolled back service
    local api_endpoint=$(aws elbv2 describe-target-groups \
        --profile $AWS_PROFILE \
        --target-group-arn "$TF_OUT_alb_target_group_blue_arn" \
        --query 'TargetGroups[0].LoadBalancerArns[0]' \
        --output text | xargs aws elbv2 describe-load-balancers \
        --profile $AWS_PROFILE \
        --load-balancer-arns \
        --query 'LoadBalancers[0].DNSName' \
        --output text)
    
    wait_for_service "http://$api_endpoint/health/live" 120
    
    log_message "INFO" "Rollback complete"
    return 0
}

# Function to clean up
cleanup() {
    log_message "INFO" "Cleaning up..."
    
    # Remove temporary files
    rm -f "$TERRAFORM_DIR/tfplan"
    rm -f "$ANSIBLE_DIR/vars/staging.yml.bak"
    
    # Clean up old deployment artifacts (keep last 5)
    log_message "INFO" "Cleaning up old deployment artifacts..."
    
    # Clean up old backups (keep last 5)
    if [ -n "$S3_BACKUP_BUCKET" ]; then
        log_message "INFO" "Cleaning up old backups..."
        # List backups, sort by date, and keep only the last 5
        aws s3 ls --profile $AWS_PROFILE "s3://$S3_BACKUP_BUCKET/vector_indices/" | \
            grep "staging-" | sort -r | tail -n +6 | \
            while read -r line; do
                backup_dir=$(echo "$line" | awk '{print $NF}')
                aws s3 rm --profile $AWS_PROFILE --recursive "s3://$S3_BACKUP_BUCKET/vector_indices/$backup_dir"
            done
    fi
    
    log_message "INFO" "Cleanup complete"
    return 0
}

# Function to run tests
run_tests() {
    log_message "INFO" "Running tests..."
    
    # Get the API endpoint from Terraform output
    API_ENDPOINT="$TF_OUT_api_endpoint"
    
    # Run smoke tests
    log_message "INFO" "Running smoke tests..."
    "$PROJECT_ROOT/tests/smoke/run_smoke_tests.sh" --url "$API_ENDPOINT"
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Smoke tests failed"
        return 1
    fi
    
    # Run integration tests
    log_message "INFO" "Running integration tests..."
    "$PROJECT_ROOT/tests/integration/run_integration_tests.sh" --url "$API_ENDPOINT" --environment staging
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Integration tests failed"
        return 1
    fi
    
    # Run performance tests
    log_message "INFO" "Running performance tests..."
    "$PROJECT_ROOT/tests/performance/run_performance_tests.sh" --url "$API_ENDPOINT" --environment staging
    if [ $? -ne 0 ]; then
        log_message "WARNING" "Performance tests did not meet all targets"
        # Don't fail deployment for performance test warnings
    fi
    
    # Generate test report
    log_message "INFO" "Generating test report..."
    "$PROJECT_ROOT/tests/generate_report.sh" \
        --output "$PROJECT_ROOT/logs/test-report-$DEPLOYMENT_TIMESTAMP.html" \
        --environment staging
    
    log_message "INFO" "Tests completed"
    return 0
}

# Main function
main() {
    log_message "INFO" "Starting staging deployment..."
    
    # Check prerequisites
    check_prerequisites
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Prerequisites check failed"
        exit 1
    fi
    
    # Setup environment
    setup_environment
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Environment setup failed"
        exit 1
    fi
    
    # Provision infrastructure
    provision_infrastructure
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Infrastructure provisioning failed"
        exit 1
    fi
    
    # Build and push Docker image
    build_and_push_image
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Docker image build and push failed"
        exit 1
    fi
    
    # Create pre-deployment backup
    create_backup
    if [ $? -ne 0 ]; then
        log_message "WARNING" "Pre-deployment backup failed, proceeding anyway..."
    fi
    
    # Deploy application
    deploy_application
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Application deployment failed"
        exit 1
    fi
    
    # Verify deployment
    verify_deployment
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Deployment verification failed"
        exit 1
    fi
    
    # Run tests against the staging environment
    run_tests
    if [ $? -ne 0 ]; then
        log_message "ERROR" "Tests failed"
        exit 1
    fi
    
    # Create post-deployment backup
    create_backup
    if [ $? -ne 0 ]; then
        log_message "WARNING" "Post-deployment backup failed"
    fi
    
    # Send success notification
    send_notification "success"
    
    # Clean up
    cleanup
    
    log_message "INFO" "Staging deployment completed successfully"
    return 0
}

# Execute the main function
main
exit $?