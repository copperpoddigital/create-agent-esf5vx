#!/bin/bash
# monitor-performance.sh - Performance monitoring script for Document Management and AI Chatbot System
# This script collects and reports on system performance metrics including API response times,
# database performance, vector search latency, and resource utilization.

# Global variables
API_URL="http://localhost:8000"
INTERVAL="60"  # Default interval in seconds
DURATION="3600"  # Default duration in seconds (1 hour)
OUTPUT_FILE=""
VERBOSE="false"
TEST_ENDPOINTS=( "/health/live" "/health/ready" "/health/dependencies" "/documents/list?limit=10" "/query/recent?limit=5" )
METRICS=()

# Displays script usage information
print_usage() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "Monitor and report performance metrics for the Document Management and AI Chatbot System."
    echo ""
    echo "Options:"
    echo "  -u, --url URL           API URL to monitor (default: http://localhost:8000)"
    echo "  -i, --interval SECONDS  Monitoring interval in seconds (default: 60)"
    echo "  -d, --duration SECONDS  Total monitoring duration in seconds (default: 3600)"
    echo "  -o, --output FILE       Output file for metrics (default: stdout only)"
    echo "  -v, --verbose           Enable verbose output"
    echo "  -h, --help              Display this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0") -u http://api.example.com -i 30 -d 1800 -o metrics.json"
    echo "  $(basename "$0") --verbose --duration 600"
}

# Parses command line arguments
parse_arguments() {
    # Process command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--url)
                API_URL="$2"
                shift 2
                ;;
            -i|--interval)
                INTERVAL="$2"
                shift 2
                ;;
            -d|--duration)
                DURATION="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE="true"
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                echo "Error: Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Validate arguments
    if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
        echo "Error: Interval must be a positive integer"
        exit 1
    fi
    
    if ! [[ "$DURATION" =~ ^[0-9]+$ ]]; then
        echo "Error: Duration must be a positive integer"
        exit 1
    fi
    
    if [[ -z "$API_URL" ]]; then
        echo "Error: API URL cannot be empty"
        exit 1
    fi
}

# Checks if required dependencies are installed
check_dependencies() {
    local missing_deps=0
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo "Error: 'curl' is required but not installed"
        missing_deps=1
    fi
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        echo "Error: 'jq' is required but not installed"
        missing_deps=1
    fi
    
    # Check for bc
    if ! command -v bc &> /dev/null; then
        echo "Error: 'bc' is required but not installed"
        missing_deps=1
    fi
    
    return $missing_deps
}

# Measures performance metrics for a specific API endpoint
measure_endpoint_performance() {
    local endpoint="$1"
    local full_url="${API_URL}${endpoint}"
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Measuring performance for endpoint: $endpoint"
    fi
    
    # Use curl to measure response time
    local response
    local http_code
    local time_total
    local size
    
    # Create a temporary file for the response
    local tmp_file
    tmp_file=$(mktemp)
    
    # Perform the request and measure timing
    response=$(curl -s -w "%{http_code},%{time_total},%{size_download}\n" -o "$tmp_file" "$full_url" 2>/dev/null)
    
    # Extract metrics from response
    http_code=$(echo "$response" | cut -d',' -f1)
    time_total=$(echo "$response" | cut -d',' -f2)
    size=$(echo "$response" | cut -d',' -f3)
    
    # Clean up temporary file
    rm -f "$tmp_file"
    
    # Return metrics
    echo "endpoint=$endpoint,status=$http_code,time=$time_total,size=$size"
}

# Collects system-level metrics like CPU, memory, and disk usage
collect_system_metrics() {
    # CPU usage
    local cpu_usage
    if command -v mpstat &> /dev/null; then
        # Use mpstat if available
        cpu_usage=$(mpstat 1 1 | grep "Average" | awk '{print 100 - $NF}')
    else
        # Fallback to top
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    fi
    
    # Memory usage
    local mem_total
    local mem_used
    local mem_usage
    mem_total=$(free -m | awk '/^Mem:/{print $2}')
    mem_used=$(free -m | awk '/^Mem:/{print $3}')
    mem_usage=$(echo "scale=2; $mem_used * 100 / $mem_total" | bc)
    
    # Disk usage
    local disk_usage
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # Return metrics
    echo "cpu=$cpu_usage,memory=$mem_usage,disk=$disk_usage"
}

# Collects database performance metrics if accessible
collect_database_metrics() {
    local db_metrics_endpoint="${API_URL}/health/database"
    local metrics
    
    # Try to access database metrics endpoint
    local response
    response=$(curl -s -o - "$db_metrics_endpoint" 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$response" ]]; then
        # Extract metrics if available
        local connection_count
        local active_queries
        local query_time
        
        # Parse the JSON response using jq
        connection_count=$(echo "$response" | jq -r '.connections.active // "N/A"')
        active_queries=$(echo "$response" | jq -r '.queries.active // "N/A"')
        query_time=$(echo "$response" | jq -r '.performance.avg_query_time // "N/A"')
        
        metrics="connections=$connection_count,active_queries=$active_queries,avg_query_time=$query_time"
    else
        # Return empty metrics if endpoint is not available
        metrics="connections=N/A,active_queries=N/A,avg_query_time=N/A"
    fi
    
    echo "$metrics"
}

# Collects vector search performance metrics
collect_vector_search_metrics() {
    local vector_metrics_endpoint="${API_URL}/health/vector-search"
    local metrics
    
    # Try to access vector search metrics endpoint
    local response
    response=$(curl -s -o - "$vector_metrics_endpoint" 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$response" ]]; then
        # Extract metrics if available
        local search_latency
        local index_size
        local query_count
        
        # Parse the JSON response using jq
        search_latency=$(echo "$response" | jq -r '.latency.avg_search_time // "N/A"')
        index_size=$(echo "$response" | jq -r '.index.size_mb // "N/A"')
        query_count=$(echo "$response" | jq -r '.queries.count // "N/A"')
        
        metrics="search_latency=$search_latency,index_size=$index_size,query_count=$query_count"
    else
        # Return empty metrics if endpoint is not available
        metrics="search_latency=N/A,index_size=N/A,query_count=N/A"
    fi
    
    echo "$metrics"
}

# Collects LLM service performance metrics
collect_llm_metrics() {
    local llm_metrics_endpoint="${API_URL}/health/llm"
    local metrics
    
    # Try to access LLM metrics endpoint
    local response
    response=$(curl -s -o - "$llm_metrics_endpoint" 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$response" ]]; then
        # Extract metrics if available
        local response_time
        local token_usage
        local cache_hit_ratio
        
        # Parse the JSON response using jq
        response_time=$(echo "$response" | jq -r '.performance.avg_response_time // "N/A"')
        token_usage=$(echo "$response" | jq -r '.usage.avg_tokens // "N/A"')
        cache_hit_ratio=$(echo "$response" | jq -r '.cache.hit_ratio // "N/A"')
        
        metrics="response_time=$response_time,token_usage=$token_usage,cache_hit_ratio=$cache_hit_ratio"
    else
        # Return empty metrics if endpoint is not available
        metrics="response_time=N/A,token_usage=N/A,cache_hit_ratio=N/A"
    fi
    
    echo "$metrics"
}

# Calculates statistical values from collected metrics
calculate_statistics() {
    local -a values=("$@")
    local metrics
    
    # Skip calculation if no values are provided
    if [[ ${#values[@]} -eq 0 ]]; then
        echo "min=N/A,max=N/A,avg=N/A,median=N/A,p95=N/A"
        return 0
    fi
    
    # Sort the values
    IFS=$'\n' sorted=($(sort -n <<<"${values[*]}"))
    unset IFS
    
    # Calculate min and max
    local min="${sorted[0]}"
    local max="${sorted[${#sorted[@]}-1]}"
    
    # Calculate average
    local sum=0
    for value in "${sorted[@]}"; do
        sum=$(echo "$sum + $value" | bc -l)
    done
    local avg=$(echo "scale=3; $sum / ${#sorted[@]}" | bc -l)
    
    # Calculate median
    local median
    local mid=$((${#sorted[@]} / 2))
    if (( ${#sorted[@]} % 2 == 0 )); then
        # Even number of elements
        median=$(echo "scale=3; (${sorted[$mid-1]} + ${sorted[$mid]}) / 2" | bc -l)
    else
        # Odd number of elements
        median="${sorted[$mid]}"
    fi
    
    # Calculate 95th percentile
    local p95_index=$(echo "scale=0; ${#sorted[@]} * 0.95 - 1" | bc -l | awk '{printf "%d", $1+0.5}')
    local p95="${sorted[$p95_index]}"
    
    metrics="min=$min,max=$max,avg=$avg,median=$median,p95=$p95"
    echo "$metrics"
}

# Formats metrics for display or output to file
format_output() {
    local -a metrics=("$@")
    local format="${2:-text}"
    
    # Determine format based on OUTPUT_FILE extension if format not specified
    if [[ -z "$format" && -n "$OUTPUT_FILE" ]]; then
        if [[ "$OUTPUT_FILE" == *.json ]]; then
            format="json"
        elif [[ "$OUTPUT_FILE" == *.csv ]]; then
            format="csv"
        else
            format="text"
        fi
    fi
    
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local output=""
    
    case "$format" in
        json)
            # Format as JSON
            output="{\n"
            output+="  \"timestamp\": \"$timestamp\",\n"
            output+="  \"metrics\": [\n"
            
            # Add metrics entries as JSON
            for (( i=0; i<${#metrics[@]}; i++ )); do
                local metric="${metrics[$i]}"
                output+="    {"
                
                # Convert comma-separated metrics to JSON
                local json_metric
                json_metric=$(echo "$metric" | sed 's/\([^=]*\)=\([^,]*\)/"\1":"\2"/g' | sed 's/,/,"/g' | sed 's/,"/","/g')
                
                output+="$json_metric"
                
                if (( i < ${#metrics[@]} - 1 )); then
                    output+="},\n"
                else
                    output+="}\n"
                fi
            done
            
            output+="  ]\n"
            output+="}"
            ;;
        csv)
            # Format as CSV
            # Headers
            output="timestamp,endpoint,status,response_time,size,cpu,memory,disk,"
            output+="db_connections,db_active_queries,db_avg_query_time,"
            output+="search_latency,index_size,query_count,"
            output+="llm_response_time,llm_token_usage,llm_cache_hit_ratio\n"
            
            # Data rows
            for metric in "${metrics[@]}"; do
                # Extract values from metric string and format as CSV
                if [[ "$metric" == *"endpoint="* ]]; then
                    local endpoint=$(echo "$metric" | grep -o "endpoint=[^,]*" | cut -d= -f2)
                    local status=$(echo "$metric" | grep -o "status=[^,]*" | cut -d= -f2)
                    local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
                    local size=$(echo "$metric" | grep -o "size=[^,]*" | cut -d= -f2)
                    
                    output+="$timestamp,$endpoint,$status,$time,$size,,,,,,,,,,,\n"
                elif [[ "$metric" == *"cpu="* ]]; then
                    local cpu=$(echo "$metric" | grep -o "cpu=[^,]*" | cut -d= -f2)
                    local memory=$(echo "$metric" | grep -o "memory=[^,]*" | cut -d= -f2)
                    local disk=$(echo "$metric" | grep -o "disk=[^,]*" | cut -d= -f2)
                    
                    output+="$timestamp,,,,,$cpu,$memory,$disk,,,,,,,,\n"
                fi
            done
            ;;
        text|*)
            # Format as human-readable text
            output="Performance Metrics Report - $timestamp\n"
            output+="======================================\n\n"
            
            # Group metrics by type
            local endpoint_metrics=""
            local system_metrics=""
            local db_metrics=""
            local vector_metrics=""
            local llm_metrics=""
            local stats_metrics=""
            
            for metric in "${metrics[@]}"; do
                if [[ "$metric" == *"endpoint="* ]]; then
                    # Format endpoint metrics
                    local endpoint=$(echo "$metric" | grep -o "endpoint=[^,]*" | cut -d= -f2)
                    local status=$(echo "$metric" | grep -o "status=[^,]*" | cut -d= -f2)
                    local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
                    local size=$(echo "$metric" | grep -o "size=[^,]*" | cut -d= -f2)
                    
                    endpoint_metrics+="$endpoint: Status=$status, Time=${time}s, Size=${size}B\n"
                elif [[ "$metric" == *"cpu="* ]]; then
                    # Format system metrics
                    local cpu=$(echo "$metric" | grep -o "cpu=[^,]*" | cut -d= -f2)
                    local memory=$(echo "$metric" | grep -o "memory=[^,]*" | cut -d= -f2)
                    local disk=$(echo "$metric" | grep -o "disk=[^,]*" | cut -d= -f2)
                    
                    system_metrics="CPU Usage: ${cpu}%, Memory Usage: ${memory}%, Disk Usage: ${disk}%\n"
                elif [[ "$metric" == *"connections="* ]]; then
                    # Format database metrics
                    local connections=$(echo "$metric" | grep -o "connections=[^,]*" | cut -d= -f2)
                    local active_queries=$(echo "$metric" | grep -o "active_queries=[^,]*" | cut -d= -f2)
                    local query_time=$(echo "$metric" | grep -o "avg_query_time=[^,]*" | cut -d= -f2)
                    
                    db_metrics="Active Connections: $connections, Active Queries: $active_queries, Avg Query Time: ${query_time}s\n"
                elif [[ "$metric" == *"search_latency="* ]]; then
                    # Format vector search metrics
                    local search_latency=$(echo "$metric" | grep -o "search_latency=[^,]*" | cut -d= -f2)
                    local index_size=$(echo "$metric" | grep -o "index_size=[^,]*" | cut -d= -f2)
                    local query_count=$(echo "$metric" | grep -o "query_count=[^,]*" | cut -d= -f2)
                    
                    vector_metrics="Search Latency: ${search_latency}s, Index Size: ${index_size}MB, Query Count: $query_count\n"
                elif [[ "$metric" == *"response_time="* ]]; then
                    # Format LLM metrics
                    local response_time=$(echo "$metric" | grep -o "response_time=[^,]*" | cut -d= -f2)
                    local token_usage=$(echo "$metric" | grep -o "token_usage=[^,]*" | cut -d= -f2)
                    local cache_hit_ratio=$(echo "$metric" | grep -o "cache_hit_ratio=[^,]*" | cut -d= -f2)
                    
                    llm_metrics="Response Time: ${response_time}s, Avg Token Usage: $token_usage, Cache Hit Ratio: $cache_hit_ratio\n"
                elif [[ "$metric" == *"min="* ]]; then
                    # Format statistics metrics
                    local min=$(echo "$metric" | grep -o "min=[^,]*" | cut -d= -f2)
                    local max=$(echo "$metric" | grep -o "max=[^,]*" | cut -d= -f2)
                    local avg=$(echo "$metric" | grep -o "avg=[^,]*" | cut -d= -f2)
                    local median=$(echo "$metric" | grep -o "median=[^,]*" | cut -d= -f2)
                    local p95=$(echo "$metric" | grep -o "p95=[^,]*" | cut -d= -f2)
                    
                    stats_metrics="Min: ${min}s, Max: ${max}s, Avg: ${avg}s, Median: ${median}s, 95th Percentile: ${p95}s\n"
                fi
            done
            
            # Add formatted sections to output
            output+="API Endpoint Performance:\n$endpoint_metrics\n"
            output+="System Metrics:\n$system_metrics\n"
            output+="Database Metrics:\n$db_metrics\n"
            output+="Vector Search Metrics:\n$vector_metrics\n"
            output+="LLM Metrics:\n$llm_metrics\n"
            output+="Response Time Statistics:\n$stats_metrics\n"
            ;;
    esac
    
    echo -e "$output"
}

# Checks if performance metrics comply with defined SLAs
check_sla_compliance() {
    local -a metrics=("$@")
    local compliance=""
    
    # Define SLA thresholds based on technical specifications
    local api_warning=1.0       # API response time warning threshold (seconds)
    local api_critical=3.0      # API response time critical threshold (seconds)
    local search_warning=0.5    # Vector search latency warning threshold (seconds)
    local search_critical=2.0   # Vector search latency critical threshold (seconds)
    local llm_warning=2.0       # LLM response time warning threshold (seconds)
    local llm_critical=5.0      # LLM response time critical threshold (seconds)
    local db_warning=0.2        # Database query time warning threshold (seconds)
    local db_critical=1.0       # Database query time critical threshold (seconds)
    
    # Initialize counters
    local api_compliant=0
    local api_total=0
    local search_compliant=0
    local search_total=0
    local llm_compliant=0
    local llm_total=0
    local db_compliant=0
    local db_total=0
    
    # Check metrics against SLA thresholds
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"endpoint="* && "$metric" == *"time="* ]]; then
            # Check API response time
            local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
            
            (( api_total++ ))
            if (( $(echo "$time <= $api_warning" | bc -l) )); then
                (( api_compliant++ ))
            fi
        elif [[ "$metric" == *"search_latency="* ]]; then
            # Check vector search latency
            local latency=$(echo "$metric" | grep -o "search_latency=[^,]*" | cut -d= -f2)
            
            if [[ "$latency" != "N/A" ]]; then
                (( search_total++ ))
                if (( $(echo "$latency <= $search_warning" | bc -l) )); then
                    (( search_compliant++ ))
                fi
            fi
        elif [[ "$metric" == *"response_time="* ]]; then
            # Check LLM response time
            local response_time=$(echo "$metric" | grep -o "response_time=[^,]*" | cut -d= -f2)
            
            if [[ "$response_time" != "N/A" ]]; then
                (( llm_total++ ))
                if (( $(echo "$response_time <= $llm_warning" | bc -l) )); then
                    (( llm_compliant++ ))
                fi
            fi
        elif [[ "$metric" == *"avg_query_time="* ]]; then
            # Check database query time
            local query_time=$(echo "$metric" | grep -o "avg_query_time=[^,]*" | cut -d= -f2)
            
            if [[ "$query_time" != "N/A" ]]; then
                (( db_total++ ))
                if (( $(echo "$query_time <= $db_warning" | bc -l) )); then
                    (( db_compliant++ ))
                fi
            fi
        fi
    done
    
    # Calculate compliance percentages
    local api_compliance="N/A"
    local search_compliance="N/A"
    local llm_compliance="N/A"
    local db_compliance="N/A"
    
    if (( api_total > 0 )); then
        api_compliance=$(echo "scale=1; $api_compliant * 100 / $api_total" | bc -l)
    fi
    
    if (( search_total > 0 )); then
        search_compliance=$(echo "scale=1; $search_compliant * 100 / $search_total" | bc -l)
    fi
    
    if (( llm_total > 0 )); then
        llm_compliance=$(echo "scale=1; $llm_compliant * 100 / $llm_total" | bc -l)
    fi
    
    if (( db_total > 0 )); then
        db_compliance=$(echo "scale=1; $db_compliant * 100 / $db_total" | bc -l)
    fi
    
    # Calculate overall compliance
    local total_compliant=$((api_compliant + search_compliant + llm_compliant + db_compliant))
    local total_metrics=$((api_total + search_total + llm_total + db_total))
    local overall_compliance="N/A"
    
    if (( total_metrics > 0 )); then
        overall_compliance=$(echo "scale=1; $total_compliant * 100 / $total_metrics" | bc -l)
    fi
    
    compliance="api=$api_compliance%,search=$search_compliance%,llm=$llm_compliance%,db=$db_compliance%,overall=$overall_compliance%"
    echo "$compliance"
}

# Displays collected metrics to stdout with formatting
display_metrics() {
    local -a metrics=("$@")
    local sla_compliance=$(check_sla_compliance "${metrics[@]}")
    
    # ANSI color codes
    local RED='\033[0;31m'
    local YELLOW='\033[0;33m'
    local GREEN='\033[0;32m'
    local NC='\033[0m' # No Color
    
    echo "============================================="
    echo "Performance Monitoring - $(date)"
    echo "API URL: $API_URL"
    echo "============================================="
    
    # Extract SLA compliance values
    local api_compliance=$(echo "$sla_compliance" | grep -o "api=[^,]*" | cut -d= -f2)
    local search_compliance=$(echo "$sla_compliance" | grep -o "search=[^,]*" | cut -d= -f2)
    local llm_compliance=$(echo "$sla_compliance" | grep -o "llm=[^,]*" | cut -d= -f2)
    local db_compliance=$(echo "$sla_compliance" | grep -o "db=[^,]*" | cut -d= -f2)
    local overall_compliance=$(echo "$sla_compliance" | grep -o "overall=[^,]*" | cut -d= -f2)
    
    # Display API endpoint performance metrics
    echo -e "\nAPI Endpoint Performance:"
    echo "--------------------------------------------"
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"endpoint="* ]]; then
            local endpoint=$(echo "$metric" | grep -o "endpoint=[^,]*" | cut -d= -f2)
            local status=$(echo "$metric" | grep -o "status=[^,]*" | cut -d= -f2)
            local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
            local size=$(echo "$metric" | grep -o "size=[^,]*" | cut -d= -f2)
            
            # Color code based on response time
            local color=$GREEN
            if (( $(echo "$time > 3.0" | bc -l) )); then
                color=$RED
            elif (( $(echo "$time > 1.0" | bc -l) )); then
                color=$YELLOW
            fi
            
            echo -e "Endpoint: $endpoint, Status: $status, Time: ${color}${time}s${NC}, Size: ${size}B"
        fi
    done
    
    # Display system resource utilization metrics
    echo -e "\nSystem Resource Utilization:"
    echo "--------------------------------------------"
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"cpu="* ]]; then
            local cpu=$(echo "$metric" | grep -o "cpu=[^,]*" | cut -d= -f2)
            local memory=$(echo "$metric" | grep -o "memory=[^,]*" | cut -d= -f2)
            local disk=$(echo "$metric" | grep -o "disk=[^,]*" | cut -d= -f2)
            
            # Color code based on utilization
            local cpu_color=$GREEN
            local mem_color=$GREEN
            local disk_color=$GREEN
            
            if (( $(echo "$cpu > 85" | bc -l) )); then
                cpu_color=$RED
            elif (( $(echo "$cpu > 70" | bc -l) )); then
                cpu_color=$YELLOW
            fi
            
            if (( $(echo "$memory > 90" | bc -l) )); then
                mem_color=$RED
            elif (( $(echo "$memory > 75" | bc -l) )); then
                mem_color=$YELLOW
            fi
            
            if (( $(echo "$disk > 90" | bc -l) )); then
                disk_color=$RED
            elif (( $(echo "$disk > 80" | bc -l) )); then
                disk_color=$YELLOW
            fi
            
            echo -e "CPU Usage: ${cpu_color}${cpu}%${NC}, Memory Usage: ${mem_color}${memory}%${NC}, Disk Usage: ${disk_color}${disk}%${NC}"
        fi
    done
    
    # Display database performance metrics if available
    echo -e "\nDatabase Performance:"
    echo "--------------------------------------------"
    local db_found=false
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"connections="* ]]; then
            local connections=$(echo "$metric" | grep -o "connections=[^,]*" | cut -d= -f2)
            local active_queries=$(echo "$metric" | grep -o "active_queries=[^,]*" | cut -d= -f2)
            local query_time=$(echo "$metric" | grep -o "avg_query_time=[^,]*" | cut -d= -f2)
            
            # Color code based on query time
            local time_color=$GREEN
            if [[ "$query_time" != "N/A" ]]; then
                if (( $(echo "$query_time > 1.0" | bc -l) )); then
                    time_color=$RED
                elif (( $(echo "$query_time > 0.2" | bc -l) )); then
                    time_color=$YELLOW
                fi
            fi
            
            echo -e "Active Connections: $connections, Active Queries: $active_queries, Avg Query Time: ${time_color}${query_time}s${NC}"
            db_found=true
        fi
    done
    
    if [[ "$db_found" == "false" ]]; then
        echo "Database metrics not available"
    fi
    
    # Display vector search metrics if available
    echo -e "\nVector Search Performance:"
    echo "--------------------------------------------"
    local vector_found=false
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"search_latency="* ]]; then
            local search_latency=$(echo "$metric" | grep -o "search_latency=[^,]*" | cut -d= -f2)
            local index_size=$(echo "$metric" | grep -o "index_size=[^,]*" | cut -d= -f2)
            local query_count=$(echo "$metric" | grep -o "query_count=[^,]*" | cut -d= -f2)
            
            # Color code based on search latency
            local latency_color=$GREEN
            if [[ "$search_latency" != "N/A" ]]; then
                if (( $(echo "$search_latency > 2.0" | bc -l) )); then
                    latency_color=$RED
                elif (( $(echo "$search_latency > 0.5" | bc -l) )); then
                    latency_color=$YELLOW
                fi
            fi
            
            echo -e "Search Latency: ${latency_color}${search_latency}s${NC}, Index Size: ${index_size}MB, Query Count: $query_count"
            vector_found=true
        fi
    done
    
    if [[ "$vector_found" == "false" ]]; then
        echo "Vector search metrics not available"
    fi
    
    # Display LLM metrics if available
    echo -e "\nLLM Service Performance:"
    echo "--------------------------------------------"
    local llm_found=false
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"response_time="* ]]; then
            local response_time=$(echo "$metric" | grep -o "response_time=[^,]*" | cut -d= -f2)
            local token_usage=$(echo "$metric" | grep -o "token_usage=[^,]*" | cut -d= -f2)
            local cache_hit_ratio=$(echo "$metric" | grep -o "cache_hit_ratio=[^,]*" | cut -d= -f2)
            
            # Color code based on response time
            local time_color=$GREEN
            if [[ "$response_time" != "N/A" ]]; then
                if (( $(echo "$response_time > 5.0" | bc -l) )); then
                    time_color=$RED
                elif (( $(echo "$response_time > 2.0" | bc -l) )); then
                    time_color=$YELLOW
                fi
            fi
            
            echo -e "Response Time: ${time_color}${response_time}s${NC}, Avg Token Usage: $token_usage, Cache Hit Ratio: $cache_hit_ratio"
            llm_found=true
        fi
    done
    
    if [[ "$llm_found" == "false" ]]; then
        echo "LLM service metrics not available"
    fi
    
    # Display response time statistics if available
    echo -e "\nResponse Time Statistics:"
    echo "--------------------------------------------"
    local stats_found=false
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"min="* ]]; then
            local min=$(echo "$metric" | grep -o "min=[^,]*" | cut -d= -f2)
            local max=$(echo "$metric" | grep -o "max=[^,]*" | cut -d= -f2)
            local avg=$(echo "$metric" | grep -o "avg=[^,]*" | cut -d= -f2)
            local median=$(echo "$metric" | grep -o "median=[^,]*" | cut -d= -f2)
            local p95=$(echo "$metric" | grep -o "p95=[^,]*" | cut -d= -f2)
            
            # Color code based on average response time
            local avg_color=$GREEN
            if (( $(echo "$avg > 3.0" | bc -l) )); then
                avg_color=$RED
            elif (( $(echo "$avg > 1.0" | bc -l) )); then
                avg_color=$YELLOW
            fi
            
            local p95_color=$GREEN
            if (( $(echo "$p95 > 3.0" | bc -l) )); then
                p95_color=$RED
            elif (( $(echo "$p95 > 1.0" | bc -l) )); then
                p95_color=$YELLOW
            fi
            
            echo -e "Min: ${min}s, Max: ${max}s, Avg: ${avg_color}${avg}s${NC}, Median: ${median}s, 95th Percentile: ${p95_color}${p95}s${NC}"
            stats_found=true
        fi
    done
    
    if [[ "$stats_found" == "false" ]]; then
        echo "Response time statistics not available"
    fi
    
    # Display SLA compliance summary
    echo -e "\nSLA Compliance Summary:"
    echo "--------------------------------------------"
    
    # Color code compliance percentages
    local api_color=$GREEN
    local search_color=$GREEN
    local llm_color=$GREEN
    local db_color=$GREEN
    local overall_color=$GREEN
    
    if [[ "$api_compliance" != "N/A" && $(echo "$api_compliance < 90" | bc -l) -eq 1 ]]; then
        api_color=$YELLOW
        if [[ $(echo "$api_compliance < 80" | bc -l) -eq 1 ]]; then
            api_color=$RED
        fi
    fi
    
    if [[ "$search_compliance" != "N/A" && $(echo "$search_compliance < 90" | bc -l) -eq 1 ]]; then
        search_color=$YELLOW
        if [[ $(echo "$search_compliance < 80" | bc -l) -eq 1 ]]; then
            search_color=$RED
        fi
    fi
    
    if [[ "$llm_compliance" != "N/A" && $(echo "$llm_compliance < 90" | bc -l) -eq 1 ]]; then
        llm_color=$YELLOW
        if [[ $(echo "$llm_compliance < 80" | bc -l) -eq 1 ]]; then
            llm_color=$RED
        fi
    fi
    
    if [[ "$db_compliance" != "N/A" && $(echo "$db_compliance < 90" | bc -l) -eq 1 ]]; then
        db_color=$YELLOW
        if [[ $(echo "$db_compliance < 80" | bc -l) -eq 1 ]]; then
            db_color=$RED
        fi
    fi
    
    if [[ "$overall_compliance" != "N/A" && $(echo "$overall_compliance < 90" | bc -l) -eq 1 ]]; then
        overall_color=$YELLOW
        if [[ $(echo "$overall_compliance < 80" | bc -l) -eq 1 ]]; then
            overall_color=$RED
        fi
    fi
    
    echo -e "API Response Time: ${api_color}${api_compliance}${NC}"
    echo -e "Vector Search Latency: ${search_color}${search_compliance}${NC}"
    echo -e "LLM Response Time: ${llm_color}${llm_compliance}${NC}"
    echo -e "Database Query Time: ${db_color}${db_compliance}${NC}"
    echo -e "Overall Compliance: ${overall_color}${overall_compliance}${NC}"
    
    # Display warnings and critical alerts
    echo -e "\nAlerts:"
    echo "--------------------------------------------"
    local has_alerts=0
    
    # Check for critical alerts
    for metric in "${metrics[@]}"; do
        if [[ "$metric" == *"endpoint="* && "$metric" == *"time="* ]]; then
            local endpoint=$(echo "$metric" | grep -o "endpoint=[^,]*" | cut -d= -f2)
            local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
            
            if (( $(echo "$time > 3.0" | bc -l) )); then
                echo -e "${RED}CRITICAL:${NC} API endpoint $endpoint response time (${time}s) exceeds critical threshold (3.0s)"
                has_alerts=1
            elif (( $(echo "$time > 1.0" | bc -l) )); then
                echo -e "${YELLOW}WARNING:${NC} API endpoint $endpoint response time (${time}s) exceeds warning threshold (1.0s)"
                has_alerts=1
            fi
        elif [[ "$metric" == *"search_latency="* ]]; then
            local latency=$(echo "$metric" | grep -o "search_latency=[^,]*" | cut -d= -f2)
            
            if [[ "$latency" != "N/A" ]]; then
                if (( $(echo "$latency > 2.0" | bc -l) )); then
                    echo -e "${RED}CRITICAL:${NC} Vector search latency (${latency}s) exceeds critical threshold (2.0s)"
                    has_alerts=1
                elif (( $(echo "$latency > 0.5" | bc -l) )); then
                    echo -e "${YELLOW}WARNING:${NC} Vector search latency (${latency}s) exceeds warning threshold (0.5s)"
                    has_alerts=1
                fi
            fi
        elif [[ "$metric" == *"response_time="* ]]; then
            local response_time=$(echo "$metric" | grep -o "response_time=[^,]*" | cut -d= -f2)
            
            if [[ "$response_time" != "N/A" ]]; then
                if (( $(echo "$response_time > 5.0" | bc -l) )); then
                    echo -e "${RED}CRITICAL:${NC} LLM response time (${response_time}s) exceeds critical threshold (5.0s)"
                    has_alerts=1
                elif (( $(echo "$response_time > 2.0" | bc -l) )); then
                    echo -e "${YELLOW}WARNING:${NC} LLM response time (${response_time}s) exceeds warning threshold (2.0s)"
                    has_alerts=1
                fi
            fi
        elif [[ "$metric" == *"avg_query_time="* ]]; then
            local query_time=$(echo "$metric" | grep -o "avg_query_time=[^,]*" | cut -d= -f2)
            
            if [[ "$query_time" != "N/A" ]]; then
                if (( $(echo "$query_time > 1.0" | bc -l) )); then
                    echo -e "${RED}CRITICAL:${NC} Database query time (${query_time}s) exceeds critical threshold (1.0s)"
                    has_alerts=1
                elif (( $(echo "$query_time > 0.2" | bc -l) )); then
                    echo -e "${YELLOW}WARNING:${NC} Database query time (${query_time}s) exceeds warning threshold (0.2s)"
                    has_alerts=1
                fi
            fi
        elif [[ "$metric" == *"cpu="* ]]; then
            local cpu=$(echo "$metric" | grep -o "cpu=[^,]*" | cut -d= -f2)
            local memory=$(echo "$metric" | grep -o "memory=[^,]*" | cut -d= -f2)
            local disk=$(echo "$metric" | grep -o "disk=[^,]*" | cut -d= -f2)
            
            if (( $(echo "$cpu > 85" | bc -l) )); then
                echo -e "${RED}CRITICAL:${NC} CPU usage (${cpu}%) exceeds critical threshold (85%)"
                has_alerts=1
            elif (( $(echo "$cpu > 70" | bc -l) )); then
                echo -e "${YELLOW}WARNING:${NC} CPU usage (${cpu}%) exceeds warning threshold (70%)"
                has_alerts=1
            fi
            
            if (( $(echo "$memory > 90" | bc -l) )); then
                echo -e "${RED}CRITICAL:${NC} Memory usage (${memory}%) exceeds critical threshold (90%)"
                has_alerts=1
            elif (( $(echo "$memory > 75" | bc -l) )); then
                echo -e "${YELLOW}WARNING:${NC} Memory usage (${memory}%) exceeds warning threshold (75%)"
                has_alerts=1
            fi
            
            if (( $(echo "$disk > 90" | bc -l) )); then
                echo -e "${RED}CRITICAL:${NC} Disk usage (${disk}%) exceeds critical threshold (90%)"
                has_alerts=1
            elif (( $(echo "$disk > 80" | bc -l) )); then
                echo -e "${YELLOW}WARNING:${NC} Disk usage (${disk}%) exceeds warning threshold (80%)"
                has_alerts=1
            fi
        fi
    done
    
    if [[ $has_alerts -eq 0 ]]; then
        echo -e "${GREEN}No alerts detected${NC}"
    fi
}

# Saves metrics to the specified output file
save_to_file() {
    local formatted_metrics="$1"
    local file_path="$2"
    
    if [[ -z "$file_path" ]]; then
        return 0
    fi
    
    # Determine format based on file extension
    local format="text"
    if [[ "$file_path" == *.json ]]; then
        format="json"
    elif [[ "$file_path" == *.csv ]]; then
        format="csv"
    fi
    
    # Format metrics for output file
    local output_data
    output_data=$(format_output "$formatted_metrics" "$format")
    
    # Append formatted metrics to the file
    echo -e "$output_data" >> "$file_path"
    
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to write metrics to file: $file_path"
        return 1
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Metrics saved to: $file_path"
    fi
    
    return 0
}

# Main function that orchestrates the performance monitoring
main() {
    # Parse command line arguments
    parse_arguments "$@"
    
    # Check dependencies
    check_dependencies
    if [[ $? -ne 0 ]]; then
        echo "Error: Missing dependencies, please install required tools"
        exit 1
    fi
    
    # Print script header
    echo "============================================="
    echo "Performance Monitoring - $(date)"
    echo "API URL: $API_URL"
    echo "Interval: $INTERVAL seconds"
    echo "Duration: $DURATION seconds"
    if [[ -n "$OUTPUT_FILE" ]]; then
        echo "Output File: $OUTPUT_FILE"
    fi
    echo "============================================="
    
    # Initialize metrics collection
    local -a collected_metrics=()
    local -a response_times=()
    local iterations=$(( DURATION / INTERVAL ))
    local exit_code=0
    
    # Loop for the specified duration
    for (( i=1; i<=iterations; i++ )); do
        local iteration_start=$(date +%s)
        
        # Collect API endpoint performance metrics
        for endpoint in "${TEST_ENDPOINTS[@]}"; do
            local endpoint_metrics
            endpoint_metrics=$(measure_endpoint_performance "$endpoint")
            collected_metrics+=("$endpoint_metrics")
            
            # Extract response time for statistics
            local response_time
            response_time=$(echo "$endpoint_metrics" | grep -o "time=[0-9.]*" | cut -d= -f2)
            response_times+=("$response_time")
        done
        
        # Collect system metrics
        local system_metrics
        system_metrics=$(collect_system_metrics)
        collected_metrics+=("$system_metrics")
        
        # Collect database metrics if available
        local db_metrics
        db_metrics=$(collect_database_metrics)
        collected_metrics+=("$db_metrics")
        
        # Collect vector search metrics if available
        local vector_metrics
        vector_metrics=$(collect_vector_search_metrics)
        collected_metrics+=("$vector_metrics")
        
        # Collect LLM metrics if available
        local llm_metrics
        llm_metrics=$(collect_llm_metrics)
        collected_metrics+=("$llm_metrics")
        
        # Display current metrics if verbose mode is enabled
        if [[ "$VERBOSE" == "true" ]]; then
            echo -e "\nIteration $i/$iterations - $(date)"
            display_metrics "${collected_metrics[@]}"
        fi
        
        # Calculate time spent in this iteration
        local iteration_end=$(date +%s)
        local iteration_duration=$((iteration_end - iteration_start))
        
        # Sleep for the remaining interval time if not the last iteration
        if (( i < iterations )); then
            local sleep_time=$((INTERVAL - iteration_duration))
            if (( sleep_time > 0 )); then
                sleep $sleep_time
            fi
        fi
    done
    
    # Calculate statistics
    local stats
    stats=$(calculate_statistics "${response_times[@]}")
    collected_metrics+=("$stats")
    
    # Display final metrics summary
    echo -e "\nFinal Metrics Summary:"
    echo "============================================="
    display_metrics "${collected_metrics[@]}"
    
    # Check for critical issues to determine exit code
    local has_critical=0
    for metric in "${collected_metrics[@]}"; do
        if [[ "$metric" == *"endpoint="* && "$metric" == *"time="* ]]; then
            local time=$(echo "$metric" | grep -o "time=[^,]*" | cut -d= -f2)
            if (( $(echo "$time > 3.0" | bc -l) )); then
                has_critical=1
            fi
        elif [[ "$metric" == *"search_latency="* ]]; then
            local latency=$(echo "$metric" | grep -o "search_latency=[^,]*" | cut -d= -f2)
            if [[ "$latency" != "N/A" && $(echo "$latency > 2.0" | bc -l) -eq 1 ]]; then
                has_critical=1
            fi
        elif [[ "$metric" == *"response_time="* ]]; then
            local response_time=$(echo "$metric" | grep -o "response_time=[^,]*" | cut -d= -f2)
            if [[ "$response_time" != "N/A" && $(echo "$response_time > 5.0" | bc -l) -eq 1 ]]; then
                has_critical=1
            fi
        elif [[ "$metric" == *"cpu="* ]]; then
            local cpu=$(echo "$metric" | grep -o "cpu=[^,]*" | cut -d= -f2)
            if (( $(echo "$cpu > 85" | bc -l) )); then
                has_critical=1
            fi
        fi
    done
    
    # Save metrics to output file if specified
    if [[ -n "$OUTPUT_FILE" ]]; then
        save_to_file "${collected_metrics[*]}" "$OUTPUT_FILE"
        if [[ $? -ne 0 ]]; then
            exit_code=1
        fi
    fi
    
    # Set exit code based on critical issues
    if [[ $has_critical -eq 1 ]]; then
        exit_code=2  # Critical issues detected
    fi
    
    return $exit_code
}

# Execute main function
main "$@"