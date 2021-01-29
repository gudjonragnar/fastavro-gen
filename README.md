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
#### Pros
The main pros to the `TypedDict` route:
1. Messages can be built using python dictionary syntax
2. Fastavro expects messages as dictionaries

#### Cons

There are a couple of restrictions with this method:
1. All fields of the dictionary have to be given at the time of creation, unless the `total` option is given as `False`.
   Having `total=False` however restricts some aspects of the type checking e.g. checking if some keys are set or not. 
   Currently this library has the total option hardcoded as `False` but that might be configurable at a later time.
2. No ability to specify defaults.

### dataclass
Dataclasses allow for easy declaration of python classes.

#### Pros
The main pros to the `dataclass` route:
1. Can handle default values for fields. As such only non-default fields have to be instantiated initiallly.
2. Easy to transform to dictionaries with the provided `dataclasses.asdict` function.

#### Cons

1. Complex nested schemas means a lot of objects being created
2. Extra overhead transforming messages to dictionaries
