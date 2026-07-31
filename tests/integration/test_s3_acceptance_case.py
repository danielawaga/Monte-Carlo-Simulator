from pathlib import Path

from scripts.run_s3_acceptance_case import REQUIRED_ARTIFACTS, run_acceptance_case


def test_s3_acceptance_case_writes_passing_evidence_report(tmp_path: Path) -> None:
    report_path = run_acceptance_case(tmp_path, simulations=600, seed=42)

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "Overall status: PASS" in report
    assert "Synthetic and explicitly non-representative data" in report
    assert "strict-no-repair" in report
    assert "Credibility of real assumptions still requires" in report

    for artifact_name in REQUIRED_ARTIFACTS:
        assert (tmp_path / "artifacts" / artifact_name).exists()
