#!/bin/bash
#
# backup-database.sh - PostgreSQL database backup script for Document Management and AI Chatbot System
#
# This script handles full database dumps, WAL archiving, and backup rotation with
# support for local and S3 storage. It provides comprehensive backup solutions
# as part of the system's disaster recovery strategy.
#
# Usage: backup-database.sh [options]
#   Options:
#     -c, --config CONFIG_FILE  Specify config file (default: /etc/document-management/backup.conf)
#     -f, --full-backup        Perform full database backup
#     -w, --wal-only          Archive WAL logs only (no full backup)
#     -s, --s3-upload         Upload backups to S3
#     -r, --retention DAYS    Override retention period (default: 30 days)
#     --no-verify             Skip backup verification
#     --verbose               Enable verbose output
#     -h, --help              Show this help message
#
# Exit codes:
#   0  Success
#   1  Configuration error
#   2  Dependency error
#   3  Database connection error
#   4  Backup error
#   5  Verification error
#   6  Upload error
#

# Default values for global variables
BACKUP_DIR="/opt/document-management/backups/database"
BACKUP_LOG_FILE="/opt/document-management/backups/logs/backup.log"
CONFIG_FILE="/etc/document-management/backup.conf"
TEMP_BACKUP_DIR="/tmp/db-backup"
S3_BUCKET="docaichatbot-backups"
RETENTION_DAYS="30"
WAL_ARCHIVE_DIR="/opt/document-management/backups/wal"

# Runtime variables
VERBOSE=false
DO_FULL_BACKUP=true
DO_WAL_ARCHIVING=true
DO_S3_UPLOAD=false
DO_VERIFY=true

# Function to log messages
log_message() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "${timestamp} - ${message}" >> "${BACKUP_LOG_FILE}"
    if [[ "${VERBOSE}" == true ]]; then
        echo "${timestamp} - ${message}"
    fi
}

# Function to load configuration from config file
load_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log_message "ERROR: Configuration file ${CONFIG_FILE} not found"
        return 1
    fi

    log_message "Loading configuration from ${CONFIG_FILE}"
    source "${CONFIG_FILE}"

    # Validate essential configuration parameters
    if [[ -z "${DB_NAME}" ]]; then
        log_message "ERROR: DB_NAME not defined in configuration file"
        return 1
    fi

    if [[ -z "${DB_USER}" ]]; then
        log_message "ERROR: DB_USER not defined in configuration file"
        return 1
    fi

    # Check if S3 configuration is present if S3 upload is enabled
    if [[ "${DO_S3_UPLOAD}" == true ]]; then
        if [[ -z "${S3_BUCKET}" ]]; then
            log_message "ERROR: S3_BUCKET not defined in configuration file but S3 upload is enabled"
            return 1
        fi
    fi

    log_message "Configuration loaded successfully"
    return 0
}

# Function to check if required dependencies are installed
check_dependencies() {
    local missing_deps=false

    # Check for PostgreSQL utilities
    if ! command -v pg_dump &> /dev/null; then
        log_message "ERROR: pg_dump not found. Please install PostgreSQL client utilities."
        missing_deps=true
    fi

    if ! command -v psql &> /dev/null; then
        log_message "ERROR: psql not found. Please install PostgreSQL client utilities."
        missing_deps=true
    fi

    if ! command -v pg_restore &> /dev/null; then
        log_message "ERROR: pg_restore not found. Please install PostgreSQL client utilities."
        missing_deps=true
    fi

    # Check for AWS CLI if S3 upload is enabled
    if [[ "${DO_S3_UPLOAD}" == true ]]; then
        if ! command -v aws &> /dev/null; then
            log_message "ERROR: aws CLI not found but S3 upload is enabled. Please install AWS CLI."
            missing_deps=true
        fi
    fi

    # Check for required utilities
    if ! command -v gzip &> /dev/null; then
        log_message "ERROR: gzip not found. Please install gzip."
        missing_deps=true
    fi

    if [[ "${missing_deps}" == true ]]; then
        return 1
    fi

    log_message "All required dependencies are installed"
    return 0
}

# Function to create necessary backup directories
create_backup_directories() {
    # Create main backup directory
    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log_message "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}"
        if [[ $? -ne 0 ]]; then
            log_message "ERROR: Failed to create backup directory: ${BACKUP_DIR}"
            return 1
        fi
    fi

    # Create WAL archive directory if WAL archiving is enabled
    if [[ "${DO_WAL_ARCHIVING}" == true && ! -d "${WAL_ARCHIVE_DIR}" ]]; then
        log_message "Creating WAL archive directory: ${WAL_ARCHIVE_DIR}"
        mkdir -p "${WAL_ARCHIVE_DIR}"
        if [[ $? -ne 0 ]]; then
            log_message "ERROR: Failed to create WAL archive directory: ${WAL_ARCHIVE_DIR}"
            return 1
        fi
    fi

    # Create logs directory if it doesn't exist
    local logs_dir=$(dirname "${BACKUP_LOG_FILE}")
    if [[ ! -d "${logs_dir}" ]]; then
        log_message "Creating logs directory: ${logs_dir}"
        mkdir -p "${logs_dir}"
        if [[ $? -ne 0 ]]; then
            log_message "ERROR: Failed to create logs directory: ${logs_dir}"
            return 1
        fi
    fi

    # Create temporary backup directory
    if [[ ! -d "${TEMP_BACKUP_DIR}" ]]; then
        log_message "Creating temporary backup directory: ${TEMP_BACKUP_DIR}"
        mkdir -p "${TEMP_BACKUP_DIR}"
        if [[ $? -ne 0 ]]; then
            log_message "ERROR: Failed to create temporary backup directory: ${TEMP_BACKUP_DIR}"
            return 1
        fi
    fi

    # Set appropriate permissions on directories
    chmod 700 "${BACKUP_DIR}" "${WAL_ARCHIVE_DIR}" "${TEMP_BACKUP_DIR}"
    
    log_message "All necessary backup directories have been created"
    return 0
}

# Function to check database connection
check_database_connection() {
    log_message "Testing database connection"

    # Set PostgreSQL environment variables from config
    export PGHOST="${DB_HOST:-localhost}"
    export PGPORT="${DB_PORT:-5432}"
    export PGDATABASE="${DB_NAME}"
    export PGUSER="${DB_USER}"
    export PGPASSWORD="${DB_PASSWORD}"

    # Attempt to connect to the database
    psql -c "SELECT 1" > /dev/null 2>&1
    local exit_status=$?

    if [[ ${exit_status} -ne 0 ]]; then
        log_message "ERROR: Failed to connect to database. Please check your credentials and database status."
        return 1
    fi

    log_message "Database connection successful"
    return 0
}

# Function to perform a full database backup
perform_full_backup() {
    log_message "Starting full database backup"

    # Set PostgreSQL environment variables from config
    export PGHOST="${DB_HOST:-localhost}"
    export PGPORT="${DB_PORT:-5432}"
    export PGDATABASE="${DB_NAME}"
    export PGUSER="${DB_USER}"
    export PGPASSWORD="${DB_PASSWORD}"

    # Generate backup filename with timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${BACKUP_DIR}/${DB_NAME}_${timestamp}.custom"

    log_message "Creating backup: ${backup_file}"

    # Use pg_dump to create a backup in custom format
    pg_dump -Fc -v -f "${backup_file}" ${DB_NAME} 2>> "${BACKUP_LOG_FILE}"
    local exit_status=$?

    if [[ ${exit_status} -ne 0 ]]; then
        log_message "ERROR: Database backup failed with exit code ${exit_status}"
        echo "" # Return empty string on failure
        return 1
    fi

    local backup_size=$(du -h "${backup_file}" | cut -f1)
    log_message "Full database backup completed successfully. File: ${backup_file}, Size: ${backup_size}"
    
    # Compress the backup if not already compressed
    if [[ "${backup_file}" != *.gz ]]; then
        log_message "Compressing backup file"
        gzip "${backup_file}"
        if [[ $? -eq 0 ]]; then
            backup_file="${backup_file}.gz"
            log_message "Backup compressed: ${backup_file}"
        else
            log_message "WARNING: Failed to compress backup file"
        fi
    fi

    # Return the backup file path
    echo "${backup_file}"
    return 0
}

# Function to configure WAL archiving in PostgreSQL
configure_wal_archiving() {
    log_message "Checking WAL archiving configuration"

    # Set PostgreSQL environment variables from config
    export PGHOST="${DB_HOST:-localhost}"
    export PGPORT="${DB_PORT:-5432}"
    export PGDATABASE="${DB_NAME}"
    export PGUSER="${DB_USER}"
    export PGPASSWORD="${DB_PASSWORD}"

    # Check if WAL archiving is already enabled
    local archive_mode=$(psql -At -c "SHOW archive_mode;")
    
    if [[ "${archive_mode}" == "on" ]]; then
        log_message "WAL archiving is already enabled"
        return 0
    fi
    
    # If we're here, WAL archiving needs to be configured
    log_message "Configuring WAL archiving"

    # We need superuser privileges to configure PostgreSQL
    if [[ "${DB_USER}" != "postgres" ]]; then
        log_message "ERROR: Configuring WAL archiving requires superuser privileges"
        log_message "Please configure WAL archiving manually or run this script as a database superuser"
        return 1
    fi

    # Construct the archive command
    local archive_command="cp %p ${WAL_ARCHIVE_DIR}/%f"

    # Update PostgreSQL configuration
    psql -c "ALTER SYSTEM SET archive_mode = on;" 2>> "${BACKUP_LOG_FILE}"
    psql -c "ALTER SYSTEM SET archive_command = '${archive_command}';" 2>> "${BACKUP_LOG_FILE}"
    
    # Reload PostgreSQL configuration
    log_message "Reloading PostgreSQL configuration"
    psql -c "SELECT pg_reload_conf();" 2>> "${BACKUP_LOG_FILE}"
    
    # Verify WAL archiving is now enabled
    archive_mode=$(psql -At -c "SHOW archive_mode;")
    local archive_cmd=$(psql -At -c "SHOW archive_command;")
    
    if [[ "${archive_mode}" == "on" && "${archive_cmd}" == "${archive_command}" ]]; then
        log_message "WAL archiving successfully configured"
        log_message "NOTE: A server restart may be required for archive_mode changes to take effect"
        return 0
    else
        log_message "ERROR: Failed to configure WAL archiving"
        return 1
    fi
}

# Function to upload backup file to S3
upload_to_s3() {
    local backup_file="$1"
    
    if [[ -z "${backup_file}" || ! -f "${backup_file}" ]]; then
        log_message "ERROR: Cannot upload to S3, backup file not found: ${backup_file}"
        return 1
    fi
    
    if [[ "${DO_S3_UPLOAD}" != true ]]; then
        log_message "S3 upload is disabled, skipping"
        return 0
    fi
    
    log_message "Uploading backup to S3: s3://${S3_BUCKET}/"
    
    # Extract just the filename from the path
    local filename=$(basename "${backup_file}")
    local s3_path="s3://${S3_BUCKET}/database-backups/${filename}"
    
    # Upload to S3
    aws s3 cp "${backup_file}" "${s3_path}" 2>> "${BACKUP_LOG_FILE}"
    local exit_status=$?
    
    if [[ ${exit_status} -ne 0 ]]; then
        log_message "ERROR: Failed to upload backup to S3"
        return 1
    fi
    
    # Verify the upload
    aws s3 ls "${s3_path}" > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        log_message "ERROR: Failed to verify backup upload to S3"
        return 1
    fi
    
    log_message "Backup successfully uploaded to S3: ${s3_path}"
    return 0
}

# Function to upload WAL archive files to S3
upload_wal_to_s3() {
    if [[ "${DO_S3_UPLOAD}" != true || "${DO_WAL_ARCHIVING}" != true ]]; then
        log_message "S3 upload or WAL archiving is disabled, skipping WAL files upload"
        return 0
    fi
    
    log_message "Uploading WAL archive files to S3"
    
    # Create a marker directory to track uploaded files
    local marker_dir="${WAL_ARCHIVE_DIR}/.uploaded"
    mkdir -p "${marker_dir}"
    
    # Find WAL files that haven't been uploaded yet
    local wal_files=$(find "${WAL_ARCHIVE_DIR}" -type f -name "*.backup" -o -name "*.history" -o -name "[0-9A-F]*" | grep -v ".uploaded")
    
    if [[ -z "${wal_files}" ]]; then
        log_message "No new WAL files to upload"
        return 0
    fi
    
    local upload_count=0
    local fail_count=0
    
    for wal_file in ${wal_files}; do
        local filename=$(basename "${wal_file}")
        local s3_path="s3://${S3_BUCKET}/wal-archives/${filename}"
        
        log_message "Uploading WAL file: ${filename}"
        aws s3 cp "${wal_file}" "${s3_path}" 2>> "${BACKUP_LOG_FILE}"
        
        if [[ $? -eq 0 ]]; then
            # Mark file as uploaded
            touch "${marker_dir}/${filename}"
            ((upload_count++))
        else
            log_message "ERROR: Failed to upload WAL file: ${filename}"
            ((fail_count++))
        fi
    done
    
    log_message "WAL files upload complete: ${upload_count} files uploaded, ${fail_count} failed"
    
    if [[ ${fail_count} -gt 0 ]]; then
        return 1
    fi
    
    return 0
}

# Function to clean up old backups
cleanup_old_backups() {
    log_message "Cleaning up old backups (retention: ${RETENTION_DAYS} days)"
    
    # Find and remove local backup files older than retention period
    local old_backups=$(find "${BACKUP_DIR}" -type f -name "${DB_NAME}_*.custom*" -mtime +${RETENTION_DAYS})
    local count=0
    
    if [[ -n "${old_backups}" ]]; then
        for backup in ${old_backups}; do
            log_message "Removing old backup: ${backup}"
            rm -f "${backup}"
            if [[ $? -eq 0 ]]; then
                ((count++))
            else
                log_message "WARNING: Failed to remove old backup: ${backup}"
            fi
        done
    fi
    
    log_message "Removed ${count} old local backup files"
    
    # Clean up old backups in S3 if enabled
    if [[ "${DO_S3_UPLOAD}" == true ]]; then
        log_message "Cleaning up old backups from S3"
        
        # Calculate cutoff date in seconds since epoch
        local cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%s)
        
        # List all backups in S3
        local s3_backups=$(aws s3 ls "s3://${S3_BUCKET}/database-backups/" | grep "${DB_NAME}_")
        local s3_count=0
        
        while read -r line; do
            if [[ -n "${line}" ]]; then
                # Extract date and filename
                local backup_date=$(echo "${line}" | awk '{print $1, $2}')
                local backup_file=$(echo "${line}" | awk '{print $4}')
                
                # Convert to seconds since epoch
                local backup_epoch=$(date -d "${backup_date}" +%s)
                
                # Check if older than retention period
                if [[ ${backup_epoch} -lt ${cutoff_date} ]]; then
                    log_message "Removing old S3 backup: ${backup_file}"
                    aws s3 rm "s3://${S3_BUCKET}/database-backups/${backup_file}" 2>> "${BACKUP_LOG_FILE}"
                    if [[ $? -eq 0 ]]; then
                        ((s3_count++))
                    else
                        log_message "WARNING: Failed to remove old S3 backup: ${backup_file}"
                    fi
                fi
            fi
        done <<< "${s3_backups}"
        
        log_message "Removed ${s3_count} old S3 backup files"
    fi
    
    return 0
}

# Function to clean up old WAL archive files
cleanup_old_wal_files() {
    if [[ "${DO_WAL_ARCHIVING}" != true ]]; then
        log_message "WAL archiving is disabled, skipping WAL file cleanup"
        return 0
    fi
    
    log_message "Cleaning up old WAL archive files (retention: ${RETENTION_DAYS} days)"
    
    # Find and remove local WAL files older than retention period
    local old_wal_files=$(find "${WAL_ARCHIVE_DIR}" -type f -mtime +${RETENTION_DAYS} | grep -v ".uploaded")
    local count=0
    
    if [[ -n "${old_wal_files}" ]]; then
        for wal_file in ${old_wal_files}; do
            log_message "Removing old WAL file: ${wal_file}"
            rm -f "${wal_file}"
            
            # Also remove the uploaded marker if it exists
            local filename=$(basename "${wal_file}")
            rm -f "${WAL_ARCHIVE_DIR}/.uploaded/${filename}"
            
            if [[ $? -eq 0 ]]; then
                ((count++))
            else
                log_message "WARNING: Failed to remove old WAL file: ${wal_file}"
            fi
        done
    fi
    
    log_message "Removed ${count} old local WAL files"
    
    # Clean up old WAL files in S3 if enabled
    if [[ "${DO_S3_UPLOAD}" == true ]]; then
        log_message "Cleaning up old WAL files from S3"
        
        # Calculate cutoff date in seconds since epoch
        local cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%s)
        
        # List all WAL files in S3
        local s3_wal_files=$(aws s3 ls "s3://${S3_BUCKET}/wal-archives/")
        local s3_count=0
        
        while read -r line; do
            if [[ -n "${line}" ]]; then
                # Extract date and filename
                local file_date=$(echo "${line}" | awk '{print $1, $2}')
                local file_name=$(echo "${line}" | awk '{print $4}')
                
                # Convert to seconds since epoch
                local file_epoch=$(date -d "${file_date}" +%s)
                
                # Check if older than retention period
                if [[ ${file_epoch} -lt ${cutoff_date} ]]; then
                    log_message "Removing old S3 WAL file: ${file_name}"
                    aws s3 rm "s3://${S3_BUCKET}/wal-archives/${file_name}" 2>> "${BACKUP_LOG_FILE}"
                    if [[ $? -eq 0 ]]; then
                        ((s3_count++))
                    else
                        log_message "WARNING: Failed to remove old S3 WAL file: ${file_name}"
                    fi
                fi
            fi
        done <<< "${s3_wal_files}"
        
        log_message "Removed ${s3_count} old S3 WAL files"
    fi
    
    return 0
}

# Function to verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    if [[ -z "${backup_file}" || ! -f "${backup_file}" ]]; then
        log_message "ERROR: Cannot verify backup, file not found: ${backup_file}"
        return 1
    fi
    
    if [[ "${DO_VERIFY}" != true ]]; then
        log_message "Backup verification is disabled, skipping"
        return 0
    fi
    
    log_message "Verifying backup integrity: ${backup_file}"
    
    # Check if file is gzipped
    local is_gzipped=false
    if [[ "${backup_file}" == *.gz ]]; then
        is_gzipped=true
    fi
    
    if [[ "${is_gzipped}" == true ]]; then
        # For gzipped files, check if we can read the header
        gunzip -t "${backup_file}" 2>> "${BACKUP_LOG_FILE}"
        local gunzip_status=$?
        
        if [[ ${gunzip_status} -ne 0 ]]; then
            log_message "ERROR: Backup file is corrupt or invalid (gunzip test failed)"
            return 1
        fi
        
        # Create a temporary copy for verification
        local temp_file="${TEMP_BACKUP_DIR}/$(basename "${backup_file}" .gz)"
        gunzip -c "${backup_file}" > "${temp_file}"
        
        # Verify using pg_restore
        pg_restore --list "${temp_file}" > /dev/null 2>> "${BACKUP_LOG_FILE}"
        local restore_status=$?
        
        # Clean up temp file
        rm -f "${temp_file}"
        
        if [[ ${restore_status} -ne 0 ]]; then
            log_message "ERROR: Backup file verification failed"
            return 1
        fi
    else
        # For non-gzipped files, directly verify
        pg_restore --list "${backup_file}" > /dev/null 2>> "${BACKUP_LOG_FILE}"
        local restore_status=$?
        
        if [[ ${restore_status} -ne 0 ]]; then
            log_message "ERROR: Backup file verification failed"
            return 1
        fi
    fi
    
    log_message "Backup file verification passed"
    return 0
}

# Function to send notifications
send_notification() {
    local status="$1"
    local message="$2"
    
    # Check if notifications are enabled
    if [[ "${ENABLE_NOTIFICATIONS:-false}" != true ]]; then
        return 0
    fi
    
    log_message "Sending notification: ${status}"
    
    # Prepare notification message
    local hostname=$(hostname)
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local notification_message="Backup Status: ${status}\nHost: ${hostname}\nTime: ${timestamp}\nDatabase: ${DB_NAME}\n\n${message}"
    
    # Send notification based on configured method
    case "${NOTIFICATION_METHOD:-email}" in
        email)
            if [[ -n "${NOTIFICATION_EMAIL}" ]]; then
                echo -e "${notification_message}" | mail -s "Database Backup ${status} - ${DB_NAME}" "${NOTIFICATION_EMAIL}"
                local send_status=$?
                
                if [[ ${send_status} -ne 0 ]]; then
                    log_message "WARNING: Failed to send email notification"
                    return 1
                fi
            else
                log_message "WARNING: Email notification enabled but NOTIFICATION_EMAIL not set"
                return 1
            fi
            ;;
        slack)
            if [[ -n "${SLACK_WEBHOOK_URL}" ]]; then
                local payload="{\"text\":\"Database Backup ${status} - ${DB_NAME}\", \"attachments\":[{\"text\":\"${notification_message}\", \"color\":\"${status,,}\"}]}"
                curl -s -X POST -H 'Content-type: application/json' --data "${payload}" "${SLACK_WEBHOOK_URL}" 2>> "${BACKUP_LOG_FILE}"
                local send_status=$?
                
                if [[ ${send_status} -ne 0 ]]; then
                    log_message "WARNING: Failed to send Slack notification"
                    return 1
                fi
            else
                log_message "WARNING: Slack notification enabled but SLACK_WEBHOOK_URL not set"
                return 1
            fi
            ;;
        *)
            log_message "WARNING: Unknown notification method: ${NOTIFICATION_METHOD}"
            return 1
            ;;
    esac
    
    log_message "Notification sent successfully"
    return 0
}

# Function to clean up temporary files
cleanup() {
    log_message "Cleaning up temporary files"
    
    # Remove temporary files
    rm -rf "${TEMP_BACKUP_DIR}"/*
    
    log_message "Cleanup completed"
    return 0
}

# Main function
main() {
    local backup_file=""
    local backup_success=true
    local start_time=$(date +%s)
    
    log_message "Starting database backup process"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -f|--full-backup)
                DO_FULL_BACKUP=true
                shift
                ;;
            -w|--wal-only)
                DO_FULL_BACKUP=false
                DO_WAL_ARCHIVING=true
                shift
                ;;
            -s|--s3-upload)
                DO_S3_UPLOAD=true
                shift
                ;;
            -r|--retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --no-verify)
                DO_VERIFY=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                echo "Usage: backup-database.sh [options]"
                echo "  Options:"
                echo "    -c, --config CONFIG_FILE  Specify config file (default: /etc/document-management/backup.conf)"
                echo "    -f, --full-backup        Perform full database backup"
                echo "    -w, --wal-only          Archive WAL logs only (no full backup)"
                echo "    -s, --s3-upload         Upload backups to S3"
                echo "    -r, --retention DAYS    Override retention period (default: 30 days)"
                echo "    --no-verify             Skip backup verification"
                echo "    --verbose               Enable verbose output"
                echo "    -h, --help              Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "${BACKUP_LOG_FILE}")"
    
    # Load configuration
    load_config
    if [[ $? -ne 0 ]]; then
        log_message "Failed to load configuration"
        send_notification "FAILED" "Configuration error"
        exit 1
    fi
    
    # Check dependencies
    check_dependencies
    if [[ $? -ne 0 ]]; then
        log_message "Missing required dependencies"
        send_notification "FAILED" "Missing dependencies"
        exit 2
    fi
    
    # Create backup directories
    create_backup_directories
    if [[ $? -ne 0 ]]; then
        log_message "Failed to create backup directories"
        send_notification "FAILED" "Failed to create backup directories"
        exit 1
    fi
    
    # Check database connection
    check_database_connection
    if [[ $? -ne 0 ]]; then
        log_message "Database connection failed"
        send_notification "FAILED" "Database connection error"
        exit 3
    fi
    
    # Configure WAL archiving if enabled
    if [[ "${DO_WAL_ARCHIVING}" == true ]]; then
        configure_wal_archiving
        if [[ $? -ne 0 ]]; then
            log_message "WARNING: Failed to configure WAL archiving"
            # Continue execution - this is not fatal
        fi
    fi
    
    # Perform full backup if enabled
    if [[ "${DO_FULL_BACKUP}" == true ]]; then
        backup_file=$(perform_full_backup)
        if [[ -z "${backup_file}" || ! -f "${backup_file}" ]]; then
            log_message "Backup failed"
            backup_success=false
        else
            # Verify backup if enabled
            if [[ "${DO_VERIFY}" == true ]]; then
                verify_backup "${backup_file}"
                if [[ $? -ne 0 ]]; then
                    log_message "Backup verification failed"
                    backup_success=false
                fi
            fi
            
            # Upload to S3 if enabled
            if [[ "${DO_S3_UPLOAD}" == true && "${backup_success}" == true ]]; then
                upload_to_s3 "${backup_file}"
                if [[ $? -ne 0 ]]; then
                    log_message "WARNING: Failed to upload backup to S3"
                    # Not treating S3 upload failure as fatal
                fi
            fi
        fi
    fi
    
    # Upload WAL archives to S3 if enabled
    if [[ "${DO_WAL_ARCHIVING}" == true && "${DO_S3_UPLOAD}" == true ]]; then
        upload_wal_to_s3
        if [[ $? -ne 0 ]]; then
            log_message "WARNING: Failed to upload some WAL files to S3"
            # Not treating WAL upload failure as fatal
        fi
    fi
    
    # Clean up old backups
    cleanup_old_backups
    if [[ $? -ne 0 ]]; then
        log_message "WARNING: Failed to clean up some old backups"
        # Not treating cleanup failure as fatal
    fi
    
    # Clean up old WAL files
    if [[ "${DO_WAL_ARCHIVING}" == true ]]; then
        cleanup_old_wal_files
        if [[ $? -ne 0 ]]; then
            log_message "WARNING: Failed to clean up some old WAL files"
            # Not treating WAL cleanup failure as fatal
        fi
    fi
    
    # Clean up temporary files
    cleanup
    
    # Calculate runtime
    local end_time=$(date +%s)
    local runtime=$((end_time - start_time))
    local minutes=$((runtime / 60))
    local seconds=$((runtime % 60))
    
    # Prepare summary
    local summary=""
    if [[ "${DO_FULL_BACKUP}" == true ]]; then
        if [[ "${backup_success}" == true ]]; then
            summary="Full backup completed successfully in ${minutes}m ${seconds}s"
            if [[ -n "${backup_file}" ]]; then
                local backup_size=$(du -h "${backup_file}" | cut -f1)
                summary="${summary}\nBackup file: ${backup_file}\nSize: ${backup_size}"
            fi
            log_message "${summary}"
            send_notification "SUCCESS" "${summary}"
            exit 0
        else
            summary="Backup process failed after ${minutes}m ${seconds}s"
            log_message "${summary}"
            send_notification "FAILED" "${summary}"
            exit 4
        fi
    else
        # WAL-only mode
        summary="WAL archiving completed in ${minutes}m ${seconds}s"
        log_message "${summary}"
        send_notification "SUCCESS" "${summary}"
        exit 0
    fi
}

# Call main function with all arguments
main "$@"