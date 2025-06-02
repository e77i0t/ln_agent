#!/bin/bash

# Ensure script fails on any error
set -e

# Default MongoDB URL for testing
export MONGODB_URL=${MONGODB_URL:-"mongodb://localhost:27017/company_research_test"}

echo "Running tests with MongoDB URL: $MONGODB_URL"

# Check if MongoDB is accessible
echo "Checking MongoDB connection..."
mongosh "$MONGODB_URL" --eval "db.version()" > /dev/null 2>&1 || {
    echo "Error: Cannot connect to MongoDB at $MONGODB_URL"
    echo "Please ensure MongoDB is running and accessible"
    exit 1
}

# Install test dependencies if requirements-test.txt exists
if [ -f requirements-test.txt ]; then
    echo "Installing test dependencies..."
    pip install -r requirements-test.txt
fi

# Run pytest with coverage
echo "Running tests..."
python -m pytest app/tests/ \
    -v \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:coverage_report \
    "$@"

# Check the exit status
if [ $? -eq 0 ]; then
    echo "All tests passed successfully!"
    echo "Coverage report available in coverage_report/index.html"
else
    echo "Some tests failed. Please check the output above for details."
    exit 1
fi 