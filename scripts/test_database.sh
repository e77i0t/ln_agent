#!/bin/bash

# Exit on any error
set -e

echo "Starting database tests..."

# Check if MongoDB is running
echo "Checking MongoDB connection..."
if ! mongosh --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; then
    echo "Error: MongoDB is not running. Please start MongoDB first."
    exit 1
fi

# Initialize the database
echo "Initializing database..."
python -m app.utils.db_init

# Run the test script
echo "Running database tests..."
python -m app.tests.test_db

# Check exit status
if [ $? -eq 0 ]; then
    echo "All tests passed successfully!"
    exit 0
else
    echo "Tests failed!"
    exit 1
fi 