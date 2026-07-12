"""
run_pipeline.py -- One-Command Setup (Final polish)
--------------------------------------------------------
Runs the ENTIRE pipeline end to end, in the correct order, with clear
progress output -- so instead of remembering and typing 9 separate
commands, you run exactly one:

    python run_pipeline.py

Add --skip-data if you've already replaced data/sensor_data.csv with
your own real sensor data and don't want it overwritten.
Add --with-tests to also run the full test suite at the end.

This does not launch the dashboard or the API (those are long-running
processes you want in their own terminal window) -- it only handles
the "get everything trained and ready" part.
"""

import subprocess
import sys
import os
import argparse
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Generating sample sensor data", ["python", "data/generate_sample_data.py"], "data"),
    ("Labeling dataset with risk categories", ["python", "src/label_dataset.py"], "skip_data_ok"),
    ("Training risk-classification models", ["python", "src/train_and_compare.py"], "skip_data_ok"),
    ("Training 1-hour-ahead forecasting model", ["python", "src/forecast_model.py"], "skip_data_ok"),
    ("Training sensor anomaly detector", ["python", "src/anomaly_detection.py"], "skip_data_ok"),
    ("Training multi-step RL ventilation advisor", ["python", "src/rl_advisor.py"], "skip_data_ok"),
    ("Backfilling Building Health history", ["python", "src/backfill_health_history.py"], "skip_data_ok"),
    ("Smoke-testing the autonomous orchestrator", ["python", "src/orchestrator.py"], "skip_data_ok"),
    ("Smoke-testing federated learning simulation", ["python", "src/federated_learning.py"], "skip_data_ok"),
]


def run_step(description: str, command: list, step_num: int, total: int) -> bool:
    print(f"\n[{step_num}/{total}] {description}...")
    t0 = time.time()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"    FAILED ({elapsed:.1f}s)")
        print("    --- error output ---")
        print("    " + result.stderr.strip().replace("\n", "\n    "))
        return False

    print(f"    Done ({elapsed:.1f}s)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run the full IAQ pipeline in one command.")
    parser.add_argument("--skip-data", action="store_true",
                        help="Skip regenerating sample data (use if you've already put your real data in data/sensor_data.csv)")
    parser.add_argument("--with-tests", action="store_true",
                        help="Also run the full pytest suite at the end")
    args = parser.parse_args()

    steps = STEPS
    if args.skip_data:
        steps = [s for s in steps if s[2] != "data"]
        print("Skipping sample data generation -- using existing data/sensor_data.csv")

    print("=" * 60)
    print("IAQ Infection Risk Monitor -- Full Pipeline Setup")
    print("=" * 60)

    for i, (description, command, _) in enumerate(steps, 1):
        ok = run_step(description, command, i, len(steps))
        if not ok:
            print(f"\nPipeline stopped at step {i}. Fix the error above and re-run.")
            sys.exit(1)

    if args.with_tests:
        print(f"\n[extra] Running full test suite...")
        result = subprocess.run(["pytest", "tests/", "-v"], cwd=ROOT)
        if result.returncode != 0:
            print("\nSome tests failed -- see output above.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("All done. Everything is trained and ready.")
    print("=" * 60)
    print("\nNext steps:")
    print("  streamlit run dashboard/Home.py     (launch the dashboard)")
    print("  uvicorn api.main:app --reload       (launch the API, in a separate terminal)")


if __name__ == "__main__":
    main()
