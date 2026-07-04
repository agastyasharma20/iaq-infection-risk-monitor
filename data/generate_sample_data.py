"""
generate_sample_data.py
------------------------
Generates a realistic sample sensor dataset for 9 classrooms, standing in
for real deployed sensor logs (CO2, temperature, humidity, occupancy).

Replace this file's output (sensor_data.csv) with your REAL logged data
once you have it -- the rest of the project reads from that CSV and
does not care whether the data came from this generator or real sensors.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

NUM_ROOMS = 9
ROOM_CAPACITY = 60          # max students per room (typical PIEMR classroom)
DAYS = 10                   # 10 days of logged data
READINGS_PER_DAY = 48       # one reading every 15 minutes across a 12-hour day
CLASS_START_HOUR = 8        # classes run 8 AM - 8 PM

rows = []

for day in range(DAYS):
    base_date = datetime(2026, 6, 1) + timedelta(days=day)

    for room_id in range(1, NUM_ROOMS + 1):
        # Each room has a slightly different baseline ventilation quality
        # (some rooms have better windows/AC than others -- this mirrors
        # real buildings where room quality is not uniform)
        room_ventilation_factor = np.random.uniform(0.6, 1.4)

        co2 = 450.0          # start at outdoor baseline ppm
        temp = np.random.uniform(24, 27)
        humidity = np.random.uniform(45, 60)

        for reading in range(READINGS_PER_DAY):
            minute_of_day = reading * 15
            hour = CLASS_START_HOUR + minute_of_day / 60.0

            # Occupancy pattern: classes in session most of the day,
            # empty during a lunch break around hour 13-14
            in_class = not (13 <= hour < 14)
            occupancy = 0
            if in_class:
                # occupancy ramps up after class starts, noisy
                occupancy = int(np.clip(
                    np.random.normal(ROOM_CAPACITY * 0.75, 8), 0, ROOM_CAPACITY))

            # --- CO2 dynamics (simplified mass-balance simulation) ---
            # CO2 rises when occupied, decays toward outdoor baseline when empty,
            # decay/rise rate depends on room ventilation quality
            if occupancy > 0:
                generation = occupancy * 15.0           # people add CO2
                removal = (co2 - 450) * 0.08 * room_ventilation_factor
                co2 = co2 + generation - removal
            else:
                co2 = co2 - (co2 - 450) * 0.15 * room_ventilation_factor
            co2 = float(np.clip(co2 + np.random.normal(0, 25), 420, 3200))

            # --- Temperature & humidity drift slightly with occupancy ---
            temp = float(np.clip(
                temp + (0.02 * occupancy / 10) - 0.01 + np.random.normal(0, 0.15),
                20, 34))
            humidity = float(np.clip(
                humidity + (0.03 * occupancy / 10) + np.random.normal(0, 0.5),
                30, 85))

            timestamp = base_date + timedelta(hours=CLASS_START_HOUR) + timedelta(minutes=minute_of_day)

            rows.append({
                "timestamp": timestamp,
                "room_id": f"Room_{room_id}",
                "co2_ppm": round(co2, 1),
                "temperature_c": round(temp, 2),
                "humidity_pct": round(humidity, 2),
                "occupancy": occupancy,
                "room_capacity": ROOM_CAPACITY,
            })

df = pd.DataFrame(rows)
import os
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensor_data.csv")
df.to_csv(OUTPUT_PATH, index=False)
print(f"Generated {len(df)} sensor readings across {NUM_ROOMS} rooms over {DAYS} days.")
print(df.head())
print("\nCO2 range:", df.co2_ppm.min(), "-", df.co2_ppm.max())
