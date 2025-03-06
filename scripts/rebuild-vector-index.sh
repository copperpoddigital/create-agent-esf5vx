#!/bin/bash

# Define script directory and paths
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
BACKEND_DIR=$(realpath "$SCRIPT_DIR/../src/backend")
VENV_DIR=$(realpath "$BACKEND_DIR/.venv")
PYTHON_SCRIPT=$(realpath "$BACKEND_DIR/scripts/rebuild_index.py")

# Function to check if the environment is set up correctly
check_environment() {
    # Check if Python virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        echo "Error: Python virtual environment not found at $VENV_DIR"
        return 1
    fi

    # Check if the rebuild_index.py script exists
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "Error: rebuild_index.py script not found at $PYTHON_SCRIPT"
        return 1
    fi

    return 0
}

# Function to print usage information
print_usage() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo
    echo "A script to rebuild the FAISS vector index for the Document Management and AI Chatbot System."
    echo
    echo "Options:"
    echo "  -f, --force         Force rebuild even if index exists"
    echo "  -b, --batch-size N  Set the number of document chunks to process in a batch (default: 100)"
    echo "  -v, --verbose       Enable verbose output for detailed logging"
    echo "  -h, --help          Display this help message and exit"
    echo
    echo "Examples:"
    echo "  $(basename "$0")                     # Rebuild index with default settings"
    echo "  $(basename "$0") -f                  # Force rebuild of the index"
    echo "  $(basename "$0") -b 200              # Rebuild with batch size of 200"
    echo "  $(basename "$0") -f -v -b 150        # Force rebuild with verbose output and batch size of 150"
}

# Function to parse command-line arguments
parse_arguments() {
    local options=""
    
    while [ $# -gt 0 ]; do
        case "$1" in
            -f|--force)
                options="${options} --force"
                ;;
            -b|--batch-size)
                if [ -z "$2" ] || [[ "$2" == -* ]]; then
                    echo "Error: Option $1 requires a numeric argument" >&2
                    print_usage
                    exit 1
                fi
                options="${options} --batch-size $2"
                shift
                ;;
            -v|--verbose)
                options="${options} --verbose"
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                echo "Error: Unknown option $1" >&2
                print_usage
                exit 1
                ;;
        esac
        shift
    done
    
    echo "${options}"
}

# Function to activate virtual environment
activate_venv() {
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        echo "Error: Python virtual environment not found at $VENV_DIR"
        return 1
    fi

    # Source the activation script
    source "$VENV_DIR/bin/activate"

    # Verify activation
    if [[ "$VIRTUAL_ENV" != "$VENV_DIR" ]]; then
        echo "Error: Failed to activate virtual environment"
        return 1
    fi

    echo "Virtual environment activated successfully"
    return 0
}

# Function to run the Python rebuild script
run_rebuild_script() {
    local options="$1"
    
    echo "Starting FAISS index rebuild..."
    echo "This process might take some time depending on the size of your document collection."
    if [ -n "$options" ]; then
        echo "Running: python $PYTHON_SCRIPT $options"
    else
        echo "Running: python $PYTHON_SCRIPT"
    fi
    
    # We intentionally want word splitting for the options
    # shellcheck disable=SC2086
    python "$PYTHON_SCRIPT" $options
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "FAISS index rebuild completed successfully!"
        echo "The vector index has been optimized and is ready for use."
    else
        echo "Error: FAISS index rebuild failed with exit code $exit_code"
        echo "Please check the error messages above for details."
    fi
    
    return $exit_code
}

# Main script execution

# Check environment
if ! check_environment; then
    exit 1
fi

# Parse command-line arguments
options=$(parse_arguments "$@")

# Activate virtual environment
if ! activate_venv; then
    exit 1
fi

# Run the rebuild script
if ! run_rebuild_script "$options"; then
    echo "FAISS index rebuild failed. See above for details."
    exit 1
fi

echo "FAISS index rebuild completed successfully."
exit 0