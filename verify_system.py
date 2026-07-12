"""
verify_system.py -- System Readiness Check (Final polish)
----------------------------------------------------------------
A single command that checks whether the system is actually ready to
demo or deploy -- every trained model file present, every core module
importable, the database reachable, config valid. Run this before a
viva, a demo, or a deployment to catch a missing step in seconds
instead of finding out mid-demo.

    python verify_system.py
"""

import os
import sys
import importlib

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

CHECKS_PASSED = 0
CHECKS_FAILED = 0


def check(description: str, condition: bool, hint: str = ""):
    global CHECKS_PASSED, CHECKS_FAILED
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {description}")
    if not condition and hint:
        print(f"         -> {hint}")
    if condition:
        CHECKS_PASSED += 1
    else:
        CHECKS_FAILED += 1


def main():
    print("=" * 60)
    print("IAQ Infection Risk Monitor -- System Readiness Check")
    print("=" * 60)

    print("\n1. Config & core modules")
    try:
        from config_loader import load_config, resolve_path
        cfg = load_config()
        check("config.yaml loads successfully", True)
    except Exception as e:
        check("config.yaml loads successfully", False, str(e))
        print("\nCannot continue further checks without a valid config. Fix this first.")
        return

    for module_name in ["wells_riley", "fuzzy_model", "explainability", "digital_twin",
                         "rl_advisor", "anomaly_detection", "orchestrator", "nlg_advisory",
                         "building_health", "graph_propagation", "federated_learning"]:
        try:
            importlib.import_module(module_name)
            check(f"src/{module_name}.py imports cleanly", True)
        except Exception as e:
            check(f"src/{module_name}.py imports cleanly", False, str(e))

    print("\n2. Data files")
    data_dir = resolve_path(cfg["paths"]["data_dir"])
    check("sensor_data.csv exists", os.path.exists(os.path.join(data_dir, cfg["paths"]["sensor_data_file"])),
          "Run: python data/generate_sample_data.py (or add your own real data)")
    check("labeled_data.csv exists", os.path.exists(os.path.join(data_dir, cfg["paths"]["labeled_data_file"])),
          "Run: python src/label_dataset.py")

    print("\n3. Trained models")
    reports_dir = resolve_path(cfg["paths"]["reports_dir"])
    model_files = {
        "fuzzy_tree_model.joblib": "python src/train_and_compare.py",
        "neural_net_model.joblib": "python src/train_and_compare.py",
        "scaler.joblib": "python src/train_and_compare.py",
        "forecast_model.joblib": "python src/forecast_model.py",
        "anomaly_model.joblib": "python src/anomaly_detection.py",
        "rl_q_table.joblib": "python src/rl_advisor.py",
    }
    for fname, fix in model_files.items():
        check(f"reports/{fname} exists", os.path.exists(os.path.join(reports_dir, fname)), f"Run: {fix}")

    print("\n4. Database")
    try:
        from db import get_session
        session = get_session()
        session.close()
        check("Database is reachable", True)
    except Exception as e:
        check("Database is reachable", False, str(e))

    print("\n5. End-to-end pipeline smoke test")
    try:
        from orchestrator import process_reading
        result = process_reading("Verify_Room", co2_ppm=1800, temperature_c=26,
                                  humidity_pct=55, occupancy=30)
        check("Orchestrator produces a complete result", "advisory" in result and result["advisory"])
    except Exception as e:
        check("Orchestrator produces a complete result", False, str(e))

    print("\n" + "=" * 60)
    total = CHECKS_PASSED + CHECKS_FAILED
    print(f"RESULT: {CHECKS_PASSED}/{total} checks passed")
    if CHECKS_FAILED == 0:
        print("System is fully ready. Launch with: streamlit run dashboard/Home.py")
    else:
        print(f"{CHECKS_FAILED} check(s) failed -- see hints above, or just run: python run_pipeline.py --with-tests")
    print("=" * 60)

    sys.exit(0 if CHECKS_FAILED == 0 else 1)


if __name__ == "__main__":
    main()
