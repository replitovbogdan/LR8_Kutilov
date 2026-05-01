# test_container.py
# Автоматизированное модульное тестирование контейнера обработки файлов

import pytest
import os
import json
import pandas as pd
import sys
from datetime import datetime

# Добавляем путь к папке tasks/utils для импорта processor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tasks'))

from processor import DataStorage, create_test_files, process_files

# Фикстуры для подготовки тестовой среды

@pytest.fixture
def storage():
    return DataStorage()

@pytest.fixture
def setup_test_files():
    create_test_files()
    yield
    test_files = ["data.json", "report.json", "config.json", "data.csv", "backup.csv"]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)

# Тесты для метода load_file

class TestLoadFile:

    def test_load_json_success(self, storage, setup_test_files):
        result = storage.load_file("data.json")
        assert result is not None
        assert "name" in result
        last_record = storage.processed_files[-1]
        assert last_record["filename"] == "data.json"
        assert last_record["format"] == "JSON"
        assert last_record["status"] == "success"
        assert last_record["error"] == ""
        assert last_record["load_time"] < 0.1

    def test_load_csv_success(self, storage, setup_test_files):
        result = storage.load_file("data.csv")
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        last_record = storage.processed_files[-1]
        assert last_record["filename"] == "data.csv"
        assert last_record["format"] == "CSV"
        assert last_record["status"] == "success"
        assert last_record["error"] == ""
        assert last_record["load_time"] < 0.1

    def test_load_unknown_format(self, storage):
        with open("test.xyz", "w") as f:
            f.write("test content")
        result = storage.load_file("test.xyz")
        assert result is not None
        assert result["file"] == "test.xyz"
        last_record = storage.processed_files[-1]
        assert last_record["filename"] == "test.xyz"
        assert last_record["format"] == "unknown"
        assert last_record["status"] == "failed"
        os.remove("test.xyz")

    def test_load_missing_file(self, storage):
        result = storage.load_file("nonexistent.file")
        assert result is not None
        assert result["file"] == "nonexistent.file"
        last_record = storage.processed_files[-1]
        assert last_record["status"] == "failed"
        assert "File not found" in last_record["error"] or "No such file" in last_record["error"]

# Тесты для функции process_files

class TestProcessFiles:

    def test_process_multiple_files(self, storage, setup_test_files):
        file_list = ["data.json", "data.csv"]
        results = process_files(file_list)
        assert len(results) == 2
        assert results[0]["filename"] == "data.json"
        assert results[1]["filename"] == "data.csv"

    def test_process_mixed_formats(self, storage):
        with open("valid.json", "w") as f:
            json.dump({"test": 123}, f)
        with open("invalid.xyz", "w") as f:
            f.write("invalid")
        file_list = ["valid.json", "invalid.xyz"]
        results = process_files(file_list)
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "failed"
        os.remove("valid.json")
        os.remove("invalid.xyz")

# Тесты для модуля логирования

class TestLogging:

    def test_logging_accumulates_records(self, storage, setup_test_files):
        storage.load_file("data.json")
        storage.load_file("data.csv")
        assert len(storage.processed_files) == 2
        assert storage.processed_files[0]["filename"] == "data.json"
        assert storage.processed_files[1]["filename"] == "data.csv"

    def test_logging_fields_completeness(self, storage):
        with open("test_complete.json", "w") as f:
            json.dump({"key": "value"}, f)
        storage.load_file("test_complete.json")
        last_record = storage.processed_files[-1]
        assert "filename" in last_record
        assert "format" in last_record
        assert "load_time" in last_record
        assert "status" in last_record
        assert "error" in last_record
        os.remove("test_complete.json")

    def test_logging_error_message(self, storage):
        storage.load_file("nonexistent_file.log")
        last_record = storage.processed_files[-1]
        assert last_record["status"] == "failed"
        assert last_record["error"] != ""

# Тесты производительности

class TestPerformance:

    def test_json_load_time_under_100ms(self, storage, setup_test_files):
        start = datetime.now()
        storage.load_file("data.json")
        end = datetime.now()
        elapsed_ms = (end - start).total_seconds() * 1000
        assert elapsed_ms < 100

    def test_csv_load_time_under_100ms(self, storage, setup_test_files):
        start = datetime.now()
        storage.load_file("data.csv")
        end = datetime.now()
        elapsed_ms = (end - start).total_seconds() * 1000
        assert elapsed_ms < 100

    def test_unknown_format_load_time_under_2sec(self, storage):
        with open("test_perf.xyz", "w") as f:
            f.write("x" * 10000)
        start = datetime.now()
        storage.load_file("test_perf.xyz")
        end = datetime.now()
        elapsed_sec = (end - start).total_seconds()
        assert elapsed_sec < 2
        os.remove("test_perf.xyz")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])