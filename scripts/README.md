# Utility Scripts

## Overview

This directory contains utility scripts for maintaining and operating the Document Management and AI Chatbot System. These scripts automate common tasks related to database management, deployment, monitoring, and system maintenance, reducing operational overhead and ensuring consistent execution of critical procedures.

The scripts are designed to be run from the command line and typically follow a consistent pattern for options and configuration. Most scripts support both command-line arguments and environment variables for configuration, with command-line options taking precedence.

## Script Categories

The utility scripts are organized into the following categories:

| Category | Purpose | Script Count |
|----------|---------|--------------|
| Database Management | PostgreSQL and FAISS vector database operations | 3 |
| Deployment | Environment-specific deployment procedures | 2 |
| Monitoring | System health and performance monitoring | 2 |
| Maintenance | Routine system maintenance tasks | 3 |

## Database Management Scripts

### backup-database.sh

**Description**: Performs automated backups of the PostgreSQL database with Write-Ahead Log (WAL) archiving support. The script creates consistent backups that can be used for point-in-time recovery.

**Usage**:
```bash
./backup-database.sh [options]

Options:
  -h, --host HOST        Database host (default: from .env)
  -p, --port PORT        Database port (default: 5432)
  -d, --database DB      Database name (default: docmanagement)
  -u, --user USER        Database user (default: from .env)
  -o, --output DIR       Backup output directory (default: ./backups)
  -w, --wal              Enable WAL archiving (default: disabled)
  -c, --compress         Compress backup (default: enabled)
  -r, --retention DAYS   Backup retention in days (default: 30)
  --help                 Show this help message
```

**Configuration**:
The script can be configured via environment variables defined in a `.env` file:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=docmanagement
DB_USER=postgres
DB_PASSWORD=secretpassword
BACKUP_DIR=/var/backups/postgres
WAL_ARCHIVE_DIR=/var/backups/postgres/wal
BACKUP_RETENTION_DAYS=30
```

**Examples**:
```bash
# Perform basic backup using settings from .env
./backup-database.sh

# Full backup with WAL archiving to a specific location
./backup-database.sh -w -o /mnt/backup-volume/postgres

# Backup with 60-day retention period
./backup-database.sh -r 60
```

### restore-database.sh

**Description**: Restores a PostgreSQL database from a backup, with support for point-in-time recovery using WAL archives.

**Usage**:
```bash
./restore-database.sh [options]

Options:
  -h, --host HOST        Database host (default: from .env)
  -p, --port PORT        Database port (default: 5432)
  -d, --database DB      Database name (default: docmanagement)
  -u, --user USER        Database user (default: from .env)
  -b, --backup FILE      Backup file to restore (required)
  -t, --timestamp TS     Point-in-time to recover to (format: YYYY-MM-DD HH:MM:SS)
  -w, --wal-dir DIR      WAL archive directory (required for point-in-time recovery)
  --drop-db              Drop the database if it exists
  --help                 Show this help message
```

**Configuration**:
Uses the same environment variables as backup-database.sh.

**Examples**:
```bash
# Restore from a specific backup file
./restore-database.sh -b /var/backups/postgres/docmanagement_2023-06-15_01-00-00.sql.gz

# Restore with point-in-time recovery
./restore-database.sh -b /var/backups/postgres/docmanagement_2023-06-15_01-00-00.sql.gz \
  -t "2023-06-15 13:30:00" -w /var/backups/postgres/wal

# Restore to a fresh database
./restore-database.sh -b /var/backups/postgres/docmanagement_2023-06-15_01-00-00.sql.gz --drop-db
```

### rebuild-vector-index.sh

**Description**: Rebuilds the FAISS vector index from document embeddings stored in the database. This is useful for repairing corrupted indices or updating to a new index format.

**Usage**:
```bash
./rebuild-vector-index.sh [options]

Options:
  -c, --config FILE      Configuration file (default: config/faiss.ini)
  -o, --output DIR       Output directory for the index (default: from config)
  -t, --type TYPE        Index type (flat, ivf, ivfpq) (default: from config)
  -b, --batch-size SIZE  Processing batch size (default: 10000)
  -v, --verbose          Enable verbose output
  --backup               Backup existing index before rebuilding
  --help                 Show this help message
```

**Configuration**:
Configuration is read from a faiss.ini file:

```ini
[index]
type = ivf
dimension = 768
nlist = 100
output_dir = /var/lib/faiss

[database]
host = localhost
port = 5432
name = docmanagement
user = postgres
password = secretpassword
```

**Examples**:
```bash
# Rebuild the index using default configuration
./rebuild-vector-index.sh

# Rebuild with a specific index type and larger batch size
./rebuild-vector-index.sh -t ivfpq -b 50000

# Rebuild with backup of the existing index
./rebuild-vector-index.sh --backup
```

## Deployment Scripts

### deploy-prod.sh

**Description**: Production deployment script implementing a blue/green deployment strategy. This script manages the deployment of the application to the production environment, including validation, traffic shifting, and rollback capabilities.

**Usage**:
```bash
./deploy-prod.sh [options]

Options:
  -v, --version VERSION   Version to deploy (required)
  -a, --approval TOKEN    Approval token for production deployment (required)
  -c, --config FILE       Deployment configuration file (default: config/deploy-prod.conf)
  --skip-tests            Skip pre-deployment tests (not recommended)
  --force                 Force deployment even if validation fails
  --rollback              Rollback to previous version
  --traffic PERCENTAGE    Initial traffic percentage (default: 10)
  --help                  Show this help message
```

**Configuration**:
Requires AWS configuration and the following environment variables:

```
AWS_PROFILE=production
AWS_REGION=us-west-2
ECS_CLUSTER=doc-management-prod
ECS_SERVICE=api-service
ECR_REPOSITORY=doc-management-api
ALB_TARGET_GROUP_BLUE=api-blue
ALB_TARGET_GROUP_GREEN=api-green
APPROVAL_TOKEN_HASH=hashed_approval_token
```

**Examples**:
```bash
# Deploy version 1.2.3 to production
./deploy-prod.sh -v 1.2.3 -a "approval-token-from-release-manager"

# Deploy with initial 25% traffic allocation
./deploy-prod.sh -v 1.2.3 -a "approval-token" --traffic 25

# Rollback to previous version
./deploy-prod.sh --rollback
```

### deploy-staging.sh

**Description**: Deploys the application to the staging environment for pre-production validation. This script is similar to deploy-prod.sh but with fewer safeguards and automatic test execution.

**Usage**:
```bash
./deploy-staging.sh [options]

Options:
  -v, --version VERSION   Version to deploy (required)
  -c, --config FILE       Deployment configuration file (default: config/deploy-staging.conf)
  --skip-tests            Skip post-deployment tests
  --force                 Force deployment even if validation fails
  --rollback              Rollback to previous version
  --help                  Show this help message
```

**Configuration**:
Uses AWS configuration similar to deploy-prod.sh but for the staging environment.

**Examples**:
```bash
# Deploy version 1.2.3 to staging
./deploy-staging.sh -v 1.2.3

# Deploy and skip automatic tests
./deploy-staging.sh -v 1.2.3 --skip-tests

# Rollback to previous version
./deploy-staging.sh --rollback
```

## Monitoring Scripts

### health-check.sh

**Description**: Performs health checks on various components of the system. This script is designed to be run periodically to verify system health and detect issues before they impact users.

**Usage**:
```bash
./health-check.sh [options]

Options:
  -c, --config FILE       Health check configuration file (default: config/health-check.conf)
  -e, --environment ENV   Environment to check (dev, staging, prod) (default: from .env)
  -o, --output FORMAT     Output format (text, json) (default: text)
  -t, --timeout SECONDS   Request timeout in seconds (default: 5)
  --components COMP       Comma-separated list of components to check
                          (api, db, vector, storage, all) (default: all)
  --fail-fast             Exit on first failure
  --quiet                 Suppress output except for errors
  --help                  Show this help message
```

**Configuration**:
Configuration file specifies endpoints and expected responses:

```ini
[api]
endpoint = https://api.example.com/health
expected_status = 200
expected_content = {"status":"healthy"}

[database]
connection_string = postgresql://user:password@host:port/dbname
query = SELECT 1

[vector]
endpoint = https://api.example.com/health/vector
expected_status = 200

[storage]
path = /var/lib/docmanagement
min_free_space_mb = 1000
```

**Examples**:
```bash
# Check all components
./health-check.sh

# Check only API and database components
./health-check.sh --components api,db

# Output results as JSON
./health-check.sh -o json

# Check production environment
./health-check.sh -e prod
```

### monitor-performance.sh

**Description**: Collects and reports performance metrics from system components. This script can be used for ad-hoc performance analysis or scheduled to run periodically for trend analysis.

**Usage**:
```bash
./monitor-performance.sh [options]

Options:
  -c, --config FILE       Monitoring configuration file (default: config/monitoring.conf)
  -d, --duration MINUTES  Monitoring duration in minutes (default: 5)
  -i, --interval SECONDS  Sampling interval in seconds (default: 10)
  -o, --output FILE       Output file (default: stdout)
  -f, --format FORMAT     Output format (text, csv, json) (default: text)
  --metrics TYPE          Metrics to collect (cpu, memory, disk, network, requests, all)
                          (default: all)
  --threshold PERCENT     Alert threshold percentage (default: 80)
  --help                  Show this help message
```

**Configuration**:
Configuration file defines endpoints and metrics collection:

```ini
[api]
endpoint = https://api.example.com/metrics
auth_token = ${API_METRICS_TOKEN}

[database]
connection_string = postgresql://user:password@host:port/dbname
metrics_query = SELECT * FROM pg_stat_database WHERE datname = 'docmanagement'

[system]
collect_cpu = true
collect_memory = true
collect_disk = true
collect_network = true
```

**Examples**:
```bash
# Monitor all metrics for 10 minutes
./monitor-performance.sh -d 10

# Monitor CPU and memory with 5-second intervals
./monitor-performance.sh --metrics cpu,memory -i 5

# Save results to a CSV file
./monitor-performance.sh -o performance_report.csv -f csv

# Monitor with a lower threshold for alerting
./monitor-performance.sh --threshold 70
```

## Maintenance Scripts

### rotate-keys.sh

**Description**: Automates the rotation of security keys, including JWT signing keys and encryption keys. This script ensures regular key rotation for security compliance.

**Usage**:
```bash
./rotate-keys.sh [options]

Options:
  -c, --config FILE       Key configuration file (default: config/security.conf)
  -t, --type TYPE         Key type to rotate (jwt, encryption, all) (default: all)
  -l, --length LENGTH     Key length in bits (default: depends on key type)
  -e, --expiry DAYS       Key expiry in days (default: 90)
  --force                 Force rotation even if current key is not expired
  --dry-run               Show what would be rotated without making changes
  --help                  Show this help message
```

**Configuration**:
Configuration defines key storage locations and rotation policies:

```ini
[jwt]
key_file = /etc/docmanagement/jwt_keys.json
key_length = 2048
rotation_days = 90
algorithm = RS256

[encryption]
key_file = /etc/docmanagement/encryption_keys.json
key_length = 256
rotation_days = 180
algorithm = AES-GCM
```

**Examples**:
```bash
# Rotate all keys
./rotate-keys.sh

# Rotate only JWT keys
./rotate-keys.sh -t jwt

# Force rotation regardless of expiry
./rotate-keys.sh --force

# Perform a dry run to see what would be rotated
./rotate-keys.sh --dry-run
```

### generate-test-data.sh

**Description**: Generates synthetic test data for development and testing purposes. This script can create realistic document data, user accounts, and query patterns.

**Usage**:
```bash
./generate-test-data.sh [options]

Options:
  -c, --config FILE       Test data configuration file (default: config/test-data.conf)
  -o, --output DIR        Output directory (default: ./test-data)
  -d, --documents COUNT   Number of documents to generate (default: 100)
  -u, --users COUNT       Number of users to generate (default: 10)
  -q, --queries COUNT     Number of queries to generate (default: 50)
  -s, --seed VALUE        Random seed for reproducible generation (default: current time)
  --format FORMAT         Document format (pdf, txt, both) (default: pdf)
  --topics LIST           Comma-separated list of topics
                          (default: technology,science,business,health)
  --help                  Show this help message
```

**Configuration**:
Configuration defines data generation parameters:

```ini
[documents]
min_size_kb = 10
max_size_kb = 5000
min_pages = 1
max_pages = 50
topics = technology,science,business,health,finance,education,art,sports

[users]
roles = admin,regular
admin_ratio = 0.1

[queries]
min_length = 5
max_length = 50
```

**Examples**:
```bash
# Generate default test dataset
./generate-test-data.sh

# Generate a large dataset
./generate-test-data.sh -d 1000 -u 50 -q 500

# Generate business and finance documents only
./generate-test-data.sh --topics business,finance

# Generate reproducible dataset
./generate-test-data.sh -s 12345
```

### cleanup-old-backups.sh

**Description**: Removes old database and vector index backups according to the configured retention policy. This script helps manage disk space and maintain organization of backup files.

**Usage**:
```bash
./cleanup-old-backups.sh [options]

Options:
  -c, --config FILE       Backup configuration file (default: config/backup.conf)
  -d, --db-retention DAYS Database backup retention in days (default: 30)
  -v, --vector-retention DAYS Vector index backup retention in days (default: 14)
  -b, --backup-dir DIR    Backup directory (default: from config)
  --dry-run               Show what would be deleted without removing files
  --force                 Skip confirmation prompt
  --help                  Show this help message
```

**Configuration**:
Configuration specifies backup locations and retention policies:

```ini
[database]
backup_dir = /var/backups/postgres
retention_days = 30
wal_retention_days = 7

[vector]
backup_dir = /var/backups/faiss
retention_days = 14
```

**Examples**:
```bash
# Clean up backups using default retention policy
./cleanup-old-backups.sh

# Use custom retention periods
./cleanup-old-backups.sh -d 60 -v 30

# Perform a dry run to see what would be deleted
./cleanup-old-backups.sh --dry-run

# Clean up without confirmation prompt
./cleanup-old-backups.sh --force
```

## Common Patterns

The utility scripts follow these common patterns and conventions:

1. **Configuration Hierarchy**:
   - Command-line options have highest precedence
   - Environment variables have second precedence
   - Configuration files have third precedence
   - Default values have lowest precedence

2. **Error Handling**:
   - Non-zero exit codes indicate failures
   - Error messages are output to stderr
   - Verbose error messages with --verbose flag
   - Cleanup of temporary files on exit

3. **Logging**:
   - Log levels: ERROR, WARNING, INFO, DEBUG
   - Default log level is INFO
   - DEBUG level enabled with --verbose
   - Timestamps included in log messages

4. **Security**:
   - Sensitive information (passwords, tokens) never logged
   - Credentials obtained from environment or secure storage
   - Temporary files with sensitive data use secure creation patterns
   - Proper permission checking before operations

## Troubleshooting

### Common Issues

1. **Permission Denied**:
   - Ensure the script has execute permissions (`chmod +x script.sh`)
   - Verify that the user has appropriate permissions for the target resources
   - Check if the script needs to be run with sudo

2. **Configuration Not Found**:
   - Verify that configuration files exist in the expected locations
   - Check if environment variables are properly set
   - Use --verbose to see which configuration files are being loaded

3. **Database Connection Issues**:
   - Verify database credentials in configuration
   - Check if the database server is accessible from the execution environment
   - Ensure firewalls allow connections to database ports

4. **AWS Authentication Problems**:
   - Check that AWS credentials are properly configured
   - Verify AWS_PROFILE is set correctly for the target environment
   - Ensure the IAM role/user has appropriate permissions

### Debugging Tips

- Run scripts with the `--verbose` or `-v` flag for detailed output
- Use `--dry-run` when available to see what would happen without making changes
- Check logs for error messages from previous runs
- For deployment issues, check the AWS console for ECS, ECR, or CloudWatch logs

## Contributing

### Guidelines for Contributing New Scripts

1. **Naming Conventions**:
   - Use kebab-case for script names (e.g., `backup-database.sh`)
   - Use descriptive names that indicate the script's purpose
   - Group related scripts by prefixing with common terms

2. **Script Structure**:
   - Start with a shebang line and script description comment
   - Define usage and help text near the top
   - Include input validation and proper error handling
   - Follow the common patterns described above

3. **Documentation**:
   - Update this README.md with details about new scripts
   - Include usage examples for common scenarios
   - Document all command-line options and configuration parameters

4. **Testing**:
   - Test scripts in development and staging environments before committing
   - Include a --dry-run option for operations that modify data
   - Consider edge cases and error scenarios in your testing

### Review Process

1. Submit a pull request with your new or modified script
2. Ensure the script follows the guidelines above
3. Include test results and validation in the PR description
4. Request review from the DevOps or SRE team

By following these guidelines, we can maintain a consistent and reliable set of utility scripts for the Document Management and AI Chatbot System.