"""
train_and_compare.py
---------------------
Trains TWO models to predict risk_category (Low/Medium/High) from raw
sensor readings, and compares them -- mirroring exactly what your
original project did (Fuzzy model vs Neural Network), just retargeted
to the new infection-risk output.

Model 1: Fuzzy-Rule-Based Decision Tree (sklearn DecisionTreeClassifier
          trained on the same features -- this is the trainable,
          data-driven cousin of your hand-crafted fuzzy rules, and is
          directly comparable to your original "Fuzzy Decision Tree")
Model 2: Neural Network (MLPClassifier)

Both are evaluated on the same held-out test set for a fair comparison,
and results are saved as a report + confusion matrix plots.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(DATA_DIR, "labeled_data.csv"))

FEATURES = ["co2_ppm", "temperature_c", "humidity_pct", "occupancy"]
TARGET = "risk_category"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# Scale features for the Neural Network (trees don't need this, but it's
# harmless to keep raw scale for the tree and scaled for the NN)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

results = {}

# ---------------- Model 1: Fuzzy Decision Tree ----------------
print("Training Fuzzy Decision Tree model...")
t0 = time.time()
tree_model = DecisionTreeClassifier(
    max_depth=6, min_samples_leaf=10, random_state=42
)
tree_model.fit(X_train, y_train)
tree_train_time = time.time() - t0

t0 = time.time()
tree_preds = tree_model.predict(X_test)
tree_infer_time = (time.time() - t0) / len(X_test) * 1000  # ms per prediction

tree_acc = accuracy_score(y_test, tree_preds)
results["Fuzzy Decision Tree"] = {
    "accuracy": tree_acc,
    "train_time_s": tree_train_time,
    "infer_time_ms": tree_infer_time,
    "preds": tree_preds,
}

# ---------------- Model 2: Neural Network ----------------
print("Training Neural Network model...")
t0 = time.time()
nn_model = MLPClassifier(
    hidden_layer_sizes=(32, 16), max_iter=500, random_state=42
)
nn_model.fit(X_train_scaled, y_train)
nn_train_time = time.time() - t0

t0 = time.time()
nn_preds = nn_model.predict(X_test_scaled)
nn_infer_time = (time.time() - t0) / len(X_test) * 1000

nn_acc = accuracy_score(y_test, nn_preds)
results["Neural Network"] = {
    "accuracy": nn_acc,
    "train_time_s": nn_train_time,
    "infer_time_ms": nn_infer_time,
    "preds": nn_preds,
}

# ---------------- Report ----------------
print("\n" + "=" * 50)
print("MODEL COMPARISON RESULTS")
print("=" * 50)
for name, r in results.items():
    print(f"\n{name}:")
    print(f"  Accuracy        : {r['accuracy']*100:.2f}%")
    print(f"  Training time   : {r['train_time_s']:.3f} s")
    print(f"  Inference time  : {r['infer_time_ms']:.4f} ms/sample")

better = max(results, key=lambda k: results[k]["accuracy"])
diff = abs(results["Fuzzy Decision Tree"]["accuracy"] - results["Neural Network"]["accuracy"]) * 100
print(f"\n>> {better} performs better by {diff:.2f} percentage points.")

# ---------------- Save detailed classification reports ----------------
with open(os.path.join(REPORTS_DIR, "model_comparison.txt"), "w") as f:
    f.write("MODEL COMPARISON RESULTS\n")
    f.write("=" * 50 + "\n\n")
    for name, r in results.items():
        f.write(f"{name}\n")
        f.write(f"Accuracy: {r['accuracy']*100:.2f}%\n")
        f.write(f"Training time: {r['train_time_s']:.3f}s\n")
        f.write(f"Inference time: {r['infer_time_ms']:.4f} ms/sample\n\n")
        f.write(classification_report(y_test, r["preds"]))
        f.write("\n" + "-" * 50 + "\n\n")
    f.write(f"WINNER: {better} (by {diff:.2f} percentage points)\n")

# ---------------- Confusion matrices ----------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
labels_order = ["Low", "Medium", "High"]

for ax, (name, r) in zip(axes, results.items()):
    cm = confusion_matrix(y_test, r["preds"], labels=labels_order)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels_order)
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title(f"{name}\nAccuracy: {r['accuracy']*100:.1f}%")

plt.tight_layout()
plt.savefig(os.path.join(REPORTS_DIR, "confusion_matrices.png"), dpi=150)
print("\nSaved: reports/model_comparison.txt and reports/confusion_matrices.png")

# Save the trained tree model + scaler + NN for use in the dashboard
import joblib
joblib.dump(tree_model, os.path.join(REPORTS_DIR, "fuzzy_tree_model.joblib"))
joblib.dump(nn_model, os.path.join(REPORTS_DIR, "neural_net_model.joblib"))
joblib.dump(scaler, os.path.join(REPORTS_DIR, "scaler.joblib"))
print("Saved trained models for dashboard use.")
