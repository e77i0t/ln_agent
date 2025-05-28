#!/bin/bash

# Exit on any error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python module exists
check_python_module() {
    python -c "import $1" >/dev/null 2>&1
}

echo "Starting database tests..."

# Check required commands
if ! command_exists python; then
    echo "Error: Python is not installed"
    exit 1
fi

# Check required Python modules
echo "Checking Python environment..."
if ! check_python_module pymongo; then
    echo "Error: Python module 'pymongo' is not installed"
    echo "Please install it using: pip install pymongo"
    exit 1
fi

# Check if the application is running and healthy
echo "Checking application health..."
if ! curl -s http://localhost:5280/health | grep -q '"status":"healthy"'; then
    echo "Error: Application is not running or not healthy"
    echo "Please ensure the application is running and accessible at http://localhost:5280"
    exit 1
fi

# Set test environment
export FLASK_ENV=testing
export MONGODB_URI="mongodb://localhost:27017/company_research_test"

# Initialize the database
echo "Initializing database..."
if ! python -m app.utils.db_init; then
    echo "Error: Failed to initialize database"
    exit 1
fi

# Run the test script
echo "Running database tests..."
if ! python -m app.tests.test_db; then
    echo "Tests failed!"
    exit 1
fi

echo "All tests passed successfully!"
exit 0 