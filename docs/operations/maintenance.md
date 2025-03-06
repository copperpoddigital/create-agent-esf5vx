---
title: '# Maintenance Guide'
description: 'Comprehensive guide for routine maintenance procedures for the Document Management and AI Chatbot System, providing detailed instructions on database maintenance, vector store optimization, security updates, backup procedures, and monitoring system maintenance.'
---

## 1. Introduction

This guide provides comprehensive instructions for routine maintenance of the Document Management and AI Chatbot System. Regular maintenance is essential for ensuring system reliability, performance, and security. This document outlines maintenance procedures, schedules, and best practices for system operators.

### 1.1 Purpose and Scope

The purpose of this maintenance guide is to provide system operators with detailed procedures for:

- Regular database maintenance
- Vector store optimization
- Security updates and patch management
- Backup verification and management
- Monitoring system maintenance
- Credential rotation

This guide covers all environments (development, staging, and production) with environment-specific considerations noted where applicable.

### 1.2 Maintenance Philosophy

The maintenance approach for this system follows these key principles:

- **Proactive Maintenance**: Regular scheduled maintenance to prevent issues rather than reactive fixes
- **Minimal Disruption**: Maintenance procedures designed to minimize or eliminate service disruption
- **Automation**: Automated maintenance where possible to ensure consistency and reduce human error
- **Verification**: Thorough testing after maintenance to ensure system integrity
- **Documentation**: Comprehensive logging of all maintenance activities

All maintenance activities should be performed during designated maintenance windows unless addressing critical issues.

### 1.3 Maintenance Windows

Maintenance should be performed during the following designated windows to minimize impact on users:

| Environment | Primary Window | Backup Window |
| --- | --- | --- |
| Development | Anytime | N/A |
| Staging | Weekdays 8 PM - 10 PM | Weekends 10 AM - 12 PM |
| Production | Sundays 2 AM - 4 AM | Saturdays 2 AM - 4 AM |

Emergency maintenance may be performed outside these windows if required to address critical issues. In such cases, appropriate notification procedures should be followed.

## 2. Database Maintenance

Regular database maintenance is essential for optimal performance and reliability. This section covers routine PostgreSQL maintenance procedures.

### 2.1 Weekly Maintenance Tasks

The following tasks should be performed weekly:

**VACUUM ANALYZE**

Run VACUUM ANALYZE to reclaim storage and update statistics:

```bash
# Connect to database
psql -h $DB_HOST -U $DB_USERNAME -d $DB_NAME

# Run VACUUM ANALYZE
VACUUM ANALYZE;
```

**Index Maintenance**

Reindex critical tables to maintain performance:

```bash
# Reindex specific tables
REINDEX TABLE documents;
REINDEX TABLE document_chunks;
REINDEX TABLE queries;
```

**Connection Monitoring**

Check for idle connections and terminate if necessary:

```bash
# Check for long-running idle connections
SELECT pid, datname, usename, state, query, 
       now() - state_change AS idle_time
FROM pg_stat_activity 
WHERE state = 'idle' AND now() - state_change > interval '1 hour';

# Terminate idle connections if needed
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND now() - state_change > interval '1 hour';
```

### 2.2 Monthly Maintenance Tasks

The following tasks should be performed monthly:

**Database Statistics Update**

Update database statistics for the query planner:

```bash
# Update statistics
ANALYZE VERBOSE;
```

**Table and Index Bloat Check**

Identify and address table and index bloat:

```bash
# Check for table bloat
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
       pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) as table_size,
       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename) - 
                      pg_relation_size(schemaname || '.' || tablename)) as index_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 10;

# Address bloat with VACUUM FULL for problematic tables (during maintenance window only)
VACUUM FULL documents;
```

**Query Performance Review**

Identify and optimize slow queries:

```bash
# Find slow queries
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# Reset statistics after review
SELECT pg_stat_statements_reset();
```

### 2.3 Quarterly Maintenance Tasks

The following tasks should be performed quarterly:

**Database Backup Verification**

Verify database backups by performing a test restore:

```bash
# Run backup verification script
./scripts/verify-db-backup.sh
```

This script will:
1. Restore the latest backup to a temporary database
2. Perform integrity checks
3. Verify data consistency
4. Clean up the temporary database

**Database Configuration Review**

Review and optimize database configuration parameters:

```bash
# Check current settings
SELECT name, setting, unit, context, short_desc
FROM pg_settings
WHERE name IN ('shared_buffers', 'work_mem', 'maintenance_work_mem', 
               'effective_cache_size', 'max_connections');
```

Adjust settings based on system performance and resource utilization.

### 2.4 Automated Database Maintenance

The system includes automated database maintenance scripts that can be scheduled using cron or similar scheduling tools.

**Backup Script**

The `backup-database.sh` script performs automated database backups:

```bash
# Full database backup
./scripts/backup-database.sh --type full

# WAL archiving
./scripts/backup-database.sh --type wal

# Full backup with S3 upload
./scripts/backup-database.sh --type full --s3
```

**Recommended Cron Schedule**

```
# Daily full backup at 1 AM
0 1 * * * /opt/document-management/scripts/backup-database.sh --type full --s3

# Hourly WAL archiving
0 * * * * /opt/document-management/scripts/backup-database.sh --type wal --s3
```

Refer to the script's help output (`./scripts/backup-database.sh --help`) for additional options and configuration.

## 3. Vector Store Maintenance

The FAISS vector store requires regular maintenance to ensure optimal search performance and accuracy.

### 3.1 Weekly Maintenance Tasks

The following tasks should be performed weekly:

**Index Verification**

Verify the integrity of the FAISS index:

```bash
# Run index verification script
python scripts/verify_faiss_index.py
```

This script checks:
- Index file integrity
- Vector count consistency with database
- Basic search functionality

**Performance Monitoring**

Monitor search performance metrics:

```bash
# Check search latency statistics
curl -s http://localhost:9090/api/v1/query?query=rate\(vector_search_duration_seconds_sum{job="vector_search"}[1d]\)/rate\(vector_search_duration_seconds_count{job="vector_search"}[1d]\) | jq
```

Review the Grafana Vector Search dashboard for detailed performance metrics.

### 3.2 Monthly Maintenance Tasks

The following tasks should be performed monthly:

**Index Optimization**

Optimize the FAISS index for better performance:

```bash
# Run index optimization script
./scripts/optimize-vector-index.sh
```

This script performs:
- Index parameter tuning based on current size
- Optimization of internal structures
- Performance benchmarking before and after

**Index Backup**

Create a backup of the FAISS index:

```bash
# Backup FAISS index
./scripts/backup-vector-index.sh
```

This ensures a recent backup is available for recovery if needed.

### 3.3 Quarterly Maintenance Tasks

The following tasks should be performed quarterly:

**Full Index Rebuild**

Rebuild the FAISS index from scratch to optimize structure and performance:

```bash
# Rebuild FAISS index
./scripts/rebuild-vector-index.sh --backup
```

This script will:
1. Backup the current index
2. Rebuild the index from document chunks in the database
3. Verify the new index
4. Replace the old index with the new one

**Search Quality Evaluation**

Evaluate search quality using test queries:

```bash
# Run search quality evaluation
python scripts/evaluate_search_quality.py
```

This script tests a set of predefined queries and evaluates relevance of results.

### 3.4 Automated Vector Store Maintenance

The system includes automated vector store maintenance scripts that can be scheduled using cron or similar scheduling tools.

**Index Rebuild Script**

The `rebuild-vector-index.sh` script rebuilds the FAISS index:

```bash
# Rebuild index with backup
./scripts/rebuild-vector-index.sh --backup

# Rebuild with specific batch size
./scripts/rebuild-vector-index.sh --batch-size 200 --backup

# Force rebuild without confirmation
./scripts/rebuild-vector-index.sh --force --backup
```

**Recommended Cron Schedule**

```
# Monthly index optimization at 2 AM on the first Sunday
0 2 * * 0 [ $(date +\%d) -le 7 ] && /opt/document-management/scripts/optimize-vector-index.sh

# Weekly index backup at 3 AM on Sunday
0 3 * * 0 /opt/document-management/scripts/backup-vector-index.sh

# Quarterly index rebuild at 2 AM on the first day of the quarter
0 2 1 1,4,7,10 * /opt/document-management/scripts/rebuild-vector-index.sh --backup --force
```

Refer to the script's help output (`./scripts/rebuild-vector-index.sh --help`) for additional options and configuration.

## 4. Security Updates

Regular security updates are essential for maintaining system security and preventing vulnerabilities.

### 4.1 Dependency Updates

Python dependencies should be regularly updated to address security vulnerabilities.

**Monthly Update Procedure**

1. Create a backup of the current environment:

```bash
# Export current dependencies
cd src/backend
pip freeze > requirements.backup.txt
```

2. Update dependencies:

```bash
# Update dependencies using Poetry
poetry update

# Or using pip
pip install --upgrade -r requirements.txt
```

3. Run security checks:

```bash
# Check for security vulnerabilities
poetry run safety check

# Or using pip-audit
pip-audit
```

4. Run tests to verify functionality:

```bash
# Run test suite
python -m pytest
```

5. If tests pass, commit the updated dependencies. If issues occur, rollback:

```bash
# Rollback if needed
pip install -r requirements.backup.txt
```

**Automated Dependency Updates**

The system uses GitHub Dependabot for automated dependency updates. Review and merge these updates regularly after verifying tests pass.

### 4.2 Container Image Updates

Container base images should be updated monthly to include security patches.

**Update Procedure**

1. Update base image version in Dockerfile:

```dockerfile
# Update from
FROM python:3.10-slim

# To latest patch version
FROM python:3.10-slim
```

2. Build and test the updated image:

```bash
# Build updated image
docker build -t document-management:latest .

# Run tests with updated image
docker-compose -f docker-compose.test.yml up --exit-code-from tests
```

3. If tests pass, push the updated image to the registry:

```bash
# Tag and push image
docker tag document-management:latest ${ECR_REGISTRY}/document-management:latest
docker push ${ECR_REGISTRY}/document-management:latest
```

4. Deploy the updated image following the standard deployment procedure.

### 4.3 Operating System Updates

For self-hosted environments, operating system updates should be applied monthly.

**Update Procedure**

1. Create a backup snapshot of the instance
2. Apply updates:

```bash
# For Ubuntu/Debian
sudo apt update
sudo apt upgrade -y

# For Amazon Linux
sudo yum update -y
```

3. Reboot if required:

```bash
sudo reboot
```

4. Verify system functionality after updates

**AWS-Managed Services**

For AWS-managed services (RDS, ECS, etc.), review and apply maintenance updates according to AWS recommendations. Schedule these updates during maintenance windows.

### 4.4 Security Scanning

Regular security scanning helps identify potential vulnerabilities.

**Weekly Scanning Procedure**

1. Run infrastructure scanning:

```bash
# Run security scan script
./scripts/security-scan.sh
```

This script performs:
- Container image scanning with Trivy
- Infrastructure-as-code scanning with tfsec
- API security scanning with OWASP ZAP

2. Review scan results and address critical findings immediately

3. Create tickets for non-critical findings

**Automated Security Scanning**

The system includes GitHub Actions workflows for automated security scanning on pull requests and scheduled runs. Review these results regularly.

### 4.5 Credential Rotation

Security credentials should be rotated regularly to minimize risk.

**Quarterly Rotation Procedure**

1. Run the credential rotation script:

```bash
# Rotate all credentials
./scripts/rotate-keys.sh --all

# Rotate specific credential type
./scripts/rotate-keys.sh --type database
./scripts/rotate-keys.sh --type api-keys
./scripts/rotate-keys.sh --type jwt-secret
```

2. Verify system functionality after credential rotation

3. Update credential documentation in secure storage

**Manual Credential Rotation**

For credentials not covered by the rotation script:

1. Generate new credentials
2. Update the credential in AWS Secrets Manager or appropriate storage
3. Update application configuration to use new credential
4. Verify functionality
5. Revoke old credential after confirmation

## 5. Backup and Cleanup

Regular backup verification and cleanup of old data are essential for system maintenance.

### 5.1 Database Backups

Database backups are automated via RDS snapshots and the backup-database.sh script.

**Verification Procedure**

1. Verify backup schedule and completion:

```bash
# Check RDS automated backups
aws rds describe-db-instances --db-instance-identifier document-management-prod | jq '.DBInstances[0].BackupRetentionPeriod'

# List recent backups
aws rds describe-db-snapshots --db-instance-identifier document-management-prod --snapshot-type automated --query 'sort_by(DBSnapshots, &SnapshotCreateTime)[-5:].SnapshotCreateTime'
```

2. Perform test restore monthly:

```bash
# Test restore to temporary instance
./scripts/verify-db-backup.sh
```

**Retention Policy**

- Daily automated backups: 30 days retention
- Weekly manual backups: 90 days retention
- Monthly backups: 1 year retention

The backup-database.sh script handles retention automatically based on configuration.

### 5.2 Document Storage Backups

Document storage (S3) is backed up using cross-region replication and versioning.

**Verification Procedure**

1. Verify replication status:

```bash
# Check replication configuration
aws s3api get-bucket-replication --bucket document-management-prod-documents

# Check replication metrics
aws s3api get-bucket-metrics-configuration --bucket document-management-prod-documents --id replication
```

2. Verify versioning status:

```bash
# Check versioning status
aws s3api get-bucket-versioning --bucket document-management-prod-documents
```

3. Test restore procedure quarterly:

```bash
# Test restore from backup region
./scripts/verify-s3-backup.sh
```

**Retention Policy**

- Current versions: Indefinite retention
- Previous versions: 90 days retention
- Deleted objects: 30 days retention

Configure lifecycle policies to enforce these retention periods.

### 5.3 Vector Index Backups

FAISS vector index backups are created using the backup-vector-index.sh script.

**Verification Procedure**

1. Verify backup completion:

```bash
# List recent backups
ls -la /opt/document-management/backups/vector-index/
```

2. Test restore procedure monthly:

```bash
# Test restore from backup
./scripts/verify-vector-index-backup.sh
```

**Retention Policy**

- Daily backups: 7 days retention
- Weekly backups: 30 days retention
- Pre-rebuild backups: 90 days retention

The backup-vector-index.sh script handles retention automatically based on configuration.

### 5.4 Log Rotation and Cleanup

System logs should be rotated and cleaned up regularly to prevent disk space issues.

**Log Rotation Configuration**

The system uses logrotate for log rotation. Configuration is in `/etc/logrotate.d/document-management`:

```
/var/log/document-management/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 document-management document-management
    sharedscripts
    postrotate
        systemctl reload document-management >/dev/null 2>&1 || true
    endscript
}
```

**Manual Cleanup Procedure**

For logs not covered by logrotate:

```bash
# Clean up old logs
./scripts/cleanup-logs.sh --days 30
```

This script removes logs older than the specified number of days.

### 5.5 Temporary File Cleanup

Temporary files should be cleaned up regularly to prevent disk space issues.

**Cleanup Procedure**

1. Run the temporary file cleanup script:

```bash
# Clean up temporary files
./scripts/cleanup-temp-files.sh
```

This script removes:
- Temporary upload files older than 24 hours
- Temporary processing files older than 24 hours
- Cached files older than 7 days

**Automated Cleanup**

Schedule the cleanup script to run daily:

```
# Daily temporary file cleanup at 4 AM
0 4 * * * /opt/document-management/scripts/cleanup-temp-files.sh
```

## 6. Monitoring System Maintenance

The monitoring system itself requires regular maintenance to ensure it functions correctly.

### 6.1 Alert Rule Review

Alert rules should be reviewed quarterly to ensure they remain relevant and effective.

**Review Procedure**

1. Review alert firing history:

```bash
# Get alert history for past month
curl -s http://localhost:9090/api/v1/query?query=ALERTS{} | jq
```

2. Identify noisy alerts (frequent firing without actionable response)

3. Identify gaps in monitoring coverage

4. Update alert rules in `infrastructure/monitoring/prometheus/rules/alerts.yml`

5. Apply changes:

```bash
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

**Alert Tuning Guidelines**

- Adjust thresholds based on historical data
- Increase "for" duration to reduce flapping
- Group related alerts to reduce notification volume
- Add additional conditions to reduce false positives

### 6.2 Dashboard Updates

Monitoring dashboards should be updated as needed to reflect system changes and improve visibility.

**Update Procedure**

1. Export updated dashboard from Grafana UI

2. Save dashboard JSON to version control:

```bash
# Save dashboard to repository
cp dashboard.json infrastructure/monitoring/grafana/dashboards/
```

3. Apply changes through deployment pipeline or manually:

```bash
# Apply dashboard changes
docker cp infrastructure/monitoring/grafana/dashboards/dashboard.json grafana:/etc/grafana/provisioning/dashboards/
```

**Dashboard Maintenance Guidelines**

- Keep dashboards focused on specific use cases
- Use consistent naming and formatting
- Include documentation within dashboards
- Organize panels in logical groups
- Test dashboard performance with different time ranges

### 6.3 Notification Channel Verification

Notification channels should be verified monthly to ensure alerts are properly delivered.

**Verification Procedure**

1. Test notification channels:

```bash
# Test notification channels
./scripts/test-alerts.sh
```

This script sends a test alert to each configured notification channel.

2. Verify receipt of test notifications

3. Update contact information if needed

**Notification Channel Maintenance**

- Keep contact information up-to-date
- Review escalation paths quarterly
- Test backup notification methods
- Document notification procedures

### 6.4 Monitoring Storage Management

Monitoring system storage should be managed to prevent disk space issues.

**Prometheus Storage**

1. Check current storage usage:

```bash
# Check Prometheus disk usage
du -sh /path/to/prometheus/data
```

2. Adjust retention period if needed:

```yaml
# In prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  # Adjust retention period as needed
  storage:
    tsdb:
      retention.time: 15d
```

3. Apply changes:

```bash
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

**Loki Storage**

1. Check current storage usage:

```bash
# Check Loki disk usage
du -sh /path/to/loki/data
```

2. Adjust retention period if needed:

```yaml
# In loki.yml
limits_config:
  retention_period: 336h  # 14 days
```

3. Apply changes:

```bash
# Restart Loki service
docker-compose restart loki
```

### 6.5 Monitoring System Backup

The monitoring system configuration should be backed up regularly.

**Backup Procedure**

1. Backup Prometheus configuration:

```bash
# Backup Prometheus configuration
cp -r /path/to/prometheus/config /opt/document-management/backups/monitoring/prometheus/$(date +%Y%m%d)
```

2. Backup Grafana dashboards and configuration:

```bash
# Backup Grafana dashboards
cp -r /path/to/grafana/dashboards /opt/document-management/backups/monitoring/grafana/$(date +%Y%m%d)
```

3. Backup AlertManager configuration:

```bash
# Backup AlertManager configuration
cp -r /path/to/alertmanager/config /opt/document-management/backups/monitoring/alertmanager/$(date +%Y%m%d)
```

**Automated Backup**

Schedule the monitoring backup script to run weekly:

```
# Weekly monitoring configuration backup at 3 AM on Sunday
0 3 * * 0 /opt/document-management/scripts/backup-monitoring-config.sh
```

## 7. Maintenance Schedule

This section provides a consolidated maintenance schedule for all system components.

### 7.1 Daily Tasks

The following tasks should be performed daily:

| Task | Component | Script/Command | Time |
| --- | --- | --- | --- |
| Database backup | PostgreSQL | `backup-database.sh --type full` | 1 AM |
| WAL archiving | PostgreSQL | `backup-database.sh --type wal` | Hourly |
| Temporary file cleanup | File system | `cleanup-temp-files.sh` | 4 AM |
| System health check | All | `health-check.sh` | 6 AM |

These tasks should be automated using cron or a similar scheduling tool.

### 7.2 Weekly Tasks

The following tasks should be performed weekly:

| Task | Component | Script/Command | Day |
| --- | --- | --- | --- |
| VACUUM ANALYZE | PostgreSQL | `psql -c "VACUUM ANALYZE;"` | Sunday |
| Index verification | FAISS | `verify_faiss_index.py` | Sunday |
| Vector index backup | FAISS | `backup-vector-index.sh` | Sunday |
| Security scanning | All | `security-scan.sh` | Monday |
| Log rotation | All | `logrotate -f /etc/logrotate.d/document-management` | Sunday |

These tasks should be scheduled during maintenance windows.

### 7.3 Monthly Tasks

The following tasks should be performed monthly:

| Task | Component | Script/Command | When |
| --- | --- | --- | --- |
| Database statistics update | PostgreSQL | `psql -c "ANALYZE VERBOSE;"` | 1st Sunday |
| Vector index optimization | FAISS | `optimize-vector-index.sh` | 1st Sunday |
| Dependency updates | Application | `poetry update` | 1st Monday |
| Container image updates | Docker | Build and deploy updated images | 2nd Monday |
| Notification channel verification | Monitoring | `test-alerts.sh` | 1st Monday |

These tasks should be scheduled during maintenance windows.

### 7.4 Quarterly Tasks

The following tasks should be performed quarterly:

| Task | Component | Script/Command | When |
| --- | --- | --- | --- |
| Database backup verification | PostgreSQL | `verify-db-backup.sh` | 1st month of quarter |
| Vector index rebuild | FAISS | `rebuild-vector-index.sh --backup --force` | 1st month of quarter |
| Credential rotation | Security | `rotate-keys.sh --all` | 1st month of quarter |
| Alert rule review | Monitoring | Manual review | 1st month of quarter |
| Database configuration review | PostgreSQL | Manual review | 1st month of quarter |

These tasks should be scheduled during extended maintenance windows.

### 7.5 Maintenance Calendar

A sample annual maintenance calendar:

| Month | Special Maintenance Activities |
| --- | --- |
| January | Q1 quarterly tasks, annual planning review |
| February | Regular monthly tasks |
| March | Regular monthly tasks |
| April | Q2 quarterly tasks, infrastructure scaling review |
| May | Regular monthly tasks |
| June | Regular monthly tasks |
| July | Q3 quarterly tasks, mid-year performance review |
| August | Regular monthly tasks |
| September | Regular monthly tasks |
| October | Q4 quarterly tasks, annual security review |
| November | Regular monthly tasks |
| December | Regular monthly tasks, year-end review |

Adjust this calendar based on your organization's specific needs and schedule.

## 8. Maintenance Scripts

This section provides an overview of the maintenance scripts included with the system.

### 8.1 Database Maintenance Scripts

The following scripts are available for database maintenance:

**backup-database.sh**

Performs database backups and WAL archiving.

```bash
# Usage
./scripts/backup-database.sh [options]
  Options:
    -c, --config CONFIG_FILE  Specify config file (default: /etc/document-management/backup.conf)
    -t, --type TYPE          Backup type: full, wal, all (default: all)
    -r, --retention DAYS     Backup retention in days (default: 30)
    -s, --s3                 Upload backup to S3
    -n, --no-compress        Skip backup compression
    -v, --verify             Verify backup integrity
    --verbose                Enable verbose output
    -h, --help               Show this help message
```

**verify-db-backup.sh**

Verifies database backup integrity by performing a test restore.

```bash
# Usage
./scripts/verify-db-backup.sh [options]
  Options:
    -b, --backup-id ID       Specify backup ID to verify (default: latest)
    -t, --temp-db NAME       Temporary database name (default: verify_restore)
    --keep-temp              Keep temporary database after verification
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**db-maintenance.sh**

Performs routine database maintenance tasks.

```bash
# Usage
./scripts/db-maintenance.sh [options]
  Options:
    -t, --tasks TASKS        Comma-separated list of tasks: vacuum,analyze,reindex,all (default: all)
    -d, --database NAME      Database name (default: from config)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

### 8.2 Vector Store Maintenance Scripts

The following scripts are available for vector store maintenance:

**rebuild-vector-index.sh**

Rebuilds the FAISS vector index.

```bash
# Usage
./scripts/rebuild-vector-index.sh [options]
  Options:
    -p, --path PATH          Specify index path (default: from settings)
    -b, --batch-size SIZE    Batch size for processing (default: 100)
    -f, --force              Force rebuild without confirmation
    -B, --backup             Backup current index before rebuilding
    -n, --no-backup          Skip backup of current index
    -r, --retention DAYS     Backup retention in days (default: 30)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**optimize-vector-index.sh**

Optimizes the FAISS vector index for better performance.

```bash
# Usage
./scripts/optimize-vector-index.sh [options]
  Options:
    -p, --path PATH          Specify index path (default: from settings)
    -t, --type TYPE          Optimization type: basic, advanced (default: basic)
    -B, --backup             Backup current index before optimization
    -f, --force              Force optimization without confirmation
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**backup-vector-index.sh**

Creates a backup of the FAISS vector index.

```bash
# Usage
./scripts/backup-vector-index.sh [options]
  Options:
    -p, --path PATH          Specify index path (default: from settings)
    -d, --destination DIR    Backup destination directory (default: from config)
    -c, --compress           Compress backup
    -r, --retention DAYS     Backup retention in days (default: 30)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

### 8.3 Security Maintenance Scripts

The following scripts are available for security maintenance:

**security-scan.sh**

Performs security scanning of the system.

```bash
# Usage
./scripts/security-scan.sh [options]
  Options:
    -t, --type TYPE          Scan type: container,code,infra,api,all (default: all)
    -o, --output FILE        Output file for results (default: security-scan-results.json)
    -s, --severity LEVEL     Minimum severity to report: critical,high,medium,low (default: high)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**rotate-keys.sh**

Rotates security credentials.

```bash
# Usage
./scripts/rotate-keys.sh [options]
  Options:
    -t, --type TYPE          Credential type: database,api-keys,jwt-secret,all (default: all)
    -e, --environment ENV    Environment: dev,staging,prod (default: current)
    -f, --force              Force rotation without confirmation
    -b, --backup             Backup current credentials
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**update-dependencies.sh**

Updates and checks dependencies for security vulnerabilities.

```bash
# Usage
./scripts/update-dependencies.sh [options]
  Options:
    -t, --type TYPE          Update type: minor,major,all (default: minor)
    -c, --check-only         Check for updates without applying
    -s, --security-only      Only update packages with security issues
    -b, --backup             Backup current dependencies
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

### 8.4 Monitoring Maintenance Scripts

The following scripts are available for monitoring system maintenance:

**backup-monitoring-config.sh**

Backups monitoring system configuration.

```bash
# Usage
./scripts/backup-monitoring-config.sh [options]
  Options:
    -d, --destination DIR    Backup destination directory (default: from config)
    -c, --components COMP    Components to backup: prometheus,grafana,alertmanager,all (default: all)
    -r, --retention DAYS     Backup retention in days (default: 90)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**test-alerts.sh**

Tests alert notification channels.

```bash
# Usage
./scripts/test-alerts.sh [options]
  Options:
    -c, --channels CHANNELS  Channels to test: email,slack,pagerduty,all (default: all)
    -m, --message MESSAGE    Custom test message
    -s, --severity LEVEL     Alert severity: critical,warning,info (default: info)
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**update-dashboards.sh**

Updates Grafana dashboards from version control.

```bash
# Usage
./scripts/update-dashboards.sh [options]
  Options:
    -s, --source DIR         Source directory for dashboards (default: from config)
    -d, --destination DIR    Grafana dashboards directory (default: from config)
    -b, --backup             Backup current dashboards
    -f, --force              Force update without confirmation
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

### 8.5 General Maintenance Scripts

The following scripts are available for general system maintenance:

**health-check.sh**

Performs a comprehensive system health check.

```bash
# Usage
./scripts/health-check.sh [options]
  Options:
    -c, --component COMP     Component to check: api,db,vector,llm,all (default: all)
    -e, --environment ENV    Environment: dev,staging,prod (default: current)
    -o, --output FORMAT      Output format: text,json (default: text)
    -n, --notify             Send notification on issues
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**cleanup-logs.sh**

Cleans up old log files.

```bash
# Usage
./scripts/cleanup-logs.sh [options]
  Options:
    -d, --days DAYS          Remove logs older than DAYS days (default: 30)
    -p, --path DIR           Log directory path (default: from config)
    -t, --type TYPE          Log types to clean: application,system,all (default: all)
    -f, --force              Force cleanup without confirmation
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message
```

**cleanup-temp-files.sh**

Cleans up temporary files.

```bash
# Usage
./scripts/cleanup-temp-files.sh [options]
  Options:
    -d, --days DAYS          Remove files older than DAYS days (default: 1)
    -p, --path DIR           Temp directory path (default: from config)
    -t, --type TYPE          File types to clean: uploads,processing,cache,all (default: all)
    -f, --force              Force cleanup without confirmation
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message