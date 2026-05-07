from scripts.export_tensorrt import main
from tests.conftest import TMP


def test_export_cli_reports_missing_model(capsys):
    cfg = TMP / "export-missing-config.yaml"
    cfg.write_text(
        """
model:
  pt_path: missing.pt
  engine_path: missing.engine
camera:
  width: 1920
  height: 1080
""",
        encoding="utf-8",
    )
    assert main(["--config", str(cfg)]) != 0
    assert "model file not found" in capsys.readouterr().err
