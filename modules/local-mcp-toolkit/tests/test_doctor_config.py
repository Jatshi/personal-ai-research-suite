from src.cli import doctor_config
from src.config.config_loader import load_config


def test_doctor_config_default_passes():
    report = doctor_config(load_config())
    assert report["success"] is True
    assert report["errors"] == []


def test_doctor_config_local_project_template_passes():
    report = doctor_config(load_config("config.local_project.example.yaml"))
    assert report["success"] is True
    assert report["rag_backend"] == "local_project"
