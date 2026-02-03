import csv
import uuid
import random
from datetime import datetime, timedelta

CENTER_LAT = -26.2041
CENTER_LON = 28.0473


def random_coord(center, spread=0.02):
    return center + random.uniform(-spread, spread)


rows = []
start_time = datetime.now()

for i in range(5000):
    rows.append(
        {
            "id": str(uuid.uuid4()),
            "timestamp": (start_time + timedelta(seconds=i)).isoformat(),
            "latitude": random_coord(CENTER_LAT),
            "longitude": random_coord(CENTER_LON),
        }
    )

with open("transactions.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "timestamp", "latitude", "longitude"])
    writer.writeheader()
    writer.writerows(rows)
