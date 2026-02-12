"""Tests for the CLI."""

from __future__ import annotations

import json
import tempfile

from bifrost_eval.cli import main


class TestCLI:
    def test_version(self) -> None:
        assert main(["--version"]) == 0

    def test_no_args(self) -> None:
        assert main([]) == 0

    def test_run_without_executor(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"name": "test", "scenarios": []}, f)
            f.flush()
            result = main(["run", f.name])
        assert result == 1

    def test_validate_valid_suite(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(
                {
                    "name": "test-suite",
                    "scenarios": [
                        {"name": "s1", "input_data": {"q": "hi"}},
                    ],
                },
                f,
            )
            f.flush()
            result = main(["validate", f.name])
        assert result == 0

    def test_validate_invalid_json(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("not json")
            f.flush()
            result = main(["validate", f.name])
        assert result == 1

    def test_validate_missing_file(self) -> None:
        result = main(["validate", "/nonexistent/file.json"])
        assert result == 1

    def test_validate_invalid_schema(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"scenarios": "not a list"}, f)
            f.flush()
            result = main(["validate", f.name])
        assert result == 1
