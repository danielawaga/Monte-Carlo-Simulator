from pathlib import Path

from openpyxl import load_workbook

from monte_carlo_simulator.io import create_risk_register_template


def test_template_contains_documentation_and_excel_validations(tmp_path: Path) -> None:
    path = create_risk_register_template(tmp_path / "template.xlsx")

    workbook = load_workbook(path)
    try:
        assert workbook.sheetnames == ["metadata", "risk_register", "instructions"]
        assert workbook["metadata"]["B2"].value == "1.0"
        assert workbook["risk_register"].freeze_panes == "A2"
        assert workbook["risk_register"].auto_filter.ref == "A1:N7"
        assert len(workbook["risk_register"].data_validations.dataValidation) == 2
        instructions = workbook["instructions"]
        assert any(
            "Never commit real client" in str(cell.value)
            for row in instructions.iter_rows()
            for cell in row
        )
    finally:
        workbook.close()
