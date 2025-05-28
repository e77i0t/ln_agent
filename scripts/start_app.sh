#!/bin/bash

# Exit on any error
set -e

# Set Flask environment variables
export FLASK_APP=app
export FLASK_ENV=development
export FLASK_DEBUG=1
export PORT=5280

# Start Flask application in the background
echo "Starting Flask application..."
python3 -m flask run --host=0.0.0.0 --port=5280 &

# Store the PID of the Flask application
FLASK_PID=$!

# Function to check if process is running
is_running() {
    ps -p $1 > /dev/null 2>&1
}

# Wait for the application to be ready (max 30 seconds)
echo "Waiting for application to be ready..."
for i in {1..30}; do
    # Check if Flask is still running
    if ! is_running $FLASK_PID; then
        echo "Error: Flask application crashed"
        exit 1
    fi
    
    # Check health endpoint
    RESPONSE=$(curl -s http://localhost:5280/health)
    if [ $? -eq 0 ] && [ "$RESPONSE" = '{"status":"healthy"}' ]; then
        echo "Application is running and healthy"
        # Write PID to file for later cleanup
        echo $FLASK_PID > .flask.pid
        exit 0
    fi
    echo "Waiting for application to start... ($i/30)"
    sleep 1
done

# If we get here, the application didn't start properly
echo "Error: Application failed to start within 30 seconds"
kill $FLASK_PID 2>/dev/null || true
exit 1 