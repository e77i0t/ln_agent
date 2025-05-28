#!/bin/bash

# Exit on any error
set -e

echo "Starting database tests..."

# Start MongoDB if not running
if ! pgrep mongod > /dev/null; then
    echo "Starting MongoDB..."
    ./scripts/start_mongodb.sh
fi

# Wait for MongoDB to be ready (max 30 seconds)
echo "Checking MongoDB connection..."
for i in {1..30}; do
    if mongosh --quiet --eval "db.runCommand({ ping: 1 }).ok" | grep -q "1"; then
        echo "MongoDB is running and accessible"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Error: MongoDB is not responding after 30 seconds"
        exit 1
    fi
    echo "Waiting for MongoDB to be ready... ($i/30)"
    sleep 1
done

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