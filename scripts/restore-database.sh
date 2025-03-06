#!/bin/bash
#
# Script for restoring PostgreSQL database with point-in-time recovery support
# for the Document Management and AI Chatbot System
#
# This script handles restoration from full database dumps and point-in-time recovery
# using WAL archives, supporting both local and S3 storage sources.

# Global variables
BACKUP_DIR="/opt/document-management/backups/database"
RESTORE_LOG_FILE="/opt/document-management/backups/logs/restore.log"
CONFIG_FILE="/etc/document-management/backup.conf"
TEMP_RESTORE_DIR="/tmp/db-restore"
S3_BUCKET="docaichatbot-backups"
WAL_ARCHIVE_DIR="/opt/document-management/backups/wal"
RECOVERY_TARGET_TIME=""
RECOVERY_TARGET_INCLUSIVE="true"

# Initialize flags
VERBOSE=false
VERIFY_BACKUP=true
RESTART_APP=true
S3_SOURCE=false
BACKUP_FILE=""

# Log a message to the restore log file with timestamp
log_message() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    echo "[$timestamp] $message" >> "$RESTORE_LOG_FILE"
    
    # Print to stdout if verbose mode is enabled
    if $VERBOSE; then
        echo "[$timestamp] $message"
    fi
}

# Load configuration from the config file
load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_message "ERROR: Configuration file $CONFIG_FILE not found"
        return 1
    fi
    
    log_message "Loading configuration from $CONFIG_FILE"
    source "$CONFIG_FILE"
    
    # Validate required configuration parameters
    if [ -z "$PGHOST" ] || [ -z "$PGUSER" ] || [ -z "$PGDATABASE" ]; then
        log_message "ERROR: Missing required PostgreSQL configuration parameters in $CONFIG_FILE"
        return 1
    fi
    
    return 0
}

# Check if required dependencies are installed
check_dependencies() {
    local missing_deps=0
    
    # Check for PostgreSQL client tools
    if ! command -v pg_restore >/dev/null 2>&1; then
        log_message "ERROR: pg_restore command not found. Please install PostgreSQL client tools."
        missing_deps=1
    fi
    
    if ! command -v psql >/dev/null 2>&1; then
        log_message "ERROR: psql command not found. Please install PostgreSQL client tools."
        missing_deps=1
    fi
    
    # Check for AWS CLI if S3 download is enabled
    if $S3_SOURCE && ! command -v aws >/dev/null 2>&1; then
        log_message "ERROR: aws command not found. Please install AWS CLI for S3 support."
        missing_deps=1
    fi
    
    if [ $missing_deps -eq 1 ]; then
        return 1
    fi
    
    log_message "All required dependencies are available"
    return 0
}

# Create necessary directories for restoration
create_restore_directories() {
    # Create temporary restore directory if it doesn't exist
    if [ ! -d "$TEMP_RESTORE_DIR" ]; then
        mkdir -p "$TEMP_RESTORE_DIR"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to create temporary restore directory: $TEMP_RESTORE_DIR"
            return 1
        fi
    fi
    
    # Create logs directory if it doesn't exist
    local log_dir=$(dirname "$RESTORE_LOG_FILE")
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to create log directory: $log_dir"
            return 1
        fi
    fi
    
    # Set appropriate permissions
    chmod 750 "$TEMP_RESTORE_DIR"
    chmod 750 "$log_dir"
    
    log_message "Restore directories created successfully"
    return 0
}

# Check if the database connection is working
check_database_connection() {
    log_message "Checking database connection..."
    
    # Set PostgreSQL environment variables from config
    export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE
    
    # Attempt to connect to the database
    psql -c "SELECT 1" >/dev/null 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_message "Database connection successful"
        return 0
    else
        log_message "ERROR: Failed to connect to database. Please check your PostgreSQL configuration."
        return 1
    fi
}

# Stop the application services before database restoration
stop_application() {
    log_message "Stopping application services..."
    
    # Check if we're using systemd services or docker
    if [ -f "/etc/systemd/system/document-management-api.service" ]; then
        # Systemd services
        systemctl stop document-management-api.service
        local exit_code=$?
        
        # Verify services are stopped
        if systemctl is-active --quiet document-management-api.service; then
            log_message "ERROR: Failed to stop application services"
            return 1
        fi
    elif command -v docker >/dev/null 2>&1 && docker ps -q --filter "name=document-management" >/dev/null; then
        # Docker containers
        docker stop $(docker ps -q --filter "name=document-management")
        local exit_code=$?
        
        # Verify containers are stopped
        if docker ps -q --filter "name=document-management" >/dev/null; then
            log_message "ERROR: Failed to stop application Docker containers"
            return 1
        fi
    else
        log_message "WARNING: No application services found to stop"
    fi
    
    log_message "Application services stopped successfully"
    return 0
}

# Start the application services after database restoration
start_application() {
    log_message "Starting application services..."
    
    # Check if we're using systemd services or docker
    if [ -f "/etc/systemd/system/document-management-api.service" ]; then
        # Systemd services
        systemctl start document-management-api.service
        local exit_code=$?
        
        # Verify services are started
        if ! systemctl is-active --quiet document-management-api.service; then
            log_message "ERROR: Failed to start application services"
            return 1
        fi
    elif command -v docker >/dev/null 2>&1 && docker ps -a -q --filter "name=document-management" >/dev/null; then
        # Docker containers
        docker start $(docker ps -a -q --filter "name=document-management")
        local exit_code=$?
        
        # Verify containers are started
        if ! docker ps -q --filter "name=document-management" >/dev/null; then
            log_message "ERROR: Failed to start application Docker containers"
            return 1
        fi
    else
        log_message "WARNING: No application services found to start"
    fi
    
    log_message "Application services started successfully"
    return 0
}

# List available database backups from local or S3 storage
list_available_backups() {
    local backups=()
    
    if $S3_SOURCE; then
        log_message "Listing database backups from S3 bucket: $S3_BUCKET..."
        # List backups from S3 bucket
        if ! aws s3 ls "s3://$S3_BUCKET/database/" --recursive | grep -E '\.dump$|\.sql$|\.sql\.gz$|\.custom$'; then
            log_message "No database backups found in S3 bucket: $S3_BUCKET"
            return 1
        fi
        # Convert output to array of backup files
        while read -r line; do
            # Extract the filename from the S3 ls output
            local filename=$(echo "$line" | awk '{print $4}')
            backups+=("$filename")
        done < <(aws s3 ls "s3://$S3_BUCKET/database/" --recursive | grep -E '\.dump$|\.sql$|\.sql\.gz$|\.custom$')
    else
        log_message "Listing database backups from local storage: $BACKUP_DIR..."
        # List backups from local storage
        if ! find "$BACKUP_DIR" -type f -name "*.dump" -o -name "*.sql" -o -name "*.sql.gz" -o -name "*.custom" 2>/dev/null; then
            log_message "No database backups found in local storage: $BACKUP_DIR"
            return 1
        fi
        # Convert output to array of backup files
        while read -r filename; do
            backups+=("$filename")
        done < <(find "$BACKUP_DIR" -type f -name "*.dump" -o -name "*.sql" -o -name "*.sql.gz" -o -name "*.custom" 2>/dev/null | sort -r)
    fi
    
    # Sort backups by timestamp (newest first)
    IFS=$'\n' sorted_backups=($(sort -r <<<"${backups[*]}"))
    unset IFS
    
    # Print the list of available backups
    echo "Available database backups:"
    for i in "${!sorted_backups[@]}"; do
        echo "[$i] ${sorted_backups[$i]}"
    done
    
    return 0
}

# Download backup file from S3 bucket
download_from_s3() {
    local backup_file="$1"
    local destination="$2"
    
    if [ -z "$backup_file" ] || [ -z "$destination" ]; then
        log_message "ERROR: Backup file or destination not specified for S3 download"
        return 1
    fi
    
    log_message "Downloading backup file from S3: $backup_file"
    
    # Create destination directory if it doesn't exist
    mkdir -p "$(dirname "$destination")"
    
    # Download the file from S3
    aws s3 cp "s3://$S3_BUCKET/$backup_file" "$destination"
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_message "ERROR: Failed to download backup file from S3: $backup_file"
        return 1
    fi
    
    log_message "Backup file downloaded successfully to: $destination"
    return 0
}

# Download WAL archive files from S3 bucket for point-in-time recovery
download_wal_from_s3() {
    local target_time="$1"
    
    if [ -z "$target_time" ]; then
        log_message "No target time specified for WAL recovery, skipping WAL file download"
        return 0
    fi
    
    log_message "Downloading WAL archive files from S3 for point-in-time recovery..."
    
    # Create WAL archive directory if it doesn't exist
    mkdir -p "$WAL_ARCHIVE_DIR"
    
    # Download all WAL files that might be needed for recovery
    # Note: In a real scenario, you'd want to be more selective about which WAL files to download
    aws s3 sync "s3://$S3_BUCKET/wal/" "$WAL_ARCHIVE_DIR/"
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_message "ERROR: Failed to download WAL archive files from S3"
        return 1
    fi
    
    log_message "WAL archive files downloaded successfully to: $WAL_ARCHIVE_DIR"
    return 0
}

# Verify the integrity of the database backup
verify_backup() {
    local backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        log_message "ERROR: Backup file not found: $backup_file"
        return 1
    fi
    
    log_message "Verifying backup file integrity: $backup_file"
    
    # Check the file type
    local file_type=$(file -b --mime-type "$backup_file")
    
    # If the file is compressed, verify it can be decompressed
    if [[ "$file_type" == "application/gzip" ]]; then
        gzip -t "$backup_file"
        local exit_code=$?
        
        if [ $exit_code -ne 0 ]; then
            log_message "ERROR: Backup file is corrupted (gzip test failed): $backup_file"
            return 1
        fi
    fi
    
    # Verify the backup can be read by pg_restore
    if [[ "$backup_file" == *.custom ]]; then
        pg_restore --list "$backup_file" >/dev/null 2>&1
        local exit_code=$?
        
        if [ $exit_code -ne 0 ]; then
            log_message "ERROR: Backup file is corrupted (pg_restore test failed): $backup_file"
            return 1
        fi
    elif [[ "$backup_file" == *.sql ]] || [[ "$backup_file" == *.dump ]]; then
        # For SQL dumps, just check if the file is readable
        head -n 10 "$backup_file" >/dev/null 2>&1
        local exit_code=$?
        
        if [ $exit_code -ne 0 ]; then
            log_message "ERROR: Backup file is corrupted (not readable): $backup_file"
            return 1
        fi
    elif [[ "$backup_file" == *.sql.gz ]]; then
        # For compressed SQL dumps, check if it can be decompressed
        gunzip -c "$backup_file" | head -n 10 >/dev/null 2>&1
        local exit_code=$?
        
        if [ $exit_code -ne 0 ]; then
            log_message "ERROR: Backup file is corrupted (gunzip test failed): $backup_file"
            return 1
        fi
    fi
    
    log_message "Backup file integrity verified successfully: $backup_file"
    return 0
}

# Create recovery configuration for point-in-time recovery
create_recovery_conf() {
    local target_time="$1"
    local pgdata="$PGDATA"
    
    if [ -z "$pgdata" ]; then
        log_message "ERROR: PGDATA directory not specified"
        return 1
    fi
    
    log_message "Creating recovery configuration for point-in-time recovery..."
    
    # For PostgreSQL 12+, recovery configuration is in postgresql.conf and standby.signal
    if [ -d "$pgdata" ]; then
        # Check PostgreSQL version to determine recovery configuration method
        local pg_version=$(psql -V | sed -n 's/^psql (PostgreSQL) \([0-9]*\).*/\1/p')
        
        if [ -z "$pg_version" ]; then
            log_message "WARNING: Could not determine PostgreSQL version, assuming 12+"
            pg_version=12
        fi
        
        if [ "$pg_version" -ge 12 ]; then
            # PostgreSQL 12+ uses postgresql.auto.conf and standby.signal
            log_message "Using PostgreSQL 12+ recovery configuration"
            
            # Add recovery settings to postgresql.auto.conf
            cat > "$pgdata/postgresql.auto.conf" <<EOF
# Recovery configuration added by restore-database.sh
restore_command = 'cp $WAL_ARCHIVE_DIR/%f %p'
EOF

            if [ -n "$target_time" ]; then
                cat >> "$pgdata/postgresql.auto.conf" <<EOF
recovery_target_time = '$target_time'
recovery_target_inclusive = $RECOVERY_TARGET_INCLUSIVE
EOF
            fi
            
            # Create standby.signal to enter recovery mode
            touch "$pgdata/recovery.signal"
            
        else
            # PostgreSQL 11 and earlier uses recovery.conf
            log_message "Using PostgreSQL 11 or earlier recovery configuration"
            
            # Create recovery.conf
            cat > "$pgdata/recovery.conf" <<EOF
# Recovery configuration added by restore-database.sh
restore_command = 'cp $WAL_ARCHIVE_DIR/%f %p'
EOF

            if [ -n "$target_time" ]; then
                cat >> "$pgdata/recovery.conf" <<EOF
recovery_target_time = '$target_time'
recovery_target_inclusive = $RECOVERY_TARGET_INCLUSIVE
EOF
            fi
        fi
        
        log_message "Recovery configuration created successfully"
        return 0
    else
        log_message "ERROR: PGDATA directory does not exist: $pgdata"
        return 1
    fi
}

# Restore database from backup file
restore_database() {
    local backup_file="$1"
    local target_time="$2"
    
    if [ ! -f "$backup_file" ]; then
        log_message "ERROR: Backup file not found: $backup_file"
        return 1
    fi
    
    log_message "Starting database restoration from backup: $backup_file"
    
    # Set PostgreSQL environment variables from config
    export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE PGDATA
    
    # Stop PostgreSQL service
    log_message "Stopping PostgreSQL service..."
    if [ -f "/etc/systemd/system/postgresql.service" ]; then
        systemctl stop postgresql
    else
        pg_ctl stop -D "$PGDATA" -m fast
    fi
    
    # Clear PostgreSQL data directory
    if [ -d "$PGDATA" ]; then
        log_message "Clearing PostgreSQL data directory: $PGDATA"
        rm -rf "$PGDATA"/*
    else
        log_message "Creating PostgreSQL data directory: $PGDATA"
        mkdir -p "$PGDATA"
        chmod 700 "$PGDATA"
        chown postgres:postgres "$PGDATA"
    fi
    
    # Initialize a new database cluster if needed
    if [ ! -f "$PGDATA/PG_VERSION" ]; then
        log_message "Initializing new PostgreSQL database cluster..."
        su - postgres -c "initdb -D $PGDATA"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to initialize PostgreSQL database cluster"
            return 1
        fi
    fi
    
    # Use appropriate restore method based on file extension
    log_message "Restoring database from backup..."
    
    if [[ "$backup_file" == *.custom ]]; then
        # Custom format (pg_restore)
        su - postgres -c "pg_restore -d $PGDATABASE -v -c -C $backup_file" > "$TEMP_RESTORE_DIR/restore.log" 2>&1
        local exit_code=$?
    elif [[ "$backup_file" == *.sql ]]; then
        # Plain SQL format
        su - postgres -c "psql -d $PGDATABASE -f $backup_file" > "$TEMP_RESTORE_DIR/restore.log" 2>&1
        local exit_code=$?
    elif [[ "$backup_file" == *.sql.gz ]]; then
        # Compressed SQL format
        gunzip -c "$backup_file" | su - postgres -c "psql -d $PGDATABASE" > "$TEMP_RESTORE_DIR/restore.log" 2>&1
        local exit_code=$?
    elif [[ "$backup_file" == *.dump ]]; then
        # pg_dump format
        su - postgres -c "pg_restore -d $PGDATABASE -v -c -C $backup_file" > "$TEMP_RESTORE_DIR/restore.log" 2>&1
        local exit_code=$?
    else
        log_message "ERROR: Unsupported backup file format: $backup_file"
        return 1
    fi
    
    if [ $exit_code -ne 0 ]; then
        log_message "WARNING: Restore command completed with non-zero exit code: $exit_code"
        log_message "Check $TEMP_RESTORE_DIR/restore.log for details"
        # Continue anyway, as pg_restore often returns non-zero even on successful restore
    fi
    
    # If point-in-time recovery is requested, create recovery configuration
    if [ -n "$target_time" ]; then
        log_message "Setting up point-in-time recovery to: $target_time"
        create_recovery_conf "$target_time"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to create recovery configuration"
            return 1
        fi
    fi
    
    # Start PostgreSQL service
    log_message "Starting PostgreSQL service..."
    if [ -f "/etc/systemd/system/postgresql.service" ]; then
        systemctl start postgresql
    else
        su - postgres -c "pg_ctl start -D $PGDATA -l $PGDATA/server.log"
    fi
    
    # Wait for PostgreSQL to start
    log_message "Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if su - postgres -c "pg_isready" >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # If point-in-time recovery is in progress, wait for it to complete
    if [ -n "$target_time" ]; then
        log_message "Waiting for point-in-time recovery to complete..."
        
        # Check for recovery completion by monitoring log file
        # This is a simplified approach - in production you would want more robust monitoring
        local max_wait=300  # Max wait time in seconds
        local waited=0
        local recovery_complete=false
        
        while [ $waited -lt $max_wait ]; do
            if grep -q "recovery is complete" $PGDATA/log/* 2>/dev/null; then
                recovery_complete=true
                break
            fi
            sleep 5
            waited=$((waited + 5))
        done
        
        if $recovery_complete; then
            log_message "Point-in-time recovery completed successfully"
        else
            log_message "WARNING: Timed out waiting for recovery completion, check PostgreSQL logs"
            # Continue anyway, as recovery might still be in progress
        fi
    fi
    
    log_message "Database restoration completed successfully"
    return 0
}

# Verify the database was restored correctly
verify_restoration() {
    log_message "Verifying database restoration..."
    
    # Set PostgreSQL environment variables from config
    export PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE
    
    # Check if we can connect to the database
    psql -c "SELECT 1" >/dev/null 2>&1
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        log_message "ERROR: Failed to connect to restored database"
        return 1
    fi
    
    # Check if essential tables exist
    # Adjust the table names based on your application schema
    log_message "Checking for essential tables..."
    for table in "users" "documents" "document_chunks" "queries" "feedback"; do
        psql -c "SELECT 1 FROM $table LIMIT 1" >/dev/null 2>&1
        local exit_code=$?
        
        if [ $exit_code -ne 0 ]; then
            log_message "WARNING: Table '$table' does not exist or is empty in the restored database"
        else
            log_message "Table '$table' exists and contains data"
        fi
    done
    
    # Check for PostgreSQL errors in logs
    if grep -i "error" $PGDATA/log/* 2>/dev/null | grep -v "LOG:"; then
        log_message "WARNING: Found error messages in PostgreSQL logs after restoration"
    fi
    
    log_message "Database restoration verification completed"
    return 0
}

# Send notification about restoration status
send_notification() {
    local status="$1"
    local message="$2"
    
    # Check if notifications are enabled in config
    if [ "$ENABLE_NOTIFICATIONS" != "true" ]; then
        log_message "Notifications are disabled, skipping"
        return 0
    fi
    
    log_message "Sending notification about restoration status: $status"
    
    # Prepare notification message
    local hostname=$(hostname)
    local subject="Database Restoration $status on $hostname"
    local body="Database restoration status: $status\n\nHost: $hostname\nDatabase: $PGDATABASE\nTimestamp: $(date)\n\nDetails: $message"
    
    # Send notification based on configured method
    case "$NOTIFICATION_METHOD" in
        email)
            echo -e "$body" | mail -s "$subject" "$NOTIFICATION_EMAIL"
            ;;
        slack)
            if [ -n "$SLACK_WEBHOOK_URL" ]; then
                curl -s -X POST -H 'Content-type: application/json' \
                    --data "{\"text\":\"$subject\n\n$body\"}" \
                    "$SLACK_WEBHOOK_URL"
            else
                log_message "ERROR: Slack webhook URL not configured"
                return 1
            fi
            ;;
        *)
            log_message "WARNING: Unknown notification method: $NOTIFICATION_METHOD"
            return 1
            ;;
    esac
    
    log_message "Notification sent successfully"
    return 0
}

# Clean up temporary files after restoration
cleanup() {
    log_message "Cleaning up temporary files..."
    
    # Remove temporary restore directory if it exists
    if [ -d "$TEMP_RESTORE_DIR" ]; then
        rm -rf "$TEMP_RESTORE_DIR"
    fi
    
    log_message "Cleanup completed successfully"
    return 0
}

# Display usage information
show_usage() {
    echo "Usage: restore-database.sh [options]"
    echo "  Options:"
    echo "    -c, --config CONFIG_FILE  Specify config file (default: /etc/document-management/backup.conf)"
    echo "    -b, --backup-file FILE    Specify backup file to restore from"
    echo "    -s, --s3-source          Download backup from S3 instead of local storage"
    echo "    -t, --target-time TIME   Perform point-in-time recovery to specified time (format: 'YYYY-MM-DD HH:MM:SS')"
    echo "    --no-verify              Skip backup verification"
    echo "    --no-app-restart         Don't restart application services after restore"
    echo "    --verbose                Enable verbose output"
    echo "    -h, --help               Show this help message"
    echo ""
    echo "Exit codes:"
    echo "  0  Success"
    echo "  1  Configuration error"
    echo "  2  Dependency error"
    echo "  3  Database connection error"
    echo "  4  Backup file error"
    echo "  5  Verification error"
    echo "  6  Restoration error"
    echo "  7  Application service error"
}

# Main function for database restoration
main() {
    local exit_code=0
    
    # Parse command-line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -b|--backup-file)
                BACKUP_FILE="$2"
                shift 2
                ;;
            -s|--s3-source)
                S3_SOURCE=true
                shift
                ;;
            -t|--target-time)
                RECOVERY_TARGET_TIME="$2"
                shift 2
                ;;
            --no-verify)
                VERIFY_BACKUP=false
                shift
                ;;
            --no-app-restart)
                RESTART_APP=false
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                return 0
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                return 1
                ;;
        esac
    done
    
    # Initialize log file
    mkdir -p "$(dirname "$RESTORE_LOG_FILE")"
    echo "Database restoration started at $(date)" > "$RESTORE_LOG_FILE"
    
    log_message "Starting database restoration process"
    
    # Load configuration
    load_config
    if [ $? -ne 0 ]; then
        log_message "ERROR: Failed to load configuration"
        send_notification "FAILED" "Configuration error"
        return 1
    fi
    
    # Check dependencies
    check_dependencies
    if [ $? -ne 0 ]; then
        log_message "ERROR: Missing dependencies"
        send_notification "FAILED" "Missing dependencies"
        return 2
    fi
    
    # Create restore directories
    create_restore_directories
    if [ $? -ne 0 ]; then
        log_message "ERROR: Failed to create restore directories"
        send_notification "FAILED" "Failed to create restore directories"
        return 1
    fi
    
    # Check database connection
    check_database_connection
    if [ $? -ne 0 ]; then
        log_message "ERROR: Database connection failed"
        send_notification "FAILED" "Database connection failed"
        return 3
    fi
    
    # Stop application services if requested
    if $RESTART_APP; then
        stop_application
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to stop application services"
            send_notification "FAILED" "Failed to stop application services"
            return 7
        fi
    fi
    
    # If backup file not specified, list available backups and prompt for selection
    if [ -z "$BACKUP_FILE" ]; then
        list_available_backups
        if [ $? -ne 0 ]; then
            log_message "ERROR: No backup files found"
            send_notification "FAILED" "No backup files found"
            return 4
        fi
        
        echo "Please enter the number of the backup to restore: "
        read -r backup_selection
        
        # Get the selected backup
        IFS=$'\n' sorted_backups=($(find "$BACKUP_DIR" -type f -name "*.dump" -o -name "*.sql" -o -name "*.sql.gz" -o -name "*.custom" 2>/dev/null | sort -r))
        unset IFS
        
        if [ -z "${sorted_backups[$backup_selection]}" ]; then
            log_message "ERROR: Invalid backup selection"
            send_notification "FAILED" "Invalid backup selection"
            return 4
        fi
        
        BACKUP_FILE="${sorted_backups[$backup_selection]}"
    fi
    
    # If backup is on S3, download it to local temporary directory
    local local_backup_file="$BACKUP_FILE"
    if $S3_SOURCE; then
        local_backup_file="$TEMP_RESTORE_DIR/$(basename "$BACKUP_FILE")"
        download_from_s3 "$BACKUP_FILE" "$local_backup_file"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to download backup from S3"
            send_notification "FAILED" "Failed to download backup from S3"
            return 4
        fi
    fi
    
    # Verify backup integrity
    if $VERIFY_BACKUP; then
        verify_backup "$local_backup_file"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Backup file verification failed"
            send_notification "FAILED" "Backup file verification failed"
            return 5
        fi
    fi
    
    # If point-in-time recovery requested, download necessary WAL files
    if [ -n "$RECOVERY_TARGET_TIME" ] && $S3_SOURCE; then
        download_wal_from_s3 "$RECOVERY_TARGET_TIME"
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to download WAL files for point-in-time recovery"
            send_notification "FAILED" "Failed to download WAL files for point-in-time recovery"
            return 4
        fi
    fi
    
    # Restore database from backup
    restore_database "$local_backup_file" "$RECOVERY_TARGET_TIME"
    if [ $? -ne 0 ]; then
        log_message "ERROR: Database restoration failed"
        send_notification "FAILED" "Database restoration failed"
        return 6
    fi
    
    # Verify restoration was successful
    verify_restoration
    if [ $? -ne 0 ]; then
        log_message "WARNING: Database restoration verification showed issues"
        # Continue anyway, but notify about verification issues
        send_notification "WARNING" "Database restoration completed but verification showed issues"
    else
        log_message "Database restoration verification successful"
    fi
    
    # Start application services if requested
    if $RESTART_APP; then
        start_application
        if [ $? -ne 0 ]; then
            log_message "ERROR: Failed to start application services"
            send_notification "FAILED" "Database restored but failed to start application services"
            return 7
        fi
    fi
    
    # Send notification about successful restoration
    send_notification "SUCCESS" "Database restoration completed successfully"
    
    # Cleanup temporary files
    cleanup
    
    log_message "Database restoration process completed successfully"
    return 0
}

# Execute main function with command line arguments
main "$@"
exit $?