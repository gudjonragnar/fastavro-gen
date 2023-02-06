from argparse import ArgumentParser
from typing import Dict, List, cast
from fastavro_gen.models import OutputType
from fastavro_gen.type_gen import read_schemas_and_generate_classes
import toml


def main() -> None:
    parser = ArgumentParser(
        description="Generate dataclasses or TypedDicts from avro schemas"
    )
    parser.add_argument("file", help="file(s) to parse, use '-' for stdin", nargs="*")
    # TODO: Better name and description for this
    parser.add_argument(
        "-o",
        "--ordered",
        dest="ordered",
        help="Path to a .toml file for multiple schemas or ordered schemas. Overwrites 'file' parameter.",
        default=None,
    )
    parser.add_argument(
        "--class-type",
        dest="classtype",
        choices=["dataclass", "TypedDict"],
        default="dataclass",
    )
    parser.add_argument(
        "--no-black",
        dest="black",
        help="Do not run output files through 'black'",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--prefix",
        help="Removes this prefix from namespace if it is contained",
        type=str,
        default="",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="Specify the output location",
        type=str,
        default=".",
    )

    args = parser.parse_args()
    schemas_to_parse: Dict[str, List[str]]
    if args.ordered:
        schemas_to_parse = cast(Dict[str, List[str]], toml.load(args.ordered))
    else:
        schemas_to_parse = {}
        for f in args.file:
            schemas_to_parse[f.split("/")[-1]] = [f]
    read_schemas_and_generate_classes(
        schemas_to_parse,
        OutputType(args.classtype),
        run_black=(not args.black),
        namespace_prefix=args.prefix,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
