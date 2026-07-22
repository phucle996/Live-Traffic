# ==============================================================================
# MLOps Lifecycle Unit Tests (tests/mlops/test_mlops_lifecycle.py)
# Tests: ExperimentTracker, ModelRegistry, ModelValidator, ModelPromoter,
#        DriftDetector, RollbackEngine, RetrainingPolicy
# ==============================================================================

import shutil
from pathlib import Path

from src.common.config import PROJECT_ROOT
from src.mlops.experiment_tracker import ExperimentTracker
from src.mlops.model_registry import ModelRegistry, REGISTRY_FILE
from src.mlops.model_validator import ModelValidator
from src.mlops.model_promoter import ModelPromoter
from src.mlops.drift_detector import DriftDetector
from src.mlops.rollback import RollbackEngine
from src.mlops.retraining_policy import RetrainingPolicy


def _clean_registry():
    """Removes registry and experiment files to ensure clean test state."""
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()
    exp_dir = PROJECT_ROOT / "artifacts" / "mlops" / "experiments"
    if exp_dir.exists():
        shutil.rmtree(exp_dir)


def test_experiment_tracker():
    """
    Tests ExperimentTracker logs params, metrics, artifacts, and persists run file.
    """
    tracker = ExperimentTracker("test_gbt_experiment")
    tracker.log_params({"maxDepth": 5, "maxIter": 20})
    tracker.log_metrics({"rmse": 7.2, "r2": 0.72, "test_rows": 1500})
    tracker.log_artifact("model_path", "artifacts/model/gbt_model")
    run_id = tracker.finish()

    run_file = PROJECT_ROOT / "artifacts" / "mlops" / "experiments" / f"{run_id}.json"
    assert run_file.exists(), "Experiment run JSON not persisted to disk"
    print(f"  ExperimentTracker: run_id={run_id} persisted OK")


def test_model_registry_register_and_query():
    """
    Tests ModelRegistry registers a version and retrieves production pointer.
    """
    _clean_registry()
    registry = ModelRegistry()
    registry.register(
        version="v1.0.0",
        run_id="abc12345",
        artifact_path="artifacts/model/gbt_model",
        metrics={"rmse": 7.2, "r2": 0.72},
        stage="Candidate",
    )

    versions = registry.get_all_versions()
    assert len(versions) == 1
    assert versions[0]["version"] == "v1.0.0"
    assert versions[0]["stage"] == "Candidate"
    print("  ModelRegistry: Register and query OK")


def test_model_validator_pass_and_fail():
    """
    Tests ModelValidator passes good metrics and fails bad metrics.
    """
    validator = ModelValidator()

    # Good candidate — should pass
    passed, reasons = validator.validate({"rmse": 7.0, "r2": 0.70, "test_rows": 2000})
    assert passed, f"Expected PASS but got FAIL: {reasons}"

    # Bad candidate — RMSE too high
    passed, reasons = validator.validate({"rmse": 12.0, "r2": 0.30, "test_rows": 500})
    assert not passed, "Expected FAIL but got PASS"
    assert len(reasons) > 0
    print("  ModelValidator: PASS/FAIL gate logic OK")


def test_model_promoter_full_lifecycle():
    """
    Tests full promote-to-staging then promote-to-production lifecycle.
    Also tests that prior Production version is archived on new promotion.
    """
    _clean_registry()
    registry = ModelRegistry()
    promoter = ModelPromoter()

    # Register v1.0.0 as Candidate
    registry.register(
        version="v1.0.0",
        run_id="aaa11111",
        artifact_path="artifacts/model/gbt_v1",
        metrics={"rmse": 7.2, "r2": 0.72, "test_rows": 1500},
    )

    # Promote to Staging then Production
    ok = promoter.promote_to_staging("v1.0.0", {"rmse": 7.2, "r2": 0.72, "test_rows": 1500})
    assert ok
    promoter.promote_to_production("v1.0.0")
    prod = registry.get_production_version()
    assert prod["version"] == "v1.0.0"

    # Register v1.1.0 and promote to Production — v1.0.0 must be archived
    registry.register(
        version="v1.1.0",
        run_id="bbb22222",
        artifact_path="artifacts/model/gbt_v2",
        metrics={"rmse": 6.5, "r2": 0.78, "test_rows": 2000},
    )
    promoter.promote_to_staging("v1.1.0", {"rmse": 6.5, "r2": 0.78, "test_rows": 2000})
    promoter.promote_to_production("v1.1.0")

    all_v = registry.get_all_versions()
    stages = {v["version"]: v["stage"] for v in all_v}
    assert stages["v1.0.0"] == "Archived", "v1.0.0 should be Archived"
    assert stages["v1.1.0"] == "Production", "v1.1.0 should be Production"
    print("  ModelPromoter: Full lifecycle and archive logic OK")


def test_drift_detector():
    """
    Tests DriftDetector KS-test and prediction drift analysis.
    """
    detector = DriftDetector()

    baseline = [30.0, 35.0, 40.0, 45.0, 50.0] * 20  # 100 values
    # Use identical distribution so KS stat is 0.0 — definitively no drift
    live_identical = list(baseline)

    # Should NOT detect drift with identical distribution
    drift_detected, ks = detector.detect_feature_drift(baseline, live_identical)
    assert not drift_detected, f"Unexpected drift detected. KS={ks}"

    # Build a strongly shifted live distribution to trigger drift
    live_shifted = [10.0, 11.0, 12.0, 13.0, 14.0] * 20  # Very different from baseline
    drift_detected, ks = detector.detect_feature_drift(baseline, live_shifted)
    assert drift_detected, f"Expected drift not detected. KS={ks}"

    # Test prediction drift
    base_pred = [35.0] * 50
    live_pred = [35.0] * 50  # Same distribution — no drift
    drift_detected, stats = detector.detect_prediction_drift(base_pred, live_pred)
    assert not drift_detected
    print("  DriftDetector: Feature drift and prediction drift OK")


def test_rollback_engine():
    """
    Tests RollbackEngine reverts Production to the previous Archived version.
    """
    _clean_registry()
    registry = ModelRegistry()
    promoter = ModelPromoter()

    # Register and promote v1.0.0 then v1.1.0 (v1.0.0 becomes archived)
    for ver, rmse in [("v1.0.0", 7.2), ("v1.1.0", 6.5)]:
        registry.register(
            version=ver,
            run_id=f"run_{ver}",
            artifact_path=f"artifacts/model/{ver}",
            metrics={"rmse": rmse, "r2": 0.72, "test_rows": 1500},
        )
        promoter.promote_to_staging(ver, {"rmse": rmse, "r2": 0.72, "test_rows": 1500})
        promoter.promote_to_production(ver)

    # v1.1.0 is now production, v1.0.0 is archived — rollback should restore v1.0.0
    rollback_engine = RollbackEngine()
    rolled_back_version = rollback_engine.rollback()
    assert rolled_back_version == "v1.0.0", f"Expected v1.0.0, got {rolled_back_version}"

    prod = registry.get_production_version()
    assert prod["version"] == "v1.0.0"
    print("  RollbackEngine: Rollback to previous archived version OK")


def test_retraining_policy():
    """
    Tests RetrainingPolicy triggers correctly based on drift count and data volume.
    """
    policy = RetrainingPolicy()

    # Should NOT retrain — drift count too low
    assert not policy.should_retrain(1, 6000)

    # Should NOT retrain — not enough new data
    assert not policy.should_retrain(5, 100)

    # Should retrain — drift persisted AND sufficient new data
    assert policy.should_retrain(5, 6000)
    print("  RetrainingPolicy: Retraining decision logic OK")


if __name__ == "__main__":
    test_experiment_tracker()
    test_model_registry_register_and_query()
    test_model_validator_pass_and_fail()
    test_model_promoter_full_lifecycle()
    test_drift_detector()
    test_rollback_engine()
    test_retraining_policy()
    print("\nAll test_mlops_lifecycle unit tests PASSED!")
