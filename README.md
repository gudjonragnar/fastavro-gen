# Avro scheme generation

This library aims to create dataclasses and/or typed dict definitions from avro schemes, that can be used to type check creation of messages using a static type checker such as mypy.

As the name suggests, it was thought of as an optional extension to use with the excellent [fastavro](github.com/fastavro/fastavro) library.
Fastavro allows users to read avro schemas, create messages and write them as avro messages, or validate against a schema.

Fastavro-gen uses fastavro to read `.avsc` files and from the schema object generated, creates classes. Classes are written one per file, using the namespace to create a directory structure.
For example, the following record output class will be created under `./example/avro/user.py`.
```json
{
    "namespace": "example.avro",
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "favorite_number",  "type": ["int", "null"]},
        {"name": "favorite_color", "type": ["string", "null"]}
    ]
}
```

## Output

The library offers the user two different output class types, `dataclass`es and `TypedDict`s.
Each has it's pros and cons that have to be weighed for the user's use cases.

### TypedDict
`TypedDict`s are only valuable during type checking, and on runtime they are simply treated as normal dicts. 
As such they can be built using common python dict syntax with an added type annotation, or using a class instantiation syntax:
```python
class A(TypedDict, total=True):
    field1: int
    field2: str
    ...

instance1: A = {
    "field1": 1,
    "field2": "2",
}

instance2 = A(
    field1=1,
    field2="2",
)
```
:heavy_plus_sign:Messages can be built using python dictionary syntax  
:heavy_plus_sign:Fastavro expects messages as dictionaries 
:heavy_minus_sign:All fields of the dictionary have to be given at the time of creation, unless the `total` option is given as `False`.
Having `total=False` however restricts some aspects of the type checking e.g. checking if some keys are set or not. 
Currently this library has the total option hardcoded as `False` but that might be configurable at a later time.  
:heavy_minus_sign:No ability to specify defaults.  

### dataclass
Dataclasses allow for easy declaration of python classes.

:heavy_plus_sign:Can handle default values for fields. As such only non-default fields have to be instantiated initially.  
:heavy_plus_sign:Easy to transform to dictionaries with the provided `dataclasses.asdict` function.  
:heavy_minus_sign:Complex nested schemas means a lot of objects being created  
:heavy_minus_sign:Extra overhead transforming messages to dictionaries 


## Usage

This is a work in progress and can't currently be installed. 

To generate classes use the CLI or import the `generate` function from `fastavro_gen`.

:bulb: When the ordered option is specified the file parameter will be ignored. Instead you can schemas specified in the file parameter as singletons in the toml file passed to ordered.

```
usage: fastavro_gen [-h] [-o ORDERED] [--class-type {dataclass,TypedDict}] [--no-black] [--prefix PREFIX] [file [file ...]]

Generate dataclasses or TypedDicts from avro schemas

positional arguments:
  file                  file(s) to parse, use '-' for stdin

optional arguments:
  -h, --help            show this help message and exit
  -o ORDERED, --ordered ORDERED
                        Path to a .toml file for multiple schemas or ordered schemas. Overwrites 'file' parameter.
  --class-type {dataclass,TypedDict}
  --no-black            Do not run output files through 'black'
  --prefix PREFIX       Removes this prefix from namespace if it is contained
```

### The `--ordered` option
The option allows users to specify an order of files to read throught fastavro's `load_schema_ordered` function.
This is useful when your files are laid out in a manner that does not follow the structure that the normal `load_schema` expects.

The option takes as value a path to a `.toml` file that describes what schemas to read and what their pre-requisites.
For example, creating classes for a schema A that depends on B and C your `.toml` would include:
```toml
schemaA = [
    "/path/to/C.avsc",
    "/path/to/B.avsc",
    "/path/to/A.avsc",
]
```
The toml file can describe multiple schema dependencies, each as their own list.

