from typing import Literal, Union
from dataclasses import fields, is_dataclass

PRIMITIVES = {str, int, float, bool}


def fields_dict(cls):
    """Turn tuple of fields to dict"""
    return {f.name: f.type for f in fields(cls)}


def fromdict(cls, record):
    """Transform a dictionary to dataclass cls"""
    _fields = fields_dict(cls)
    return cls(**{k: _handle_type(_fields[k], v) for k, v in record.items()})


def _handle_type(_type, val):
    """Helper method to handle different types"""
    if not val:
        return val
    if _type in PRIMITIVES:
        return val
    try:
        if is_dataclass(_type):
            return fromdict(_type, val)
        if _type.__origin__ == Literal:
            return val
        if _type._name == "List":
            return [_handle_type(_type.__args__[0], v) for v in val]
        if _type._name == "Optional":
            return _handle_type(_type.__args__[0], val)
        if _type._name == "Dict":
            return {k: _handle_type(_type.__args__[1], v) for k, v in val.items()}
        if _type.__origin__ == Union:
            for t in _type.__args__:
                try:
                    return _handle_type(t, val)
                except:
                    pass

    except:
        raise Exception("Failed parsing value {} with type {}".format(val, _type))
