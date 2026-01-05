#!/bin/bash
# Script to copy HR CSV file to MidPoint container

set -e

echo "Copying HR CSV file to MidPoint container..."

# Create import directory if it doesn't exist
docker exec midpoint-core mkdir -p /opt/midpoint/var/import

# Copy CSV file
docker cp datasets/hr_sample.csv midpoint-core:/opt/midpoint/var/import/hr_sample.csv

# Verify the file was copied
echo "Verifying file..."
docker exec midpoint-core ls -lh /opt/midpoint/var/import/hr_sample.csv

echo "CSV file successfully copied to MidPoint container!"
echo "Path inside container: /opt/midpoint/var/import/hr_sample.csv"
