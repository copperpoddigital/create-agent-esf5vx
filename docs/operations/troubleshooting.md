## 1. Introduction

This guide provides comprehensive troubleshooting procedures for the Document Management and AI Chatbot System. It covers diagnostic approaches, common issues, detailed runbooks, and preventive measures to help system operators quickly identify and resolve problems across all system components.

### 1.1 Purpose and Scope

The purpose of this troubleshooting guide is to provide system operators with:

- Systematic diagnostic procedures for identifying issues
- Solutions for common problems across all system components
- Detailed runbooks for specific issue scenarios
- Preventive measures to avoid recurring problems

This guide covers all environments (development, staging, and production) with environment-specific considerations noted where applicable.

### 1.2 System Architecture Overview

The Document Management and AI Chatbot System consists of several key components that work together:

- **API Layer**: FastAPI application handling HTTP requests and routing
- **Document Processor**: Extracts text from PDFs and generates embeddings
- **Vector Search Engine**: FAISS-based vector similarity search
- **LLM Integration**: OpenAI API integration for response generation
- **Database**: PostgreSQL for metadata and structured data storage
- **File Storage**: Storage for original document files
- **Monitoring**: Prometheus, Loki, and Grafana for system monitoring

Understanding these components and their interactions is essential for effective troubleshooting. Refer to the [System Architecture](../architecture/system-overview.md) document for detailed information.

### 1.3 Troubleshooting Philosophy

The troubleshooting approach for this system follows these key principles:

- **Systematic Diagnosis**: Start with broad health checks and narrow down to specific components
- **Evidence-Based**: Use logs, metrics, and diagnostics to identify issues rather than assumptions
- **Minimal Impact**: Troubleshooting steps should minimize impact on system operation
- **Root Cause Analysis**: Focus on identifying and addressing root causes, not just symptoms
- **Documentation**: Document all issues and resolutions for future reference

When troubleshooting, always start with the simplest and least invasive diagnostic steps before moving to more complex or impactful interventions.

### 1.4 Using This Guide

This guide is organized to help you quickly find relevant information:

1. **Diagnostic Procedures**: Start here to systematically identify issues
2. **Common Issues**: Reference this section for known issues and their solutions
3. **Runbooks**: Follow these detailed procedures for specific scenarios
4. **Preventive Measures**: Implement these to prevent recurring issues

For urgent production issues, refer directly to the runbooks in Section 4 for immediate resolution steps. For systematic troubleshooting, start with the diagnostic procedures in Section 2.

## 2. Diagnostic Procedures

This section provides systematic procedures for diagnosing issues across different system components.

### 2.1 System Health Verification

Start troubleshooting by checking the overall health of the system using the health check endpoints.

**Basic Health Check**

```bash
# Check API liveness
curl http://<api-host>:<port>/api/v1/health/live

# Check API readiness
curl http://<api-host>:<port>/api/v1/health/ready

# Check all dependencies
curl http://<api-host>:<port>/api/v1/health/dependencies
```

The `/health/dependencies` endpoint provides a comprehensive health check of all system components. A healthy response looks like:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2023-06-15T12:34:56Z",
  "components": {
    "api": "ok",
    "database": "ok",
    "vector_store": "ok",
    "llm_service": "ok"
  }
}
```

If any component reports a non-"ok" status, proceed to the specific diagnostic procedures for that component.

### 2.2 Log Analysis

Logs are a primary source of diagnostic information. Use the following approaches to analyze logs effectively.

**Accessing Logs**

For containerized environments:

```bash
# View API container logs
docker logs -f document-management-api

# For AWS ECS
aws logs get-log-events --log-group-name /ecs/document-management-prod \
  --log-stream-name ecs/app/<task-id>
```

For centralized logging with Loki (via Grafana):

1. Access the Grafana UI (typically at http://<grafana-host>:3000)
2. Navigate to Explore > Loki
3. Use LogQL queries to filter logs:

```
# All logs from the API service
{service="api"}

# Error logs from any service
{} |= "ERROR"

# Logs related to a specific document
{} |= "document_id=doc123"

# Logs for a specific correlation ID (request tracing)
{} |= "correlation_id=abc123"
```

**Common Error Patterns**

Look for these common error patterns in logs:

- `ERROR` level logs indicating critical issues
- Exception stack traces
- Connection failures to dependencies
- Timeout messages
- Resource exhaustion warnings (memory, connections, etc.)

Correlate logs across components using the correlation ID included in all logs for a specific request.

### 2.3 Metrics Analysis

Metrics provide insights into system performance and behavior. Use the following approaches to analyze metrics effectively.

**Accessing Metrics**

For Prometheus metrics (via Grafana):

1. Access the Grafana UI (typically at http://<grafana-host>:3000)
2. Navigate to the appropriate dashboard:
   - System Overview Dashboard for high-level metrics
   - Component-specific dashboards for detailed metrics

For direct Prometheus queries:

```bash
# Query API request rate
curl -s "http://<prometheus-host>:9090/api/v1/query?query=sum(rate(http_requests_total{job='api'}[5m]))"

# Query error rate
curl -s "http://<prometheus-host>:9090/api/v1/query?query=sum(rate(http_requests_total{job='api',status~='5..'}[5m]))/sum(rate(http_requests_total{job='api'}[5m]))"
```

**Key Performance Indicators**

Monitor these key metrics for each component:

- **API Layer**: Request rate, error rate, response time
- **Database**: Query time, connection pool status, transaction rate
- **Vector Search**: Search latency, index size, relevance scores
- **LLM Service**: Response time, token usage, error rate
- **Resources**: CPU usage, memory usage, disk space

Look for anomalies such as sudden spikes or drops, gradual degradation, or values exceeding thresholds.

### 2.4 Database Diagnostics

Use these procedures to diagnose database-related issues.

**Connection Verification**

```bash
# Check database connectivity
psql -h <db-host> -U <db-user> -d <db-name> -c "SELECT 1;"
```

**Performance Diagnostics**

```bash
# Check active connections
psql -h <db-host> -U <db-user> -d <db-name> -c \
"SELECT count(*) FROM pg_stat_activity;"

# Check connection states
psql -h <db-host> -U <db-user> -d <db-name> -c \
"SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"

# Identify long-running queries
psql -h <db-host> -U <db-user> -d <db-name> -c \
"SELECT pid, now() - query_start AS duration, query \
FROM pg_stat_activity \
WHERE state = 'active' AND now() - query_start > interval '5 seconds' \
ORDER BY duration DESC;"
```

**Table and Index Statistics**

```bash
# Check table sizes
psql -h <db-host> -U <db-user> -d <db-name> -c \
"SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) \
FROM pg_catalog.pg_statio_user_tables \
ORDER BY pg_total_relation_size(relid) DESC;"

# Check index usage
psql -h <db-host> -U <db-user> -d <db-name> -c \
"SELECT relname, indexrelname, idx_scan \
FROM pg_stat_user_indexes \
ORDER BY idx_scan DESC;"
```

**Common Database Issues**

- Connection pool exhaustion
- Long-running queries blocking other operations
- Table or index bloat
- Missing or unused indexes
- Insufficient resources (CPU, memory, disk)

For RDS instances, also check the AWS RDS console for additional metrics and diagnostics.

### 2.5 Vector Store Diagnostics

Use these procedures to diagnose FAISS vector store issues.

**Index Verification**

```bash
# Run index verification script
python -m scripts.verify_faiss_index
```

This script checks:
- Index file integrity
- Vector count consistency with database
- Basic search functionality

**Memory Usage**

FAISS is memory-intensive, so check memory usage:

```bash
# Check memory usage
free -h

# Check process memory usage
ps -o pid,user,%mem,command ax | grep faiss
```

**Search Performance**

```bash
# Run search benchmark
python -m scripts.benchmark_vector_search
```

**Common Vector Store Issues**

- Corrupted index files
- Insufficient memory for index size
- Inconsistency between database and vector store
- Poor search performance due to suboptimal index type
- Missing vectors for documents

For serious index corruption, consider rebuilding the index using the `rebuild-vector-index.sh` script.

### 2.6 LLM Service Diagnostics

Use these procedures to diagnose LLM service (OpenAI API) issues.

**API Connectivity**

```bash
# Test OpenAI API connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Token Usage and Limits**

Check token usage in the OpenAI dashboard or via API:

```bash
# Get usage information (requires organization ID)
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Test Basic Completion**

```bash
# Test basic completion
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

**Common LLM Service Issues**

- Invalid or expired API key
- Rate limiting or quota exhaustion
- Network connectivity issues
- Timeout due to complex queries
- Token limit exceeded for context window

For rate limiting issues, implement exponential backoff and retry logic in the application.

### 2.7 File Storage Diagnostics

Use these procedures to diagnose file storage issues.

**Storage Accessibility**

For local file storage:

```bash
# Check directory permissions
ls -la /path/to/document/storage

# Check disk space
df -h /path/to/document/storage
```

For S3 storage:

```bash
# List buckets
aws s3 ls

# List objects in bucket
aws s3 ls s3://document-management-prod-documents/

# Check bucket permissions
aws s3api get-bucket-policy --bucket document-management-prod-documents
```

**File Integrity**

```bash
# Check file integrity
md5sum /path/to/document/file.pdf

# For S3
aws s3api head-object --bucket document-management-prod-documents --key path/to/file.pdf
```

**Common File Storage Issues**

- Insufficient disk space
- Permission issues
- Corrupted files
- S3 bucket policy restrictions
- Network connectivity issues (for S3)

For S3 issues, also check the AWS CloudTrail logs for access denied events or other errors.

### 2.8 API Layer Diagnostics

Use these procedures to diagnose API layer issues.

**Service Status**

```bash
# Check if service is running
ps aux | grep uvicorn

# For containerized environments
docker ps | grep document-management-api

# For AWS ECS
aws ecs list-tasks --cluster document-management-prod-cluster \
  --service-name document-management-prod-service
```

**Request Testing**

```bash
# Test API endpoint with curl
curl -v http://<api-host>:<port>/api/v1/health/live

# Test authenticated endpoint
curl -v -H "Authorization: Bearer $TOKEN" \
  http://<api-host>:<port>/api/v1/documents/list
```

**Performance Testing**

```bash
# Simple load test with Apache Bench
ab -n 100 -c 10 http://<api-host>:<port>/api/v1/health/live
```

**Common API Layer Issues**

- Service not running or crashing
- Configuration errors
- Authentication failures
- Rate limiting or throttling
- Resource constraints (CPU, memory)
- Dependency failures

Check the API logs for detailed error information and stack traces.

### 2.9 Deployment and Infrastructure Diagnostics

Use these procedures to diagnose deployment and infrastructure issues.

**Deployment Status Verification**

```bash
# Check deployment status in AWS ECS
aws ecs describe-services \
  --cluster document-management-prod-cluster \
  --services document-management-prod-service

# Check deployment status in Kubernetes
kubectl get deployments
kubectl describe deployment document-management-api

# Check container image status
docker image ls | grep document-management
```

**Infrastructure State**

```bash
# Check Terraform state
cd infrastructure/terraform/environments/prod
terraform state list
terraform state show aws_ecs_service.app

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name document-management-prod
```

**Load Balancer Status**

```bash
# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check ALB listener rules
aws elbv2 describe-rules \
  --listener-arn <listener-arn>
```

**Network Configuration**

```bash
# Check security group rules
aws ec2 describe-security-groups \
  --group-ids <security-group-id>

# Check VPC endpoints
aws ec2 describe-vpc-endpoints \
  --filters Name=vpc-id,Values=<vpc-id>
```

**Common Deployment Issues**

- Failed container startup
- Health check failures
- Configuration errors
- Resource constraints
- Networking issues
- Permission or IAM role issues

For deployment failures, check the deployment logs for error messages and consider rolling back to a previous known-good version using the deployment rollback procedures.

### 2.10 Monitoring and Alerting Diagnostics

Use these procedures to diagnose monitoring and alerting issues.

**Prometheus Status**

```bash
# Check Prometheus status
curl http://<prometheus-host>:9090/-/healthy

# Check Prometheus targets
curl http://<prometheus-host>:9090/api/v1/targets | jq
```

**Grafana Status**

```bash
# Check Grafana health
curl http://<grafana-host>:3000/api/health

# Check Grafana datasources
curl -u admin:password http://<grafana-host>:3000/api/datasources
```

**Loki Status**

```bash
# Check Loki status
curl http://<loki-host>:3100/ready

# Test Loki query
curl -G -s "http://<loki-host>:3100/loki/api/v1/query_range" \
  --data-urlencode "query={job=\"api\"}" \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000" \
  --data-urlencode "limit=5" | jq
```

**AlertManager Status**

```bash
# Check AlertManager status
curl http://<alertmanager-host>:9093/-/healthy

# Check active alerts
curl http://<alertmanager-host>:9093/api/v1/alerts | jq
```

**Common Monitoring Issues**

- Missing metrics due to scraping issues
- Alerting delays or failures
- Dashboard rendering problems
- Log collection failures
- Alert notification issues

**Alert Management**

To manage alerts during incident response or maintenance:

```bash
# Silence an alert in AlertManager
curl -X POST http://<alertmanager-host>:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "HighErrorRate", "isRegex": false}
    ],
    "startsAt": "2023-01-01T00:00:00Z",
    "endsAt": "2023-01-01T01:00:00Z",
    "createdBy": "operator",
    "comment": "Maintenance window"
  }'
```

**Incident Response Coordination**

During incident response, use these tools to coordinate activities:

- Create an incident channel in Slack: `#incident-<date>-<brief-description>`
- Start a video conference call for real-time communication
- Assign roles: Incident Commander, Technical Lead, Communications Lead
- Document timeline and actions in a shared document
- Provide regular status updates to stakeholders

## 3. Common Issues and Solutions

This section covers common issues encountered in the system and their solutions.

### 3.1 API and Authentication Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| API Service Unavailable | 503 Service Unavailable, health check fails | Service crashed, resource exhaustion, deployment issue | Check service logs, restart service, check resource usage |
| Authentication Failures | 401 Unauthorized responses | Invalid or expired JWT token, incorrect credentials | Verify token validity, check authentication service logs, ensure correct credentials |
| Rate Limiting | 429 Too Many Requests | Excessive requests, misconfigured rate limits | Implement client-side throttling, adjust rate limits if needed |
| Slow API Response | High latency, timeout errors | Database performance, resource constraints, inefficient queries | Check database performance, optimize queries, scale resources |
| CORS Issues | Browser console errors, blocked requests | Misconfigured CORS settings | Update CORS configuration to allow required origins |

**Authentication Troubleshooting Steps**

1. Verify token format and expiration:
   ```bash
   # Decode JWT token (replace YOUR_TOKEN with actual token)
   echo YOUR_TOKEN | cut -d '.' -f 2 | base64 -d 2>/dev/null | jq
   ```

2. Check for token validation errors in logs:
   ```
   {service="api"} |= "token" |= "invalid"
   ```

3. Verify authentication service is functioning:
   ```bash
   curl -X POST http://<api-host>:<port>/api/v1/auth/token \
     -H "Content-Type: application/json" \
     -d '{"username":"test@example.com","password":"password"}'
   ```

4. If using refresh tokens, try obtaining a new access token:
   ```bash
   curl -X POST http://<api-host>:<port>/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
   ```

### 3.2 Document Processing Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| Document Upload Failure | Error response from upload endpoint | File size too large, invalid format, storage issues | Check file size and format, verify storage access, check upload logs |
| Text Extraction Failure | Document status shows error, no text extracted | Corrupted PDF, unsupported format, PyMuPDF issues | Verify PDF integrity, check document processor logs, try alternative extraction method |
| Vector Generation Failure | Document processing incomplete, no vectors generated | Embedding service issues, resource constraints | Check embedding service logs, verify memory availability, restart embedding service |
| Document Not Found in Search | Search returns no results for known content | Missing vectors, index not updated, search query issues | Verify document was processed successfully, check vector count, rebuild index if necessary |
| Slow Document Processing | Long processing times, timeouts | Large documents, resource constraints, concurrent processing | Optimize chunking parameters, increase resources, limit concurrent processing |

**Document Processing Troubleshooting Steps**

1. Check document status in database:
   ```sql
   SELECT id, title, status, upload_date FROM documents WHERE id = '<document_id>';
   ```

2. Verify document chunks were created:
   ```sql
   SELECT COUNT(*) FROM document_chunks WHERE document_id = '<document_id>';
   ```

3. Check for processing errors in logs:
   ```
   {service="document_processor"} |= "<document_id>" |= "error"
   ```

4. Verify vector embeddings were generated:
   ```bash
   python -m scripts.verify_document_vectors --document-id=<document_id>
   ```

5. For persistent issues, try reprocessing the document:
   ```bash
   python -m scripts.reprocess_document --document-id=<document_id>
   ```

### 3.3 Vector Search Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| Search Returns No Results | Empty results for valid queries | Index corruption, no matching documents, query embedding issues | Verify index integrity, check query embedding generation, rebuild index if necessary |
| Poor Search Relevance | Irrelevant results, low relevance scores | Suboptimal embeddings, index quality issues | Tune similarity threshold, optimize embedding model, rebuild index with better parameters |
| Slow Search Performance | High search latency, timeouts | Large index, inefficient index type, resource constraints | Optimize index type for dataset size, increase resources, implement caching |
| Index Corruption | Search errors, inconsistent results | Disk issues, improper shutdown, concurrent modifications | Restore from backup, rebuild index, implement proper concurrency control |
| Memory Errors | OOM errors, service crashes | Index too large for available memory, memory leaks | Increase memory allocation, optimize index for memory usage, implement index sharding |

**Vector Search Troubleshooting Steps**

1. Check FAISS index integrity:
   ```bash
   python -m scripts.verify_faiss_index
   ```

2. Verify vector count matches document chunks:
   ```bash
   python -m scripts.check_vector_consistency
   ```

3. Test search with a known document:
   ```bash
   python -m scripts.test_vector_search --text="known text from document"
   ```

4. Check memory usage during search:
   ```bash
   watch -n 1 "ps -o pid,user,%mem,command ax | grep faiss"
   ```

5. For persistent issues, rebuild the index:
   ```bash
   ./scripts/rebuild-vector-index.sh --backup
   ```

### 3.4 LLM Integration Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| LLM Service Unavailable | Error responses from query endpoint, health check fails | API key issues, rate limiting, network problems | Verify API key, check rate limits, test direct API connectivity |
| Poor Response Quality | Irrelevant or nonsensical responses | Insufficient context, prompt issues, model limitations | Optimize prompt engineering, provide more context, adjust model parameters |
| Token Limit Exceeded | Error responses, truncated context | Large documents, excessive context | Optimize context selection, reduce context size, implement chunking |
| High Latency | Slow response generation | Complex queries, model performance, network issues | Implement caching, optimize prompt length, use faster models for simple queries |
| Cost Overruns | Excessive API usage, high costs | Inefficient prompts, unnecessary requests, missing caching | Implement caching, optimize token usage, monitor and limit usage |

**LLM Integration Troubleshooting Steps**

1. Verify OpenAI API key:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. Check for rate limiting or quota issues:
   ```
   {service="llm_service"} |= "rate limit" |= "exceeded"
   ```

3. Test basic prompt completion:
   ```bash
   python -m scripts.test_llm_service --prompt="Hello, how are you?"
   ```

4. Check token usage for a query:
   ```bash
   python -m scripts.estimate_token_usage --query="your test query" --documents=3
   ```

5. Implement exponential backoff for rate limiting:
   ```python
   # Pseudocode for retry with exponential backoff
   max_retries = 5
   for attempt in range(max_retries):
       try:
           response = openai.ChatCompletion.create(...)
           break
       except openai.error.RateLimitError:
           if attempt == max_retries - 1:
               raise
           time.sleep(2 ** attempt)
   ```

### 3.5 Database Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| Connection Failures | Database health check fails, connection errors in logs | Network issues, credential problems, database down | Verify network connectivity, check credentials, ensure database is running |
| Connection Pool Exhaustion | Error: "too many clients already", connection timeouts | Connection leaks, insufficient pool size, long-running transactions | Increase pool size, fix connection leaks, optimize transaction duration |
| Slow Queries | High query latency, timeouts | Missing indexes, inefficient queries, table bloat | Add appropriate indexes, optimize queries, perform VACUUM ANALYZE |
| Disk Space Issues | Error: "no space left on device" | Database growth, WAL files, temporary files | Free disk space, archive WAL files, increase storage allocation |
| High CPU Usage | Database performance degradation, high CPU metrics | Inefficient queries, excessive connections, background processes | Optimize queries, limit connections, tune database parameters |

**Database Troubleshooting Steps**

1. Check database connectivity:
   ```bash
   psql -h <db-host> -U <db-user> -d <db-name> -c "SELECT 1;"
   ```

2. Check active connections and states:
   ```sql
   SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
   ```

3. Identify long-running queries:
   ```sql
   SELECT pid, now() - query_start AS duration, query 
   FROM pg_stat_activity 
   WHERE state = 'active' AND now() - query_start > interval '5 seconds' 
   ORDER BY duration DESC;
   ```

4. Check table and index bloat:
   ```sql
   SELECT 
     schemaname, 
     tablename, 
     pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size
   FROM pg_tables
   WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
   ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
   LIMIT 10;
   ```

5. Perform database maintenance:
   ```sql
   VACUUM ANALYZE;
   ```

### 3.6 Resource and Performance Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| High CPU Usage | System slowdown, high CPU metrics | Inefficient code, excessive load, background processes | Optimize code, scale resources, limit concurrent operations |
| Memory Exhaustion | OOM errors, service crashes | Memory leaks, insufficient allocation, large datasets | Increase memory allocation, fix memory leaks, optimize memory usage |
| Disk Space Issues | No space errors, write failures | Log accumulation, temporary files, database growth | Free disk space, implement log rotation, increase storage allocation |
| Network Bottlenecks | High latency, timeout errors | Bandwidth limitations, network congestion, DNS issues | Optimize network usage, increase bandwidth, resolve DNS issues |
| Container Resource Limits | Service throttling, OOM kills | Insufficient container resources, resource contention | Increase container resource limits, optimize resource usage |

**Resource Troubleshooting Steps**

1. Check system resource usage:
   ```bash
   # CPU and memory usage
   top
   
   # Disk usage
   df -h
   
   # I/O statistics
   iostat -x 1
   ```

2. Check container resource usage:
   ```bash
   # Docker stats
   docker stats
   
   # For Kubernetes
   kubectl top pods
   ```

3. Check for memory leaks:
   ```bash
   # Monitor memory usage over time
   ps -o pid,user,%mem,rss,command ax | grep python
   ```

4. Check network connectivity and latency:
   ```bash
   # Network connectivity
   ping <host>
   
   # Network latency
   traceroute <host>
   ```

5. Optimize resource allocation:
   ```bash
   # Update container resource limits
   docker update --cpu=2 --memory=4g document-management-api
   ```

### 3.7 Monitoring and Alerting Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| Missing Metrics | Blank dashboards, no data in Grafana | Prometheus configuration, scraping issues, exporter problems | Check Prometheus configuration, verify exporters, check connectivity |
| Missing Logs | No logs in Loki, incomplete log data | Promtail configuration, log shipping issues | Check Promtail configuration, verify log sources, check connectivity |
| False Positive Alerts | Excessive alerts, alerts for normal conditions | Inappropriate thresholds, noisy metrics | Adjust alert thresholds, add better conditions, implement alert grouping |
| Missed Alerts | Issues not detected, no alerts for problems | Missing alert rules, inappropriate thresholds | Add comprehensive alert rules, adjust thresholds, test alert conditions |
| Alert Notification Failures | Alerts not delivered, notification delays | Notification channel issues, configuration problems | Verify notification channels, check AlertManager configuration |

**Monitoring Troubleshooting Steps**

1. Check Prometheus targets:
   ```bash
   curl http://<prometheus-host>:9090/api/v1/targets | jq
   ```

2. Verify Loki is receiving logs:
   ```bash
   curl -G -s "http://<loki-host>:3100/loki/api/v1/query_range" \
     --data-urlencode "query={job=\"api\"}" \
     --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
     --data-urlencode "end=$(date +%s)000000000" \
     --data-urlencode "limit=5" | jq
   ```

3. Check AlertManager configuration:
   ```bash
   curl http://<alertmanager-host>:9093/api/v1/status | jq
   ```

4. Test alert notification channels:
   ```bash
   ./scripts/test-alerts.sh
   ```

5. Review alert rules and thresholds:
   ```bash
   curl http://<prometheus-host>:9090/api/v1/rules | jq
   ```

### 3.8 Deployment and Infrastructure Issues

| Issue | Symptoms | Possible Causes | Resolution |
| --- | --- | --- | --- |
| Deployment Failures | CI/CD pipeline errors, failed deployments | Build errors, configuration issues, resource constraints | Check build logs, verify configuration, ensure sufficient resources |
| Container Startup Failures | Containers exit immediately, health check failures | Missing dependencies, configuration errors, permission issues | Check container logs, verify configuration, fix permission issues |
| Infrastructure Provisioning Failures | Terraform errors, CloudFormation failures | Permission issues, resource constraints, configuration errors | Check IAM permissions, verify resource availability, fix configuration |
| Service Discovery Issues | Services unable to find each other, connection failures | DNS issues, network configuration, service registration problems | Verify DNS resolution, check network configuration, ensure proper service registration |
| Load Balancer Issues | Traffic not reaching services, health check failures | Health check configuration, target group issues, network ACLs | Verify health check configuration, check target group status, review network ACLs |

**Deployment Troubleshooting Steps**

1. Check deployment logs:
   ```bash
   # GitHub Actions logs
   # Access through GitHub UI
   
   # AWS CloudFormation events
   aws cloudformation describe-stack-events \
     --stack-name document-management-prod
   ```

2. Verify container status:
   ```bash
   # Docker container status
   docker ps -a | grep document-management
   
   # ECS task status
   aws ecs describe-tasks \
     --cluster document-management-prod-cluster \
     --tasks <task-id>
   ```

3. Check infrastructure state:
   ```bash
   # Terraform state
   cd infrastructure/terraform/environments/prod
   terraform state list
   terraform state show aws_ecs_service.app
   ```

4. Verify load balancer configuration:
   ```bash
   # ALB target group health
   aws elbv2 describe-target-health \
     --target-group-arn <target-group-arn>
   ```

5. For failed deployments, implement a rollback procedure:
   ```bash
   # Manual rollback script
   ./scripts/rollback.sh --environment=production --version=<previous-version>
   ```

6. Check for deployment configuration issues:
   ```bash
   # Review ECS service configuration
   aws ecs describe-services --cluster document-management-prod-cluster \
     --services document-management-prod-service
   
   # Check task definition
   aws ecs describe-task-definition \
     --task-definition document-management-prod:1
   ```

7. Verify environment variables and secrets:
   ```bash
   # Check environment variables in container
   docker exec document-management-api env
   
   # Verify secrets exist in AWS Secrets Manager
   aws secretsmanager list-secrets | grep document-management
   ```

## 4. Runbooks

This section provides detailed runbooks for specific issue scenarios.

### 4.1 API Performance Degradation

**Symptoms**
- Increased API response times
- Timeout errors
- High error rates
- Degraded user experience

**Diagnostic Steps**

1. **Verify the issue**
   ```bash
   # Check API response time
   time curl -s http://<api-host>:<port>/api/v1/health/live
   
   # Check error rate in Prometheus
   curl -s "http://<prometheus-host>:9090/api/v1/query?query=sum(rate(http_requests_total{job='api',status~='5..'}[5m]))/sum(rate(http_requests_total{job='api'}[5m]))"
   ```

2. **Check system resources**
   ```bash
   # CPU and memory usage
   docker stats
   
   # For AWS resources, check CloudWatch metrics
   aws cloudwatch get-metric-statistics \
     --namespace AWS/ECS \
     --metric-name CPUUtilization \
     --dimensions Name=ServiceName,Value=document-management-prod-service Name=ClusterName,Value=document-management-prod-cluster \
     --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Average
   ```

3. **Check database performance**