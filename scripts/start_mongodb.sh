#!/bin/bash

# Check if MongoDB is already running
if pgrep mongod > /dev/null; then
    echo "MongoDB is already running"
    exit 0
fi

# Create MongoDB data directory if it doesn't exist
mkdir -p /data/db

# Start MongoDB in the background
echo "Starting MongoDB..."
mongod --bind_ip_all &

# Wait for MongoDB to start (max 30 seconds)
for i in {1..30}; do
    if mongosh --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; then
        echo "MongoDB started successfully"
        exit 0
    fi
    echo "Waiting for MongoDB to start... ($i/30)"
    sleep 1
done

echo "Error: MongoDB failed to start within 30 seconds"
exit 1 