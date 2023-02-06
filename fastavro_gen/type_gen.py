from fastavro.schema import load_schema, load_schema_ordered
import os
from typing import Dict, List, Optional, Set, Tuple, Union, cast
from io import StringIO
import re
import shutil
import subprocess
from copy import deepcopy
from fastavro_gen.models import OutputType, SimpleField, Record, AvroEnum, Collector


PRIMITIVE_TO_TYPE: Dict[str, str] = {
    "string": "str",
    "int": "int",
    "long": "int",
    "boolean": "bool",
    "float": "float",
    "double": "float",
    "null": "None",
}

PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def _name_to_filepath(name: str, *, joiner="/") -> Tuple[str, str]:
    _namesplit = name.split(".")
    path = joiner.join(_namesplit[:-1])
    filename = _to_snake_case(_namesplit[-1])
    return path, f"{filename}.py"


def _to_snake_case(s: str) -> str:
    return PATTERN.sub("_", s).lower()


def _remove_prefix(name: str, namespace_prefix: str):
    if name.startswith(namespace_prefix):
        return name[len(namespace_prefix) :]
    return name


def _write_imports(
    data: StringIO,
    collector: Collector,
) -> None:
    """Extra should contain full import statements"""
    data.seek(0)
    if collector.typing:
        data.write(f"from typing import {', '.join(sorted(list(collector.typing)))}\n")
    if collector.dataclass:
        data.write(
            f"from dataclasses import {', '.join(sorted(list(collector.dataclass)))}\n"
        )
    for schema in collector.schemas:
        path, fname = _name_to_filepath(schema, joiner=".")
        schema_name = schema.split(".")[-1]
        data.write(f"from {path}.{fname[:-3]} import {schema_name}\n")


def _parse_type(
    _type: Union[str, list, dict],
    collector: Collector,
    namespace_prefix: str = "",
) -> str:
    # Union types
    if isinstance(_type, list):
        if len(_type) == 1:
            return _parse_type(_type[0], collector, namespace_prefix=namespace_prefix)
        if len(_type) == 2 and "null" in _type:
            _other = [i for i in _type if i != "null"]
            collector.typing.add("Optional")
            return f"Optional[{_parse_type(_other[0], collector, namespace_prefix=namespace_prefix)}]"

        else:
            collector.typing.add("Union")
            return f"Union[{', '.join([_parse_type(t, collector, namespace_prefix=namespace_prefix) for t in _type])}]"
    # Map, enum, record, array
    elif isinstance(_type, dict):
        return _parse_dict_type(_type, collector, namespace_prefix=namespace_prefix)
    # String
    elif _type in PRIMITIVE_TO_TYPE:
        return PRIMITIVE_TO_TYPE[_type]
    # String, but a named schema
    elif isinstance(_type, str) and "." in _type:
        collector.schemas.add(_remove_prefix(_type, namespace_prefix))
        return _type.split(".")[-1]
    else:
        raise Exception(f"Failed parsing type of {_type}")


def _parse_dict_type(
    _type: dict,
    collector: Collector,
    *,
    namespace_prefix: str = "",
) -> str:
    if _type["type"] == "enum":
        return _parse_type(_type["name"], collector, namespace_prefix=namespace_prefix)
    elif _type["type"] == "map":
        collector.typing.add("Dict")
        return f"Dict[str, {_parse_type(_type['values'], collector, namespace_prefix=namespace_prefix)}]"
    elif _type["type"] == "array":
        collector.typing.add("List")
        return f"List[{_parse_type(_type['items'], collector, namespace_prefix=namespace_prefix)}]"
    elif _type["type"] == "record":
        return _parse_type(_type["name"], collector, namespace_prefix=namespace_prefix)
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


def write_file(collector: Collector, output_dir: str = "."):
    data = StringIO()
    _write_imports(data, collector)
    for line in collector.lines:
        data.write(line)
    for line in collector.lines_with_default:
        data.write(line)
    path, fname = _name_to_filepath(collector.record["name"])
    path = f"{output_dir}/{path}"
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, fname), "w+") as f:
        data.seek(0)
        shutil.copyfileobj(data, f)
    data.close()


def write_record(
    record: Record,
    base_dirs: Set[str],
    output_type: OutputType,
    *,
    namespace_prefix: str = "",
    output_dir: str = ".",
) -> None:
    record["name"] = _remove_prefix(record["name"], namespace_prefix)
    collector = Collector(record)
    classname = record["name"].split(".")[-1]
    base = record["name"].split(".")[0]
    if output_type == OutputType.DATACLASS:
        collector.dataclass.add("dataclass")
        collector.lines.append("@dataclass\n")
        collector.lines.append(f"class {classname}:\n")
    elif output_type == OutputType.TYPEDDICT:
        collector.typing.add("TypedDict")
        collector.lines.append(f"class {classname}(TypedDict, total=False):\n")
    if "doc" in record:
        collector.lines.append(f"    \"\"\"{record['doc']}\"\"\"\n")
    for field in record["fields"]:
        t = _parse_type(field["type"], collector, namespace_prefix=namespace_prefix)

        # search for direct cycle imports and change them in literal strigs
        t_search = re.search(r"(\[(?:\[??[^\[]*?\]))", t)
        if t_search:
            t_list = [
                x.replace(" ", "")
                for x in t_search.group(1).replace("[", "").replace("]", "").split(",")
            ]
            if classname in t_list:
                t = t.replace(classname, f"'{classname}'")
                collector.schemas.remove(record["name"])

        default = _extract_default(field, output_type)
        if default:
            if "field" in default:
                collector.dataclass.add("field")
            collector.lines_with_default.append(f"    {field['name']}: {t}{default}\n")
        else:
            collector.lines.append(f"    {field['name']}: {t}\n")
    write_file(collector, output_dir=output_dir)
    base_dirs.add(base)


def write_enum(
    enum: AvroEnum,
    base_dirs: Set[str],
    *,
    namespace_prefix: str = "",
    output_dir: str = ".",
) -> None:
    enum["name"] = _remove_prefix(enum["name"], namespace_prefix)
    collector = Collector(record=enum)
    collector.typing.add("Literal")
    classname = enum["name"].split(".")[-1]
    base = enum["name"].split(".")[0]
    if "doc" in enum:
        collector.lines.append(f"\"\"\"{enum['doc']}\"\"\"\n")
    symbols = [f"'{s}'" for s in enum["symbols"]]
    collector.lines.append(f"{classname} = Literal[{', '.join(symbols)}]")
    write_file(collector, output_dir=output_dir)
    base_dirs.add(base)


def add_init_files(base_dirs: Set[str]) -> None:
    print("Adding __init__ files...")
    for base in base_dirs:
        for root, _, _ in os.walk(base):
            if not os.path.exists(os.path.join(root, "__init__.py")):
                open(os.path.join(root, "__init__.py"), "w+").close()


def write_schema(
    schema: dict,
    base_dirs: Set[str],
    output_type: OutputType,
    *,
    namespace_prefix: str = "",
    output_dir: str = ".",
) -> None:
    _schema = deepcopy(schema)
    if _schema["type"] == "record":
        write_record(
            cast(Record, _schema),
            base_dirs,
            output_type,
            namespace_prefix=namespace_prefix,
            output_dir=output_dir,
        )
    elif _schema["type"] == "enum":
        write_enum(
            cast(AvroEnum, _schema),
            base_dirs,
            namespace_prefix=namespace_prefix,
            output_dir=output_dir,
        )
    else:
        raise Exception(f"Cant write file for schema of type {_schema['type']}")


def generate_classes(
    schema: dict,
    output_type: OutputType,
    *,
    run_black: bool = True,
    namespace_prefix: str = "",
    output_dir: str = ".",
) -> None:
    base_dirs: Set[str] = set()
    if "__named_schemas" in schema:
        for _, named_schema in schema["__named_schemas"].items():
            write_schema(
                named_schema,
                base_dirs,
                output_type,
                namespace_prefix=namespace_prefix,
                output_dir=output_dir,
            )
    write_schema(
        schema,
        base_dirs,
        output_type,
        namespace_prefix=namespace_prefix,
        output_dir=output_dir,
    )
    extended_base_dirs = set([f"{output_dir}/{b}" for b in base_dirs])
    add_init_files(extended_base_dirs)
    if run_black and extended_base_dirs:
        print("Blackening generated files...")
        for base in extended_base_dirs:
            subprocess.call(["black", base])


def read_schemas_and_generate_classes(
    schema_files: Dict[str, List[str]],
    output_type: OutputType,
    *,
    run_black: bool = True,
    namespace_prefix: str = "",
    output_dir: str = ".",
) -> None:
    for name, files in schema_files.items():
        print(f"Parsing schema/s for {name}")
        if len(files) == 1:
            schema = load_schema(files[0])
        else:
            schema = load_schema_ordered(files)
        print(f"Generate {output_type.value}s...")
        generate_classes(
            schema,
            output_type,
            run_black=run_black,
            namespace_prefix=namespace_prefix,
            output_dir=output_dir,
        )
