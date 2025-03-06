#!/bin/bash
#
# health-check.sh
# 
# This script performs health checks on the Document Management and AI Chatbot System 
# components. It verifies the availability and proper functioning of the API, database, 
# vector store, and LLM service, providing a comprehensive system health status.

# Global variables
API_URL="http://localhost:8000"
TIMEOUT="5"
EXIT_CODE=0
VERBOSE=false

# Color codes for pretty output
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Function to display usage information
print_usage() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo ""
    echo "This script performs health checks on the Document Management and AI Chatbot System components."
    echo ""
    echo "Options:"
    echo "  -u, --url URL       Specify the API URL (default: http://localhost:8000)"
    echo "  -t, --timeout SEC   Specify the timeout in seconds (default: 5)"
    echo "  -v, --verbose       Enable verbose output"
    echo "  -h, --help          Display this help message and exit"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0") -u http://api.example.com -t 10 -v"
    echo "  $(basename "$0") --url http://api.example.com --timeout 10 --verbose"
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -u|--url)
                if [[ -z "$2" || "$2" == -* ]]; then
                    echo "Error: URL is required for -u/--url option"
                    exit 1
                fi
                API_URL="$2"
                shift 2
                ;;
            -t|--timeout)
                if [[ -z "$2" || "$2" == -* ]]; then
                    echo "Error: Timeout value is required for -t/--timeout option"
                    exit 1
                fi
                if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                    echo "Error: Timeout must be a positive integer"
                    exit 1
                fi
                TIMEOUT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
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

    # Validate API_URL format
    if ! [[ "$API_URL" =~ ^https?:// ]]; then
        echo "Error: API URL must start with http:// or https://"
        exit 1
    fi
}

# Function to check API liveness
check_api_liveness() {
    echo -e "${BLUE}Checking API liveness...${RESET}"
    
    local endpoint="${API_URL}/health/live"
    local component="API Liveness"
    local status="unhealthy"
    local details="Failed to connect to the API"
    local result=1
    
    # Make HTTP request to the liveness endpoint
    response=$(curl -s -o - -w "%{http_code}" -m "$TIMEOUT" "$endpoint" 2>/dev/null)
    if [ $? -ne 0 ]; then
        print_result "$component" "$status" "Connection timed out after ${TIMEOUT}s"
        return 1
    fi
    
    # Extract HTTP status code and response body
    http_code="${response: -3}"
    body="${response:0:${#response}-3}"
    
    if [ "$http_code" == "200" ]; then
        # Check if the response contains the expected status
        if echo "$body" | grep -q '"status":\s*"ok"'; then
            status="healthy"
            details="API is responding to liveness checks"
            result=0
        else
            details="API responded with an unexpected format: $body"
        fi
    else
        details="API responded with HTTP $http_code: $body"
    fi
    
    print_result "$component" "$status" "$details"
    return $result
}

# Function to check API readiness
check_api_readiness() {
    echo -e "${BLUE}Checking API readiness...${RESET}"
    
    local endpoint="${API_URL}/health/ready"
    local component="API Readiness"
    local status="unhealthy"
    local details="Failed to connect to the API"
    local result=1
    
    # Make HTTP request to the readiness endpoint
    response=$(curl -s -o - -w "%{http_code}" -m "$TIMEOUT" "$endpoint" 2>/dev/null)
    if [ $? -ne 0 ]; then
        print_result "$component" "$status" "Connection timed out after ${TIMEOUT}s"
        return 1
    fi
    
    # Extract HTTP status code and response body
    http_code="${response: -3}"
    body="${response:0:${#response}-3}"
    
    if [ "$http_code" == "200" ]; then
        # Check if the response contains the expected status
        if echo "$body" | grep -q '"status":\s*"ok"'; then
            status="healthy"
            details="API is ready to accept requests"
            result=0
        else
            details="API responded with an unexpected format: $body"
        fi
    else
        details="API responded with HTTP $http_code: $body"
    fi
    
    print_result "$component" "$status" "$details"
    return $result
}

# Function to check system dependencies
check_dependencies() {
    echo -e "${BLUE}Checking system dependencies...${RESET}"
    
    local endpoint="${API_URL}/health/dependencies"
    local overall_result=0
    
    # Make HTTP request to the dependencies endpoint
    response=$(curl -s -o - -w "%{http_code}" -m "$TIMEOUT" "$endpoint" 2>/dev/null)
    if [ $? -ne 0 ]; then
        print_result "Dependencies" "unhealthy" "Connection timed out after ${TIMEOUT}s"
        return 1
    fi
    
    # Extract HTTP status code and response body
    http_code="${response: -3}"
    body="${response:0:${#response}-3}"
    
    if [ "$http_code" != "200" ]; then
        print_result "Dependencies" "unhealthy" "API responded with HTTP $http_code: $body"
        return 1
    fi
    
    # Parse JSON response
    # This is a simple parsing for bash script without requiring jq
    # For more robust JSON parsing, consider using jq if available
    
    # Check database status
    if echo "$body" | grep -q '"database":\s*{[^}]*"status":\s*"healthy"'; then
        print_result "Database" "healthy" "Database connection is working properly"
    else
        print_result "Database" "unhealthy" "Database health check failed"
        overall_result=1
    fi
    
    # Check vector store status
    if echo "$body" | grep -q '"vector_store":\s*{[^}]*"status":\s*"healthy"'; then
        print_result "Vector Store" "healthy" "FAISS vector store is functioning properly"
    else
        print_result "Vector Store" "unhealthy" "Vector store health check failed"
        overall_result=1
    fi
    
    # Check LLM service status
    if echo "$body" | grep -q '"llm_service":\s*{[^}]*"status":\s*"healthy"'; then
        print_result "LLM Service" "healthy" "LLM API connection is working properly"
    else
        print_result "LLM Service" "unhealthy" "LLM service health check failed"
        overall_result=1
    fi
    
    return $overall_result
}

# Function to print formatted result
print_result() {
    local component="$1"
    local status="$2"
    local details="$3"
    local color="$RED"
    
    # Set color based on status
    if [ "$status" == "healthy" ]; then
        color="$GREEN"
    fi
    
    # Print component status with padding for alignment
    printf "%-20s: %b%s%b" "$component" "$color" "$status" "$RESET"
    
    # Print details if verbose mode is enabled
    if [ "$VERBOSE" == true ]; then
        echo -e " - $details"
    else
        echo ""
    fi
}

# Main function
main() {
    # Parse command line arguments
    parse_arguments "$@"
    
    # Print header
    echo -e "${YELLOW}====== Document Management and AI Chatbot System Health Check ======${RESET}"
    echo -e "${YELLOW}Date: $(date)${RESET}"
    echo -e "${YELLOW}API URL: $API_URL${RESET}"
    echo ""
    
    # Check API liveness
    check_api_liveness
    if [ $? -ne 0 ]; then
        EXIT_CODE=1
    fi
    
    # Check API readiness
    check_api_readiness
    if [ $? -ne 0 ]; then
        EXIT_CODE=1
    fi
    
    # Check system dependencies
    check_dependencies
    if [ $? -ne 0 ]; then
        EXIT_CODE=1
    fi
    
    # Print summary
    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}All systems are healthy${RESET}"
    else
        echo -e "${RED}One or more systems are unhealthy${RESET}"
    fi
    
    return $EXIT_CODE
}

# Execute main function
main "$@"
exit $?