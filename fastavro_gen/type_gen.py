import os
from fastavro import parse_schema
from fastavro.schema import load_schema
from typing import Dict, List, Optional, Set, Tuple, TypedDict, Union
from io import StringIO
import re
import shutil
import subprocess
from enum import Enum, auto


class OutputType(Enum):
    DATACLASS = auto
    TYPEDDICT = auto


class SimpleField(TypedDict):
    name: str
    type: str


class Record(TypedDict):
    name: str
    type: str
    doc: Optional[str]
    fields: List[SimpleField]


class AvroEnum(TypedDict):
    name: str
    type: str
    symbols: List[str]
    doc: Optional[str]


PRIMITIVE_TO_TYPE: Dict[str, str] = {
    "string": "str",
    "int": "int",
    "long": "int",
    "boolean": "bool",
    "float": "float",
    "double": "float",
}

PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def _name_to_filepath(name: str, *, joiner="/") -> Tuple[str, str]:
    _namesplit = name.split(".")
    path = joiner.join(_namesplit[:-1])
    filename = _to_snake_case(_namesplit[-1])
    return path, f"{filename}.py"


def _to_snake_case(s: str) -> str:
    return PATTERN.sub("_", s).lower()


def _write_imports(
    data: StringIO,
    typing_imports: Set[str],
    schema_imports: Set[str],
    *,
    extra: List[str] = [],
) -> None:
    """Extra should contain full import statements"""
    data.seek(0)
    if typing_imports:
        data.write(f"from typing import {', '.join(sorted(list(typing_imports)))}\n")
    for schema in schema_imports:
        path, fname = _name_to_filepath(schema, joiner=".")
        schema_name = schema.split(".")[-1]
        data.write(f"from {path}.{fname[:-3]} import {schema_name}\n")
    for e in extra:
        data.write(e)


def _parse_type(
    _type: Union[str, list, dict],
    typing_imports: Set[str],
    schema_imports: Set[str],
) -> str:
    # Union types
    if isinstance(_type, list):
        if len(_type) == 1:
            return _parse_type(_type[0], typing_imports, schema_imports)
        if len(_type) == 2 and _type[0] == "null":
            typing_imports.add("Optional")
            return f"Optional[{_parse_type(_type[1], typing_imports, schema_imports)}]"
        else:
            typing_imports.add("Union")
            return f"Union[{', '.join([_parse_type(t, typing_imports, schema_imports) for t in _type])}]"
    # Map, enum, record, array
    elif isinstance(_type, dict):
        return _parse_dict_type(_type, typing_imports, schema_imports)
    # String
    elif _type in PRIMITIVE_TO_TYPE:
        return PRIMITIVE_TO_TYPE[_type]
    # String, but a named schema
    elif isinstance(_type, str) and "." in _type:
        schema_imports.add(_type)
        return _type.split(".")[-1]
    else:
        raise Exception(f"Failed parsing type of {_type}")


def _parse_dict_type(
    _type: dict, typing_imports: Set[str], schema_imports: Set[str]
) -> str:
    if _type["type"] == "enum":
        return _parse_type(_type["name"], typing_imports, schema_imports)
    elif _type["type"] == "map":
        typing_imports.add("Dict")
        return (
            f"Dict[str, {_parse_type(_type['values'], typing_imports, schema_imports)}]"
        )
    elif _type["type"] == "array":
        typing_imports.add("List")
        return f"List[{_parse_type(_type['items'], typing_imports, schema_imports)}]"
    elif _type["type"] == "record":
        return _parse_type(_type["name"], typing_imports, schema_imports)
    elif _type["type"] in PRIMITIVE_TO_TYPE:
        return PRIMITIVE_TO_TYPE[_type["type"]]
    else:
        raise Exception(f"Failed parsing type {_type}")


def _extract_default(field: SimpleField, output_type: OutputType) -> Optional[str]:
    if output_type == OutputType.DATACLASS and "default" in field:
        if isinstance(field["default"], str):
            return f" = '{field['default']}'"
        elif isinstance(field["default"], list):
            return " = field(default_factory=list)"
        elif isinstance(field["default"], dict):
            return " = field(default_factory=dict)"
        else:
            return f" = {field['default']}"
    return None


def write_record(record: Record, base_dirs: Set[str], output_type: OutputType) -> None:
    data = StringIO()
    _typing: Set[str] = set()
    _schema_imports: Set[str] = set()
    extra: List[str] = []
    main_class: List[str] = []
    with_defaults: List[str] = []
    classname = record["name"].split(".")[-1]
    base = record["name"].split(".")[0]
    if output_type == OutputType.DATACLASS:
        extra.append("from dataclasses import dataclass, field\n")
        main_class.append("@dataclass\n")
        main_class.append(f"class {classname}:\n")
    elif output_type == OutputType.TYPEDDICT:
        _typing.add("TypedDict")
        main_class.append(f"class {classname}(TypedDict, total=False):\n")
    if "doc" in record:
        main_class.append(f"    \"\"\"{record['doc']}\"\"\"\n")
    for field in record["fields"]:
        t = _parse_type(field["type"], _typing, _schema_imports)
        default = _extract_default(field, output_type)
        if default:
            with_defaults.append(f"    {field['name']}: {t}{default}\n")
        else:
            main_class.append(f"    {field['name']}: {t}\n")
    _write_imports(data, _typing, _schema_imports, extra=extra)
    for line in main_class:
        data.write(line)
    for line in with_defaults:
        data.write(line)
    path, fname = _name_to_filepath(record["name"])
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, fname), "w+") as f:
        data.seek(0)
        shutil.copyfileobj(data, f)
    data.close()
    base_dirs.add(base)


def write_enum(enum: AvroEnum, base_dirs: Set[str]) -> None:
    data = StringIO()
    _typing: Set[str] = set(["Literal"])
    _schema_imports: Set[str] = set()
    main_class: List[str] = []
    classname = enum["name"].split(".")[-1]
    base = enum["name"].split(".")[0]
    if "doc" in enum:
        main_class.append(f"\"\"\"{enum['doc']}\"\"\"\n")
    symbols = [f"'{s}'" for s in enum["symbols"]]
    main_class.append(f"{classname} = Literal[{', '.join(symbols)}]")
    _write_imports(data, _typing, _schema_imports)
    for line in main_class:
        data.write(line)
    path, fname = _name_to_filepath(enum["name"])
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, fname), "w+") as f:
        data.seek(0)
        shutil.copyfileobj(data, f)
    data.close()
    base_dirs.add(base)


def add_init_files(base_dirs: Set[str]) -> None:
    print("Adding __init__ files...")
    for base in base_dirs:
        for root, _, _ in os.walk(base):
            if not os.path.exists(os.path.join(root, "__init__.py")):
                open(os.path.join(root, "__init__.py"), "w+").close()


def generate_types(
    schema: dict, output_type: OutputType, *, run_black: bool = True
) -> None:
    base_dirs: Set[str] = set()
    if "__named_schemas" in schema:
        for _, v in schema["__named_schemas"].items():
            if v["type"] == "record":
                write_record(v, base_dirs, output_type)
            elif v["type"] == "enum":
                write_enum(v, base_dirs)
            else:
                raise Exception(f"Cant write file for named schema of type {v['type']}")
    if schema["type"] == "record":
        write_record(Record(**schema), base_dirs, output_type)
    elif schema["type"] == "enum":
        write_enum(AvroEnum(**schema), base_dirs)
    else:
        raise Exception(f"Cant write file for schema of type {schema['type']}")
    add_init_files(base_dirs)
    if run_black and base_dirs:
        print("Blackening generated files...")
        for base in base_dirs:
            subprocess.call(["black", base])
