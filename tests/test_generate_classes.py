import pytest
from fastavro_gen.models import OutputType
from fastavro_gen.type_gen import generate_classes, read_schemas_and_generate_classes
import os
import sys
from contextlib import contextmanager


@contextmanager
def temp_sys_path(path):
    try:
        sys.path.append(path)
        yield
    finally:
        sys.path.remove(path)


@pytest.mark.parametrize("output_type", [e for e in OutputType])
def test_generate_schema_classes(output_type, tmp_path):
    read_schemas_and_generate_classes(
        {"weather schema": ["./resources/weather.avsc"]},
        output_type,
        output_dir=str(tmp_path),
    )

    assert os.path.exists(str(tmp_path / "my/test/weather.py"))
    with temp_sys_path(str(tmp_path)):
        from my.test.weather import Weather
