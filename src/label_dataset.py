"""
label_dataset.py
-----------------
Applies the Wells-Riley formula to every row of sensor_data.csv,
producing the "ground truth" risk_score and risk_category columns
that the AI models will learn to predict directly from raw sensor
readings (so the formula doesn't need to be recalculated live).
"""

import os
import pandas as pd
from wells_riley import infection_risk_score, risk_category

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DATA_DIR = os.path.join(BASE_DIR, "data")

df = pd.read_csv(os.path.join(DATA_DIR, "sensor_data.csv"))

df["risk_score"] = df.apply(
    lambda r: infection_risk_score(r["co2_ppm"], r["occupancy"]), axis=1
)
df["risk_category"] = df["risk_score"].apply(risk_category)

df.to_csv(os.path.join(DATA_DIR, "labeled_data.csv"), index=False)

print("Label distribution:")
print(df["risk_category"].value_counts())
print(f"\nTotal rows labeled: {len(df)}")
