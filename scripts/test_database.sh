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
if ! command_exists mongo; then
    echo "Error: MongoDB client (mongo) is not installed"
    exit 1
fi

if ! command_exists mongod; then
    echo "Error: MongoDB server (mongod) is not installed"
    exit 1
fi

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

# Start MongoDB if not running
if ! pgrep mongod > /dev/null; then
    echo "Starting MongoDB..."
    if ! ./scripts/start_mongodb.sh; then
        echo "Error: Failed to start MongoDB"
        exit 1
    fi
fi

# Wait for MongoDB to be ready (max 30 seconds)
echo "Checking MongoDB connection..."
mongodb_ready=false
for i in {1..30}; do
    if mongo --quiet --eval "db.runCommand({ ping: 1 }).ok" > /dev/null 2>&1; then
        echo "MongoDB is running and accessible"
        mongodb_ready=true
        break
    fi
    echo "Waiting for MongoDB to be ready... ($i/30)"
    sleep 1
done

if [ "$mongodb_ready" = false ]; then
    echo "Error: MongoDB is not responding after 30 seconds"
    exit 1
fi

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