from fastavro import parse_schema
from fastavro.schema import load_schema
from typing import List, Optional, TypedDict, Union
from io import StringIO


class SimpleField(TypedDict):
    name: str
    type: str


class Record(TypedDict):
    name: str
    type: str
    doc: Optional[str]
    fields: List[SimpleField]


def _parse_type(_type: Union[str, List[str]]) -> str:
    if _type == "string":
        return "str"
    elif _type == "int" or _type == "long":
        return "int"
    elif _type == "boolean":
        return "bool"
    elif _type == "float" or _type == "double":
        return "float"
    elif isinstance(_type, list):
        if len(_type) == 2 and _type[0] == "null":
            return f"Optional[{_parse_type(_type[1])}]"
        else:
            return f"Union[{', '.join([_parse_type(t) for t in _type])}]"
    else:
        raise Exception(f"Failed parsing type of {_type}")


def write_record_as_typed_dict(record: Record) -> StringIO:
    data = StringIO()
    classname = record["name"].split(".")[-1].capitalize()
    data.write(f"class {classname}(TypedDict, total=False):\n")
    if "doc" in record:
        data.write(f"    \"\"\"{record['doc']}\"\"\"\n")
    for field in record["fields"]:
        t = _parse_type(field["type"])
        data.write(f"    {field['name']}: {t}\n")
    print(data.getvalue())
    data.close()
    return data


if __name__ == "__main__":
    schema = {
        "doc": "A weather reading.",
        "name": "Weather",
        "namespace": "test",
        "type": "record",
        "fields": [
            {"name": "station", "type": "string"},
            {"name": "time", "type": "long"},
            {"name": "temp", "type": "int"},
        ],
    }
    parsed_schema: Record = parse_schema(schema)  # type: ignore
    write_record_as_typed_dict(parsed_schema)
    parsed_from_file: Record = load_schema("resources/weather.avsc")  # type: ignore
    write_record_as_typed_dict(parsed_from_file)
