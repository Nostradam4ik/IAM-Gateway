# Script to copy HR CSV file to MidPoint container

Write-Host "Copying HR CSV file to MidPoint container..." -ForegroundColor Green

# Create import directory if it doesn't exist
docker exec midpoint-core mkdir -p /opt/midpoint/var/import

# Copy CSV file
docker cp datasets/hr_sample.csv midpoint-core:/opt/midpoint/var/import/hr_sample.csv

# Verify the file was copied
Write-Host "Verifying file..." -ForegroundColor Yellow
docker exec midpoint-core ls -lh /opt/midpoint/var/import/hr_sample.csv

Write-Host "CSV file successfully copied to MidPoint container!" -ForegroundColor Green
Write-Host "Path inside container: /opt/midpoint/var/import/hr_sample.csv" -ForegroundColor Cyan
