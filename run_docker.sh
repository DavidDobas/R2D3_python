#!/bin/bash
# Helper script to run the CLI in Docker

# Build the image if needed
if [[ "$(docker images -q arm-controller 2> /dev/null)" == "" ]]; then
    echo "Building Docker image..."
    docker-compose build
fi

# Run the CLI with all passed arguments
docker-compose run --rm arm-controller python arm_cli.py "$@"

