import pytest
from fastavro_gen.models import OutputType
from fastavro_gen.type_gen import read_schemas_and_generate_classes
import os
import sys
from contextlib import contextmanager
from tests.utils import roundtrip


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


def test_weather_roundtrip(tmp_path):
    read_schemas_and_generate_classes(
        {"weather schema": ["./resources/weather.avsc"]},
        OutputType.DATACLASS,
        output_dir=str(tmp_path),
    )

    assert os.path.exists(str(tmp_path / "my/test/weather.py"))
    with temp_sys_path(str(tmp_path)):
        from my.test.weather import Weather
        from my.test.record import Record

        record = Weather(
            station="weather station A",
            time=1000,
            temp=37,
            optional="not None",
            union=3.0,
            array=["this", "is", "an", "array"],
            map={"key": "value", "another key": "another value"},
            enum="EnumA",
            record=Record(Field1="only field"),
            circle={"key":  'Weather'}
        )
        assert record == roundtrip(record)
