#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
until PGPASSWORD="${POSTGRES_PASSWORD:-khambane325}" psql -h "db" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-locations_db}" -c '\q' 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run the ingestion script
echo "Running data ingestion..."
python scripts/ingestion.py

# Start the application
echo "Starting the application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
