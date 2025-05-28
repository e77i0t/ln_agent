#!/bin/bash

# Check if PID file exists
if [ -f .flask.pid ]; then
    PID=$(cat .flask.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping Flask application (PID: $PID)..."
        kill $PID
        rm .flask.pid
        echo "Flask application stopped"
    else
        echo "Flask application is not running"
        rm .flask.pid
    fi
else
    echo "Flask application is not running (no PID file found)"
fi 