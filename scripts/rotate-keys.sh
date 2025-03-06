#!/bin/bash

# rotate-keys.sh
# 
# Automates the rotation of security keys and secrets used in the 
# Document Management and AI Chatbot System. This script handles
# the rotation of JWT secrets, API keys, and other sensitive credentials
# to enhance system security through regular key rotation.

set -e

# Global variables
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
ENV_FILE=$PROJECT_ROOT/src/backend/.env
ENV_BACKUP=$PROJECT_ROOT/src/backend/.env.backup.$(date +%Y%m%d%H%M%S)
LOG_FILE=$PROJECT_ROOT/logs/key_rotation.log
ROTATION_TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Default retention period for backups (90 days)
BACKUP_RETENTION_DAYS=90

# Function to log messages to console and log file
log_message() {
    local message="$1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $message"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $message" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log_message "Checking prerequisites..."
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_message "ERROR: .env file not found at $ENV_FILE"
        return 1
    fi
    
    # Check if we have write permissions to .env file
    if [ ! -w "$ENV_FILE" ]; then
        log_message "ERROR: No write permission to $ENV_FILE"
        return 1
    }
    
    # Create log directory if it doesn't exist
    if [ ! -d "$(dirname "$LOG_FILE")" ]; then
        mkdir -p "$(dirname "$LOG_FILE")"
        log_message "Created log directory: $(dirname "$LOG_FILE")"
    fi
    
    # Check if required commands are available
    for cmd in openssl sed grep; do
        if ! command -v $cmd &> /dev/null; then
            log_message "ERROR: Required command '$cmd' is not available"
            return 1
        fi
    done
    
    log_message "All prerequisites satisfied"
    return 0
}

# Function to backup .env file
backup_env_file() {
    log_message "Creating backup of .env file to $ENV_BACKUP"
    
    cp "$ENV_FILE" "$ENV_BACKUP"
    
    if [ $? -ne 0 ] || [ ! -f "$ENV_BACKUP" ]; then
        log_message "ERROR: Failed to create backup of .env file"
        return 1
    fi
    
    log_message "Backup created successfully"
    return 0
}

# Function to generate new JWT secret
generate_jwt_secret() {
    log_message "Generating new JWT secret..."
    
    # Generate a secure random string (64 bytes in hex)
    local new_secret=$(openssl rand -hex 64)
    
    echo "$new_secret"
    return 0
}

# Function to update JWT secret in .env file
update_jwt_secret() {
    local new_secret="$1"
    log_message "Updating JWT secret in .env file..."
    
    # Check if JWT_SECRET exists in the file
    if grep -q "^JWT_SECRET=" "$ENV_FILE"; then
        # Replace existing JWT_SECRET
        sed -i.tmp "s/^JWT_SECRET=.*/JWT_SECRET=$new_secret/" "$ENV_FILE"
        rm -f "${ENV_FILE}.tmp"
    else
        # Add JWT_SECRET if it doesn't exist
        echo "JWT_SECRET=$new_secret" >> "$ENV_FILE"
    fi
    
    # Verify the secret was updated
    if ! grep -q "^JWT_SECRET=$new_secret$" "$ENV_FILE"; then
        log_message "ERROR: Failed to update JWT secret in .env file"
        return 1
    fi
    
    log_message "JWT secret updated successfully"
    return 0
}

# Function to revoke all active tokens
revoke_all_tokens() {
    log_message "Revoking all active tokens..."
    
    # Source the updated .env file to get the new secrets
    source "$ENV_FILE"
    
    # Execute token revocation
    # This could be calling an API endpoint, updating a database, etc.
    # Example: curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" https://api.example.com/auth/revoke-all
    
    # For demonstration, we'll assume a script exists for this purpose
    if [ -f "$PROJECT_ROOT/scripts/revoke-tokens.sh" ]; then
        bash "$PROJECT_ROOT/scripts/revoke-tokens.sh"
        if [ $? -eq 0 ]; then
            log_message "All tokens revoked successfully"
            return 0
        else
            log_message "WARNING: Token revocation may have failed"
            return 1
        fi
    else
        log_message "WARNING: Token revocation script not found. Manual revocation may be needed."
        return 0  # Not failing the script for this
    fi
}

# Function to rotate LLM API key
rotate_llm_api_key() {
    log_message "Checking if LLM API key rotation is needed..."
    
    # Check if the rotation is requested via environment variable or argument
    if [ "$ROTATE_LLM_API_KEY" = "true" ] || [ "$1" = "--rotate-llm" ]; then
        log_message "LLM API key rotation requested"
        
        # Prompt for new API key or get it from secure storage
        # For security, we'll prompt the user rather than hardcoding or automating
        echo -n "Enter new LLM API key (or press Enter to skip): "
        read -s new_api_key
        echo  # New line after input
        
        if [ -z "$new_api_key" ]; then
            log_message "LLM API key rotation skipped by user"
            return 0
        fi
        
        # Update the API key in the .env file
        if grep -q "^LLM_API_KEY=" "$ENV_FILE"; then
            sed -i.tmp "s/^LLM_API_KEY=.*/LLM_API_KEY=$new_api_key/" "$ENV_FILE"
            rm -f "${ENV_FILE}.tmp"
        else
            echo "LLM_API_KEY=$new_api_key" >> "$ENV_FILE"
        fi
        
        # Verify the key was updated (checking pattern, not actual value for security)
        if ! grep -q "^LLM_API_KEY=" "$ENV_FILE"; then
            log_message "ERROR: Failed to update LLM API key in .env file"
            return 1
        fi
        
        log_message "LLM API key rotated successfully"
    else
        log_message "LLM API key rotation not requested, skipping"
    fi
    
    return 0
}

# Function to restart services
restart_services() {
    log_message "Restarting services to apply new keys..."
    
    # Determine the environment
    local env="development"
    if [ -f "$PROJECT_ROOT/.env" ]; then
        source "$PROJECT_ROOT/.env"
        env="${ENVIRONMENT:-development}"
    fi
    
    log_message "Detected environment: $env"
    
    case "$env" in
        development)
            # For development, restart Docker containers
            if command -v docker &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
                log_message "Restarting Docker containers..."
                cd "$PROJECT_ROOT" && docker-compose restart
                restart_status=$?
            else
                log_message "WARNING: Docker or docker-compose.yml not found"
                restart_status=1
            fi
            ;;
            
        staging|production)
            # For staging/production, use orchestration tools or deployment pipeline
            if [ -f "$PROJECT_ROOT/scripts/deploy.sh" ]; then
                log_message "Triggering deployment process..."
                bash "$PROJECT_ROOT/scripts/deploy.sh" --reload-only
                restart_status=$?
            else
                log_message "WARNING: Deployment script not found. Manual service restart may be needed."
                restart_status=1
            fi
            ;;
            
        *)
            log_message "Unknown environment: $env. Manual service restart may be needed."
            restart_status=1
            ;;
    esac
    
    if [ $restart_status -eq 0 ]; then
        log_message "Services restarted successfully"
    else
        log_message "WARNING: Service restart may have failed"
    fi
    
    return $restart_status
}

# Function to notify administrators
notify_admins() {
    log_message "Notifying administrators about key rotation..."
    
    # Create notification message
    local message="Security key rotation performed at $ROTATION_TIMESTAMP\n"
    message+="Affected keys: JWT_SECRET"
    
    if [ "$ROTATE_LLM_API_KEY" = "true" ] || [ "$1" = "--rotate-llm" ]; then
        message+=", LLM_API_KEY"
    fi
    
    message+="\nBackup created at: $ENV_BACKUP"
    
    # Send notification
    # This could be email, Slack, or other notification methods
    # Example using mail command if available
    if command -v mail &> /dev/null && [ -n "$ADMIN_EMAIL" ]; then
        echo -e "$message" | mail -s "Security Key Rotation Notification" "$ADMIN_EMAIL"
        if [ $? -eq 0 ]; then
            log_message "Admin notification sent via email to $ADMIN_EMAIL"
        else
            log_message "WARNING: Failed to send email notification"
        fi
    else
        log_message "Admin notification details: "
        log_message "$message"
        log_message "WARNING: Could not send notification. Please inform administrators manually."
    fi
    
    return 0
}

# Function to cleanup old backups
cleanup_old_backups() {
    log_message "Cleaning up old backup files..."
    
    # Find and delete backup files older than retention period
    local backup_dir=$(dirname "$ENV_BACKUP")
    local backup_pattern=$(basename "$ENV_FILE").backup.*
    
    if [ -d "$backup_dir" ]; then
        # Find files older than BACKUP_RETENTION_DAYS
        local old_backups=$(find "$backup_dir" -name "$backup_pattern" -type f -mtime +$BACKUP_RETENTION_DAYS 2>/dev/null)
        
        if [ -n "$old_backups" ]; then
            local count=$(echo "$old_backups" | wc -l)
            log_message "Found $count backup files older than $BACKUP_RETENTION_DAYS days"
            
            # Delete old backups
            echo "$old_backups" | xargs rm -f
            
            if [ $? -eq 0 ]; then
                log_message "Old backup files deleted successfully"
            else
                log_message "WARNING: Failed to delete some old backup files"
            fi
        else
            log_message "No old backup files to delete"
        fi
    else
        log_message "Backup directory not found: $backup_dir"
    fi
    
    return 0
}

# Main function
main() {
    local exit_status=0
    
    log_message "Starting security key rotation script"
    
    # Check prerequisites
    check_prerequisites
    if [ $? -ne 0 ]; then
        log_message "ERROR: Prerequisites not met. Aborting."
        return 1
    fi
    
    # Backup current .env file
    backup_env_file
    if [ $? -ne 0 ]; then
        log_message "ERROR: Failed to backup .env file. Aborting."
        return 1
    fi
    
    # Generate and update JWT secret
    local new_jwt_secret=$(generate_jwt_secret)
    update_jwt_secret "$new_jwt_secret"
    if [ $? -ne 0 ]; then
        log_message "ERROR: Failed to update JWT secret. Check the backup at $ENV_BACKUP"
        exit_status=1
    fi
    
    # Rotate LLM API key if requested
    rotate_llm_api_key "$@"
    if [ $? -ne 0 ]; then
        log_message "ERROR: Failed to rotate LLM API key. Check the backup at $ENV_BACKUP"
        exit_status=1
    fi
    
    # Restart services to apply new keys
    restart_services
    if [ $? -ne 0 ]; then
        log_message "WARNING: Service restart may have failed. Manual restart may be needed."
        # Not failing the script for this
    fi
    
    # Revoke all active tokens
    revoke_all_tokens
    if [ $? -ne 0 ]; then
        log_message "WARNING: Token revocation may have failed. Manual verification recommended."
        # Not failing the script for this
    fi
    
    # Notify administrators
    notify_admins "$@"
    
    # Cleanup old backups
    cleanup_old_backups
    
    if [ $exit_status -eq 0 ]; then
        log_message "Security key rotation completed successfully"
    else
        log_message "Security key rotation completed with warnings/errors"
    fi
    
    return $exit_status
}

# Execute main function and pass all script arguments
main "$@"
exit $?