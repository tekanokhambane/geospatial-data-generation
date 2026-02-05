import csv
import requests
import psycopg2
import os


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print(
    f"Using Google API Key: {GOOGLE_API_KEY[:10]}..."
    if GOOGLE_API_KEY
    else "WARNING: GOOGLE_API_KEY not set!"
)
print(f"Connecting to: {os.getenv('DATABASE_URL')}")

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "..", "transactions.csv")


def reverse_geocode(lat, lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    res = requests.get(
        url, params={"latlng": f"{lat},{lon}", "key": GOOGLE_API_KEY}
    ).json()

    if res["results"]:
        print(res["results"][0]["formatted_address"])
        return res["results"][0]["formatted_address"]
    return None


cur.execute(
    """
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE TABLE IF NOT EXISTS locations_data (
        id UUID PRIMARY KEY,
        timestamp TIMESTAMP,
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        address TEXT,
        geom GEOGRAPHY(POINT, 4326)
    );
    TRUNCATE TABLE locations_data RESTART IDENTITY;
"""
)
conn.commit()

with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        address = reverse_geocode(row["latitude"], row["longitude"])

        cur.execute(
            """
            INSERT INTO locations_data (id, timestamp, latitude, longitude, address, geom)
            VALUES (%s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
            )
        """,
            (
                row["id"],
                row["timestamp"],
                row["latitude"],
                row["longitude"],
                address,
                row["longitude"],
                row["latitude"],
            ),
        )

conn.commit()
cur.close()
conn.close()
