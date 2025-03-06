#!/bin/bash

#######################################################################
# Script for cleaning up old backup files based on retention policies
#
# Usage: cleanup-old-backups.sh [options]
#   Options:
#     -c, --config CONFIG_FILE  Specify config file (default: /etc/document-management/backup.conf)
#     -d, --db-retention DAYS   Override database backup retention period (default: 30 days)
#     -v, --vector-retention DAYS Override vector index backup retention period (default: 14 days)
#     -w, --wal-retention DAYS  Override WAL archive retention period (default: 7 days)
#     -s, --s3-cleanup         Clean up backups in S3 bucket
#     --verbose                Enable verbose output
#     -h, --help               Show this help message
#
# Exit codes:
#   0  Success
#   1  Configuration error
#   2  Dependency error
#   3  Filesystem error
#   4  S3 operation error
#######################################################################

# Default global variables
BACKUP_DIR="/opt/document-management/backups"
DATABASE_BACKUP_DIR="${BACKUP_DIR}/database"
VECTOR_BACKUP_DIR="${BACKUP_DIR}/vector"
WAL_ARCHIVE_DIR="${BACKUP_DIR}/wal"
LOG_FILE="${BACKUP_DIR}/logs/cleanup.log"
CONFIG_FILE="/etc/document-management/backup.conf"
S3_BUCKET="docaichatbot-backups"
DB_RETENTION_DAYS="30"
VECTOR_RETENTION_DAYS="14"
WAL_RETENTION_DAYS="7"
VERBOSE="false"
ENABLE_S3_CLEANUP="false"

# Function to log messages with timestamp
log_message() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    mkdir -p "$(dirname "${LOG_FILE}")"
    echo "[${timestamp}] $1" >> "${LOG_FILE}"
    
    if [[ "${VERBOSE}" == "true" ]]; then
        echo "[${timestamp}] $1"
    fi
}

# Function to load configuration from the config file
load_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log_message "ERROR: Configuration file ${CONFIG_FILE} not found."
        return 1
    fi
    
    log_message "Loading configuration from ${CONFIG_FILE}"
    # shellcheck source=/dev/null
    source "${CONFIG_FILE}"
    
    # Override default retention periods if specified in config
    DB_RETENTION_DAYS=${DB_RETENTION_DAYS:-30}
    VECTOR_RETENTION_DAYS=${VECTOR_RETENTION_DAYS:-14}
    WAL_RETENTION_DAYS=${WAL_RETENTION_DAYS:-7}
    
    # Validate required configuration parameters
    if [[ -z "${BACKUP_DIR}" ]]; then
        log_message "ERROR: BACKUP_DIR is not set in configuration."
        return 1
    fi
    
    if [[ "${ENABLE_S3_CLEANUP}" == "true" && -z "${S3_BUCKET}" ]]; then
        log_message "ERROR: S3_BUCKET is not set in configuration but S3 cleanup is enabled."
        return 1
    fi
    
    # Update derived variables
    DATABASE_BACKUP_DIR="${BACKUP_DIR}/database"
    VECTOR_BACKUP_DIR="${BACKUP_DIR}/vector"
    WAL_ARCHIVE_DIR="${BACKUP_DIR}/wal"
    LOG_FILE="${BACKUP_DIR}/logs/cleanup.log"
    
    log_message "Configuration loaded successfully"
    log_message "Database backup retention: ${DB_RETENTION_DAYS} days"
    log_message "Vector backup retention: ${VECTOR_RETENTION_DAYS} days"
    log_message "WAL archive retention: ${WAL_RETENTION_DAYS} days"
    log_message "S3 cleanup enabled: ${ENABLE_S3_CLEANUP}"
    if [[ "${ENABLE_S3_CLEANUP}" == "true" ]]; then
        log_message "S3 bucket: ${S3_BUCKET}"
    fi
    
    return 0
}

# Function to check if required dependencies are installed
check_dependencies() {
    # Check if find command is available
    if ! command -v find &> /dev/null; then
        log_message "ERROR: 'find' command not found."
        return 1
    fi
    
    # Check if aws cli is available if S3 cleanup is enabled
    if [[ "${ENABLE_S3_CLEANUP}" == "true" ]]; then
        if ! command -v aws &> /dev/null; then
            log_message "ERROR: 'aws' command not found but S3 cleanup is enabled."
            return 1
        fi
    fi
    
    log_message "All required dependencies are available"
    return 0
}

# Function to create log directory if it doesn't exist
create_log_directory() {
    local log_dir
    log_dir=$(dirname "${LOG_FILE}")
    
    if [[ ! -d "${log_dir}" ]]; then
        mkdir -p "${log_dir}"
        if [[ $? -ne 0 ]]; then
            echo "ERROR: Failed to create log directory ${log_dir}"
            return 1
        fi
        
        # Set appropriate permissions on directory
        chmod 750 "${log_dir}"
    fi
    
    return 0
}

# Function to remove database backup files older than retention period from local storage
cleanup_local_database_backups() {
    if [[ ! -d "${DATABASE_BACKUP_DIR}" ]]; then
        log_message "WARNING: Database backup directory ${DATABASE_BACKUP_DIR} does not exist"
        return 0
    fi
    
    log_message "Starting cleanup of database backups older than ${DB_RETENTION_DAYS} days"
    
    # Find backup files older than DB_RETENTION_DAYS
    local files_to_delete
    files_to_delete=$(find "${DATABASE_BACKUP_DIR}" -type f \( -name "*.sql.gz" -o -name "*.dump" -o -name "*.backup" \) -mtime +"${DB_RETENTION_DAYS}" 2>/dev/null)
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No database backup files found to clean up"
        return 0
    fi
    
    log_message "Found ${file_count} database backup files to remove"
    
    # Remove old backup files
    echo "${files_to_delete}" | xargs -r rm -f
    
    if [[ $? -ne 0 ]]; then
        log_message "ERROR: Failed to remove old database backup files"
        return 1
    fi
    
    log_message "Successfully removed ${file_count} old database backup files"
    return 0
}

# Function to remove vector index backup files older than retention period from local storage
cleanup_local_vector_backups() {
    if [[ ! -d "${VECTOR_BACKUP_DIR}" ]]; then
        log_message "WARNING: Vector backup directory ${VECTOR_BACKUP_DIR} does not exist"
        return 0
    fi
    
    log_message "Starting cleanup of vector backups older than ${VECTOR_RETENTION_DAYS} days"
    
    # Find backup files older than VECTOR_RETENTION_DAYS
    local files_to_delete
    files_to_delete=$(find "${VECTOR_BACKUP_DIR}" -type f \( -name "*.index" -o -name "*.faiss" -o -name "*.bin" \) -mtime +"${VECTOR_RETENTION_DAYS}" 2>/dev/null)
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No vector backup files found to clean up"
        return 0
    fi
    
    log_message "Found ${file_count} vector backup files to remove"
    
    # Remove old backup files
    echo "${files_to_delete}" | xargs -r rm -f
    
    if [[ $? -ne 0 ]]; then
        log_message "ERROR: Failed to remove old vector backup files"
        return 1
    fi
    
    log_message "Successfully removed ${file_count} old vector backup files"
    return 0
}

# Function to remove WAL archive files older than retention period from local storage
cleanup_local_wal_archives() {
    if [[ ! -d "${WAL_ARCHIVE_DIR}" ]]; then
        log_message "WARNING: WAL archive directory ${WAL_ARCHIVE_DIR} does not exist"
        return 0
    fi
    
    log_message "Starting cleanup of WAL archives older than ${WAL_RETENTION_DAYS} days"
    
    # Find WAL files older than WAL_RETENTION_DAYS
    local files_to_delete
    files_to_delete=$(find "${WAL_ARCHIVE_DIR}" -type f \( -name "*.wal" -o -name "*.archive" \) -mtime +"${WAL_RETENTION_DAYS}" 2>/dev/null)
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No WAL archive files found to clean up"
        return 0
    fi
    
    log_message "Found ${file_count} WAL archive files to remove"
    
    # Remove old WAL files
    echo "${files_to_delete}" | xargs -r rm -f
    
    if [[ $? -ne 0 ]]; then
        log_message "ERROR: Failed to remove old WAL archive files"
        return 1
    fi
    
    log_message "Successfully removed ${file_count} old WAL archive files"
    return 0
}

# Function to remove database backup files older than retention period from S3 bucket
cleanup_s3_database_backups() {
    if [[ "${ENABLE_S3_CLEANUP}" != "true" ]]; then
        return 0
    fi
    
    log_message "Starting cleanup of database backups in S3 bucket ${S3_BUCKET} older than ${DB_RETENTION_DAYS} days"
    
    local cutoff_date
    cutoff_date=$(date -d "-${DB_RETENTION_DAYS} days" +%Y-%m-%d)
    
    # List database backup files in S3 bucket
    local files_to_delete
    files_to_delete=$(aws s3 ls "s3://${S3_BUCKET}/database/" --recursive | awk -v date="${cutoff_date}" '$1 < date {print $4}')
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No database backup files found to clean up in S3"
        return 0
    fi
    
    log_message "Found ${file_count} database backup files to remove from S3"
    
    # Remove old backup files from S3 bucket
    local exit_status=0
    while IFS= read -r file; do
        if [[ -n "${file}" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/${file}"
            if [[ $? -ne 0 ]]; then
                log_message "ERROR: Failed to remove S3 object: ${file}"
                exit_status=1
            fi
        fi
    done <<< "${files_to_delete}"
    
    if [[ ${exit_status} -eq 0 ]]; then
        log_message "Successfully removed ${file_count} old database backup files from S3"
    else
        log_message "Encountered errors while removing database backup files from S3"
        return 1
    fi
    
    return 0
}

# Function to remove vector index backup files older than retention period from S3 bucket
cleanup_s3_vector_backups() {
    if [[ "${ENABLE_S3_CLEANUP}" != "true" ]]; then
        return 0
    fi
    
    log_message "Starting cleanup of vector backups in S3 bucket ${S3_BUCKET} older than ${VECTOR_RETENTION_DAYS} days"
    
    local cutoff_date
    cutoff_date=$(date -d "-${VECTOR_RETENTION_DAYS} days" +%Y-%m-%d)
    
    # List vector backup files in S3 bucket
    local files_to_delete
    files_to_delete=$(aws s3 ls "s3://${S3_BUCKET}/vector/" --recursive | awk -v date="${cutoff_date}" '$1 < date {print $4}')
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No vector backup files found to clean up in S3"
        return 0
    fi
    
    log_message "Found ${file_count} vector backup files to remove from S3"
    
    # Remove old backup files from S3 bucket
    local exit_status=0
    while IFS= read -r file; do
        if [[ -n "${file}" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/${file}"
            if [[ $? -ne 0 ]]; then
                log_message "ERROR: Failed to remove S3 object: ${file}"
                exit_status=1
            fi
        fi
    done <<< "${files_to_delete}"
    
    if [[ ${exit_status} -eq 0 ]]; then
        log_message "Successfully removed ${file_count} old vector backup files from S3"
    else
        log_message "Encountered errors while removing vector backup files from S3"
        return 1
    fi
    
    return 0
}

# Function to remove WAL archive files older than retention period from S3 bucket
cleanup_s3_wal_archives() {
    if [[ "${ENABLE_S3_CLEANUP}" != "true" ]]; then
        return 0
    fi
    
    log_message "Starting cleanup of WAL archives in S3 bucket ${S3_BUCKET} older than ${WAL_RETENTION_DAYS} days"
    
    local cutoff_date
    cutoff_date=$(date -d "-${WAL_RETENTION_DAYS} days" +%Y-%m-%d)
    
    # List WAL archive files in S3 bucket
    local files_to_delete
    files_to_delete=$(aws s3 ls "s3://${S3_BUCKET}/wal/" --recursive | awk -v date="${cutoff_date}" '$1 < date {print $4}')
    
    # Count number of files to be removed
    local file_count
    file_count=$(echo "${files_to_delete}" | grep -v '^$' | wc -l)
    
    if [[ ${file_count} -eq 0 ]]; then
        log_message "No WAL archive files found to clean up in S3"
        return 0
    fi
    
    log_message "Found ${file_count} WAL archive files to remove from S3"
    
    # Remove old WAL files from S3 bucket
    local exit_status=0
    while IFS= read -r file; do
        if [[ -n "${file}" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/${file}"
            if [[ $? -ne 0 ]]; then
                log_message "ERROR: Failed to remove S3 object: ${file}"
                exit_status=1
            fi
        fi
    done <<< "${files_to_delete}"
    
    if [[ ${exit_status} -eq 0 ]]; then
        log_message "Successfully removed ${file_count} old WAL archive files from S3"
    else
        log_message "Encountered errors while removing WAL archive files from S3"
        return 1
    fi
    
    return 0
}

# Function to send notification about cleanup status
send_notification() {
    local status="$1"
    local message="$2"
    
    # Check if notifications are enabled in config
    if [[ "${ENABLE_NOTIFICATIONS:-false}" != "true" ]]; then
        return 0
    fi
    
    log_message "Sending notification: ${status} - ${message}"
    
    # Check notification method from config
    case "${NOTIFICATION_METHOD:-email}" in
        email)
            if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
                echo "${message}" | mail -s "Backup Cleanup ${status}" "${NOTIFICATION_EMAIL}"
                if [[ $? -ne 0 ]]; then
                    log_message "ERROR: Failed to send email notification"
                    return 1
                fi
            else
                log_message "WARNING: Email notification enabled but NOTIFICATION_EMAIL not set"
                return 1
            fi
            ;;
        slack)
            if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
                local payload
                payload=$(printf '{"text": "Backup Cleanup %s: %s"}' "${status}" "${message}")
                curl -s -X POST -H 'Content-type: application/json' --data "${payload}" "${SLACK_WEBHOOK_URL}"
                if [[ $? -ne 0 ]]; then
                    log_message "ERROR: Failed to send Slack notification"
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

# Main function that orchestrates the backup cleanup process
main() {
    local exit_status=0
    local error_count=0
    local start_time
    local end_time
    local elapsed_time
    
    start_time=$(date +%s)
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -d|--db-retention)
                DB_RETENTION_DAYS="$2"
                shift 2
                ;;
            -v|--vector-retention)
                VECTOR_RETENTION_DAYS="$2"
                shift 2
                ;;
            -w|--wal-retention)
                WAL_RETENTION_DAYS="$2"
                shift 2
                ;;
            -s|--s3-cleanup)
                ENABLE_S3_CLEANUP="true"
                shift
                ;;
            --verbose)
                VERBOSE="true"
                shift
                ;;
            -h|--help)
                echo "Script for cleaning up old backup files based on retention policies"
                echo
                echo "Usage: cleanup-old-backups.sh [options]"
                echo "  Options:"
                echo "    -c, --config CONFIG_FILE   Specify config file (default: /etc/document-management/backup.conf)"
                echo "    -d, --db-retention DAYS    Override database backup retention period (default: 30 days)"
                echo "    -v, --vector-retention DAYS Override vector index backup retention period (default: 14 days)"
                echo "    -w, --wal-retention DAYS   Override WAL archive retention period (default: 7 days)"
                echo "    -s, --s3-cleanup           Clean up backups in S3 bucket"
                echo "    --verbose                  Enable verbose output"
                echo "    -h, --help                 Show this help message"
                echo
                echo "Exit codes:"
                echo "  0  Success"
                echo "  1  Configuration error"
                echo "  2  Dependency error"
                echo "  3  Filesystem error"
                echo "  4  S3 operation error"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Run 'cleanup-old-backups.sh --help' for usage information"
                exit 1
                ;;
        esac
    done
    
    # Create log directory
    create_log_directory
    if [[ $? -ne 0 ]]; then
        echo "Failed to create log directory. Exiting."
        exit 3
    fi
    
    # Log script start with timestamp
    log_message "Starting backup cleanup script"
    
    # Load configuration from config file
    load_config
    if [[ $? -ne 0 ]]; then
        log_message "Failed to load configuration. Exiting."
        send_notification "FAILED" "Failed to load configuration"
        exit 1
    fi
    
    # Check dependencies
    check_dependencies
    if [[ $? -ne 0 ]]; then
        log_message "Missing dependencies. Exiting."
        send_notification "FAILED" "Missing required dependencies"
        exit 2
    fi
    
    # Cleanup local backups
    cleanup_local_database_backups
    if [[ $? -ne 0 ]]; then
        log_message "Error cleaning up local database backups"
        exit_status=3
        ((error_count++))
    fi
    
    cleanup_local_vector_backups
    if [[ $? -ne 0 ]]; then
        log_message "Error cleaning up local vector backups"
        exit_status=3
        ((error_count++))
    fi
    
    cleanup_local_wal_archives
    if [[ $? -ne 0 ]]; then
        log_message "Error cleaning up local WAL archives"
        exit_status=3
        ((error_count++))
    fi
    
    # If S3 enabled, cleanup S3 backups
    if [[ "${ENABLE_S3_CLEANUP}" == "true" ]]; then
        cleanup_s3_database_backups
        if [[ $? -ne 0 ]]; then
            log_message "Error cleaning up S3 database backups"
            exit_status=4
            ((error_count++))
        fi
        
        cleanup_s3_vector_backups
        if [[ $? -ne 0 ]]; then
            log_message "Error cleaning up S3 vector backups"
            exit_status=4
            ((error_count++))
        fi
        
        cleanup_s3_wal_archives
        if [[ $? -ne 0 ]]; then
            log_message "Error cleaning up S3 WAL archives"
            exit_status=4
            ((error_count++))
        fi
    fi
    
    # Calculate elapsed time
    end_time=$(date +%s)
    elapsed_time=$((end_time - start_time))
    
    # Log summary of cleanup operations
    if [[ ${exit_status} -eq 0 ]]; then
        log_message "Backup cleanup completed successfully in ${elapsed_time} seconds"
        send_notification "SUCCESS" "Backup cleanup completed successfully in ${elapsed_time} seconds"
    else
        log_message "Backup cleanup completed with ${error_count} errors in ${elapsed_time} seconds"
        send_notification "ERROR" "Backup cleanup completed with ${error_count} errors in ${elapsed_time} seconds"
    fi
    
    return ${exit_status}
}

# Execute main function
main "$@"
exit $?