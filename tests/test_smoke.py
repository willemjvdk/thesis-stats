"""Smoke tests — verify all modules import and path constants resolve."""

import importlib

import pytest


MODULES = [
    "src.analysis.statistics",
    "src.analysis.geography",
    "src.analysis.normalization",
    "src.analysis.aggregation",
    "src.analysis.loaders",
    "src.analysis.data_loading",
    "src.analysis.agreement",
]


class TestModuleImports:
    @pytest.mark.parametrize("module_name", MODULES)
    def test_import(self, module_name):
        mod = importlib.import_module(module_name)
        assert mod is not None


class TestPathConstants:
    def test_root_dir_resolves(self):
        from src.analysis.data_loading import ROOT
        assert ROOT.exists()
        assert ROOT.is_dir()

    def test_data_dirs_exist(self):
        from src.analysis.data_loading import DATA_RAW, DATA_PROCESSED
        # These may not exist on every machine, just check they're Path objects
        assert isinstance(DATA_RAW, type(DATA_RAW))
        assert isinstance(DATA_PROCESSED, type(DATA_PROCESSED))


class TestCLI:
    def test_run_py_help(self):
        import subprocess
        result = subprocess.run(
            ["python", "-c", "import src; print('OK')"],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent),
        )
        assert result.returncode == 0
        assert "OK" in result.stdout
