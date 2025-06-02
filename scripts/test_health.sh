#!/bin/bash

# Base URL
BASE_URL="http://localhost:5280"

# Function to make a request and format the response
check_endpoint() {
    local endpoint=$1
    echo "Testing $endpoint..."
    echo "Response:"
    curl -s "$BASE_URL$endpoint" | python3 -m json.tool
    echo -e "\n"
}

# Test all health endpoints
check_endpoint "/health"
check_endpoint "/health/mongodb"
check_endpoint "/health/redis"
check_endpoint "/health/celery"
check_endpoint "/health/all" 